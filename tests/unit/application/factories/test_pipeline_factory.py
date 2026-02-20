
import pytest
from unittest.mock import MagicMock
from backend.application.factories.pipeline_factory import PipelineFactory
from backend.application.processors.vad_processor import VADProcessor
from backend.application.processors.stt_processor import STTProcessor
from backend.application.processors.llm_processor import LLMProcessor
from backend.application.processors.tts_processor import TTSProcessor
from backend.domain.ports.stt_port import STTPort
from backend.domain.ports.tts_port import TTSPort
from backend.domain.ports.llm_port import LLMPort
from backend.domain.use_cases.detect_turn_end import DetectTurnEndUseCase
from backend.domain.use_cases.execute_tool import ExecuteToolUseCase

class MockConfig:
    client_type = "twilio"

@pytest.mark.asyncio
async def test_pipeline_creation():
    config = MockConfig()
    stt_port = MagicMock(spec=STTPort)
    llm_port = MagicMock(spec=LLMPort)
    tts_port = MagicMock(spec=TTSPort)
    detect_turn = MagicMock(spec=DetectTurnEndUseCase)
    execute_tool = MagicMock(spec=ExecuteToolUseCase)
    history = []
    
    processors = await PipelineFactory.create_pipeline(
        config, stt_port, llm_port, tts_port, detect_turn, execute_tool, history
    )
    
    # Verify sequence
    assert len(processors) == 4
    chain = processors.processors
    assert isinstance(chain[0], VADProcessor)
    assert isinstance(chain[1], STTProcessor)
    assert isinstance(chain[2], LLMProcessor)
    assert isinstance(chain[3], TTSProcessor)
    
    # Verify Wiring
    # vad -> stt
    # stt -> llm
    # llm -> tts
    
    # We can check internal _downstream if available, but it's protected.
    # We can rely on logic that link() assigns it.
    # processor.dict_link? 
    # Let's trust constructor logic for now or inspect protected members.
    
    assert chain[0]._next == chain[1]
    assert chain[1]._next == chain[2]
    assert chain[2]._next == chain[3]
