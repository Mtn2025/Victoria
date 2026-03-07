"""
Telnyx Client (Infrastructure Adapter).
Part of the Infrastructure Layer (Hexagonal Architecture).

Implements TelephonyPort for Telnyx Call Control API.

MIGRATED (Sprint Limpieza — Marzo 2026):
  - 100% SDK oficial telnyx 4.x (AsyncClient)
  - Eliminado httpx crudo, _post() helper y _http AsyncClient
  - command_id en todos los comandos (idempotencia garantizada)
  - Codec L16 / PCMU configurable en start_streaming()
  - gather_using_ai() y gather_stop() nativos del SDK

References:
  - telnyx_call_architecture.md §6 — Reglas de Producción
  - sprint4_reference.md — B-05, B-08, B-09, B-10
"""
import base64
import json
import logging
import uuid
from typing import Optional

import telnyx
from telnyx import AsyncClient
from telnyx import APIError, APITimeoutError, APIConnectionError

from backend.infrastructure.config.settings import settings
from backend.domain.ports.telephony_port import TelephonyPort
from backend.domain.value_objects.call_id import CallId
from backend.domain.value_objects.phone_number import PhoneNumber

logger = logging.getLogger(__name__)


class TelnyxClient(TelephonyPort):
    """
    Official Telnyx SDK client for Call Control API.

    Uses telnyx.AsyncClient (SDK 4.x) exclusively — no raw httpx.
    All action commands include a `command_id` for idempotency.

    Lifecycle:
        client = TelnyxClient()
        ...
        await client.close()   # on server shutdown
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TELNYX_API_KEY
        self.base_url = settings.TELNYX_API_BASE

        if not self.api_key:
            logger.warning("⚠️ [TelnyxClient] API Key not set. All calls will be skipped.")

        # Official async SDK client — manages connection pooling internally
        self._sdk = AsyncClient(
            api_key=self.api_key or "",
            base_url=self.base_url,
            timeout=10.0,
            max_retries=2,
        )

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the SDK client. Call on server shutdown."""
        await self._sdk.close()
        logger.info("✅ [TelnyxClient] SDK client closed")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _cid(self, prefix: str, call_id: str) -> str:
        """
        Generate unique command_id for idempotency.
        Format: {prefix}-{last8_of_call_id}-{random6hex}
        Telnyx deduplicates commands with same command_id within 60s.
        """
        short = (call_id or "unknown")[-8:].replace(":", "")
        return f"{prefix}-{short}-{uuid.uuid4().hex[:6]}"

    async def _run(self, coro, label: str):
        """Execute an SDK coroutine with unified error handling."""
        try:
            return await coro
        except APITimeoutError:
            logger.error(f"[TelnyxClient] ⏱️ Timeout: {label}")
        except APIConnectionError as exc:
            logger.error(f"[TelnyxClient] 🔌 Connection error: {label} — {exc}")
        except APIError as exc:
            if hasattr(exc, "status_code") and exc.status_code == 422:
                logger.info(f"[TelnyxClient] 422 Unprocessable (call ended?): {label}")
            else:
                logger.error(f"[TelnyxClient] ❌ API error: {label} — {exc}")
        except Exception as exc:
            logger.error(f"[TelnyxClient] ❌ Unexpected error: {label} — {exc}")
        return None

    # ── TelephonyPort — Core Commands ─────────────────────────────────────────

    async def answer_call(self, call_control_id: str) -> None:
        """Answer an incoming call."""
        if not self.api_key:
            return

        client_state = base64.b64encode(
            json.dumps({"call_control_id": call_control_id}).encode()
        ).decode()

        result = await self._run(
            self._sdk.calls.actions.answer(
                call_control_id,
                client_state=client_state,
                command_id=self._cid("ans", call_control_id),
            ),
            label=f"answer({call_control_id})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] Call answered: {call_control_id}")

    async def start_streaming(
        self,
        call_control_id: str,
        stream_url: str,
        client_state: Optional[str] = None,
        codec: str = "PCMU",
    ) -> None:
        """
        Start bidirectional media streaming.

        B-05 — Codec configurable:
          "PCMU"  → G.711 µ-law 8kHz (legacy telephony, default)
          "L16"   → PCM linear 16kHz (Voice AI, lower latency)

        To enable L16: set ConfigDTO.audio_codec = "L16" in agent config.
        telnyx_stream.py detects codec automatically from the 'start' event.
        """
        if not self.api_key:
            return

        sample_rate = 16000 if codec == "L16" else 8000
        extra: dict = {
            "stream_bidirectional_mode": "rtp",
            "stream_bidirectional_codec": codec,
            "stream_bidirectional_sampling_rate": sample_rate,
            "command_id": self._cid("str", call_control_id),
        }
        if client_state:
            extra["client_state"] = client_state

        result = await self._run(
            self._sdk.calls.actions.start_streaming(
                call_control_id,
                stream_url=stream_url,
                stream_track="both_tracks",
                **extra,
            ),
            label=f"start_streaming({call_control_id}, codec={codec})",
        )
        if result is not None:
            logger.info(
                f"☎️ [TelnyxClient] Streaming started: {call_control_id} "
                f"(codec={codec}, rate={sample_rate}Hz)"
            )
            # Activate Telnyx noise suppression (non-critical best-effort)
            await self.start_noise_suppression(call_control_id)

    async def start_noise_suppression(self, call_control_id: str) -> None:
        """
        Activate Telnyx native noise suppression.
        NOTE: Re-enable only with explicit config flag —
        Telnyx AGC was found to cause volume fluctuations (FASE 8).
        """
        try:
            await self._sdk.calls.actions.suppression_start(
                call_control_id, direction="both"
            )
        except Exception:
            pass  # Non-critical — failure is silent

    async def start_recording(
        self, call_control_id: str, channels: str = "dual",
        s3_destination: Optional[str] = None,
    ) -> None:
        """Start call recording in MP3 format.

        Args:
            channels:        'mono' or 'dual'
            s3_destination:  Optional S3 URL (s3://bucket/prefix/) for direct upload.
                             When set, Telnyx writes directly to S3 without intermediary.
        """
        if not self.api_key:
            return

        kwargs: dict = {
            "format": "mp3",
            "channels": channels,
            "play_beep": False,
            "command_id": self._cid("rec", call_control_id),
        }
        if s3_destination:
            kwargs["s3_destination"] = s3_destination

        result = await self._run(
            self._sdk.calls.actions.record_start(
                call_control_id,
                **kwargs,
            ),
            label=f"record_start({call_control_id}, s3={bool(s3_destination)})",
        )
        if result is not None:
            logger.info(
                f"☎️ [TelnyxClient] Recording started: {call_control_id} "
                f"[{channels}]{'  → S3' if s3_destination else ''}"
            )

    async def configure_hipaa(self, profile_id: Optional[str] = None) -> None:
        """
        P2: Habilita HIPAA compliance en la cuenta/perfil Telnyx.
        Llama a PUT /voice/settings para activar hipaa_mode.

        IMPORTANT: Este es un cambio a nivel de cuenta, no de llamada individual.
        Llama solo una vez cuando hipaaEnabledTelnyx cambia, no en cada llamada.

        Reference: Telnyx Voice Settings API
        """
        if not self.api_key:
            return

        try:
            # La API Telnyx de voz settings requiere httpx crudo porque
            # el SDK 4.x no tiene binding para este endpoint todavía.
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {"data": {"type": "voice_settings", "attributes": {"hipaa_mode": True}}}
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.put(
                    f"{self.base_url}/voice/settings",
                    headers=headers,
                    json=payload,
                    timeout=10.0,
                )
                if resp.status_code in (200, 201, 204):
                    logger.info(f"☎️ [TelnyxClient] 🔒 HIPAA mode enabled on account")
                else:
                    logger.warning(f"☎️ [TelnyxClient] HIPAA settings returned {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            logger.error(f"[TelnyxClient] configure_hipaa error: {exc}")

    async def end_call(self, call_id: CallId) -> None:
        """Hang up an active call (TelephonyPort interface)."""
        if not self.api_key:
            return

        cid = call_id.value
        result = await self._run(
            self._sdk.calls.actions.hangup(
                cid,
                command_id=self._cid("hup", cid),
            ),
            label=f"hangup({cid})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] Call hung up: {cid}")

    async def hangup_call(self, call_control_id: str) -> None:
        """
        Convenience hangup by raw call_control_id string.
        Used from webhook handlers that don't have a CallId VO.
        """
        if not self.api_key:
            return

        await self._run(
            self._sdk.calls.actions.hangup(
                call_control_id,
                command_id=self._cid("hup", call_control_id),
            ),
            label=f"hangup({call_control_id})",
        )

    async def transfer_call(self, call_id: CallId, target: PhoneNumber) -> None:
        """Transfer (REFER) call to another number."""
        if not self.api_key:
            return

        cid = call_id.value
        kwargs: dict = {
            "to": target.value,
            "command_id": self._cid("xfr", cid),
        }
        if hasattr(settings, "BASE_URL") and settings.BASE_URL:
            kwargs["webhook_url"] = (
                f"{settings.BASE_URL}/telephony/telnyx/call-control"
            )

        result = await self._run(
            self._sdk.calls.actions.transfer(cid, **kwargs),
            label=f"transfer({cid} → {target.value})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] Call transferred: {cid} → {target.value}")

    async def send_dtmf(self, call_id: CallId, digits: str) -> None:
        """Send DTMF tones on an active call."""
        if not self.api_key:
            return

        cid = call_id.value
        result = await self._run(
            self._sdk.calls.actions.send_dtmf(
                cid,
                digits=digits,
                command_id=self._cid("dtmf", cid),
            ),
            label=f"send_dtmf({cid}, {digits!r})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] DTMF sent: {cid} → {digits!r}")

    # ── Extended Commands ─────────────────────────────────────────────────────

    async def bridge_call(
        self, call_control_id: str, target_number: str, from_number: str
    ) -> None:
        """Transfer caller to a human agent."""
        if not self.api_key or not target_number:
            return

        result = await self._run(
            self._sdk.calls.actions.transfer(
                call_control_id,
                to=target_number,
                **{"from": from_number},
                command_id=self._cid("brd", call_control_id),
            ),
            label=f"bridge({call_control_id} → {target_number})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] Call bridged: {call_control_id} → {target_number}")

    async def start_forking(self, call_control_id: str, udp_target: str) -> None:
        """Fork RTP audio stream to an external UDP endpoint."""
        if not self.api_key or not udp_target:
            return

        ip, _, port_str = udp_target.rpartition(":")
        udp_uri = f"udp:{ip}:{port_str}" if ip else f"udp:{udp_target}"
        await self._run(
            self._sdk.calls.actions.fork_start(
                call_control_id,
                target=udp_uri,
                rx=udp_uri,
                tx=udp_uri,
            ),
            label=f"fork_start({call_control_id} → {udp_target})",
        )

    async def start_siprec(self, call_control_id: str, siprec_dest: str) -> None:
        """Start SIPREC compliance recording to an external recorder."""
        if not self.api_key or not siprec_dest:
            return

        await self._run(
            self._sdk.calls.actions.siprec_start(
                call_control_id,
                connector_name=siprec_dest,
            ),
            label=f"siprec_start({call_control_id})",
        )

    async def playback_start(
        self,
        call_control_id: str,
        audio_url: str,
        client_state: Optional[str] = None,
    ) -> None:
        """Play an audio file on the call."""
        if not self.api_key:
            return

        kwargs: dict = {
            "audio_url": audio_url,
            "command_id": self._cid("pb", call_control_id),
        }
        if client_state:
            kwargs["client_state"] = client_state

        result = await self._run(
            self._sdk.calls.actions.playback_start(call_control_id, **kwargs),
            label=f"playback_start({call_control_id})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] Playback started: {call_control_id}")

    # ── B-10: gather_using_ai ─────────────────────────────────────────────────

    async def gather_using_ai(
        self,
        call_control_id: str,
        greeting: str,
        parameters: dict,
        voice: Optional[str] = None,
    ) -> None:
        """
        Telnyx native AI-powered data gathering (Sep 2024).

        Sends a conversational prompt and collects structured data from
        the caller using a Telnyx-hosted LLM.

        Response arrives in the 'gather.ended' webhook:
            payload.parameters_result → dict of collected fields

        Args:
            greeting:    Opening message to the caller
            parameters:  JSON Schema defining fields to collect
            voice:       Optional TTS voice (e.g. "Polly.Lupe-Neural")

        Reference: sprint4_reference.md §B-10
        """
        if not self.api_key:
            return

        kwargs: dict = {
            "greeting": greeting,
            "parameters": parameters,
            "command_id": self._cid("gai", call_control_id),
        }
        if voice:
            kwargs["voice"] = voice

        result = await self._run(
            self._sdk.calls.actions.gather_using_ai(call_control_id, **kwargs),
            label=f"gather_using_ai({call_control_id})",
        )
        if result is not None:
            logger.info(f"☎️ [TelnyxClient] gather_using_ai started: {call_control_id}")

    async def gather_stop(self, call_control_id: str) -> None:
        """Cancel an active gather session."""
        if not self.api_key:
            return

        await self._run(
            self._sdk.calls.actions.gather_stop(
                call_control_id,
                command_id=self._cid("gstop", call_control_id),
            ),
            label=f"gather_stop({call_control_id})",
        )
        logger.info(f"☎️ [TelnyxClient] gather_stop sent: {call_control_id}")
