"""
Tool Value Objects.
Part of the Domain Layer (Hexagonal Architecture).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class ToolDefinition:
    """Tool metadata exportable for LLM function calling."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate tool definition."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Tool name must be a non-empty string")
        if not self.description:
            raise ValueError("Tool description cannot be empty")

    def to_openai_format(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required
            }
        }

@dataclass
class ToolRequest:
    """Request to execute a tool."""
    tool_name: str
    arguments: Dict[str, Any]
    trace_id: str = ""
    timeout_seconds: float = 10.0
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate tool request."""
        if not self.tool_name:
            raise ValueError("Tool name cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

@dataclass
class ToolResponse:
    """Response from tool execution."""
    tool_name: str
    result: Any
    success: bool
    error_message: str = ""
    execution_time_ms: float = 0.0
    trace_id: str = ""
