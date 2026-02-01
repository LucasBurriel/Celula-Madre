"""
Célula Madre MVP - Main execution script.
Price-driven evolution of AI coding agents.
"""

from src.database import Database, AgentConfig
from src.agent import SimpleAgent
from src.marketplace import Marketplace
from src.evolution import EvolutionaryEngine


def main():
    """Run the Célula Madre MVP experiment."""
    print("=" * 60)
    print("CÉLULA MADRE MVP: Price-Driven Agent Evolution")
    print("=" * 60)
    print()

    # Initialize database
    print("[Setup] Initializing database...")
    db = Database("celula_madre.db")

    # EXPERIMENTAL vs CONTROL GROUP
    USE_GUIDED_MUTATION = True  # CONTROL GROUP: Random mutations

    # Check for existing checkpoint (resume support)
    existing_agents = db.get_all_agents()
    completed_txs = db.get_transaction_count_total()

    if existing_agents and completed_txs > 0:
        print(f"[RESUME] Found checkpoint: {completed_txs} transactions completed, {len(existing_agents)} agents")
        agents = []
        for agent_config in existing_agents:
            if agent_config.status == "active":
                agent = SimpleAgent(agent_config)
                agents.append(agent)
        print(f"[RESUME] Loaded {len(agents)} active agents")
        start_tx = completed_txs
    else:
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
        start_tx = 0

    # Initialize marketplace and evolution
    print("\n[Setup] Initializing marketplace and evolution engine...")
    marketplace = Marketplace(agents, db)

    evolution_engine = EvolutionaryEngine(use_guided_mutation=USE_GUIDED_MUTATION)

    print(f"   Mode: {'EXPERIMENTAL (guided evolution)' if USE_GUIDED_MUTATION else 'CONTROL (random mutations)'}")

    # Simulate transactions
    NUM_TRANSACTIONS = 200  # Full experiment
    remaining = NUM_TRANSACTIONS - start_tx
    print(f"\n[Simulation] Running {remaining} remaining transactions ({start_tx}/{NUM_TRANSACTIONS} done)...")
    print("-" * 60)

    for i in range(start_tx, NUM_TRANSACTIONS):
        # Generate and process request
        try:
            request = marketplace.generate_request()
            transaction = marketplace.process_request(request)
        except Exception as e:
            print(f"[Tx {i+1:2d}] ERROR: {e} — skipping")
            continue

        # Update database
        db.save_transaction(transaction)
        db.update_agent_revenue(transaction.agent_id, transaction.price_paid, transaction.api_cost)

        # Print transaction
        print(f"[Tx {i+1:2d}] Agent: {transaction.agent_id:15s} | "
              f"Price: ${transaction.price_paid:5.2f} | "
              f"Client: {transaction.client_name:18s} | "
              f"Feedback: {transaction.feedback}")

        # Evolve every 10 transactions
        if (i + 1) % 10 == 0:
            try:
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
            except Exception as e:
                print(f"   >> EVOLUTION ERROR: {e} — continuing without evolution")

            print("-" * 60)

    # Display final results
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

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

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
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
            print(f"\n[WARNING] No clear improvement yet (more transactions needed)")

    # Generation diversity
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
    print("Experiment complete! Check celula_madre.db for full data.")
    print("=" * 60)

    # Cleanup
    db.close()


if __name__ == "__main__":
    main()
