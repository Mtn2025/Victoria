"""
Sprint 1 — Tests de Simulación: Seguridad e Infraestructura Telnyx

Tests que verifican:
  - S1-A: Módulo de firma Ed25519 (bypass en dev, bloqueo sin clave)
  - S1-B: TelnyxClient (command_id presente, httpx persistente)
  - S1-C: Conversión µ-law → PCM16 (sin audioop, Python 3.13 compatible)
  - S1-C: Dead code 'worker_task' eliminado de telnyx_stream.py

Ejecutar: python -m pytest test_sprint1_telnyx.py -v
"""
import asyncio
import inspect
import struct
import sys
import unittest
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch


# ────────────────────────────────────────────────────────────────────────────
# S1-C: Conversión µ-law
# ────────────────────────────────────────────────────────────────────────────

def _get_ulaw_converter():
    """Import the pure-Python µ-law converter from telnyx_stream."""
    from backend.interfaces.websocket.endpoints.telnyx_stream import _ulaw_to_pcm16
    return _ulaw_to_pcm16


class TestUlawConversion(unittest.TestCase):
    """Tests for the pure-Python G.711 µ-law to PCM16 converter."""

    def setUp(self):
        self.convert = _get_ulaw_converter()

    def test_output_size_is_double_input(self):
        """Each µ-law byte produces exactly 2 PCM16 bytes."""
        for size in [1, 10, 160, 320]:  # 160 bytes = 20ms @8kHz
            ulaw = bytes([0xFF] * size)
            pcm = self.convert(ulaw)
            self.assertEqual(
                len(pcm), size * 2,
                f"Expected {size*2} bytes, got {len(pcm)} for input size {size}"
            )

    def test_silence_maps_to_near_zero(self):
        """µ-law silence (0xFF) maps to PCM samples near zero."""
        ulaw = bytes([0xFF] * 10)
        pcm = self.convert(ulaw)
        samples = [
            struct.unpack('<h', pcm[i:i+2])[0]
            for i in range(0, len(pcm), 2)
        ]
        for s in samples:
            self.assertLess(abs(s), 200, f"Silence sample too large: {s}")

    def test_output_is_bytes(self):
        """Output is always bytes, never bytearray."""
        ulaw = bytes([0x80, 0x7F, 0x00])
        pcm = self.convert(ulaw)
        self.assertIsInstance(pcm, bytes)

    def test_all_byte_values_produce_valid_int16(self):
        """All 256 possible µ-law values convert without error."""
        ulaw = bytes(range(256))
        pcm = self.convert(ulaw)
        self.assertEqual(len(pcm), 256 * 2)
        # All samples must be valid int16
        for i in range(0, len(pcm), 2):
            sample = struct.unpack('<h', pcm[i:i+2])[0]
            self.assertGreaterEqual(sample, -32768)
            self.assertLessEqual(sample, 32767)

    def test_no_audioop_imported(self):
        """Confirm audioop is NOT imported as a module (removed in Python 3.13)."""
        import backend.interfaces.websocket.endpoints.telnyx_stream as mod
        # Check that 'audioop' is not in the actual imported modules
        self.assertNotIn(
            'audioop',
            mod.__dict__,
            "audioop is still imported as a module attribute — must be replaced"
        )
        # Also verify the converter function exists (meaning replacement was implemented)
        self.assertTrue(
            hasattr(mod, '_ulaw_to_pcm16'),
            "_ulaw_to_pcm16 function missing — audioop replacement not implemented"
        )

    def test_no_dead_worker_task_code(self):
        """Confirm dead code pattern 'worker_task' is removed from telnyx_stream.py."""
        import backend.interfaces.websocket.endpoints.telnyx_stream as mod
        source = inspect.getsource(mod)
        # The dead code pattern was: if 'worker_task' in locals() and worker_task:
        self.assertNotIn(
            "'worker_task' in locals()",
            source,
            "Dead code pattern 'worker_task' in locals() still present in telnyx_stream.py"
        )


# ────────────────────────────────────────────────────────────────────────────
# S1-A: Signature verification
# ────────────────────────────────────────────────────────────────────────────

