from typing import Dict, Type
from backend.domain.ports.telephony_port import TelephonyPort
from backend.infrastructure.adapters.telephony.telnyx_client import TelnyxClient
from backend.infrastructure.adapters.telephony.twilio_adapter import TwilioAdapter
from backend.infrastructure.adapters.telephony.dummy_adapter import DummyTelephonyAdapter

class TelephonyAdapterFactory:
    """
    Factory to select the appropriate Telephony Adapter based on client type.
    """
    
    @staticmethod
    def get_adapter(client_type: str) -> TelephonyPort:
        if client_type == "telnyx":
            # In a real DI scenario, this would come from a container
            return TelnyxClient()
        elif client_type == "twilio":
            return TwilioAdapter()
        elif client_type == "browser":
            # Browser might not need full telephony control, 
            # or uses a specific adapter for simulation.
            # For now, Dummy is safe or a specific BrowserAdapter.
            return DummyTelephonyAdapter()
        else:
            # Default fallback or error
            return DummyTelephonyAdapter()
