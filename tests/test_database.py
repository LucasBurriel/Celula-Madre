"""
Unit tests for Database component.
Tests based on acceptance criteria from plan.
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from src.database import Database, AgentConfig, Transaction


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Copy schema to temp location accessible by database
    db = Database(path)

    yield db

    # Cleanup
    db.close()
    os.unlink(path)


def test_save_and_load_agent(temp_db):
    """
    Acceptance criteria: Save agent → load → config identical
    """
    # Arrange
    config = AgentConfig(
        agent_id="test_agent_001",
        generation=0,
        parent_id=None,
        system_prompt="Test prompt",
        total_revenue=0.0,
        transaction_count=0
    )

    # Act
    temp_db.save_agent(config)
    loaded_agents = temp_db.get_all_agents()

    # Assert
    assert len(loaded_agents) == 1
    loaded = loaded_agents[0]
    assert loaded.agent_id == config.agent_id
    assert loaded.generation == config.generation
    assert loaded.parent_id == config.parent_id
    assert loaded.system_prompt == config.system_prompt
    assert loaded.total_revenue == config.total_revenue
    assert loaded.transaction_count == config.transaction_count


def test_update_revenue_atomic(temp_db):
    """
    Acceptance criteria: Update revenue → revenue and count updated correctly
    """
    # Arrange
    config = AgentConfig(
        agent_id="test_agent_002",
        generation=0,
        parent_id=None,
        system_prompt="Test prompt",
        total_revenue=0.0,
        transaction_count=0
    )
    temp_db.save_agent(config)

    # Act - Perform 3 revenue updates
    temp_db.update_agent_revenue("test_agent_002", 10.5)
    temp_db.update_agent_revenue("test_agent_002", 15.0)
    temp_db.update_agent_revenue("test_agent_002", 7.25)

    # Assert
    loaded = temp_db.get_all_agents()[0]
    assert loaded.total_revenue == pytest.approx(32.75)  # 10.5 + 15.0 + 7.25
    assert loaded.transaction_count == 3


def test_get_recent_feedback(temp_db):
    """
    Acceptance criteria: 10 txs saved → last 5 returned
    """
    # Arrange
    config = AgentConfig(
        agent_id="test_agent_003",
        generation=0,
        parent_id=None,
        system_prompt="Test prompt"
    )
    temp_db.save_agent(config)

    # Act - Create 10 transactions with numbered feedback
    for i in range(10):
        tx = Transaction(
            request_id=f"req_{i}",
            agent_id="test_agent_003",
            code_generated=f"def test_{i}(): pass",
            price_paid=10.0,
            client_name="TestClient",
            feedback=f"Feedback {i}"
        )
        temp_db.save_transaction(tx)
        time.sleep(0.01)  # Ensure distinct timestamps

    # Get last 5
    recent_feedback = temp_db.get_recent_feedback("test_agent_003", limit=5)

    # Assert
    assert len(recent_feedback) == 5
    # Should be in reverse chronological order (most recent first)
    assert recent_feedback[0] == "Feedback 9"
    assert recent_feedback[4] == "Feedback 5"


def test_agents_ordered_by_revenue(temp_db):
    """
    Test that get_all_agents returns agents sorted by revenue (highest first).
    """
    # Arrange - Create 3 agents with different revenues
    agents = [
        AgentConfig("agent_low", 0, None, "Prompt 1", total_revenue=5.0),
        AgentConfig("agent_high", 0, None, "Prompt 2", total_revenue=50.0),
        AgentConfig("agent_mid", 0, None, "Prompt 3", total_revenue=25.0),
    ]

    for agent in agents:
        temp_db.save_agent(agent)

    # Act
    sorted_agents = temp_db.get_all_agents()

    # Assert
    assert len(sorted_agents) == 3
    assert sorted_agents[0].agent_id == "agent_high"  # $50
    assert sorted_agents[1].agent_id == "agent_mid"   # $25
    assert sorted_agents[2].agent_id == "agent_low"   # $5


def test_agent_lineage_preserved(temp_db):
    """
    Test that parent-child relationships are preserved.
    """
    # Arrange
    parent = AgentConfig("parent_001", 0, None, "Parent prompt")
    child = AgentConfig("child_001", 1, "parent_001", "Child prompt")

    # Act
    temp_db.save_agent(parent)
    temp_db.save_agent(child)

    # Assert
    agents = temp_db.get_all_agents()
    child_loaded = next(a for a in agents if a.agent_id == "child_001")
    assert child_loaded.parent_id == "parent_001"
    assert child_loaded.generation == 1
