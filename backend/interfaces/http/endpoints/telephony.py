"""
Telephony Endpoints.
Part of the Interfaces Layer (HTTP).
Handles webhooks for Twilio and Telnyx.

REFACTORED Sprint 2 (Marzo 2026):
  - Dispatcher completo: 18 eventos según catálogo oficial Telnyx
  - call_session_id como correlator principal (cross-leg identifier)
  - Verificación de firma Ed25519 integrada (bypass en dev)
  - Singleton telnyx_adapter eliminado → instancia local por handler
  - asyncio.create_task() para todo procesamiento pesado

References:
  - telnyx_call_architecture.md §4 (catálogo eventos), §6 (reglas producción)
  - telnyx_native_orchestrator.md §2 Layer 1 (Call Control API)
"""
import asyncio
import logging
import base64
import json
from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks, HTTPException

from backend.infrastructure.config.settings import settings
from backend.interfaces.deps import get_config_repository, get_call_repository, get_agent_repository
from backend.domain.ports.config_repository_port import ConfigRepositoryPort
from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.application.services.outbound_service import OutboundDialerService
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
from backend.infrastructure.security.telnyx_signature import verify_telnyx_signature
from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
from backend.domain.use_cases.telephony_actions import AnswerCallUseCase, StartStreamUseCase

router = APIRouter(prefix="/telephony", tags=["telephony"])
protected_router = APIRouter(prefix="/telephony", tags=["Telephony Actions"])
logger = logging.getLogger(__name__)

# NOTE: telnyx_adapter singleton REMOVED (Sprint 2).
# Each handler creates its own TelnyxClient() instance.
# This prevents import-time failures if TELNYX_API_KEY is not yet loaded.


# ─────────────────────────────────────────────────────────────────────────────
# TWILIO endpoints (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

@router.api_route("/twilio/incoming-call", methods=["GET", "POST"])
async def twilio_incoming_call(request: Request):
    """Twilio Webhook. Returns TwiML to connect to WebSocket."""
    host = request.headers.get("host")
    if not host:
        raise ValueError("Host header is missing")
    ws_url = f"wss://{host}{settings.WS_MEDIA_STREAM_PATH}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.api_route("/twilio/outbound-twiml", methods=["GET", "POST"])
async def twilio_outbound_twiml(request: Request, agent_id: str):
    """Twilio Webhook for outbound calls. Returns TwiML WS Connect with agent_id."""
    host = request.headers.get("host")
    if not host:
        raise ValueError("Host header is missing")
    ws_url = f"wss://{host}{settings.WS_MEDIA_STREAM_PATH}"
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="agent_id" value="{agent_id}" />
        </Stream>
    </Connect>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.api_route("/twilio/amd-callback", methods=["POST"])
async def twilio_amd_callback(
    request: Request,
    agent_id: str,
    config_repo: ConfigRepositoryPort = Depends(get_config_repository),
    call_repo: CallRepository = Depends(get_call_repository),
):
    """Async webhook from Twilio reporting Answering Machine Detection result."""
    form = await request.form()
    answered_by = form.get("AnsweredBy")
    call_sid = form.get("CallSid")
    logger.info(f"☎️ Twilio AMD Callback: Call {call_sid} answered by {answered_by}")

    if answered_by in ("machine_start", "machine_end_beep", "machine_end_other"):
        config_dto = await config_repo.get_config(agent_id)
        action = getattr(config_dto, "amd_action", "hangup")
        amd_message = getattr(config_dto, "amd_message", "Hola, le llamábamos para darle información.")
        logger.info(f"AMD action config for agent {agent_id}: {action}")

        if call_sid:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            if account_sid and auth_token:
                import httpx
                url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls/{call_sid}.json"
                async with httpx.AsyncClient(auth=(account_sid, auth_token)) as client:
                    if action == "leave_message" and amd_message:
                        host = request.headers.get("host", "localhost")
                        scheme = request.headers.get("x-forwarded-proto", "https")
                        play_url = f"{scheme}://{host}/api/telephony/voicemail-audio?agent_id={agent_id}"
                        twiml_str = f"<Response><Play>{play_url}</Play><Hangup/></Response>"
                        await client.post(url, data={"Twiml": twiml_str})
                        logger.info(f"Injected Leave Message TwiML (Play) into call {call_sid}")
                    else:
                        await client.post(url, data={"Status": "completed"})
                        logger.info(f"Hung up call {call_sid} due to machine detection")

            try:
                from backend.domain.value_objects.call_id import CallId
                call = await call_repo.get_by_id(CallId(call_sid))
                if call:
                    call.end("voicemail")
                    await call_repo.save(call)
            except Exception as e:
                logger.error(f"Error marking call {call_sid} as voicemail in DB: {e}")

    return Response(content="OK", status_code=200)


