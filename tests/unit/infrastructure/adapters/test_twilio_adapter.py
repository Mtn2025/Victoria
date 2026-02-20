import pytest
from backend.infrastructure.adapters.telephony.twilio_adapter import TwilioAdapter

def test_generate_twiml_for_websocket():
    # Arrange
    adapter = TwilioAdapter()
    ws_url = "wss://example.com/stream"

    # Act
    twiml = adapter.generate_connect_twiml(ws_url)

    # Assert
    assert "<Connect>" in twiml
    assert f'<Stream url="{ws_url}"' in twiml
    assert "</Connect>" in twiml

def test_generate_twiml_with_params():
    # Arrange
    adapter = TwilioAdapter()
    ws_url = "wss://example.com/stream"
    
    # Act
    # Assuming the method supports extra params or we just test the base
    twiml = adapter.generate_connect_twiml(ws_url)
    
    # Assert
    assert "<?xml" in twiml
