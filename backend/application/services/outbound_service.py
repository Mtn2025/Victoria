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
        # Missing Twilio Account SID and Auth Token? Read from settings.
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        # Need a "from" number. Assuming TWILIO_PHONE_NUMBER exists or hardcode for now.
        from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "+1234567890")

        if not account_sid or not auth_token:
            raise ValueError("Twilio credentials not configured")

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
        
        # The webhook that Twilio will hit when the call starts ringing/answered
        # Important: Since it's outbound, when it's answered, it plays TwiML.
        base_url = getattr(settings, "BASE_URL", "https://your-domain.ngrok.app")
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
        Crea una llamada outbound Telnyx vía SDK oficial.

        Lee de connectivity_config:
          - amdConfig       → answering_machine_detection (4 opciones Telnyx)
          - geoRegionTelnyx → geo_region del punto de presencia
          - callerIdTelnyx  → from number override del agente
          - telnyxConnectionId → connection_id override del agente
        """
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        import telnyx

        api_key = settings.TELNYX_API_KEY
        if not api_key:
            raise ValueError("Telnyx API Key not configured")

        # ── Resolver credenciales ──────────────────────────────────────────────
        # connectivity_config es un dict JSON del agente
        conn_cfg: dict = getattr(config_dto, "connectivity_config", None) or {}

        from_number = (
            conn_cfg.get("callerIdTelnyx")
            or getattr(config_dto, "telnyx_phone_number", None)
            or getattr(settings, "TELNYX_PHONE_NUMBER", "+1234567890")
        )
        connection_id = (
            conn_cfg.get("telnyxConnectionId")
            or getattr(config_dto, "telnyx_connection_id", None)
            or settings.TELNYX_CONNECTION_ID
        )
        if connection_id:
            connection_id = str(connection_id).strip()

        # ── Payload base ───────────────────────────────────────────────────────
        payload: dict = {
            "to": to_number,
            "from": from_number,
            "connection_id": connection_id,
        }

        # ── AMD granular (P0) ──────────────────────────────────────────────────
        # Lee amdConfig de connectivity_config (4 opciones Telnyx reales):
        # "disabled" | "detect" | "detect_hangup" | "detect_message_end"
        amd_config = conn_cfg.get("amdConfig", "disabled")
        if amd_config and amd_config != "disabled":
            payload["answering_machine_detection"] = amd_config
            logger.info(f"TELNYX OUTBOUND: AMD={amd_config!r}")
        elif amd_enabled:
            # Backward-compat: legacy flag booleano → detect básico
            payload["answering_machine_detection"] = "detect"

        # ── Geo Region (P0) ─────────────────────────────────────────────────────
        geo_region = conn_cfg.get("geoRegionTelnyx")
        if geo_region and geo_region != "global":
            # Telnyx acepta: "us-central", "us-east", etc.
            payload["media_region"] = geo_region
            logger.info(f"TELNYX OUTBOUND: geo_region={geo_region!r}")

        logger.info(f"TELNYX PAYLOAD GENERATED: { {k: v for k, v in payload.items() if k != 'from'} }")

        # ── Crear llamada vía SDK oficial (evita httpx crudo) ─────────────────
        try:
            client = TelnyxClient(api_key=api_key)
            result = await client._run(
                client._sdk.calls.create(**payload),
                label=f"calls.create({to_number})",
            )
            await client.close()

            if result is None:
                raise RuntimeError("Telnyx SDK calls.create() returned None — check API key/connection_id")

            tx_data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
            call_control_id = (tx_data.get("data") or {}).get("call_control_id") or getattr(result, "call_control_id", None)

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
                )
            except Exception as e:
                logger.error(f"Failed to record Telnyx outbound call {call_control_id} in DB: {e}")

        return tx_data if isinstance(tx_data, dict) else {"data": {"call_control_id": call_control_id}}
