"""
Sprint 4 Simulation Tests — B-05, B-08, B-09, B-10

Tests:
  B-05: L16 codec — start_streaming() payload, _decode_audio() dispatcher
  B-08: SDK telnyx — TelnyxClient initialization with SDK
  B-09: DTMF routing — DtmfRegistry, handle_dtmf() action dispatch
  B-10: gather_using_ai — payload correctness, gather.ended data persistence

Run: python -m pytest tests/test_sprint4_telnyx.py -v
"""
import asyncio
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────────────────────────────────────
# B-05: L16 Codec Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestL16Codec:

    def test_decode_audio_l16_passthrough(self):
        """L16 audio passes through without any conversion."""
        from backend.interfaces.websocket.endpoints.telnyx_stream import _decode_audio
        raw = bytes([0x10, 0x20, 0x30, 0x40])
        result = _decode_audio(raw, "L16")
        assert result == raw, "L16 must pass through unchanged (it's already PCM16)"

    def test_decode_audio_pcmu_converts(self):
        """PCMU audio gets converted via µ-law decompression."""
        from backend.interfaces.websocket.endpoints.telnyx_stream import _decode_audio
        raw = bytes([0x7F, 0x80, 0xFF])
        result = _decode_audio(raw, "PCMU")
        # Output is 2 bytes per input byte
        assert len(result) == len(raw) * 2
        assert result != raw, "PCMU must be decoded (output != input)"

    def test_decode_audio_pcmu_output_is_int16(self):
        """PCMU decode output is valid signed int16 (no overflow)."""
        import struct
        from backend.interfaces.websocket.endpoints.telnyx_stream import _decode_audio
        raw = bytes(range(256))  # all possible µ-law byte values
        result = _decode_audio(raw, "PCMU")
        for i in range(0, len(result), 2):
            sample = struct.unpack_from('<h', result, i)[0]
            assert -32768 <= sample <= 32767

    def test_decode_audio_l16_does_not_call_ulaw(self):
        """L16 path never calls _ulaw_to_pcm16."""
        from backend.interfaces.websocket.endpoints import telnyx_stream
        raw = bytes([0x00, 0x01, 0x02])
        with patch.object(telnyx_stream, '_ulaw_to_pcm16') as mock_ulaw:
            telnyx_stream._decode_audio(raw, "L16")
            mock_ulaw.assert_not_called()

    def test_start_streaming_pcmu_default_payload(self):
        """start_streaming() sends PCMU with 8000Hz by default."""
        client, actions = _sdk_client()
        _run(client.start_streaming("cid-123", "wss://example.com"))
        calls = [c for c in actions.calls if c["method"] == "start_streaming"]
        assert calls, "SDK start_streaming not called"
        kwargs = calls[0]["kwargs"]
        assert kwargs["stream_bidirectional_codec"] == "PCMU"
        assert kwargs["stream_bidirectional_sampling_rate"] == 8000

    def test_start_streaming_l16_payload(self):
        """start_streaming() sends L16 with 16000Hz when codec='L16'."""
        client, actions = _sdk_client()
        _run(client.start_streaming("cid-123", "wss://example.com", codec="L16"))
        calls = [c for c in actions.calls if c["method"] == "start_streaming"]
        assert calls, "SDK start_streaming not called"
        kwargs = calls[0]["kwargs"]
        assert kwargs["stream_bidirectional_codec"] == "L16"
        assert kwargs["stream_bidirectional_sampling_rate"] == 16000

    def test_config_dto_has_audio_codec_field(self):
        """ConfigDTO has audio_codec field (the SSoT for L16/PCMU)."""
        from backend.domain.ports.config_repository_port import ConfigDTO
        cfg = ConfigDTO()
        assert hasattr(cfg, "audio_codec")
        assert cfg.audio_codec == "PCMU"  # default

    def test_config_dto_audio_codec_can_be_l16(self):
        """ConfigDTO audio_codec can be set to L16."""
        from backend.domain.ports.config_repository_port import ConfigDTO
        cfg = ConfigDTO(audio_codec="L16")
        assert cfg.audio_codec == "L16"


# ─────────────────────────────────────────────────────────────────────────────
# B-08: SDK telnyx Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestTelnyxSDK:

    def test_telnyx_sdk_importable(self):
        """telnyx SDK must be importable (pip install telnyx)."""
        import telnyx as sdk
        assert sdk is not None

    def test_telnyx_client_has_sdk_attribute(self):
        """TelnyxClient.__init__ creates _sdk (AsyncClient) — no more httpx."""
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        client = TelnyxClient(api_key="test-key")
        assert hasattr(client, "_sdk"), "_sdk attribute missing — SDK migration incomplete"
        assert not hasattr(client, "_http"), "_http still present — httpx not removed"
        _run(client.close())

    def test_telnyx_client_sdk_is_async_client(self):
        """TelnyxClient._sdk is a telnyx.AsyncClient instance."""
        import telnyx
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        client = TelnyxClient(api_key="my-test-api-key")
        assert isinstance(client._sdk, telnyx.AsyncClient), (
            f"Expected AsyncClient, got {type(client._sdk)}"
        )
        _run(client.close())


