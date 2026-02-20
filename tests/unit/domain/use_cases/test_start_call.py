import pytest
from backend.domain.use_cases.start_call import StartCallUseCase
from backend.domain.entities.agent import Agent
from backend.domain.value_objects.voice_config import VoiceConfig
from tests.mocks.mock_ports import MockCallRepository, MockAgentRepository

class TestStartCallUseCase:
    @pytest.fixture
    def mock_repos(self):
        call_repo = MockCallRepository()
        agent_repo = MockAgentRepository()
        
        # Seed an agent
        agent = Agent(name="agent-1", system_prompt="sys", voice_config=VoiceConfig(name="v"))
        agent_repo.agents["agent-1"] = agent
        
        return call_repo, agent_repo

    @pytest.mark.asyncio
    async def test_start_call_success(self, mock_repos):
        call_repo, agent_repo = mock_repos
        uc = StartCallUseCase(call_repo, agent_repo)
        
        call = await uc.execute(
            agent_id="agent-1",
            call_id_value="call-123",
            from_number="+15551234567"
        )
        
        assert call is not None
        assert call.id.value == "call-123"
        assert call.status == "in_progress" # UC calls start()
        
        # Verify persistence
        saved_call = await call_repo.get_by_id(call.id)
        assert saved_call is not None
        assert saved_call.id.value == "call-123"

    @pytest.mark.asyncio
    async def test_start_call_agent_not_found(self, mock_repos):
        call_repo, agent_repo = mock_repos
        uc = StartCallUseCase(call_repo, agent_repo)
        
        with pytest.raises(ValueError, match="Agent not found"):
            await uc.execute(agent_id="unknown", call_id_value="call-123")
