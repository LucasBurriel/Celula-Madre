"""
Célula Madre MVP-3: AI Clients Experiment
Full AI-to-AI marketplace where both agents AND clients are AI-powered.
"""

from src.database import Database, AgentConfig
from src.agent import SimpleAgent
from src.ai_clients import (
    create_budget_client,
    create_quality_client,
    create_experimental_client,
    create_pragmatic_client
)
from src.ai_marketplace import AIMarketplace
from src.evolution import EvolutionaryEngine


def main():
    """Run MVP-3: AI Clients experiment."""
    print("=" * 60)
    print("CÉLULA MADRE MVP-3: AI Clients Experiment")
    print("Both agents AND clients are AI-powered")
    print("=" * 60)
    print()

    # Initialize database
    print("[Setup] Initializing database...")
    db = Database("celula_madre.db")

    # Create initial population (3 agents with different prompts)
    print("[Setup] Creating initial agent population...")
    initial_prompts = [
        "You are a helpful Python coding assistant. Generate clean, working code.",
        "You are a minimalist coder. Prefer brevity and simplicity.",
        "You are a documentation-focused developer. Always include comprehensive docstrings and comments."
    ]

    agents = []
    for i, prompt in enumerate(initial_prompts):
        config = AgentConfig(
            agent_id=f"agent_gen0_{i}",
            generation=0,
            parent_id=None,
            system_prompt=prompt
        )
        agent = SimpleAgent(config)
        agents.append(agent)
        db.save_agent(config)
        print(f"  Created: {config.agent_id}")

    # Create AI clients with different personalities
    print("\n[Setup] Creating AI clients with distinct personalities...")
    clients = [
        create_budget_client(),       # $100 budget, cost-conscious
        create_quality_client(),      # $400 budget, quality-focused
        create_experimental_client(), # $200 budget, tries new agents
        create_pragmatic_client()     # $150 budget, balanced
    ]

    for client in clients:
        print(f"  {client.client_id:25s} - Budget: ${client.budget:6.2f}")

    # Initialize AI marketplace and evolution
    print("\n[Setup] Initializing AI marketplace and evolution engine...")
    marketplace = AIMarketplace(agents, clients, db)
    evolution_engine = EvolutionaryEngine(use_guided_mutation=True)
    print("   Mode: EXPERIMENTAL (guided evolution + AI clients)")

    # Simulate transactions
    NUM_TRANSACTIONS = 200
    print(f"\n[Simulation] Running {NUM_TRANSACTIONS} AI-driven transactions...")
    print("-" * 60)

    for i in range(NUM_TRANSACTIONS):
        # Generate and process request (AI client chooses and evaluates!)
        request = marketplace.generate_request()
        transaction = marketplace.process_request(request)

        # Update database
        db.save_transaction(transaction)
        db.update_agent_revenue(transaction.agent_id, transaction.price_paid, transaction.api_cost)

        # Print transaction
        print(f"[Tx {i+1:3d}] Agent: {transaction.agent_id:15s} | "
              f"Price: ${transaction.price_paid:5.2f} | "
              f"Client: {transaction.client_name:25s} | "
              f"Feedback: {transaction.feedback[:50]}")

        # Evolve every 10 transactions
        if (i + 1) % 10 == 0:
            new_agent = evolution_engine.evolve_generation(agents, db)
            agents.append(new_agent)
            marketplace.agents = agents  # Update marketplace

            print()
            print(">> EVOLUTION: New agent created!")
            print(f"   ID: {new_agent.config.agent_id}")
            print(f"   Generation: {new_agent.config.generation}")
            print(f"   Parent: {new_agent.config.parent_id}")
            print(f"   Prompt (first 80 chars): {new_agent.config.system_prompt[:80]}...")

            # Retire old agents
            current_generation = max(a.config.generation for a in agents)
            retired = marketplace.retire_old_agents(current_generation)
            if retired:
                print(f"   >> RETIRED {len(retired)} agents: {[a.config.agent_id for a in retired]}")

            # Print client budget status
            print("\n   Client Budget Status:")
            for client in clients:
                pct_remaining = (client.budget / client.initial_budget) * 100
                print(f"   - {client.client_id:25s}: ${client.budget:6.2f} / ${client.initial_budget:6.2f} ({pct_remaining:5.1f}% remaining)")

            print("-" * 60)

    # Display final results
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    # Agent statistics
    all_agents = db.get_all_agents()
    for agent in all_agents:
        avg_price = agent.total_revenue / max(1, agent.transaction_count)
        print(f"\nAgent: {agent.agent_id} [{agent.status.upper()}]")
        print(f"  Generation: {agent.generation}")
        print(f"  Parent: {agent.parent_id or 'None (initial)'}")
        print(f"  Total Revenue: ${agent.total_revenue:.2f}")
        print(f"  Total Costs: ${agent.total_costs:.2f}")
        print(f"  Net Profit: ${agent.net_profit:.2f}")
        print(f"  Transactions: {agent.transaction_count}")
        print(f"  Avg Price: ${avg_price:.2f}")
        print(f"  Prompt: {agent.system_prompt[:100]}...")

    # Client statistics
    print("\n" + "=" * 60)
    print("CLIENT STATISTICS")
    print("=" * 60)

    for client in clients:
        print(f"\n{client.client_id}:")
        print(f"  Budget: ${client.initial_budget:.2f} → ${client.budget:.2f} (spent ${client.spent:.2f})")
        print(f"  Transactions: {len(client.experience)}")
        print(f"  Avg Price Paid: ${client.spent / max(1, len(client.experience)):.2f}")
        print(f"  Avg Satisfaction: {sum(e.satisfaction for e in client.experience) / max(1, len(client.experience)):.1f}/10")

        # Agent preferences (who did they hire most?)
        agent_counts = {}
        for exp in client.experience:
            agent_counts[exp.agent_id] = agent_counts.get(exp.agent_id, 0) + 1

        if agent_counts:
            top_agent = max(agent_counts.items(), key=lambda x: x[1])
            print(f"  Most hired: {top_agent[0]} ({top_agent[1]} times)")

    # Market statistics
    print("\n" + "=" * 60)
    print("MARKET STATISTICS")
    print("=" * 60)

    market_stats = marketplace.get_market_stats()
    print(f"Total Transactions: {market_stats['total_transactions']}")
    print(f"Active Agents: {market_stats['active_agents']}")
    print(f"\nAgent Economics:")
    print(f"  Total Revenue: ${market_stats['total_revenue']:.2f}")
    print(f"  Total Costs: ${market_stats['total_costs']:.2f}")
    print(f"  Total Profit: ${market_stats['total_profit']:.2f}")
    print(f"\nClient Economics:")
    print(f"  Initial Budget: ${market_stats['client_budget_initial']:.2f}")
    print(f"  Total Spent: ${market_stats['client_spent']:.2f}")
    print(f"  Remaining: ${market_stats['client_remaining']:.2f}")

    # Generation analysis
    print("\n" + "=" * 60)
    print("GENERATION ANALYSIS")
    print("=" * 60)

    gen0_agents = [a for a in all_agents if a.generation == 0]
    evolved_agents = [a for a in all_agents if a.generation > 0]
    active_agents = [a for a in all_agents if a.status == "active"]
    retired_agents = [a for a in all_agents if a.status == "retired"]

    print(f"Total Agents: {len(all_agents)} (Active: {len(active_agents)}, Retired: {len(retired_agents)})")
    print(f"Generations: 0-{max(a.generation for a in all_agents)}")

    if gen0_agents:
        gen0_avg_revenue = sum(a.total_revenue for a in gen0_agents) / len(gen0_agents)
        gen0_avg_cost = sum(a.total_costs for a in gen0_agents) / len(gen0_agents)
        gen0_avg_profit = sum(a.net_profit for a in gen0_agents) / len(gen0_agents)
        gen0_avg_price = sum(a.total_revenue / max(1, a.transaction_count) for a in gen0_agents) / len(gen0_agents)
        print(f"\nGeneration 0 (baseline):")
        print(f"  Avg Revenue: ${gen0_avg_revenue:.2f}")
        print(f"  Avg Cost: ${gen0_avg_cost:.2f}")
        print(f"  Avg Net Profit: ${gen0_avg_profit:.2f}")
        print(f"  Avg Price per Transaction: ${gen0_avg_price:.2f}")

    if evolved_agents:
        evolved_avg_revenue = sum(a.total_revenue for a in evolved_agents) / len(evolved_agents)
        evolved_avg_cost = sum(a.total_costs for a in evolved_agents) / len(evolved_agents)
        evolved_avg_profit = sum(a.net_profit for a in evolved_agents) / len(evolved_agents)
        evolved_avg_price = sum(a.total_revenue / max(1, a.transaction_count) for a in evolved_agents) / len(evolved_agents)
        print(f"\nEvolved Agents (gen > 0):")
        print(f"  Avg Revenue: ${evolved_avg_revenue:.2f}")
        print(f"  Avg Cost: ${evolved_avg_cost:.2f}")
        print(f"  Avg Net Profit: ${evolved_avg_profit:.2f}")
        print(f"  Avg Price per Transaction: ${evolved_avg_price:.2f}")

        if gen0_agents and evolved_avg_price > gen0_avg_price:
            improvement = ((evolved_avg_price - gen0_avg_price) / gen0_avg_price) * 100
            print(f"\n[SUCCESS] Improvement: +{improvement:.1f}% avg price (evolution working!)")
        elif gen0_agents:
            print(f"\n[WARNING] No clear improvement yet")

    # Transaction distribution by generation
    gen_distribution = {}
    for agent in all_agents:
        gen_distribution[agent.generation] = gen_distribution.get(agent.generation, 0) + agent.transaction_count

    print(f"\nTransaction Distribution by Generation:")
    total_txs = sum(gen_distribution.values())
    for gen in sorted(gen_distribution.keys()):
        count = gen_distribution[gen]
        pct = (count / total_txs) * 100 if total_txs > 0 else 0
        print(f"  Gen {gen}: {count} txs ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("MVP-3 AI Clients experiment complete!")
    print("Check celula_madre.db for full data.")
    print("=" * 60)

    # Cleanup
    db.close()


if __name__ == "__main__":
    main()
