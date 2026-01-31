"""
Unit tests for Marketplace component.
Tests based on acceptance criteria from plan.
"""

import pytest
from unittest.mock import Mock, patch
from src.marketplace import Marketplace, Request
from src.agent import SimpleAgent
from src.database import AgentConfig


@pytest.fixture
def test_agents():
    """Create test agents."""
    agents = []
    for i in range(3):
        config = AgentConfig(
            agent_id=f"test_agent_{i}",
            generation=0,
            parent_id=None,
            system_prompt="Test prompt"
        )
        agents.append(SimpleAgent(config))
    return agents


@pytest.fixture
def marketplace(test_agents):
    """Create marketplace with test agents."""
    return Marketplace(test_agents)


def test_generate_request_has_client(marketplace):
    """
    Acceptance criteria: Request generated → has client assigned
    """
    # Act
    request = marketplace.generate_request()

    # Assert
    assert isinstance(request, Request)
    assert request.request_id is not None
    assert request.description is not None
    assert request.client is not None
    # Client should be one of the 4 client types
    assert request.client.__class__.__name__ in [
        'MinimalistClient', 'DocumenterClient', 'TesterClient', 'PragmaticClient'
    ]


def test_process_request_updates_revenue(marketplace, test_agents):
    """
    Acceptance criteria: After transaction → agent.total_revenue updated
    """
    # Arrange
    request = marketplace.generate_request()
    initial_revenue = sum(a.config.total_revenue for a in test_agents)

    # Mock agent to control which one is selected and its output
    selected_agent = test_agents[0]
    mock_code = "def test(): pass"

    with patch.object(marketplace, 'assign_agent', return_value=selected_agent):
        with patch.object(selected_agent, 'solve_request', return_value=mock_code):
            # Act
            transaction = marketplace.process_request(request)

    # Assert
    final_revenue = sum(a.config.total_revenue for a in test_agents)
    assert final_revenue > initial_revenue
    assert transaction.price_paid > 0
    assert selected_agent.config.total_revenue == transaction.price_paid


def test_multiple_transactions_accumulate(marketplace, test_agents):
    """
    Acceptance criteria: 3 transactions → revenue accumulated correctly
    """
    # Arrange
    agent = test_agents[0]
    initial_revenue = agent.config.total_revenue
    mock_code = "def test(): pass"

    with patch.object(marketplace, 'assign_agent', return_value=agent):
        with patch.object(agent, 'solve_request', return_value=mock_code):
            # Act - Process 3 transactions
            prices = []
            for _ in range(3):
                request = marketplace.generate_request()
                transaction = marketplace.process_request(request)
                prices.append(transaction.price_paid)

    # Assert
    expected_revenue = initial_revenue + sum(prices)
    assert agent.config.total_revenue == pytest.approx(expected_revenue)
    assert agent.config.transaction_count == 3
    assert len(marketplace.transactions) == 3


def test_assign_agent_returns_valid_agent(marketplace, test_agents):
    """
    Test that assign_agent returns one of the agents in the pool
    """
    # Act
    assigned = marketplace.assign_agent()

    # Assert
    assert assigned in test_agents
    assert isinstance(assigned, SimpleAgent)


def test_marketplace_tracks_transactions(marketplace):
    """
    Test that marketplace maintains transaction history
    """
    # Arrange
    agent = marketplace.agents[0]
    mock_code = "def hello(): return 'world'"

    with patch.object(marketplace, 'assign_agent', return_value=agent):
        with patch.object(agent, 'solve_request', return_value=mock_code):
            # Act
            initial_count = len(marketplace.transactions)
            request = marketplace.generate_request()
            marketplace.process_request(request)

    # Assert
    assert len(marketplace.transactions) == initial_count + 1
    assert marketplace.transactions[-1].agent_id == agent.config.agent_id
