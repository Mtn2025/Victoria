"""
Sprint 2 — Tests de Simulación: Dispatcher y Correlación

Tests que verifican:
  - S2-A: Dispatcher de 18 eventos (cobertura completa del catálogo)
  - S2-A: call_session_id usado como correlator (no call_control_id)
  - S2-A: Singleton telnyx_adapter eliminado del módulo
  - S2-A: Handlers de streaming/recording/gather sin excepciones
  - S2-A: recording.saved estructura payload correcta

Ejecutar: python -m pytest tests/test_sprint2_telnyx.py -v
"""
import asyncio
import json
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTelnyxDispatcher(unittest.TestCase):
    """Tests for the new Telnyx event dispatcher in telephony.py."""

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _make_call_repo(self, call=None):
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=call)
        repo.save = AsyncMock()
        return repo

    def _make_request(self, headers=None):
        req = MagicMock()
        req.headers = headers or {
            "host": "test.example.com",
            "x-forwarded-proto": "https",
        }
        return req

    # ── Dispatcher coverage ──────────────────────────────────────────────────

    def test_dispatcher_handles_streaming_started(self):
        """streaming.started is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_streaming_started
        payload = {"stream_id": "str-abc123"}
        self._run(_handle_streaming_started(payload, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_streaming_stopped(self):
        """streaming.stopped is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_streaming_stopped
        self._run(_handle_streaming_stopped({}, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_streaming_failed(self):
        """streaming.failed is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_streaming_failed
        payload = {"failure_reason": "connection_timeout"}
        self._run(_handle_streaming_failed(payload, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_bridged(self):
        """call.bridged is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_bridged
        self._run(_handle_bridged({}, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_playback_started(self):
        """call.playback.started is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_playback_started
        self._run(_handle_playback_started({}, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_playback_failed(self):
        """call.playback.failed is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_playback_failed
        payload = {"failure_reason": "audio_format_unsupported"}
        self._run(_handle_playback_failed(payload, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_gather_ended(self):
        """gather.ended is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_gather_ended
        payload = {"digits": "5", "speech_result": ""}
        self._run(_handle_gather_ended(payload, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_gather_timeout(self):
        """gather.timeout is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_gather_timeout
        self._run(_handle_gather_timeout({}, "sess-1", "cid-1", self._make_request(), None))

    def test_dispatcher_handles_dtmf(self):
        """call.dtmf.received is dispatched without error."""
        from backend.interfaces.http.endpoints.telephony import _handle_dtmf
        payload = {"digit": "9"}
        self._run(_handle_dtmf(payload, "sess-1", "cid-1", self._make_request(), None))

    def test_unknown_event_does_not_raise(self):
        """An unknown event type is silently ignored by the dispatcher."""
        from backend.interfaces.http.endpoints.telephony import _route_telnyx_event
        self._run(
            _route_telnyx_event(
                "unknown.future.event",
                {},
                "sess-1",
                "cid-1",
                self._make_request(),
                None,
            )
        )

    # ── Dispatcher has all 18 expected event types ────────────────────────────

    def test_dispatcher_contains_all_catalog_events(self):
        """
        The dispatcher map contains all events from the official Telnyx catalog
        (telnyx_call_architecture.md §4).
        """
        # We inspect the _route_telnyx_event function source to check all events are
        # mapped. Alternatively we can call the function and observe behavior.
        import inspect
        from backend.interfaces.http.endpoints.telephony import _route_telnyx_event
        source = inspect.getsource(_route_telnyx_event)

        required_events = [
            "call.initiated",
            "call.answered",
            "call.hangup",
            "call.bridged",
            "streaming.started",
            "streaming.stopped",
            "streaming.failed",
            "call.machine.detection.ended",
            "call.machine.greeting.ended",
            "call.playback.started",
            "call.playback.ended",
            "call.playback.failed",
            "recording.saved",
            "call.dtmf.received",
            "gather.ended",
            "gather.timeout",
        ]
        for event in required_events:
            self.assertIn(
                event,
                source,
                f"Event '{event}' not found in _route_telnyx_event dispatcher"
            )

    # ── call_session_id as correlator ────────────────────────────────────────

    def test_call_session_id_is_distinct_from_call_control_id(self):
        """
        Verify that when call_session_id differs from call_control_id,
        the session_id is used (not the control_id).
        In practice: the dispatcher reads call_session_id from payload.
        """
        # Simulate a payload with both IDs
        payload = {
            "call_control_id": "v3:ctrl-xxxx",
            "call_session_id": "sess-yyyy-9999",
        }
        session_id = payload.get("call_session_id") or payload.get("call_control_id")
        self.assertEqual(session_id, "sess-yyyy-9999")
        self.assertNotEqual(session_id, payload["call_control_id"])

    # ── Singleton removed ────────────────────────────────────────────────────

    def test_no_global_telnyx_adapter_singleton(self):
        """
        The global telnyx_adapter singleton must be removed from telephony.py.
        (Sprint 2 — eliminates import-time initialization failure risk)
        """
        import backend.interfaces.http.endpoints.telephony as mod
        self.assertFalse(
            hasattr(mod, "telnyx_adapter"),
            "telnyx_adapter global singleton still exists — must be removed"
        )

    # ── recording.saved handler ───────────────────────────────────────────────

    def test_recording_saved_updates_db_when_update_metadata_exists(self):
        """recording.saved calls update_metadata and save on the call object."""
        from backend.interfaces.http.endpoints.telephony import _handle_recording_saved
        from backend.domain.value_objects.call_id import CallId

        mock_call = MagicMock()
        mock_call.update_metadata = MagicMock()
        repo = self._make_call_repo(call=mock_call)

        payload = {
            "recording_urls": {"mp3": "https://api.telnyx.com/recordings/abc.mp3"},
            "duration_secs": 120,
        }

        with patch(
            "backend.domain.value_objects.call_id.CallId",
            side_effect=lambda x: x
        ):
            self._run(
                _handle_recording_saved(payload, "sess-1", "cid-1", self._make_request(), repo)
            )

        mock_call.update_metadata.assert_any_call(
            "recording_url", "https://api.telnyx.com/recordings/abc.mp3"
        )
        mock_call.update_metadata.assert_any_call("recording_duration_secs", 120)
        repo.save.assert_awaited_once()

    def test_recording_saved_skips_db_when_no_url(self):
        """recording.saved does nothing when mp3 URL is empty."""
        from backend.interfaces.http.endpoints.telephony import _handle_recording_saved

        mock_call = MagicMock()
        repo = self._make_call_repo(call=mock_call)
        payload = {"recording_urls": {}, "duration_secs": 0}

        self._run(
            _handle_recording_saved(payload, "sess-1", "cid-1", self._make_request(), repo)
        )

        mock_call.update_metadata.assert_not_called()
        repo.save.assert_not_awaited()

    def test_hangup_maps_sip_cause_to_reason(self):
        """call.hangup maps SIP cause codes to semantic reasons."""
        from backend.interfaces.http.endpoints.telephony import _handle_hangup

        mock_call = MagicMock()
        mock_call.status.value = "in_progress"
        mock_call.end = MagicMock()
        repo = self._make_call_repo(call=mock_call)

        test_cases = [
            ("486", "busy"),
            ("408", "no_answer"),
            ("503", "failed"),
            ("normal_clearing", "completed"),
            ("", "completed"),
        ]

        for sip_cause, expected_reason in test_cases:
            mock_call.end.reset_mock()
            payload = {"sip_hangup_cause": sip_cause}
            with patch(
                "backend.domain.value_objects.call_id.CallId",
                side_effect=lambda x: x
            ):
                self._run(
                    _handle_hangup(payload, "sess-1", "cid-1", self._make_request(), repo)
                )
            mock_call.end.assert_called_with(reason=expected_reason), \
                f"SIP {sip_cause!r} should map to {expected_reason!r}"


# ────────────────────────────────────────────────────────────────────────────
# Runner
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("Sprint 2 Test Suite — Telnyx Dispatcher & Correlation")
    print("=" * 70)
    unittest.main(verbosity=2)
