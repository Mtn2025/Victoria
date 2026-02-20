import asyncio
import base64
from typing import Optional, AsyncGenerator, List, Dict, Any
from fastapi import HTTPException

class MockAzureTTS:
    """
    High-fidelity mock for Azure Text-to-Speech.
    Simulates latency, rate limits, and valid WAV structure.
    """
    def __init__(self, latency: float = 0.1, simulate_errors: bool = False):
        self.latency = latency
        self.simulate_errors = simulate_errors

    async def speak_ssml_async(self, ssml: str) -> Any:
        """Mock the SDK method interaction."""
        await asyncio.sleep(self.latency)
        
        if self.simulate_errors:
            raise Exception("Simulated Azure Error")
            
        # Create a mock result object as expected by the adapter
        class MockResult:
            def __init__(self, data):
                self.audio_data = data
                # reason = ResultReason.SynthesizingAudioCompleted (usually an enum)
                self.reason = "SynthesizingAudioCompleted" 
                
        class MockFuture:
            def get(self):
                return MockResult(self._generate_fake_wav(len(ssml)))
            
            def _generate_fake_wav(self, length: int) -> bytes:
                 # Minimal valid WAV header
                return b"RIFF" + (length + 36).to_bytes(4, 'little') + b"WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data" + length.to_bytes(4, 'little') + b"\x00" * length

        return MockFuture()

class MockGroqLLM:
    """
    High-fidelity mock for Groq LLM.
     Simonulates token streaming and latency.
    """
    def __init__(self, latency: float = 0.05):
        self.latency = latency
        self.chat = self._MockChat()

    class _MockChat:
        def __init__(self):
            self.completions = self._MockCompletions()

        class _MockCompletions:
            async def create(self, model: str, messages: List[Dict[str, str]], stream: bool = False, **kwargs):
                if stream:
                    return self._stream_generator()
                return self._mock_response()

            async def _stream_generator(self):
                # Simulate thinking
                await asyncio.sleep(0.1)
                
                # Yield tokens
                response_text = "This is a mock response from Groq."
                for word in response_text.split(" "):
                    await asyncio.sleep(0.05)
                    
                    class MockChunk:
                        def __init__(self, content):
                            self.choices = [type('Choice', (), {'delta': type('Delta', (), {'content': content})})]
                            
                    yield MockChunk(word + " ")
                    
                # Final empty chunk
                yield MockChunk("")

            def _mock_response(self):
                 # Non-streaming response structure
                pass

class MockTelnyxClient:
    """
    High-fidelity mock for Telnyx Client.
    """
    async def answer_call(self, call_control_id: str, client_state: Optional[str] = None):
        await asyncio.sleep(0.1)
        return {"result": "ok"}

    async def start_streaming(self, call_control_id: str, stream_url: str, client_state: Optional[str] = None):
        await asyncio.sleep(0.1)
        return {"result": "ok"}