@router.api_route("/twilio/status-callback", methods=["POST"])
async def twilio_status_callback(
    request: Request,
    call_repo: CallRepository = Depends(get_call_repository),
):
    """Twilio StatusCallback webhook — lifecycle events."""
    form = await request.form()
    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus")
    logger.info(f"☎️ Twilio Status Callback: Call {call_sid} → {call_status}")

    if call_sid and call_status in ("completed", "busy", "no-answer", "failed", "canceled"):
        from backend.domain.value_objects.call_id import CallId
        try:
            call = await call_repo.get_by_id(CallId(call_sid))
            if call and call.status.value not in ("completed", "voicemail", "failed", "busy", "no_answer"):
                call.end(reason=call_status)
                await call_repo.save(call)
                logger.info(f"✅ DB Update: Call {call_sid} → {call_status}")
        except Exception as e:
            logger.error(f"Failed to update call {call_sid}: {e}")

    return Response(content="OK", status_code=200)


# ─────────────────────────────────────────────────────────────────────────────
# TELNYX CALL CONTROL — Dispatcher completo
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/telnyx/call-control")
async def telnyx_call_control(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Telnyx Call Control Webhook — Dispatcher completo (18 eventos).

    Production rules (telnyx_call_architecture.md §6):
    1. Responder INMEDIATAMENTE < 2s → asyncio.create_task() para todo
    2. Verificar firma Ed25519 ANTES de procesar
    3. Usar call_session_id como correlator principal

    IMPORTANT — Session lifecycle:
    call_repo is NOT injected via FastAPI DI here. The DI session is tied to
    the HTTP request lifecycle — it gets closed the moment we return 200.
    Background tasks spawned with asyncio.create_task() would then operate on
    a closed session → IllegalStateChangeError.
    Each handler creates its OWN session via AsyncSessionLocal().
    """
    # 1. Leer body como bytes (necesario para verificación de firma)
    body = await request.body()

    # 2. Verificar firma Ed25519 (bypass automático en ENVIRONMENT=development)
    if not await verify_telnyx_signature(request, body):
        logger.warning("❌ [TELNYX] Invalid webhook signature — rejecting")
        raise HTTPException(status_code=403, detail="Invalid Telnyx webhook signature")

    # 3. Parsear JSON
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        logger.error("❌ [TELNYX] Invalid JSON body")
        return Response(status_code=400)

    data            = event.get("data", {})
    event_type      = data.get("event_type", "")
    payload         = data.get("payload", {})
    call_control_id = payload.get("call_control_id", "")
    # call_session_id = cross-leg correlator (canonical identifier per telnyx spec)
    call_session_id = payload.get("call_session_id") or call_control_id

    logger.info(f"☎️ [TELNYX] [{call_session_id}] Event: {event_type}")

    # 4. Dispatch async — NEVER await here
    # NOTE: call_repo is NOT passed — each handler opens its own session
    asyncio.create_task(
        _route_telnyx_event(
            event_type, payload, call_session_id, call_control_id, request
        )
    )

    # 5. Responder INMEDIATAMENTE
    return Response(status_code=200)


async def _route_telnyx_event(
    event_type: str,
    payload: dict,
    session_id: str,
    cid: str,
    request: Request,
) -> None:
    """
    Dispatcher central. Catálogo completo según telnyx_call_architecture.md §4.

    Each handler creates its own DB session via AsyncSessionLocal() to avoid
    the IllegalStateChangeError caused by using a FastAPI DI session that is
    tied to the parent request lifecycle (already closed by the time this
    background task runs).
    """
    from backend.infrastructure.database.session import AsyncSessionLocal
    from backend.infrastructure.database.repositories import SqlAlchemyCallRepository

    async with AsyncSessionLocal() as db:
        call_repo = SqlAlchemyCallRepository(db)
        await _dispatch_event(event_type, payload, session_id, cid, request, call_repo)


async def _dispatch_event(
    event_type: str,
    payload: dict,
    session_id: str,
    cid: str,
    request: Request,
    call_repo: CallRepository,
) -> None:
    """Inner dispatcher — runs with a guaranteed-fresh DB session."""
    handlers = {
        # Ciclo de vida
        "call.initiated":    _handle_initiated,
        "call.answered":     _handle_answered,
        "call.hangup":       _handle_hangup,
        "call.bridged":      _handle_bridged,
        # Media Streaming
        "streaming.started": _handle_streaming_started,
        "streaming.stopped": _handle_streaming_stopped,
        "streaming.failed":  _handle_streaming_failed,
        # AMD
        "call.machine.detection.ended":        _handle_amd,
        "call.machine.greeting.ended":          _handle_amd,
        "call.machine.premium.greeting.ended":  _handle_amd,
        "call.machine.detect":                  _handle_amd,
        # Playback
        "call.playback.started": _handle_playback_started,
        "call.playback.ended":   _handle_playback_ended,
        "call.playback.failed":  _handle_playback_failed,
        # Recording
        "recording.saved": _handle_recording_saved,
        # DTMF
        "call.dtmf.received": _handle_dtmf,
        # Gather
        "gather.ended":   _handle_gather_ended,
        "gather.timeout": _handle_gather_timeout,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            await handler(payload, session_id, cid, request, call_repo)
        except Exception as exc:
            logger.error(
                f"☎️ [TELNYX] [{session_id}] Handler error ({event_type}): {exc}",
                exc_info=True,
            )
    else:
        logger.debug(
            f"☎️ [TELNYX] [{session_id}] No handler for event: {event_type}"
        )


# ── Handlers individuales ─────────────────────────────────────────────────────

async def _handle_initiated(payload, session_id, cid, request, call_repo):
    direction = payload.get("direction", "")
    from_ = payload.get("from", "")
    if direction == "inbound":
        logger.info(f"☎️ [TELNYX] [{session_id}] Incoming call from {from_}")
        client = TelnyxClient()
        await AnswerCallUseCase(client).execute(cid)
    else:
        logger.info(f"☎️ [TELNYX] [{session_id}] Outbound ringing — awaiting answered")


async def _handle_answered(payload, session_id, cid, request, call_repo):
    client_state = payload.get("client_state")
    proto = request.headers.get("x-forwarded-proto", "https")
    host  = request.headers.get("x-forwarded-host") or request.headers.get("host", "localhost")
    ws_scheme = "wss" if proto == "https" else "ws"
    ws_url = (
        f"{ws_scheme}://{host}{settings.WS_MEDIA_STREAM_PATH}"
        f"?client=telnyx&call_control_id={cid}"
    )
    if client_state:
        ws_url += f"&client_state={client_state}"

    logger.info(f"☄️ [TELNYX] [{session_id}] Starting stream → {ws_url}")

    # Load agent config to determine codec and gather settings
    agent_id = None
    config = None
    codec = "PCMU"  # Default codec (safe fallback)
    try:
        from backend.domain.value_objects.call_id import CallId
        call = await call_repo.get_by_id(CallId(cid))
        if call:
            agent_id = getattr(getattr(call, "agent", None), "agent_uuid", None)
            if agent_id:
                from backend.infrastructure.database.session import AsyncSessionLocal
                from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
                async with AsyncSessionLocal() as db:
                    config = await ConfigRepository(db).get_config(str(agent_id))
                    codec = getattr(config, "audio_codec", "PCMU")  # B-05: L16 or PCMU
    except Exception as exc:
        logger.warning(f"☄️ [TELNYX] [{session_id}] Could not load config for codec: {exc}")

    # Start media stream with configured codec (B-05)
    client = TelnyxClient()
    await StartStreamUseCase(client).execute(cid, ws_url, client_state, codec=codec)

    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if call:
            try:
                call.start()  # no-op para outbound (ya in_progress desde outbound_service)
            except Exception as state_exc:
                # Outbound calls ya están en in_progress — ignorar error de transición
                logger.info(f"☄️ [TELNYX] [{session_id}] Call state: {state_exc} (outbound, expected)")
            else:
                logger.info(f"☄️ [TELNYX] [{session_id}] ✅ DB: IN_PROGRESS (codec={codec})")
            await call_repo.save(call)
    except Exception as exc:
        logger.error(f"☄️ [TELNYX] [{session_id}] DB (answered) error: {exc}")

    await _start_recording_if_enabled(cid, session_id, call_repo)
    await _start_siprec_if_enabled(cid, session_id, call_repo)

    # B-10: trigger gather_using_ai if enabled in agent config
    if config and getattr(config, "gather_ai_enabled", False):
        schema = getattr(config, "gather_ai_schema", None) or {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre completo del caller"}
            },
            "required": ["nombre"]
        }
        greeting = getattr(config, "gather_ai_greeting", "¿Con quién tengo el gusto de hablar?")
        voice    = getattr(config, "gather_ai_voice", None)
        try:
            await TelnyxClient().gather_using_ai(
                cid,
                greeting=greeting,
                parameters=schema,
                voice=voice,
            )
            logger.info(f"☄️ [TELNYX] [{session_id}] 📋 gather_using_ai started")
        except Exception as exc:
            logger.error(f"☄️ [TELNYX] [{session_id}] gather_using_ai error: {exc}")


async def _start_recording_if_enabled(cid: str, session_id: str, call_repo) -> None:
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if call and hasattr(call, "agent") and call.agent:
            conn = getattr(call.agent, "connectivity_config", {}) or {}
            if conn.get("enableRecordingTelnyx", False):
                channels = conn.get("recordingChannelsTelnyx", "dual")
                # S3 direct upload si el agente lo tiene configurado
                s3_destination = None
                if conn.get("telnyxRecordS3", False):
                    s3_bucket = conn.get("telnyxS3Bucket", "").strip()
                    if s3_bucket:
                        s3_destination = s3_bucket if s3_bucket.startswith("s3://") else f"s3://{s3_bucket}"
                logger.info(
                    f"☎️ [TELNYX] [{session_id}] 📼 Starting recording "
                    f"({channels}){' → S3' if s3_destination else ''}"
                )
                await TelnyxClient().start_recording(cid, channels, s3_destination=s3_destination)
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] Recording start error: {exc}")



async def _start_siprec_if_enabled(cid: str, session_id: str, call_repo) -> None:
    """
    P0: Si telnyxSiprecDest está configurado en el agente, dispara SIPREC/fork.
    Admite tanto destinos SIPREC (sip:...) como UDP (ip:port).
    """
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if call and hasattr(call, "agent") and call.agent:
            conn = getattr(call.agent, "connectivity_config", {}) or {}
            siprec_dest = conn.get("telnyxSiprecDest", "").strip()
            if not siprec_dest:
                return

            client = TelnyxClient()
            # Si el destino es una URI SIP → SIPREC; si es IP:port → UDP fork
            if siprec_dest.lower().startswith("sip:"):
                await client.start_siprec(cid, siprec_dest)
                logger.info(f"☎️ [TELNYX] [{session_id}] 🎙️ SIPREC started → {siprec_dest}")
            else:
                await client.start_forking(cid, siprec_dest)
                logger.info(f"☎️ [TELNYX] [{session_id}] 📡 UDP Fork started → {siprec_dest}")
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] SIPREC/Fork start error: {exc}")


async def _handle_hangup(payload, session_id, cid, request, call_repo):
    raw = payload.get("sip_hangup_cause") or payload.get("hangup_cause") or ""
    cause = str(raw).lower()
    if "busy" in cause or cause in ("486", "600", "603"):
        reason = "busy"
    elif "no answer" in cause or "timeout" in cause or cause in ("408", "480"):
        reason = "no_answer"
    elif cause in ("404", "410", "484", "503"):
        reason = "failed"
    else:
        reason = "completed"
    logger.info(f"☎️ [TELNYX] [{session_id}] Hangup cause={raw!r} → {reason}")
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if call and call.status.value not in ("completed", "voicemail", "failed", "busy", "no_answer"):
            call.end(reason=reason)
            await call_repo.save(call)
            logger.info(f"☎️ [TELNYX] [{session_id}] ✅ DB: ended ({reason})")
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] DB (hangup) error: {exc}")

    # P1: Fallback transfer si la llamada falló y hay número configurado
    if reason in ("failed", "busy", "no_answer"):
        await _handle_fallback_if_configured(cid, session_id, call_repo)


async def _handle_fallback_if_configured(cid: str, session_id: str, call_repo) -> None:
    """
    P1: Si fallbackNumberTelnyx está configurado y la llamada falló/no contestó,
    inicia una nueva llamada al número de fallback.
    Evita bucles: solo actúa en llamadas originadas (no en las de fallback mismas).
    """
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if not call or not hasattr(call, "agent") or not call.agent:
            return
        conn = getattr(call.agent, "connectivity_config", {}) or {}
        fallback_number = conn.get("fallbackNumberTelnyx", "").strip()
        if not fallback_number:
            return

        # Evitar bucle: el metadata "is_fallback" debe estar ausente
        metadata = getattr(call, "metadata", {}) or {}
        if metadata.get("is_fallback"):
            logger.info(f"☎️ [TELNYX] [{session_id}] Fallback skip (already a fallback call)")
            return

        agent_id = str(getattr(call.agent, "agent_uuid", ""))
        caller_id = conn.get("callerIdTelnyx") or getattr(
            getattr(call, "from_number", None), "value", ""
        )
        logger.info(f"☎️ [TELNYX] [{session_id}] 📲 Initiating fallback → {fallback_number}")

        fb_client = TelnyxClient()
        from backend.infrastructure.database.session import AsyncSessionLocal
        from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
        async with AsyncSessionLocal() as db:
            config_dto = await ConfigRepository(db).get_config(agent_id)
            conn_cfg = getattr(config_dto, "connectivity_config", {}) or {}
            connection_id = (
                conn_cfg.get("telnyxConnectionId")
                or getattr(config_dto, "telnyx_connection_id", None)
                or ""
            )
            if connection_id:
                connection_id = str(connection_id).strip()

        result = await fb_client._run(
            fb_client._sdk.calls.create(
                **{
                    "to": fallback_number,
                    "from": caller_id,
                    "connection_id": connection_id,
                    "client_state": __import__('base64').b64encode(
                        __import__('json').dumps({"is_fallback": True, "original_call_id": cid}).encode()
                    ).decode(),
                }
            ),
            label=f"fallback.create({fallback_number})",
        )
        await fb_client.close()
        if result:
            logger.info(f"☎️ [TELNYX] [{session_id}] ✅ Fallback call initiated → {fallback_number}")
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] Fallback error: {exc}")

async def _handle_bridged(payload, session_id, cid, request, call_repo):
    logger.info(f"☎️ [TELNYX] [{session_id}] 🔗 Call bridged")


async def _handle_streaming_started(payload, session_id, cid, request, call_repo):
    logger.info(f"☎️ [TELNYX] [{session_id}] 📡 Streaming started (stream_id={payload.get('stream_id','')})")


async def _handle_streaming_stopped(payload, session_id, cid, request, call_repo):
    logger.warning(f"☎️ [TELNYX] [{session_id}] 📡 Streaming STOPPED")


async def _handle_streaming_failed(payload, session_id, cid, request, call_repo):
    logger.error(f"☎️ [TELNYX] [{session_id}] ❌ Streaming FAILED: {payload.get('failure_reason','unknown')}")
    # TODO Sprint 4: retry with exponential backoff


async def _handle_amd(payload, session_id, cid, request, call_repo):
    amd_result = payload.get("result", "")
    if amd_result != "machine":
        logger.info(f"☎️ [TELNYX] [{session_id}] 🤖 AMD {amd_result!r} (not machine)")
        return
    logger.info(f"☎️ [TELNYX] [{session_id}] 🤖 Machine detected")
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if not call:
            return
        host = request.headers.get("host", "localhost")
        scheme = request.headers.get("x-forwarded-proto", "https")
        agent_id    = getattr(getattr(call, "agent", None), "agent_uuid", None)
        action      = "hangup"
        amd_message = "Hola, le llamábamos para darle información."
        if agent_id:
            from backend.infrastructure.database.session import AsyncSessionLocal
            from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
            async with AsyncSessionLocal() as db:
                config_dto  = await ConfigRepository(db).get_config(str(agent_id))
                action      = getattr(config_dto, "amd_action", "hangup")
                amd_message = getattr(config_dto, "amd_message", amd_message)
        client = TelnyxClient()
        if action == "leave_message" and amd_message:
            audio_url = f"{scheme}://{host}/api/telephony/voicemail-audio?agent_id={agent_id}"
            cs = base64.b64encode(
                json.dumps({"call_control_id": cid, "action": "hangup_after_playback"}).encode()
            ).decode()
            await client.playback_start(cid, audio_url, client_state=cs)
            logger.info(f"☎️ [TELNYX] [{session_id}] ▶️ Voicemail playback started")
        else:
            await client.hangup_call(cid)
            logger.info(f"☎️ [TELNYX] [{session_id}] 📵 Hung up (machine)")
        call.end("voicemail")
        await call_repo.save(call)
        logger.info(f"☎️ [TELNYX] [{session_id}] ✅ DB: voicemail")
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] AMD error: {exc}", exc_info=True)


async def _handle_playback_started(payload, session_id, cid, request, call_repo):
    logger.debug(f"☎️ [TELNYX] [{session_id}] ▶️ Playback started")


async def _handle_playback_ended(payload, session_id, cid, request, call_repo):
    cs_b64 = payload.get("client_state", "")
    if not cs_b64:
        return
    try:
        state = json.loads(base64.b64decode(cs_b64).decode())
        if state.get("action") == "hangup_after_playback":
            logger.info(f"☎️ [TELNYX] [{session_id}] 📵 Hanging up after voicemail")
            await TelnyxClient().hangup_call(cid)
    except Exception as exc:
        logger.error(f"☎️ [TELNYX] [{session_id}] playback_ended error: {exc}")


async def _handle_playback_failed(payload, session_id, cid, request, call_repo):
    logger.error(f"☎️ [TELNYX] [{session_id}] ❌ Playback FAILED: {payload.get('failure_reason','unknown')}")


async def _handle_recording_saved(payload, session_id, cid, request, call_repo):
    mp3_url  = payload.get("recording_urls", {}).get("mp3", "")
    duration = payload.get("duration_secs", 0)
    logger.info(f"☎️ [TELNYX] [{session_id}] 📼 Recording saved: {mp3_url} ({duration}s)")
    if mp3_url and call_repo:
        from backend.domain.value_objects.call_id import CallId
        try:
            call = await call_repo.get_by_id(CallId(cid))
            if call and hasattr(call, "update_metadata"):
                call.update_metadata("recording_url", mp3_url)
                call.update_metadata("recording_duration_secs", duration)
                await call_repo.save(call)
                logger.info(f"☎️ [TELNYX] [{session_id}] ✅ Recording URL saved to DB")
        except Exception as exc:
            logger.error(f"☎️ [TELNYX] [{session_id}] Recording DB save error: {exc}")


async def _handle_dtmf(payload, session_id, cid, request, call_repo):
    """
    B-09: Route DTMF digit to orchestrator — only if dtmfListeningEnabledTelnyx is ON.
    P1 fix: ahora condicional según connectivity_config del agente.
    """
    digit = payload.get("digit", "")
    logger.info(f"☄️ [TELNYX] [{session_id}] 🔢 DTMF received: {digit!r}")

    # Verificar que DTMF esté habilitado en el agente
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(cid))
        if call and hasattr(call, "agent") and call.agent:
            conn = getattr(call.agent, "connectivity_config", {}) or {}
            dtmf_enabled = conn.get("dtmfListeningEnabledTelnyx", True)  # Default True para backward-compat
            if not dtmf_enabled:
                logger.debug(f"☄️ [TELNYX] [{session_id}] DTMF {digit!r} ignored (dtmfListeningEnabledTelnyx=False)")
                return
    except Exception:
        pass  # Si no se puede leer config, procesar de todas formas (safe default)

    orchestrator = DtmfRegistry.get(session_id)
    if orchestrator and hasattr(orchestrator, "handle_dtmf"):
        try:
            await orchestrator.handle_dtmf(digit)
            logger.info(f"☄️ [TELNYX] [{session_id}] DTMF {digit!r} routed to orchestrator")
        except Exception as exc:
            logger.error(f"☄️ [TELNYX] [{session_id}] DTMF routing error: {exc}")
    else:
        logger.debug(
            f"☄️ [TELNYX] [{session_id}] DTMF {digit!r} — no active orchestrator (call not yet streaming)"
        )


async def _handle_gather_ended(payload, session_id, cid, request, call_repo):
    """B-10: gather.ended — persist structured data collected by gather_using_ai."""
    digits  = payload.get("digits", "")
    speech  = payload.get("speech_result", "")
    result  = payload.get("parameters_result", {})
    logger.info(
        f"☄️ [TELNYX] [{session_id}] 🔢 Gather ended — "
        f"DTMF={digits!r} Speech={speech!r} Data={result}"
    )
    # Persist gathered data in call metadata
    if result and call_repo:
        from backend.domain.value_objects.call_id import CallId
        try:
            call = await call_repo.get_by_id(CallId(cid))
            if call and hasattr(call, "update_metadata"):
                call.update_metadata("gathered_data", result)
                if speech:
                    call.update_metadata("gather_transcript", speech)
                await call_repo.save(call)
                logger.info(f"☄️ [TELNYX] [{session_id}] ✅ Gathered data persisted: {result}")
        except Exception as exc:
            logger.error(f"☄️ [TELNYX] [{session_id}] gather.ended DB error: {exc}")


async def _handle_gather_timeout(payload, session_id, cid, request, call_repo):
    logger.info(f"☎️ [TELNYX] [{session_id}] ⏱️ Gather timeout")


# ─────────────────────────────────────────────────────────────────────────────
# Outbound + utility endpoints (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class OutboundCallRequest(BaseModel):
    agent_id: str
    to_number: str
    provider: str = "twilio"


@protected_router.post("/outbound")
async def create_outbound_call(
    request: OutboundCallRequest,
    config_repo: ConfigRepositoryPort = Depends(get_config_repository),
    call_repo: CallRepository = Depends(get_call_repository),
    agent_repo: AgentRepository = Depends(get_agent_repository),
):
    """Initiates an outbound call via Twilio or Telnyx."""
    dialer = OutboundDialerService(config_repo=config_repo, call_repo=call_repo, agent_repo=agent_repo)
    try:
        result = await dialer.create_call(
            agent_id=request.agent_id,
            to_number=request.to_number,
            provider=request.provider,
        )
        call_id = None
        if request.provider == "telnyx":
            call_id = result.get("data", {}).get("call_control_id")
        elif request.provider == "twilio":
            call_id = result.get("sid")
        return {"status": "success", "call": result, "call_id": call_id or "undefined"}
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error creating outbound call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@protected_router.get("/status/{call_id}")
async def get_call_status(
    call_id: str,
    call_repo: CallRepository = Depends(get_call_repository),
):
    """Lightweight endpoint for frontend polling of live call status."""
    from backend.domain.value_objects.call_id import CallId
    try:
        call = await call_repo.get_by_id(CallId(call_id))
        if call:
            st = call.status.value
            ui_status = "ringing"
            if st == "in_progress":
                ui_status = "in_progress"
            elif st in ("completed", "voicemail", "failed", "busy", "no_answer"):
                ui_status = "ended"
            return {"status": "success", "call_status": ui_status}
        return {"status": "not_found", "call_status": "idle"}
    except Exception as e:
        logger.error(f"Error fetching status for {call_id}: {e}")
        return {"status": "error", "message": str(e), "call_status": "idle"}


@router.get("/voicemail-audio")
async def get_voicemail_audio(agent_id: str):
    """Generates TTS audio for voicemail dropping. Returns 16kHz WAV."""
    from backend.infrastructure.database.session import AsyncSessionLocal
    from backend.infrastructure.adapters.persistence.config_repository import ConfigRepository
    from backend.infrastructure.adapters.tts.static_registry import StaticTTSRegistryAdapter
    from backend.domain.value_objects.voice_config import VoiceConfig
    from backend.domain.value_objects.audio_format import AudioFormat

    async with AsyncSessionLocal() as session:
        conf_repo = ConfigRepository(session)
        try:
            config_dto = await conf_repo.get_config(agent_id)
        except Exception as e:
            logger.error(f"Failed to find config for voicemail audio: {e}")
            raise HTTPException(status_code=404, detail="Config not found")

        provider   = getattr(config_dto, "tts_provider", "azure")
        voice_name = getattr(config_dto, "tts_voice", "es-MX-DaliaNeural")
        amd_msg    = getattr(config_dto, "amd_message", "Hola, le llamábamos para darle información.")
        speed      = getattr(config_dto, "tts_speed", 1.0)
        pitch      = getattr(config_dto, "tts_pitch", "default")

        registry = StaticTTSRegistryAdapter()
        try:
            adapter = registry.get_provider_adapter(provider)
            vc = VoiceConfig(name=voice_name, speed=speed, pitch=pitch)
            if hasattr(adapter, "synthesize_for_preview"):
                audio_bytes = await adapter.synthesize_for_preview(text=amd_msg, voice=vc)
            else:
                fmt = AudioFormat(encoding="pcm", sample_rate=16000, channels=1)
                audio_bytes = await adapter.synthesize(text=amd_msg, voice=vc, format=fmt)
            return Response(content=audio_bytes, media_type="audio/wav")
        except Exception as e:
            logger.error(f"Voicemail TTS generation failed: {e}")
            raise HTTPException(status_code=500, detail="TTS generation failed")
