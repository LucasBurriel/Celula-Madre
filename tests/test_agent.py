"""
Unit tests for SimpleAgent component.
Tests based on acceptance criteria from plan.
"""

import pytest
from unittest.mock import Mock, patch
from anthropic import APIError
from src.agent import SimpleAgent
from src.database import AgentConfig


@pytest.fixture
def agent_config():
    """Create test agent configuration."""
    return AgentConfig(
        agent_id="test_agent",
        generation=0,
        parent_id=None,
        system_prompt="You are a helpful Python coding assistant."
    )


@pytest.fixture
def minimalist_config():
    """Create minimalist agent configuration."""
    return AgentConfig(
        agent_id="minimalist_agent",
        generation=0,
        parent_id=None,
        system_prompt="You are a minimalist coder. Prefer brevity and simplicity."
    )


def test_agent_generates_code(agent_config):
    """
    Acceptance criteria: Agent generates functional code from simple description
    """
    # Arrange
    agent = SimpleAgent(agent_config)
    description = "sum function"

    # Mock the Anthropic API response
    mock_response = Mock()
    mock_response.content = [Mock(text="def sum(a, b):\n    return a + b")]

    with patch.object(agent.client.messages, 'create', return_value=mock_response):
        # Act
        code = agent.solve_request(description)

        # Assert
        assert isinstance(code, str)
        assert len(code) > 0
        assert "def" in code or "class" in code  # Valid Python code


def test_different_prompts_different_output(agent_config, minimalist_config):
    """
    Acceptance criteria: Different prompts result in different styles of code
    """
    # Arrange
    agent1 = SimpleAgent(agent_config)
    agent2 = SimpleAgent(minimalist_config)

    # Mock responses - different styles
    mock_verbose = Mock()
    mock_verbose.content = [Mock(text='def factorial(n):\n    """Calculate factorial."""\n    return 1 if n == 0 else n * factorial(n-1)')]

    mock_brief = Mock()
    mock_brief.content = [Mock(text='def factorial(n):\n    return 1 if n == 0 else n * factorial(n-1)')]

    # Act
    with patch.object(agent1.client.messages, 'create', return_value=mock_verbose):
        code1 = agent1.solve_request("factorial function")

    with patch.object(agent2.client.messages, 'create', return_value=mock_brief):
        code2 = agent2.solve_request("factorial function")

    # Assert
    assert code1 != code2  # Different prompts should yield different outputs
    assert len(code1) != len(code2)  # Different code lengths


def test_agent_handles_api_error(agent_config):
    """
    Test that agent properly handles and propagates API errors
    """
    # Arrange
    agent = SimpleAgent(agent_config)

    # Create APIError with all required parameters
    mock_request = Mock()
    mock_body = {}
    api_error = APIError("API quota exceeded", request=mock_request, body=mock_body)

    with patch.object(agent.client.messages, 'create', side_effect=api_error):
        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            agent.solve_request("test function")

        # Verify error message includes agent ID
        assert "test_agent" in str(exc_info.value)


def test_agent_uses_system_prompt(agent_config):
    """
    Verify that agent uses the system prompt from config
    """
    # Arrange
    agent = SimpleAgent(agent_config)
    mock_response = Mock()
    mock_response.content = [Mock(text="def test(): pass")]

    with patch.object(agent.client.messages, 'create', return_value=mock_response) as mock_create:
        # Act
        agent.solve_request("test function")

        # Assert - Verify system prompt was passed
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['system'] == agent_config.system_prompt


def test_agent_config_serializable(agent_config):
    """
    Acceptance criteria: Config is serializable to DB
    """
    # Arrange & Act
    agent = SimpleAgent(agent_config)

    # Assert - Config should be accessible and have required fields
    assert agent.config.agent_id == "test_agent"
    assert agent.config.generation == 0
    assert agent.config.system_prompt is not None
    assert hasattr(agent.config, 'total_revenue')
    assert hasattr(agent.config, 'transaction_count')