# ─────────────────────────────────────────────────────────────────────────────
# B-09: DTMF Registry and Routing Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDtmfRegistry:

    def setup_method(self):
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        DtmfRegistry.clear()

    def test_register_and_get(self):
        """register() → get() returns the same orchestrator."""
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        mock_orch = MagicMock()
        _run(DtmfRegistry.register("session-abc", mock_orch))
        assert DtmfRegistry.get("session-abc") is mock_orch

    def test_unregister_removes_session(self):
        """unregister() removes the session entry."""
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        mock_orch = MagicMock()
        _run(DtmfRegistry.register("session-xyz", mock_orch))
        _run(DtmfRegistry.unregister("session-xyz"))
        assert DtmfRegistry.get("session-xyz") is None

    def test_get_unknown_session_returns_none(self):
        """get() for non-existent session returns None (no KeyError)."""
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        assert DtmfRegistry.get("nonexistent-session") is None

    def test_count_tracks_active_sessions(self):
        """count() returns number of registered sessions."""
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        assert DtmfRegistry.count() == 0
        _run(DtmfRegistry.register("s1", MagicMock()))
        _run(DtmfRegistry.register("s2", MagicMock()))
        assert DtmfRegistry.count() == 2

    def test_multiple_unregister_is_safe(self):
        """Calling unregister() twice for same session does not raise."""
        from backend.infrastructure.registries.dtmf_registry import DtmfRegistry
        _run(DtmfRegistry.register("s-safe", MagicMock()))
        _run(DtmfRegistry.unregister("s-safe"))
        _run(DtmfRegistry.unregister("s-safe"))  # must not raise


class TestHandleDtmf:

    def test_dtmf_digit_0_triggers_transfer(self):
        """Digit '0' maps to _trigger_human_transfer()."""
        from backend.application.services.call_orchestrator import CallOrchestrator
        orch = MagicMock(spec=CallOrchestrator)
        orch.handle_dtmf = CallOrchestrator.handle_dtmf.__get__(orch, CallOrchestrator)
        orch._dtmf_map = {}
        orch._trigger_human_transfer = AsyncMock()
        orch.end_session = AsyncMock()
        orch._replay_last_message = AsyncMock()
        orch.pipeline = None
        _run(orch.handle_dtmf("0"))
        orch._trigger_human_transfer.assert_awaited_once()

    def test_dtmf_hash_triggers_hangup(self):
        """Digit '#' maps to end_session(reason='dtmf_hangup')."""
        from backend.application.services.call_orchestrator import CallOrchestrator
        orch = MagicMock(spec=CallOrchestrator)
        orch.handle_dtmf = CallOrchestrator.handle_dtmf.__get__(orch, CallOrchestrator)
        orch._dtmf_map = {}
        orch._trigger_human_transfer = AsyncMock()
        orch.end_session = AsyncMock()
        orch._replay_last_message = AsyncMock()
        orch.pipeline = None
        _run(orch.handle_dtmf("#"))
        orch.end_session.assert_awaited_once_with(reason="dtmf_hangup")

    def test_dtmf_9_triggers_replay(self):
        """Digit '9' maps to _replay_last_message()."""
        from backend.application.services.call_orchestrator import CallOrchestrator
        orch = MagicMock(spec=CallOrchestrator)
        orch.handle_dtmf = CallOrchestrator.handle_dtmf.__get__(orch, CallOrchestrator)
        orch._dtmf_map = {}
        orch._trigger_human_transfer = AsyncMock()
        orch.end_session = AsyncMock()
        orch._replay_last_message = AsyncMock()
        orch.pipeline = None
        _run(orch.handle_dtmf("9"))
        orch._replay_last_message.assert_awaited_once()

    def test_dtmf_unknown_digit_does_not_raise(self):
        """Unknown digit logs and doesn't raise."""
        from backend.application.services.call_orchestrator import CallOrchestrator
        orch = MagicMock(spec=CallOrchestrator)
        orch.handle_dtmf = CallOrchestrator.handle_dtmf.__get__(orch, CallOrchestrator)
        orch._dtmf_map = {}
        orch._trigger_human_transfer = AsyncMock()
        orch.end_session = AsyncMock()
        orch._replay_last_message = AsyncMock()
        orch.pipeline = None
        _run(orch.handle_dtmf("7"))   # No mapping → log only
        orch._trigger_human_transfer.assert_not_awaited()
        orch.end_session.assert_not_awaited()


