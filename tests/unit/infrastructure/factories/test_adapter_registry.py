"""
Unit tests for AdapterRegistry.

Tests cover:
- Basic registration and retrieval
- Runtime swapping
- Input validation
- Edge cases
- Magic methods
"""
import pytest
from unittest.mock import Mock
from backend.infrastructure.factories.adapter_registry import AdapterRegistry


class MockAdapter:
    """Mock adapter for testing."""
    def __init__(self, name: str = "MockAdapter"):
        self.name = name

    def __repr__(self):
        return f"MockAdapter({self.name})"


class TestAdapterRegistry:
    """Test suite for AdapterRegistry."""

    def test_init_creates_empty_registry(self):
        """Test that initialization creates empty registry."""
        registry = AdapterRegistry()
        
        assert len(registry) == 0
        assert registry.list_adapters() == {}

    def test_register_adapter_success(self):
        """Test successful adapter registration."""
        registry = AdapterRegistry()
        adapter = MockAdapter("TestAdapter")
        
        registry.register("test", adapter)
        
        assert len(registry) == 1
        assert "test" in registry
        assert registry.get("test") == adapter

    def test_register_overwrite_logs_warning(self, caplog):
        """Test that overwriting adapter logs warning."""
        registry = AdapterRegistry()
        adapter1 = MockAdapter("First")
        adapter2 = MockAdapter("Second")
        
        registry.register("test", adapter1)
        registry.register("test", adapter2)
        
        assert registry.get("test") == adapter2
        assert "Overwriting existing adapter" in caplog.text

    def test_register_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            registry.register("", adapter)

    def test_register_none_adapter_raises_error(self):
        """Test that None adapter raises ValueError."""
        registry = AdapterRegistry()
        
        with pytest.raises(ValueError, match="cannot be None"):
            registry.register("test", None)

    def test_swap_adapter_success(self, caplog):
        """Test successful adapter swap."""
        registry = AdapterRegistry()
        adapter1 = MockAdapter("Original")
        adapter2 = MockAdapter("Swapped")
        
        registry.register("test", adapter1)
        registry.swap("test", adapter2)
        
        assert registry.get("test") == adapter2
        assert "SWAPPED" in caplog.text
        assert "MockAdapter" in caplog.text

    def test_swap_nonexistent_raises_keyerror(self):
        """Test that swapping nonexistent adapter raises KeyError."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        with pytest.raises(KeyError, match="not registered"):
            registry.swap("nonexistent", adapter)

    def test_swap_none_adapter_raises_error(self):
        """Test that swapping to None raises ValueError."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        registry.register("test", adapter)
        
        with pytest.raises(ValueError, match="cannot be None"):
            registry.swap("test", None)

    def test_get_adapter_success(self):
        """Test successful adapter retrieval."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        registry.register("test", adapter)
        
        retrieved = registry.get("test")
        assert retrieved == adapter

    def test_get_nonexistent_raises_keyerror(self):
        """Test that getting nonexistent adapter raises KeyError."""
        registry = AdapterRegistry()
        
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_get_empty_name_raises_error(self):
        """Test that getting with empty name raises ValueError."""
        registry = AdapterRegistry()
        
        with pytest.raises(ValueError, match="name cannot be empty"):
            registry.get("")

    def test_list_adapters_empty(self):
        """Test listing adapters when registry is empty."""
        registry = AdapterRegistry()
        
        adapters = registry.list_adapters()
        
        assert adapters == {}

    def test_list_adapters_multiple(self):
        """Test listing multiple registered adapters."""
        registry = AdapterRegistry()
        adapter1 = MockAdapter("First")
        adapter2 = MockAdapter("Second")
        adapter3 = MockAdapter("Third")
        
        registry.register("a", adapter1)
        registry.register("b", adapter2)
        registry.register("c", adapter3)
        
        adapters = registry.list_adapters()
        
        assert len(adapters) == 3
        assert adapters["a"] == "MockAdapter"
        assert adapters["b"] == "MockAdapter"
        assert adapters["c"] == "MockAdapter"

    def test_unregister_existing_adapter(self):
        """Test unregistering existing adapter."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        registry.register("test", adapter)
        assert "test" in registry
        
        registry.unregister("test")
        
        assert "test" not in registry
        assert len(registry) == 0

    def test_unregister_nonexistent_logs_warning(self, caplog):
        """Test that unregistering nonexistent adapter logs warning."""
        registry = AdapterRegistry()
        
        registry.unregister("nonexistent")
        
        assert "Cannot unregister" in caplog.text

    def test_has_adapter_returns_true_when_exists(self):
        """Test has_adapter returns True for existing adapter."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        registry.register("test", adapter)
        
        assert registry.has_adapter("test") is True

    def test_has_adapter_returns_false_when_not_exists(self):
        """Test has_adapter returns False for nonexistent adapter."""
        registry = AdapterRegistry()
        
        assert registry.has_adapter("nonexistent") is False

    def test_clear_removes_all_adapters(self):
        """Test clear removes all adapters."""
        registry = AdapterRegistry()
        
        registry.register("a", MockAdapter())
        registry.register("b", MockAdapter())
        registry.register("c", MockAdapter())
        
        assert len(registry) == 3
        
        registry.clear()
        
        assert len(registry) == 0
        assert registry.list_adapters() == {}

    def test_len_returns_correct_count(self):
        """Test __len__ magic method."""
        registry = AdapterRegistry()
        
        assert len(registry) == 0
        
        registry.register("a", MockAdapter())
        assert len(registry) == 1
        
        registry.register("b", MockAdapter())
        assert len(registry) == 2
        
        registry.unregister("a")
        assert len(registry) == 1

    def test_contains_magic_method(self):
        """Test __contains__ magic method (in operator)."""
        registry = AdapterRegistry()
        adapter = MockAdapter()
        
        assert "test" not in registry
        
        registry.register("test", adapter)
        
        assert "test" in registry

    def test_repr_shows_registered_adapters(self):
        """Test __repr__ shows registered adapters."""
        registry = AdapterRegistry()
        
        # Empty
        repr_empty = repr(registry)
        assert "AdapterRegistry" in repr_empty
        
        # With adapters
        registry.register("tts", MockAdapter("TTS"))
        registry.register("stt", MockAdapter("STT"))
        
        repr_full = repr(registry)
        assert "AdapterRegistry" in repr_full
        assert "tts" in repr_full or "stt" in repr_full

    def test_multiple_operations_scenario(self):
        """Test complex scenario with multiple operations."""
        registry = AdapterRegistry()
        
        # Register multiple
        tts1 = MockAdapter("AzureTTS")
        stt1 = MockAdapter("AzureSTT")
        llm1 = MockAdapter("GroqLLM")
        
        registry.register("tts", tts1)
        registry.register("stt", stt1)
        registry.register("llm", llm1)
        
        assert len(registry) == 3
        
        # Swap one
        tts2 = MockAdapter("GoogleTTS")
        registry.swap("tts", tts2)
        
        assert registry.get("tts") == tts2
        assert registry.get("stt") == stt1
        
        # Unregister one
        registry.unregister("llm")
        
        assert len(registry) == 2
        assert "llm" not in registry
        
        # List remaining
        adapters = registry.list_adapters()
        assert len(adapters) == 2
        assert "tts" in adapters
        assert "stt" in adapters

    def test_adapter_can_be_any_type(self):
        """Test that adapter can be any Python object."""
        registry = AdapterRegistry()
        
        # Mock object
        mock_obj = Mock()
        registry.register("mock", mock_obj)
        assert registry.get("mock") == mock_obj
        
        # Lambda
        func = lambda x: x * 2
        registry.register("func", func)
        assert registry.get("func") == func
        
        # String (unusual but valid)
        registry.register("string", "test_string")
        assert registry.get("string") == "test_string"

    def test_error_messages_include_available_adapters(self):
        """Test that error messages show available adapters."""
        registry = AdapterRegistry()
        registry.register("tts", MockAdapter())
        registry.register("stt", MockAdapter())
        
        try:
            registry.get("llm")
            assert False, "Should have raised KeyError"
        except KeyError as e:
            error_msg = str(e)
            assert "tts" in error_msg
            assert "stt" in error_msg
