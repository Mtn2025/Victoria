
import pytest
from unittest.mock import AsyncMock, MagicMock
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
from backend.domain.value_objects.audio_format import AudioFormat

class MockConfig:
    client_type = "twilio"


class MockBrowserConfig:
    client_type = "browser"

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
    assert chain[0]._next == chain[1]
    assert chain[1]._next == chain[2]
    assert chain[2]._next == chain[3]

    # Verify STTProcessor received telephony format (twilio = 8kHz MuLaw)
    stt: STTProcessor = chain[1]
    assert stt.audio_format is not None
    assert stt.audio_format.sample_rate == 8000
    assert stt.audio_format.encoding == "mulaw"


@pytest.mark.asyncio
async def test_pipeline_creation_browser():
    """PipelineFactory debe pasar 24kHz PCM al STTProcessor para clientes browser."""
    config = MockBrowserConfig()
    stt_port = MagicMock(spec=STTPort)
    llm_port = MagicMock(spec=LLMPort)
    tts_port = MagicMock(spec=TTSPort)
    detect_turn = MagicMock(spec=DetectTurnEndUseCase)
    execute_tool = MagicMock(spec=ExecuteToolUseCase)
    history = []

    processors = await PipelineFactory.create_pipeline(
        config, stt_port, llm_port, tts_port, detect_turn, execute_tool, history
    )

    chain = processors.processors
    stt: STTProcessor = chain[1]

    # El STTProcessor debe recibir el formato del browser (24kHz PCM16)
    assert stt.audio_format is not None, "audio_format no debe ser None para browser"
    assert stt.audio_format.sample_rate == 24000, (
        f"Browser necesita 24kHz, recibio {stt.audio_format.sample_rate}"
    )
    assert stt.audio_format.encoding == "pcm"
    assert stt.audio_format.bits_per_sample == 16


@pytest.mark.asyncio
async def test_stt_raises_without_format():
    """STTProcessor debe lanzar ValueError si start() se llama sin audio_format."""
    mock_port = MagicMock(spec=STTPort)
    # Instanciar sin audio_format (simula el bug anterior)
    stt = STTProcessor(stt_provider=mock_port)
    assert stt.audio_format is None

    with pytest.raises(ValueError, match="audio_format"):
        await stt.start()
