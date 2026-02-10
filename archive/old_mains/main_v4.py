"""
Célula Madre V4 — Biologically-Inspired Evolution
Crossover, niche specialization, adaptive mutation, population cap.
"""

import sys
from src.database import Database, AgentConfig
from src.agent import SimpleAgent
from src.marketplace_v3 import MarketplaceV3  # Reuse V3 marketplace (good mechanics)
from src.evolution_v4 import EvolutionV4


def main():
    print("=" * 60)
    print("CÉLULA MADRE V4: Biologically-Inspired Evolution")
    print("=" * 60)
    print()
    print("New in V4 (on top of V3 market):")
    print("  - Sexual reproduction (crossover from TWO parents)")
    print("  - Niche specialization (evolve toward best client)")
    print("  - Adaptive mutation rate (conservative/aggressive)")
    print("  - Population cap (max 8, weakest replaced)")
    print("  - Better mutation prompts (concrete, specific)")
    print()

    db = Database("celula_madre.db")

    # Check for resume
    existing_agents = db.get_all_agents()
    completed_txs = db.get_transaction_count_total()

    if existing_agents and completed_txs > 0:
        print(f"[RESUME] {completed_txs} txs done, {len(existing_agents)} agents")
        agents = [SimpleAgent(ac) for ac in existing_agents if ac.status == "active"]
        print(f"[RESUME] Loaded {len(agents)} active agents")
        start_tx = completed_txs
    else:
        print("[Setup] Creating initial population (diverse specialists)...")
        # V4: Start with SPECIALIZED agents, not generic ones
        initial_prompts = [
            # Minimalist specialist
            "Write Python in under 20 lines. No comments, no docstrings, no fluff. "
            "One function, minimal imports, return the result. Brevity is everything.",
            
            # Documentation specialist
            "Every function gets a docstring with Args/Returns/Example. Every block gets a comment. "
            "Use type hints on all parameters and returns. Documentation is the product.",
            
            # Testing specialist  
            "For every function, write at least 3 test functions using assert. "
            "Test edge cases, empty inputs, and normal cases. Tests are more important than the code itself.",
            
            # Pragmatist specialist
            "Write simple, working Python. Use try/except for error handling. "
            "Keep it under 25 lines. No fancy patterns, just code that parses and runs correctly.",
        ]

        agents = []
        specialist_names = ["minimalist", "documenter", "tester", "pragmatist"]
        for i, (prompt, name) in enumerate(zip(initial_prompts, specialist_names)):
            config = AgentConfig(
                agent_id=f"agent_gen0_{name}",
                generation=0,
                parent_id=None,
                system_prompt=prompt
            )
            agent = SimpleAgent(config)
            agents.append(agent)
            db.save_agent(config)
            print(f"  Created: {config.agent_id}")
            print(f"    → {prompt[:80]}...")
        start_tx = 0

    marketplace = MarketplaceV3(agents, db)
    evolution = EvolutionV4()

    NUM_TRANSACTIONS = 200
    EVOLVE_EVERY = 10
    remaining = NUM_TRANSACTIONS - start_tx

    print(f"\n[Run] {remaining} transactions remaining ({start_tx}/{NUM_TRANSACTIONS})")
    print("-" * 60)

    for i in range(start_tx, NUM_TRANSACTIONS):
        try:
            request = marketplace.generate_request()
            transaction = marketplace.process_request(request)
        except Exception as e:
            print(f"[Tx {i+1:3d}] ERROR: {e}")
            continue

        db.save_transaction(transaction)
        db.update_agent_revenue(transaction.agent_id, transaction.price_paid, transaction.api_cost)

        print(f"[Tx {i+1:3d}] {transaction.agent_id:25s} | ${transaction.price_paid:5.2f} | "
              f"{transaction.client_name:18s} | {transaction.feedback[:45]}")

        # Evolution phase
        if (i + 1) % EVOLVE_EVERY == 0:
            print()
            
            # Starvation check
            starved = evolution.check_starvation(agents, i + 1, db)
            for agent in starved:
                agent.config.status = "retired"
                db.update_agent_status(agent.config.agent_id, "retired")
                print(f"  🏜️  STARVED: {agent.config.agent_id} (never selected, market rejected)")
            
            # Evolve (crossover + mutation)
            try:
                active = [a for a in agents if a.config.status == "active"]
                marketplace.agents = active
                
                new_agent = evolution.evolve_generation(agents, db, i + 1)
                if new_agent:
                    agents.append(new_agent)
                    active = [a for a in agents if a.config.status == "active"]
                    marketplace.agents = active

                    print(f"  🧬 BORN: {new_agent.config.agent_id} (gen {new_agent.config.generation})")
                    print(f"     Parents: {new_agent.config.parent_id}")
                    print(f"     Prompt: {new_agent.config.system_prompt[:80]}...")
            except Exception as e:
                print(f"  🧬 EVOLUTION ERROR: {e}")

            # Retirement by lifespan/bankruptcy
            retired = marketplace.retire_old_agents(
                max(a.config.generation for a in agents if a.config.status == "active")
            )
            for agent, reason in retired:
                avg_p = agent.config.total_revenue / max(1, agent.config.transaction_count)
                print(f"  💀 {reason.upper():10s}: {agent.config.agent_id} "
                      f"({agent.config.transaction_count}txs, avg ${avg_p:.2f})")

            # Population snapshot
            active = [a for a in agents if a.config.status == "active"]
            marketplace.agents = active
            print(f"\n  📊 Population: {len(active)} active")
            for a in sorted(active, key=lambda x: x.config.total_revenue / max(1, x.config.transaction_count), reverse=True):
                avg = a.config.total_revenue / max(1, a.config.transaction_count)
                niche = evolution._get_agent_niche(a.config.agent_id, db) or "?"
                print(f"     {a.config.agent_id:25s} gen{a.config.generation} "
                      f"{a.config.transaction_count:2d}txs ${avg:5.2f}/tx "
                      f"niche={niche}")
            
            print("-" * 60)

    # === RESULTS ===
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    all_agents = db.get_all_agents()
    
    # Generation analysis
    gen_data = {}
    for agent in all_agents:
        g = agent.generation
        if g not in gen_data:
            gen_data[g] = {'agents': [], 'rev': 0, 'cost': 0, 'txs': 0}
        gen_data[g]['agents'].append(agent)
        gen_data[g]['rev'] += agent.total_revenue
        gen_data[g]['cost'] += agent.total_costs
        gen_data[g]['txs'] += agent.transaction_count

    for g in sorted(gen_data.keys()):
        d = gen_data[g]
        n = len(d['agents'])
        avg_price = d['rev'] / max(1, d['txs'])
        avg_profit = (d['rev'] - d['cost']) / n
        print(f"\nGen {g}: {n} agents, {d['txs']} txs, avg ${avg_price:.2f}/tx, profit ${avg_profit:.2f}/agent")
        for a in d['agents']:
            ap = a.total_revenue / max(1, a.transaction_count)
            status = "✓" if a.status == "active" else "✗"
            print(f"  {status} {a.agent_id:25s} {a.transaction_count:2d}txs ${ap:5.2f}/tx | {a.system_prompt[:60]}...")

    # Key comparison
    gen0 = gen_data.get(0, {'rev': 0, 'txs': 0})
    evolved = {k: v for k, v in gen_data.items() if k > 0}
    
    if gen0['txs'] > 0 and evolved:
        gen0_avg = gen0['rev'] / gen0['txs']
        ev_rev = sum(v['rev'] for v in evolved.values())
        ev_txs = sum(v['txs'] for v in evolved.values())
        if ev_txs > 0:
            ev_avg = ev_rev / ev_txs
            delta = ((ev_avg - gen0_avg) / gen0_avg) * 100

            print(f"\n{'=' * 40}")
            print(f"Gen 0 avg:     ${gen0_avg:.2f}/tx")
            print(f"Evolved avg:   ${ev_avg:.2f}/tx")
            print(f"Delta:         {delta:+.1f}%")
            
            if delta > 5:
                print(f"\n✅ EVOLUTION WORKS! Agents are improving!")
            elif delta > -5:
                print(f"\n⚖️  Neutral — no significant difference")
            else:
                print(f"\n❌ Still regressing — more changes needed")

    # Distribution
    print(f"\nTransaction Distribution:")
    total = sum(d['txs'] for d in gen_data.values())
    for g in sorted(gen_data.keys()):
        d = gen_data[g]
        pct = (d['txs'] / total) * 100 if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  Gen {g}: {d['txs']:3d} txs ({pct:4.1f}%) {bar}")

    # Top 5 all time
    print(f"\n🏆 Top 5 agents (by avg price/tx, min 5 txs):")
    qualified = [a for a in all_agents if a.transaction_count >= 5]
    qualified.sort(key=lambda a: a.total_revenue / a.transaction_count, reverse=True)
    for a in qualified[:5]:
        ap = a.total_revenue / a.transaction_count
        print(f"  ${ap:.2f}/tx - {a.agent_id} (gen{a.generation}, {a.transaction_count}txs)")
        print(f"    {a.system_prompt[:80]}...")

    print(f"\n{'=' * 60}")
    print("V4 complete!")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
