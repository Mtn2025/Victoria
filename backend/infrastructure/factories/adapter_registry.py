"""
AdapterRegistry - Runtime adapter management and swapping.

Enables hot-swapping of infrastructure adapters for:
- Runtime debugging (swap to different provider)
- A/B testing (compare providers)
- Graceful degradation (swap to fallback)

Architecture: Infrastructure - Factory/Registry Pattern
"""
import logging
from typing import Any, TypeVar, Generic, Optional

logger = logging.getLogger(__name__)

# Generic type for adapters (can be bounded to specific Port types)
T = TypeVar('T')


class AdapterRegistry:
    """
    Registry for runtime adapter management and hot-swapping.

    Enables:
    - Runtime adapter replacement for debugging
    - A/B testing between providers
    - Graceful degradation to fallback adapters

    Example:
        >>> registry = AdapterRegistry()
        >>> 
        >>> # Register adapters
        >>> registry.register("tts", AzureTTSAdapter())
        >>> registry.register("stt", AzureSTTAdapter())
        >>> 
        >>> # Runtime swap for debugging
        >>> registry.swap("tts", GoogleTTSAdapter())
        >>> 
        >>> # Get current adapter
        >>> tts = registry.get("tts")  # Returns GoogleTTSAdapter instance
        >>> 
        >>> # List all registered adapters
        >>> registry.list_adapters()
        {'tts': 'GoogleTTSAdapter', 'stt': 'AzureSTTAdapter'}
    """

    def __init__(self):
        """Initialize empty adapter registry."""
        self._adapters: dict[str, Any] = {}
        logger.info("[AdapterRegistry] Initialized")

    def register(self, name: str, adapter: Any) -> None:
        """
        Register an adapter instance.

        Args:
            name: Adapter identifier (e.g., "tts", "stt", "llm")
            adapter: Adapter instance implementing a Port interface

        Raises:
            ValueError: If name is empty or adapter is None

        Example:
            >>> registry.register("tts", AzureTTSAdapter())
        """
        # Input validation (IMPROVEMENT from legacy)
        if not name:
            raise ValueError("[AdapterRegistry] Adapter name cannot be empty")
        if adapter is None:
            raise ValueError(f"[AdapterRegistry] Adapter for '{name}' cannot be None")

        if name in self._adapters:
            logger.warning(
                f"[AdapterRegistry] Overwriting existing adapter: {name} "
                f"(was: {type(self._adapters[name]).__name__})"
            )

        self._adapters[name] = adapter
        logger.info(
            f"[AdapterRegistry] Registered: {name} → {type(adapter).__name__}"
        )

    def swap(self, name: str, new_adapter: Any) -> None:
        """
        Swap adapter at runtime (hot-swap).

        Args:
            name: Adapter identifier to swap
            new_adapter: New adapter instance

        Raises:
            KeyError: If adapter name not registered
            ValueError: If new_adapter is None

        Example:
            >>> # Swap TTS from Azure to Google
            >>> registry.swap("tts", GoogleTTSAdapter())
            # [AdapterRegistry] 🔄 SWAPPED: tts - AzureTTSAdapter → GoogleTTSAdapter
        """
        # Input validation (IMPROVEMENT from legacy)
        if new_adapter is None:
            raise ValueError(f"[AdapterRegistry] New adapter for '{name}' cannot be None")

        if name not in self._adapters:
            raise KeyError(
                f"[AdapterRegistry] Cannot swap: '{name}' not registered. "
                f"Available: {list(self._adapters.keys())}"
            )

        old_adapter = self._adapters[name]
        self._adapters[name] = new_adapter

        logger.warning(
            f"[AdapterRegistry] 🔄 SWAPPED: {name} - "
            f"{type(old_adapter).__name__} → {type(new_adapter).__name__}"
        )

    def get(self, name: str) -> Any:
        """
        Get current adapter instance.

        Args:
            name: Adapter identifier

        Returns:
            Current adapter instance

        Raises:
            KeyError: If adapter not registered
            ValueError: If name is empty

        Example:
            >>> tts_adapter = registry.get("tts")
        """
        # Input validation (IMPROVEMENT from legacy)
        if not name:
            raise ValueError("[AdapterRegistry] Adapter name cannot be empty")

        if name not in self._adapters:
            raise KeyError(
                f"[AdapterRegistry] Adapter '{name}' not found. "
                f"Available: {list(self._adapters.keys())}"
            )

        return self._adapters[name]

    def list_adapters(self) -> dict[str, str]:
        """
        List all registered adapters.

        Returns:
            Dict mapping adapter names to their class names

        Example:
            >>> registry.list_adapters()
            {'tts': 'AzureTTSAdapter', 'stt': 'AzureSTTAdapter', 'llm': 'GroqLLMAdapter'}
        """
        return {
            name: type(adapter).__name__
            for name, adapter in self._adapters.items()
        }

    def unregister(self, name: str) -> None:
        """
        Unregister an adapter.

        Args:
            name: Adapter identifier to remove

        Note:
            Silently ignores if adapter not found (logs warning instead)
        """
        if name in self._adapters:
            adapter_type = type(self._adapters[name]).__name__
            del self._adapters[name]
            logger.info(f"[AdapterRegistry] Unregistered: {name} ({adapter_type})")
        else:
            logger.warning(f"[AdapterRegistry] Cannot unregister: '{name}' not found")

    def has_adapter(self, name: str) -> bool:
        """
        Check if adapter is registered.

        Args:
            name: Adapter identifier

        Returns:
            True if adapter registered, False otherwise

        Example:
            >>> if registry.has_adapter("tts"):
            >>>     tts = registry.get("tts")
        """
        return name in self._adapters

    def clear(self) -> None:
        """
        Unregister all adapters.

        Example:
            >>> registry.clear()
            # [AdapterRegistry] Cleared 3 adapters
        """
        count = len(self._adapters)
        self._adapters.clear()
        logger.info(f"[AdapterRegistry] Cleared {count} adapters")

    def __len__(self) -> int:
        """Return number of registered adapters."""
        return len(self._adapters)

    def __contains__(self, name: str) -> bool:
        """Support 'in' operator."""
        return name in self._adapters

    def __repr__(self) -> str:
        """String representation."""
        adapter_list = ", ".join(
            f"{name}={type(adapter).__name__}"
            for name, adapter in self._adapters.items()
        )
        return f"AdapterRegistry({adapter_list})"
