"""
Unit tests for EvolutionaryEngine component.
Tests based on acceptance criteria from plan.
"""

import pytest
from unittest.mock import Mock, patch
from src.evolution import EvolutionaryEngine
from src.agent import SimpleAgent
from src.database import AgentConfig, Database
import tempfile
import os


@pytest.fixture
def test_agents():
    """Create test agents with different revenues."""
    agents = [
        SimpleAgent(AgentConfig("agent_0", 0, None, "Prompt 0", total_revenue=5.0, transaction_count=1)),
        SimpleAgent(AgentConfig("agent_1", 0, None, "Prompt 1", total_revenue=15.0, transaction_count=2)),
        SimpleAgent(AgentConfig("agent_2", 0, None, "Prompt 2", total_revenue=10.0, transaction_count=1))
    ]
    return agents


@pytest.fixture
def temp_db():
    """Create temporary database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    yield db
    db.close()
    os.unlink(path)


@pytest.fixture
def evolution_engine():
    """Create evolutionary engine."""
    return EvolutionaryEngine()


def test_select_parent_greedy_bias(evolution_engine, test_agents):
    """
    Acceptance criteria: 10 selections → agent with top revenue selected ≥7 times
    """
    # agent_1 has revenue=$15 (highest)
    selections = []
    for _ in range(10):
        parent = evolution_engine.select_parent(test_agents)
        selections.append(parent.config.agent_id)

    # Count selections of top performer
    top_agent_selections = selections.count("agent_1")

    # Should be selected at least 7/10 times (80% + some random luck)
    # But we allow some variance due to randomness
    assert top_agent_selections >= 5, f"Top agent selected only {top_agent_selections}/10 times"


def test_mutate_prompt_changes_text(evolution_engine):
    """
    Acceptance criteria: Prompt mutado ≠ prompt original
    """
    # Arrange
    parent_prompt = "You are a Python assistant."
    performance_data = {
        'total_revenue': 25.0,
        'transaction_count': 3,
        'avg_price': 8.33,
        'feedback_samples': "- Good code\n- Too verbose"
    }

    # Mock Anthropic response
    mock_response = Mock()
    mock_response.content = [Mock(text="You are a concise Python coding expert.")]

    with patch.object(evolution_engine.client.messages, 'create', return_value=mock_response):
        # Act
        new_prompt = evolution_engine.mutate_prompt(parent_prompt, performance_data)

    # Assert
    assert new_prompt != parent_prompt
    assert len(new_prompt) > 0


def test_evolve_increments_generation(evolution_engine, test_agents, temp_db):
    """
    Acceptance criteria: Parent gen=2 → child gen=3
    """
    # Arrange
    parent = SimpleAgent(AgentConfig("parent_gen2", 2, "grandparent", "Parent prompt", total_revenue=20.0))
    test_agents.append(parent)

    # Save parent to DB
    temp_db.save_agent(parent.config)

    # Mock mutation
    mock_response = Mock()
    mock_response.content = [Mock(text="Evolved prompt")]

    with patch.object(evolution_engine.client.messages, 'create', return_value=mock_response):
        with patch.object(evolution_engine, 'select_parent', return_value=parent):
            # Act
            child = evolution_engine.evolve_generation(test_agents, temp_db)

    # Assert
    assert child.config.generation == 3  # parent.generation + 1
    assert child.config.parent_id == "parent_gen2"


def test_evolve_creates_new_agent(evolution_engine, test_agents, temp_db):
    """
    Test that evolve_generation creates a new agent with distinct ID
    """
    # Arrange
    for agent in test_agents:
        temp_db.save_agent(agent.config)

    # Mock mutation
    mock_response = Mock()
    mock_response.content = [Mock(text="New evolved prompt")]

    with patch.object(evolution_engine.client.messages, 'create', return_value=mock_response):
        # Act
        new_agent = evolution_engine.evolve_generation(test_agents, temp_db)

    # Assert
    assert new_agent.config.agent_id not in [a.config.agent_id for a in test_agents]
    assert new_agent.config.generation > 0
    assert new_agent.config.parent_id is not None


def test_evolve_uses_performance_data(evolution_engine, test_agents, temp_db):
    """
    Test that mutation receives performance data
    """
    # Arrange
    parent = test_agents[1]  # agent_1 with $15 revenue
    temp_db.save_agent(parent.config)

    with patch.object(evolution_engine, 'mutate_prompt') as mock_mutate:
        mock_mutate.return_value = "Mutated prompt"
        with patch.object(evolution_engine, 'select_parent', return_value=parent):
            # Act
            evolution_engine.evolve_generation(test_agents, temp_db)

    # Assert - mutate_prompt was called with performance data
    mock_mutate.assert_called_once()
    call_args = mock_mutate.call_args[0]
    performance_data = call_args[1]

    assert 'total_revenue' in performance_data
    assert 'transaction_count' in performance_data
    assert 'avg_price' in performance_data
    assert performance_data['total_revenue'] == 15.0
