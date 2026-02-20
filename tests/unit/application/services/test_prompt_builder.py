
import pytest
import json
from unittest.mock import MagicMock
from backend.application.services.prompt_builder import PromptBuilder

@pytest.fixture
def mock_config():
    """Mock configuration object."""
    config = MagicMock()
    # Default values
    config.system_prompt = "Base prompt."
    config.response_length = "short"
    config.conversation_tone = "neutral"
    config.conversation_formality = "casual"
    config.dynamic_vars_enabled = False
    return config

def test_build_system_prompt_defaults(mock_config):
    """Test building prompt with basic configuration."""
    prompt = PromptBuilder.build_system_prompt(mock_config)
    
    assert "Base prompt." in prompt
    assert "<dynamic_style_overrides>" in prompt
    # Check for mapped instructions
    assert "Mantén las respuestas cortas" in prompt  # short
    assert "Sé neutral y desapegado" in prompt       # neutral
    assert "Trata de 'tú'" in prompt                 # casual

def test_build_system_prompt_with_context(mock_config):
    """Test injecting context variables."""
    context = {"customer_name": "Juan", "account_type": "Premium"}
    
    prompt = PromptBuilder.build_system_prompt(mock_config, context=context)
    
    assert "<context_data>" in prompt
    assert "- customer_name: Juan" in prompt
    assert "- account_type: Premium" in prompt

def test_build_system_prompt_dynamic_vars(mock_config):
    """Test injecting dynamic variables into placeholders."""
    mock_config.system_prompt = "Hello {name}, your balance is {balance}."
    mock_config.dynamic_vars_enabled = True
    mock_config.dynamic_vars = {"name": "Martin", "balance": "100"}
    
    prompt = PromptBuilder.build_system_prompt(mock_config)
    
    assert "Hello Martin" in prompt
    assert "your balance is 100" in prompt
    # Verify no placeholders remain
    assert "{name}" not in prompt

def test_build_system_prompt_dynamic_vars_json_string(mock_config):
    """Test dynamic vars when provided as JSON string."""
    mock_config.system_prompt = "Val: {value}"
    mock_config.dynamic_vars_enabled = True
    mock_config.dynamic_vars = '{"value": 123}'
    
    prompt = PromptBuilder.build_system_prompt(mock_config)
    
    assert "Val: 123" in prompt

def test_build_system_prompt_missing_config_attributes():
    """Test resiliency when config is a dict or missing attributes."""
    config_dict = {
        "system_prompt": "Dict prompt"
    }
    
    prompt = PromptBuilder.build_system_prompt(config_dict)
    
    assert "Dict prompt" in prompt
    # Should use defaults for missing keys (sane fallbacks check)
    # The code defaults length='short', tone='warm', formality='semi_formal' if not found? 
    # Actually get_cfg defaults to 'short', 'warm', 'semi_formal'
    assert "Mantén las respuestas cortas" in prompt  # default short