class TestTelnyxSignature(unittest.TestCase):
    """Tests for the Ed25519 signature verification module."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _make_request(self, headers: dict) -> MagicMock:
        req = MagicMock()
        req.headers = headers
        return req

    def test_dev_bypass_always_true(self):
        """In development environment, signature check is bypassed (returns True)."""
        from backend.infrastructure.security.telnyx_signature import verify_telnyx_signature

        async def run():
            # settings is imported lazy inside verify_telnyx_signature,
            # so we patch it at the infrastructure config level
            with patch(
                "backend.infrastructure.config.settings.settings"
            ) as mock_settings:
                mock_settings.ENVIRONMENT = "development"
                req = self._make_request({})
                result = await verify_telnyx_signature(req, b"any_body")
                return result

        self.assertTrue(self._run(run()), "Dev bypass should return True")

    def test_returns_false_without_public_key(self):
        """Without TELNYX_PUBLIC_KEY configured, verification fails safely."""
        from backend.infrastructure.security.telnyx_signature import verify_telnyx_signature

        async def run():
            with patch(
                "backend.infrastructure.config.settings.settings"
            ) as mock_settings:
                mock_settings.ENVIRONMENT = "production"
                mock_settings.TELNYX_PUBLIC_KEY = None
                req = self._make_request({})
                result = await verify_telnyx_signature(req, b"body")
                return result

        self.assertFalse(self._run(run()), "Should return False without public key")

    def test_returns_false_with_missing_headers(self):
        """Missing signature headers return False (not an exception)."""
        from backend.infrastructure.security.telnyx_signature import verify_telnyx_signature

        async def run():
            with patch(
                "backend.infrastructure.config.settings.settings"
            ) as mock_settings:
                mock_settings.ENVIRONMENT = "production"
                mock_settings.TELNYX_PUBLIC_KEY = "dGVzdA=="  # base64 'test'
                req = self._make_request({})  # no signature headers
                result = await verify_telnyx_signature(req, b"body")
                return result

        self.assertFalse(self._run(run()), "Should return False without headers")

    def test_returns_false_with_old_timestamp(self):
        """Timestamps older than 5 minutes are rejected."""
        from backend.infrastructure.security.telnyx_signature import verify_telnyx_signature
        import time

        async def run():
            with patch(
                "backend.infrastructure.config.settings.settings"
            ) as mock_settings:
                mock_settings.ENVIRONMENT = "production"
                mock_settings.TELNYX_PUBLIC_KEY = "dGVzdA=="
                old_timestamp = str(int(time.time()) - 400)  # 400s ago
                req = self._make_request({
                    "telnyx-signature-ed25519": "c2ln",
                    "telnyx-timestamp": old_timestamp,
                })
                result = await verify_telnyx_signature(req, b"body")
                return result

        self.assertFalse(self._run(run()), "Old timestamp should be rejected")


# ────────────────────────────────────────────────────────────────────────────
# S1-B: TelnyxClient
# ────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────
# S1-B: TelnyxClient — ahora con SDK oficial
# ────────────────────────────────────────────────────────────────────────────

class MockSDKActions:
    """
    Fake telnyx SDK actions resource.
    Captures method calls and their kwargs for assertion.
    """
    def __init__(self):
        self.calls: list[dict] = []

    def _make_method(self, name):
        async def method(call_control_id, **kwargs):
            self.calls.append({"method": name, "cid": call_control_id, "kwargs": kwargs})
        return method

    def __getattr__(self, name):
        return self._make_method(name)


def _make_sdk_client() -> tuple:
    """Build a TelnyxClient wired to MockSDKActions."""
    from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient

    mock_actions = MockSDKActions()

    mock_calls_resource = MagicMock()
    mock_calls_resource.actions = mock_actions

    mock_sdk = MagicMock()
    mock_sdk.calls = mock_calls_resource
    mock_sdk.close = AsyncMock()

    client = TelnyxClient.__new__(TelnyxClient)
    client.api_key = "test-key"
    client.base_url = "https://api.telnyx.com/v2"
    client._sdk = mock_sdk
    return client, mock_actions


class TestTelnyxClient(unittest.TestCase):
    """Tests for TelnyxClient using the official telnyx SDK (4.x)."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_answer_call_includes_command_id(self):
        """answer_call() must include command_id (idempotency)."""
        client, actions = _make_sdk_client()
        self._run(client.answer_call("ctrl-test-abcd1234"))
        calls = [c for c in actions.calls if c["method"] == "answer"]
        self.assertTrue(calls, "SDK actions.answer() was not called")
        kwargs = calls[0]["kwargs"]
        self.assertIn("command_id", kwargs, "command_id MISSING from answer_call")
        self.assertTrue(kwargs["command_id"].startswith("ans-"))

    def test_start_streaming_includes_command_id(self):
        """start_streaming() must include command_id."""
        client, actions = _make_sdk_client()
        self._run(client.start_streaming("ctrl-abcd1234", "wss://example.com/ws"))
        calls = [c for c in actions.calls if c["method"] == "start_streaming"]
        self.assertTrue(calls, "SDK actions.start_streaming() was not called")
        kwargs = calls[0]["kwargs"]
        self.assertIn("command_id", kwargs, "command_id MISSING from start_streaming")
        self.assertTrue(kwargs["command_id"].startswith("str-"))

    def test_end_call_includes_command_id(self):
        """end_call() must include command_id."""
        from backend.domain.value_objects.call_id import CallId
        client, actions = _make_sdk_client()
        self._run(client.end_call(CallId("ctrl-abcd1234")))
        calls = [c for c in actions.calls if c["method"] == "hangup"]
        self.assertTrue(calls, "SDK actions.hangup() was not called")
        kwargs = calls[0]["kwargs"]
        self.assertIn("command_id", kwargs, "command_id MISSING from end_call")
        self.assertTrue(kwargs["command_id"].startswith("hup-"))

    def test_start_recording_includes_command_id(self):
        """start_recording() must include command_id."""
        client, actions = _make_sdk_client()
        self._run(client.start_recording("ctrl-abcd1234"))
        calls = [c for c in actions.calls if c["method"] == "record_start"]
        self.assertTrue(calls, "SDK actions.record_start() was not called")
        kwargs = calls[0]["kwargs"]
        self.assertIn("command_id", kwargs, "command_id MISSING from start_recording")
        self.assertTrue(kwargs["command_id"].startswith("rec-"))

    def test_sdk_client_is_persistent(self):
        """The same _sdk client instance is reused (no new client per call)."""
        client, actions = _make_sdk_client()
        sdk_id_before = id(client._sdk)
        self._run(client.answer_call("ctrl-aaaa1111"))
        self._run(client.answer_call("ctrl-bbbb2222"))
        sdk_id_after = id(client._sdk)
        self.assertEqual(
            sdk_id_before, sdk_id_after,
            "SDK client was replaced between calls — not persistent!"
        )

    def test_command_ids_are_unique(self):
        """Two calls to the same method produce different command_ids."""
        client, actions = _make_sdk_client()
        self._run(client.answer_call("ctrl-test-1234xxxx"))
        self._run(client.answer_call("ctrl-test-1234xxxx"))
        answer_calls = [c for c in actions.calls if c["method"] == "answer"]
        ids = [c["kwargs"]["command_id"] for c in answer_calls]
        self.assertEqual(len(ids), 2)
        self.assertNotEqual(ids[0], ids[1], "command_ids must be unique per call")

    def test_no_api_key_skips_call(self):
        """With no API key, no SDK call is made (silent skip)."""
        client, actions = _make_sdk_client()
        client.api_key = None
        self._run(client.answer_call("ctrl-xyz"))
        answer_calls = [c for c in actions.calls if c["method"] == "answer"]
        self.assertEqual(len(answer_calls), 0, "Should NOT call SDK without API key")

    def test_uses_sdk_not_httpx(self):
        """TelnyxClient must NOT have _http (httpx) attribute — SDK only."""
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        client = TelnyxClient.__new__(TelnyxClient)
        self.assertFalse(
            hasattr(client, "_http"),
            "TelnyxClient still has _http (httpx) — migration to SDK incomplete"
        )

    def test_has_sdk_attribute(self):
        """TelnyxClient must have _sdk (official telnyx.AsyncClient)."""
        from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
        with patch("backend.infrastructure.adapters.telephony.telnyx_client.settings") as ms:
            ms.TELNYX_API_KEY = "fake-key"
            ms.TELNYX_API_BASE = "https://api.telnyx.com/v2"
            client = TelnyxClient()
            self.assertTrue(hasattr(client, "_sdk"), "_sdk attribute missing")
            self.assertIsNotNone(client._sdk)
            self._run(client.close())

    def test_start_streaming_l16_uses_sdk(self):
        """start_streaming() with L16 passes correct codec to SDK."""
        client, actions = _make_sdk_client()
        self._run(client.start_streaming("ctrl-l16", "wss://example.com", codec="L16"))
        calls = [c for c in actions.calls if c["method"] == "start_streaming"]
        self.assertTrue(calls, "SDK start_streaming not called")
        kwargs = calls[0]["kwargs"]
        self.assertEqual(kwargs.get("stream_bidirectional_codec"), "L16")
        self.assertEqual(kwargs.get("stream_bidirectional_sampling_rate"), 16000)


# ────────────────────────────────────────────────────────────────────────────
# Runner
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Sprint 1 Test Suite — Telnyx Security & Infrastructure")
    print("=" * 70)
    unittest.main(verbosity=2)

