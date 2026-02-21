from backend.domain.ports.persistence_port import CallRepository, AgentRepository
from backend.domain.ports.stt_port import STTPort, STTSession
from backend.domain.ports.llm_port import LLMPort, LLMResponseChunk
from backend.domain.ports.tts_port import TTSPort
from backend.domain.ports.telephony_port import TelephonyPort
from backend.domain.entities.call import Call
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.call_id import CallId
from typing import Optional, AsyncGenerator, AsyncIterator

class MockCallRepository(CallRepository):
    def __init__(self):
        self.calls = {}
        
    async def save(self, call: Call) -> None:
        self.calls[call.id.value] = call
        
    async def get_by_id(self, call_id: CallId) -> Optional[Call]:
        return self.calls.get(call_id.value)
        
    async def get_calls(self, limit=20, offset=0, client_type=None):
        return list(self.calls.values()), len(self.calls)

    async def delete(self, call_id: CallId) -> None:
        if call_id.value in self.calls:
            del self.calls[call_id.value]
            
    async def clear(self) -> int:
        count = len(self.calls)
        self.calls.clear()
        return count

class MockAgentRepository(AgentRepository):
    def __init__(self):
        self.agents = {}

    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    async def update_agent(self, agent: Agent) -> None:
        self.agents[agent.name] = agent  # name as key for mock

    # ------------------------------------------------------------------ #
    # New abstract methods required by AgentRepository port               #
    # ------------------------------------------------------------------ #

    async def get_all_agents(self) -> list:
        return list(self.agents.values())

    async def create_agent(self, agent: Agent) -> Agent:
        self.agents[agent.name] = agent
        return agent

    async def get_agent_by_uuid(self, agent_uuid: str) -> Optional[Agent]:
        for agent in self.agents.values():
            if getattr(agent, 'agent_uuid', None) == agent_uuid:
                return agent
        return None

    async def set_active_agent(self, agent_uuid: str) -> Agent:
        target = None
        for agent in self.agents.values():
            agent.is_active = (getattr(agent, 'agent_uuid', None) == agent_uuid)
            if agent.is_active:
                target = agent
        if target is None:
            from backend.domain.ports.persistence_port import AgentNotFoundError
            raise AgentNotFoundError(f"No agent with uuid={agent_uuid}")
        return target

    async def delete_agent(self, agent_uuid: str) -> None:
        agent = await self.get_agent_by_uuid(agent_uuid)
        if agent:
            del self.agents[agent.name]

class MockSTTPort(STTPort):
    async def transcribe(self, audio: bytes, format, language="es-MX") -> str:
        return "mock transcription"
        
    async def start_stream(self, format, language="es-MX") -> STTSession:
        pass # Not needed for simple UC tests usually

    async def close(self) -> None:
        pass

class MockLLMPort(LLMPort):
    async def generate_response(self, conversation, agent) -> str:
        return "mock response"
        
    async def generate_stream(self, request) -> AsyncIterator[LLMResponseChunk]:
        yield LLMResponseChunk(text="mock response")

    async def get_available_models(self):
        return ["mock-model-1", "mock-model-2"]

    def is_model_safe_for_voice(self, model: str) -> bool:
        return True

class MockTelephonyPort(TelephonyPort):
    def __init__(self):
        self.ended_calls = []
        
    async def end_call(self, call_id: CallId) -> None:
        self.ended_calls.append(call_id.value)
        
    async def transfer_call(self, call_id, target) -> None:
        pass
        
    async def send_dtmf(self, call_id, digits) -> None:
        pass

    async def answer_call(self, call_control_id: str) -> None:
        pass

    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: str = None) -> None:
        pass

class MockTTSPort(TTSPort):
    async def synthesize(self, text, voice, format) -> bytes:
        return b"mock audio bytes"

    async def synthesize_stream(self, text, voice, format):
        yield b"mock audio bytes"

    async def get_available_voices(self, language=None):
        return []

    async def get_voice_styles(self, voice_name: str) -> list[str]:
        return ["default"]

    async def synthesize_ssml(self, ssml: str, format) -> bytes:
        return b"mock ssml audio"

    async def synthesize_request(self, request) -> bytes:
        return b"mock request audio"

    async def close(self) -> None:
        pass
