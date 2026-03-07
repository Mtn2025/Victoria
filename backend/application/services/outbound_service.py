import logging
import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from backend.infrastructure.config.settings import settings
from backend.domain.ports.config_repository_port import ConfigRepositoryPort
from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.domain.use_cases.start_call import StartCallUseCase

logger = logging.getLogger(__name__)

class OutboundDialerService:
    def __init__(self, config_repo: ConfigRepositoryPort, call_repo: CallRepository, agent_repo: AgentRepository):
        self.config_repo = config_repo
        self.call_repo = call_repo
        self.agent_repo = agent_repo
        self.start_call_uc = StartCallUseCase(call_repository=call_repo, agent_repository=agent_repo)

    async def create_call(self, agent_id: str, to_number: str, provider: str = "twilio") -> Dict[str, Any]:
        """
        Creates an outbound call to `to_number` using the specified provider.
        It injects AMD configuration based on the Agent's flow_config.
        """
        config_dto = await self.config_repo.get_config(agent_id)
        if not config_dto:
            raise ValueError(f"Agent config not found: {agent_id}")

        amd_enabled = getattr(config_dto, 'amd_enabled', False)
        # We can also read amd_sensitivity, amd_action if we want to pass them directly to the provider.

        if provider == "twilio":
            return await self._create_twilio_call(to_number, config_dto, amd_enabled)
        elif provider == "telnyx":
            return await self._create_telnyx_call(to_number, config_dto, amd_enabled, agent_id)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _create_twilio_call(self, to_number: str, config_dto: Any, amd_enabled: bool) -> Dict[str, Any]:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        from_number = settings.TWILIO_PHONE_NUMBER  # fuente única: env TWILIO_PHONE_NUMBER

        if not account_sid or not auth_token:
            raise ValueError("Twilio credentials not configured (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN)")
        if not from_number:
            raise ValueError("TWILIO_PHONE_NUMBER env var not configured")

        base_url = settings.BASE_URL
        if not base_url:
            raise ValueError("BASE_URL env var not configured — required for Twilio webhooks")


        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
        twiml_url = f"{base_url}/telephony/twilio/outbound-twiml?agent_id={config_dto.agent_id}"

        payload = {
            "To": to_number,
            "From": from_number,
            "Url": twiml_url,
            "Method": "POST",
            "StatusCallback": f"{base_url}/telephony/twilio/status-callback",
            "StatusCallbackMethod": "POST",
            "StatusCallbackEvent": ["ringing", "answered", "completed"],
        }

        # --- FLOW CONFIG: Twilio AMD ---
        if amd_enabled:
            payload["MachineDetection"] = "Enable"
            # Webhook for async AMD result
            payload["AsyncAmd"] = "true"
            payload["AsyncAmdStatusCallback"] = f"{base_url}/telephony/twilio/amd-callback?agent_id={config_dto.agent_id}"
            payload["AsyncAmdStatusCallbackMethod"] = "POST"

            # Optional mapping of sensitivity to timeout
            # e.g., sensitivity 1.0 -> 5 sec, 0.0 -> 30 sec timeout maybe?
            # Or just pass MachineDetectionTimeout
            
        async with httpx.AsyncClient(auth=(account_sid, auth_token)) as client:
            resp = await client.post(url, data=payload)
            if resp.status_code >= 400:
                logger.error(f"Twilio Call creation failed: {resp.text}")
                raise RuntimeError(f"Twilio API error: {resp.text}")
                
            tw_data = resp.json()
            sid = tw_data.get("sid")
            if sid:
                # 2. Registrar en base de datos la llamada enviada.
                try:
                    await self.start_call_uc.execute(
                        agent_id=agent_id,
                        call_id_value=sid,
                        from_number=from_number,
                        to_number=to_number
                    )
                except Exception as e:
                    logger.error(f"Failed to record Twilio outbound call {sid} in DB: {e}")

            return tw_data

    async def _create_telnyx_call(self, to_number: str, config_dto: Any, amd_enabled: bool, agent_id: str) -> Dict[str, Any]:
        """
        Crea una llamada outbound Telnyx vía SDK oficial (telnyx 4.60.0).

        SDK 4.x usa calls.dial() (no calls.create).
        Parámetros clave:
          - from_          → nota el underscore (Python keyword avoidance)
          - connection_id  → requerido
          - sip_region     → 'US' | 'Europe' | 'Canada' | 'Australia' | 'Middle East'
          - answering_machine_detection → 'detect' | 'detect_beep' | 'detect_words' | 'greeting_end' | 'disabled' | 'premium'
        """
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        import uuid as _uuid

        api_key = settings.TELNYX_API_KEY
        if not api_key:
            raise ValueError("Telnyx API Key not configured")

        # ── Resolver credenciales ──────────────────────────────────────────────
        conn_cfg: dict = getattr(config_dto, "connectivity_config", None) or {}

        from_number = (
            conn_cfg.get("callerIdTelnyx")
            or getattr(config_dto, "telnyx_phone_number", None)
            or settings.TELNYX_PHONE_NUMBER  # fuente única: env TELNYX_PHONE_NUMBER
        )
        if not from_number:
            raise ValueError(
                "Caller ID Telnyx no configurado: define TELNYX_PHONE_NUMBER en env "
                "o callerIdTelnyx en la connectivity_config del agente"
            )
        connection_id = (
            conn_cfg.get("telnyxConnectionId")
            or getattr(config_dto, "telnyx_connection_id", None)
            or settings.TELNYX_CONNECTION_ID
        )
        if connection_id:
            connection_id = str(connection_id).strip()

        # ── AMD (normalizar valores al catálogo real del SDK 4.x) ─────────────
        # SDK acepta: 'detect' | 'detect_beep' | 'detect_words' | 'greeting_end' | 'disabled' | 'premium'
        # El UI guardaba 'detect_hangup' y 'detect_message_end' que ya no existen → mapear
        AMD_MAP = {
            "detect":           "detect",
            "detect_hangup":    "detect",          # deprecated alias → detect
            "detect_message_end": "detect_words",  # deprecated alias → detect_words
            "detect_beep":      "detect_beep",
            "detect_words":     "detect_words",
            "greeting_end":     "greeting_end",
            "premium":          "premium",
            "disabled":         "disabled",
        }
        amd_raw = conn_cfg.get("amdConfig", "disabled") or "disabled"
        amd_sdk  = AMD_MAP.get(amd_raw, "detect") if amd_raw != "disabled" else None
        if not amd_sdk and amd_enabled:
            amd_sdk = "detect"

        # ── Geo Region → sip_region ────────────────────────────────────────────
        # SDK 4.x: sip_region acepta 'US' | 'Europe' | 'Canada' | 'Australia' | 'Middle East'
        GEO_MAP = {
            "us-central": "US", "us-east": "US", "us-west": "US",
            "europe":     "Europe", "eu":   "Europe",
            "canada":     "Canada", "ca":   "Canada",
            "australia":  "Australia", "au": "Australia",
            "middle-east": "Middle East",
        }
        geo_raw    = conn_cfg.get("geoRegionTelnyx", "").lower().strip()
        sip_region = GEO_MAP.get(geo_raw) if geo_raw and geo_raw != "global" else None

        logger.info(
            f"TELNYX DIAL: to={to_number} from={from_number!r} "
            f"conn={connection_id!r} amd={amd_sdk!r} region={sip_region!r}"
        )

        # ── Crear llamada vía SDK 4.x calls.dial() ────────────────────────────
        try:
            client = TelnyxClient(api_key=api_key)

            # Construir kwargs explícitos (type-safe, sin **dict con claves Python-keyword)
            dial_kwargs: Dict[str, Any] = {
                "to":            to_number,
                "from_":         from_number,   # NOTE: underscore obligatorio en SDK 4.x
                "connection_id": connection_id,
                "command_id":    f"dial-{_uuid.uuid4().hex[:12]}",
            }
            if amd_sdk:
                dial_kwargs["answering_machine_detection"] = amd_sdk
            if sip_region:
                dial_kwargs["sip_region"] = sip_region

            result = await client._run(
                client._sdk.calls.dial(**dial_kwargs),
                label=f"calls.dial({to_number})",
            )
            await client.close()

            if result is None:
                raise RuntimeError("Telnyx SDK calls.dial() returned None — check API key/connection_id")

            tx_data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
            call_control_id = (
                (tx_data.get("data") or {}).get("call_control_id")
                or getattr(result, "call_control_id", None)
            )

        except Exception as exc:
            logger.error(f"Telnyx SDK call creation failed: {exc}")
            raise RuntimeError(f"Telnyx call creation error: {exc}") from exc

        # ── Registrar en BD ───────────────────────────────────────────────────
        if call_control_id:
            try:
                await self.start_call_uc.execute(
                    agent_id=agent_id,
                    call_id_value=str(call_control_id),
                    from_number=from_number,
                    to_number=to_number,
                    client_type="telnyx",
                    direction="outbound",
                )
            except Exception as e:
                logger.error(f"Failed to record Telnyx outbound call {call_control_id} in DB: {e}")

        return tx_data if isinstance(tx_data, dict) else {"data": {"call_control_id": call_control_id}}

