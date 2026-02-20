"""
Unit tests for ControlChannel.

Tests signal sending, receiving, and queue management.
"""
import pytest
import asyncio

from backend.application.services.control_channel import (
    ControlChannel,
    ControlSignal,
    ControlMessage,
    send_interrupt,
    send_cancel,
    send_emergency_stop
)


class TestControlChannel:
    """Test control channel signal management."""
    
    @pytest.mark.asyncio
    async def test_send_and_receive_signal(self):
        """Test basic signal send and receive."""
        channel = ControlChannel()
        
        await channel.send_signal(
            ControlSignal.INTERRUPT,
            metadata={'text': 'hello'}
        )
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg is not None
        assert msg.signal == ControlSignal.INTERRUPT
        assert msg.metadata['text'] == 'hello'
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        """Test wait_for_signal returns None on timeout."""
        channel = ControlChannel()
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg is None
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_multiple_signals(self):
        """Test multiple signals are processed in order."""
        channel = ControlChannel()
        
        await channel.send_signal(ControlSignal.INTERRUPT)
        await channel.send_signal(ControlSignal.CANCEL)
        await channel.send_signal(ControlSignal.CLEAR_PIPELINE)
        
        msg1 = await channel.wait_for_signal(timeout=0.1)
        msg2 = await channel.wait_for_signal(timeout=0.1)
        msg3 = await channel.wait_for_signal(timeout=0.1)
        
        assert msg1.signal == ControlSignal.INTERRUPT
        assert msg2.signal == ControlSignal.CANCEL
        assert msg3.signal == ControlSignal.CLEAR_PIPELINE
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_clear_pending_signals(self):
        """Test clear removes all pending signals."""
        channel = ControlChannel()
        
        await channel.send_signal(ControlSignal.INTERRUPT)
        await channel.send_signal(ControlSignal.CANCEL)
        await channel.send_signal(ControlSignal.INTERRUPT)
        
        assert channel.pending_count == 3
        
        await channel.clear()
        
        assert channel.pending_count == 0
        
        msg = await channel.wait_for_signal(timeout=0.1)
        assert msg is None
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_send_after_close_is_ignored(self):
        """Test signals sent after close are dropped."""
        channel = ControlChannel()
        channel.close()
        
        await channel.send_signal(ControlSignal.INTERRUPT)
        
        assert channel.is_active is False
        assert channel.pending_count == 0
    
    @pytest.mark.asyncio
    async def test_receive_after_close_returns_none(self):
        """Test wait_for_signal returns None after close."""
        channel = ControlChannel()
        
        await channel.send_signal(ControlSignal.INTERRUPT)
        channel.close()
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg is None
    
    @pytest.mark.asyncio
    async def test_send_interrupt_helper(self):
        """Test send_interrupt convenience function."""
        channel = ControlChannel()
        
        await send_interrupt(channel, reason="user_spoke", text="hello")
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg.signal == ControlSignal.INTERRUPT
        assert msg.metadata['reason'] == "user_spoke"
        assert msg.metadata['text'] == "hello"
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_send_cancel_helper(self):
        """Test send_cancel convenience function."""
        channel = ControlChannel()
        
        await send_cancel(channel, reason="user_interrupted")
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg.signal == ControlSignal.CANCEL
        assert msg.metadata['reason'] == "user_interrupted"
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_send_emergency_stop_helper(self):
        """Test send_emergency_stop convenience function."""
        channel = ControlChannel()
        
        await send_emergency_stop(channel, reason="max_duration_exceeded")
        
        msg = await channel.wait_for_signal(timeout=0.1)
        
        assert msg.signal == ControlSignal.EMERGENCY_STOP
        assert msg.metadata['reason'] == "max_duration_exceeded"
        
        channel.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_send_receive(self):
        """Test concurrent producers and consumer."""
        channel = ControlChannel()
        
        async def producer():
            for i in range(5):
                await channel.send_signal(
                    ControlSignal.INTERRUPT,
                    metadata={'count': i}
                )
                await asyncio.sleep(0.01)
        
        async def consumer():
            received = []
            for _ in range(5):
                msg = await channel.wait_for_signal(timeout=1.0)
                if msg:
                    received.append(msg.metadata['count'])
            return received
        
        producer_task = asyncio.create_task(producer())
        consumer_task = asyncio.create_task(consumer())
        
        await producer_task
        counts = await consumer_task
        
        assert counts == [0, 1, 2, 3, 4]
        
        channel.close()