# ─────────────────────────────────────────────────────────────────────────────
# B-10: gather_using_ai Tests
# ─────────────────────────────────────────────────────────────────────────────

def _sdk_client() -> tuple:
    """Build TelnyxClient with MockSDKActions for SDK-based assertions."""
    from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient

    class MockActions:
        def __init__(self):
            self.calls: list[dict] = []
        def _make(self, name):
            async def method(cid, **kwargs):
                self.calls.append({"method": name, "cid": cid, "kwargs": kwargs})
            return method
        def __getattr__(self, name):
            return self._make(name)

    mock_actions = MockActions()
    mock_sdk = MagicMock()
    mock_sdk.calls.actions = mock_actions
    mock_sdk.close = AsyncMock()

    client = TelnyxClient.__new__(TelnyxClient)
    client.api_key = "test-key"
    client.base_url = "https://api.telnyx.com/v2"
    client._sdk = mock_sdk
    return client, mock_actions


class TestGatherUsingAI:

    def test_gather_using_ai_correct_endpoint(self):
        """gather_using_ai() calls SDK actions.gather_using_ai()."""
        client, actions = _sdk_client()
        _run(client.gather_using_ai(
            "cid-abc",
            greeting="¿Cuál es tu nombre?",
            parameters={"type": "object", "properties": {"nombre": {"type": "string"}}},
        ))
        calls = [c for c in actions.calls if c["method"] == "gather_using_ai"]
        assert calls, "SDK actions.gather_using_ai() not called"
        assert calls[0]["cid"] == "cid-abc"

    def test_gather_using_ai_includes_greeting(self):
        """gather_using_ai() payload includes the greeting text."""
        client, actions = _sdk_client()
        _run(client.gather_using_ai(
            "cid-abc",
            greeting="Hola, ¿cuál es tu nombre?",
            parameters={"type": "object", "properties": {}},
        ))
        calls = [c for c in actions.calls if c["method"] == "gather_using_ai"]
        assert calls[0]["kwargs"]["greeting"] == "Hola, ¿cuál es tu nombre?"

    def test_gather_using_ai_includes_command_id(self):
        """gather_using_ai() includes command_id for idempotency."""
        client, actions = _sdk_client()
        _run(client.gather_using_ai("cid-abc", greeting="Hola", parameters={}))
        calls = [c for c in actions.calls if c["method"] == "gather_using_ai"]
        assert "command_id" in calls[0]["kwargs"]
        assert calls[0]["kwargs"]["command_id"].startswith("gai-")

    def test_gather_using_ai_optional_voice(self):
        """gather_using_ai() includes 'voice' when provided."""
        client, actions = _sdk_client()
        _run(client.gather_using_ai(
            "cid-abc", greeting="Hola",
            parameters={}, voice="Polly.Lupe-Neural"
        ))
        calls = [c for c in actions.calls if c["method"] == "gather_using_ai"]
        assert calls[0]["kwargs"]["voice"] == "Polly.Lupe-Neural"

    def test_gather_using_ai_no_api_key_skips(self):
        """gather_using_ai() skips silently if no API key."""
        client, actions = _sdk_client()
        client.api_key = None
        _run(client.gather_using_ai("cid-abc", greeting="Hola", parameters={}))
        gather_calls = [c for c in actions.calls if c["method"] == "gather_using_ai"]
        assert len(gather_calls) == 0, "Should NOT call SDK gather_using_ai without API key"

    def test_gather_stop_endpoint(self):
        """gather_stop() calls SDK actions.gather_stop()."""
        client, actions = _sdk_client()
        _run(client.gather_stop("cid-abc"))
        calls = [c for c in actions.calls if c["method"] == "gather_stop"]
        assert calls, "SDK actions.gather_stop() not called"
        assert "command_id" in calls[0]["kwargs"]

    def test_config_dto_has_gather_ai_fields(self):
        """ConfigDTO has all gather_ai_* fields (B-10 SSoT)."""
        from backend.domain.ports.config_repository_port import ConfigDTO
        cfg = ConfigDTO()
        assert hasattr(cfg, "gather_ai_enabled")
        assert hasattr(cfg, "gather_ai_greeting")
        assert hasattr(cfg, "gather_ai_schema")
        assert hasattr(cfg, "gather_ai_voice")
        assert cfg.gather_ai_enabled is False  # default off
