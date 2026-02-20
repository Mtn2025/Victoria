"""
Generate Response Use Case.
Part of the Domain Layer (Hexagonal Architecture).
"""
from typing import AsyncGenerator

from backend.domain.entities.call import Call
from backend.domain.value_objects.conversation_turn import ConversationTurn
from backend.domain.ports.llm_port import LLMPort, LLMRequest, LLMMessage
from backend.domain.ports.tts_port import TTSPort


class GenerateResponseUseCase:
    """
    Orchestrates the generation of an AI response (LLM -> TTS).
    
    Domain Layer Use Case - uses only Domain types and primitives.
    Returns bytes (primitive type) to maintain architectural purity.
    """

    def __init__(self, llm_port: LLMPort, tts_port: TTSPort):
        self.llm_port = llm_port
        self.tts_port = tts_port

    async def execute(self, user_text: str, call: Call) -> AsyncGenerator[bytes, None]:
        """
        Generate a response based on user input and history.
        Streams audio chunks.
        
        Args:
            user_text: The user's input text.
            call: The active call entity.
            
        Yields:
             Audio bytes (or AudioFrame data).
        """
        # 1. Update Conversation with User Turn
        if user_text:
            call.conversation.add_turn(ConversationTurn(role="user", content=user_text))
            
        # 2. Build LLM Request
        messages = [
            LLMMessage(role=turn.role, content=turn.content) 
            for turn in call.conversation.turns
        ]
        
        request = LLMRequest(
            messages=messages,
            system_prompt=call.agent.system_prompt,
            model=call.agent.llm_config.get("model") if call.agent.llm_config else None
        )
        
        full_response_text = ""
        
        # 3. Stream LLM -> TTS
        # Logic: Accumulate text until sentence end, then TTS? 
        # For simplicity in this Phase: Accumulate all, then TTS? 
        # Or Just stream chunks if mocked?
        # The E2E test mocks LLM stream.
        # Let's simple accumulate for now to ensure robustness, or chunking.
        # Ideally: buffer sentences.
        
        async for chunk in self.llm_port.generate_stream(request):
            if chunk.text:
                full_response_text += chunk.text
                # A heuristic check for sentence end could go here to stream faster.
                
        # 4. Synthesize (Full text for now)
        if full_response_text:
            # Update History with Assistant Turn
            call.conversation.add_turn(ConversationTurn(role="assistant", content=full_response_text))
            
            # TTS
            audio_bytes = await self.tts_port.synthesize(full_response_text, call.agent.voice_config, None) # format=None for now?
            
            # Yield audio data
            if audio_bytes:
                yield audio_bytes
                
        # Future: Real streaming TTS would yield chunks loop.
