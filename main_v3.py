"""
Célula Madre V3 - Market Redesign Experiment
Fixes: exploration, costs, aggressive retirement, bankruptcy, granular pricing.
"""

import sys
from src.database import Database, AgentConfig
from src.agent import SimpleAgent
from src.marketplace_v3 import MarketplaceV3
from src.evolution import EvolutionaryEngine


def main():
    """Run V3 experiment."""
    print("=" * 60)
    print("CÉLULA MADRE V3: Market Redesign Experiment")
    print("=" * 60)
    print()
    print("Changes from V2:")
    print("  - 30% client exploration (try new agents)")
    print("  - Neutral defaults for unknown agents")
    print("  - Simulated token costs ($0.001/token)")
    print("  - Aggressive retirement (15 txs / 2 gen gap)")
    print("  - Bankruptcy (avg price < $6 after 5 txs = death)")
    print("  - More granular pricing (continuous scale)")
    print("  - More diverse requests (15 types)")
    print()

    # Initialize
    db = Database("celula_madre.db")

    # Check for resume
    existing_agents = db.get_all_agents()
    completed_txs = db.get_transaction_count_total()

    if existing_agents and completed_txs > 0:
        print(f"[RESUME] Found checkpoint: {completed_txs} transactions, {len(existing_agents)} agents")
        agents = []
        for agent_config in existing_agents:
            if agent_config.status == "active":
                agent = SimpleAgent(agent_config)
                agents.append(agent)
        print(f"[RESUME] Loaded {len(agents)} active agents")
        start_tx = completed_txs
    else:
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

    marketplace = MarketplaceV3(agents, db)
    evolution_engine = EvolutionaryEngine(use_guided_mutation=True)

    NUM_TRANSACTIONS = 200
    EVOLVE_EVERY = 10
    remaining = NUM_TRANSACTIONS - start_tx

    print(f"\n[Simulation] Running {remaining} transactions ({start_tx}/{NUM_TRANSACTIONS} done)...")
    print(f"   Mode: EXPERIMENTAL (guided evolution + market redesign)")
    print("-" * 60)

    for i in range(start_tx, NUM_TRANSACTIONS):
        try:
            request = marketplace.generate_request()
            transaction = marketplace.process_request(request)
        except Exception as e:
            print(f"[Tx {i+1:3d}] ERROR: {e} — skipping")
            continue

        db.save_transaction(transaction)
        db.update_agent_revenue(transaction.agent_id, transaction.price_paid, transaction.api_cost)

        # Compact output
        cost_str = f"Cost: ${transaction.api_cost:.2f}" if transaction.api_cost > 0 else ""
        print(f"[Tx {i+1:3d}] {transaction.agent_id:20s} | ${transaction.price_paid:5.2f} | "
              f"{transaction.client_name:18s} | {transaction.feedback[:50]} {cost_str}")

        # Evolution phase
        if (i + 1) % EVOLVE_EVERY == 0:
            print()
            
            # Evolve
            try:
                new_agent = evolution_engine.evolve_generation(agents, db)
                agents.append(new_agent)
                marketplace.agents = agents

                print(f"  🧬 NEW: {new_agent.config.agent_id} (gen {new_agent.config.generation}) "
                      f"← {new_agent.config.parent_id}")
                print(f"     Prompt: {new_agent.config.system_prompt[:80]}...")
            except Exception as e:
                print(f"  🧬 EVOLUTION ERROR: {e}")

            # Retire/bankrupt
            retired = marketplace.retire_old_agents(
                max(a.config.generation for a in agents)
            )
            for agent, reason in retired:
                avg_p = agent.config.total_revenue / max(1, agent.config.transaction_count)
                print(f"  💀 {reason.upper():10s}: {agent.config.agent_id} "
                      f"(gen{agent.config.generation}, {agent.config.transaction_count}txs, "
                      f"avg ${avg_p:.2f})")

            # Population snapshot
            active = [a for a in agents if a.config.status == "active"]
            print(f"  📊 Population: {len(active)} active agents")
            for a in active:
                avg = a.config.total_revenue / max(1, a.config.transaction_count)
                profit = a.config.net_profit
                print(f"     {a.config.agent_id:20s} gen{a.config.generation} "
                      f"{a.config.transaction_count:2d}txs avg${avg:5.2f} profit${profit:6.2f}")
            
            print("-" * 60)

    # === FINAL RESULTS ===
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    all_agents = db.get_all_agents()
    
    # Per-agent results
    for agent in all_agents:
        avg_price = agent.total_revenue / max(1, agent.transaction_count)
        margin = (agent.net_profit / max(0.01, agent.total_revenue)) * 100
        print(f"\n{agent.agent_id} [{agent.status.upper()}]")
        print(f"  Gen: {agent.generation} | Parent: {agent.parent_id or 'None'}")
        print(f"  Revenue: ${agent.total_revenue:.2f} | Costs: ${agent.total_costs:.2f} | "
              f"Profit: ${agent.net_profit:.2f} ({margin:.0f}% margin)")
        print(f"  Txs: {agent.transaction_count} | Avg: ${avg_price:.2f}")
        print(f"  Prompt: {agent.system_prompt[:100]}...")

    # Summary by generation
    print("\n" + "=" * 60)
    print("GENERATION ANALYSIS")
    print("=" * 60)

    gen_data = {}
    for agent in all_agents:
        g = agent.generation
        if g not in gen_data:
            gen_data[g] = {'agents': [], 'total_rev': 0, 'total_cost': 0, 'total_txs': 0}
        gen_data[g]['agents'].append(agent)
        gen_data[g]['total_rev'] += agent.total_revenue
        gen_data[g]['total_cost'] += agent.total_costs
        gen_data[g]['total_txs'] += agent.transaction_count

    for g in sorted(gen_data.keys()):
        d = gen_data[g]
        n = len(d['agents'])
        avg_rev = d['total_rev'] / n
        avg_price = d['total_rev'] / max(1, d['total_txs'])
        avg_profit = (d['total_rev'] - d['total_cost']) / n
        print(f"\nGen {g}: {n} agents, {d['total_txs']} txs")
        print(f"  Avg Revenue/agent: ${avg_rev:.2f}")
        print(f"  Avg Price/tx: ${avg_price:.2f}")
        print(f"  Avg Profit/agent: ${avg_profit:.2f}")

    # Key comparison
    gen0 = gen_data.get(0, {'total_rev': 0, 'total_txs': 0, 'agents': []})
    evolved_gens = {k: v for k, v in gen_data.items() if k > 0}
    
    if gen0['total_txs'] > 0 and evolved_gens:
        gen0_avg = gen0['total_rev'] / gen0['total_txs']
        evolved_rev = sum(v['total_rev'] for v in evolved_gens.values())
        evolved_txs = sum(v['total_txs'] for v in evolved_gens.values())
        if evolved_txs > 0:
            evolved_avg = evolved_rev / evolved_txs
            delta = ((evolved_avg - gen0_avg) / gen0_avg) * 100
            
            print(f"\n{'=' * 40}")
            print(f"Gen 0 avg price/tx:     ${gen0_avg:.2f}")
            print(f"Evolved avg price/tx:   ${evolved_avg:.2f}")
            print(f"Delta:                  {delta:+.1f}%")
            
            if delta > 5:
                print(f"\n✅ SUCCESS: Evolution is improving agents!")
            elif delta > -5:
                print(f"\n⚖️  NEUTRAL: No significant difference")
            else:
                print(f"\n❌ REGRESSION: Evolved agents performing worse")

    # Transaction distribution
    print(f"\nTransaction Distribution:")
    total_txs = sum(d['total_txs'] for d in gen_data.values())
    for g in sorted(gen_data.keys()):
        d = gen_data[g]
        pct = (d['total_txs'] / total_txs) * 100 if total_txs > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  Gen {g}: {d['total_txs']:3d} txs ({pct:4.1f}%) {bar}")

    print("\n" + "=" * 60)
    print("V3 experiment complete!")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
