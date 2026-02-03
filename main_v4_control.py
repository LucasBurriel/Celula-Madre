"""
Célula Madre V4 Control Group — Random Evolution (no market feedback)

IDENTICAL to main_v4.py EXCEPT:
- Uses EvolutionV4Control instead of EvolutionV4
- Random parent selection (not fitness-based)
- Random mutation (no market feedback in prompts)
- Uses separate DB: celula_madre_v4_control.db

Same: initial agents, marketplace, clients, retirement, death rules.
This isolates the effect of price-guided evolution.
"""

import sys
import random
from src.database import Database, AgentConfig
from src.agent import SimpleAgent
from src.marketplace_v3 import MarketplaceV3
from src.evolution_v4_control import EvolutionV4Control


def main():
    print("=" * 60)
    print("CÉLULA MADRE V4 CONTROL: Random Evolution (no feedback)")
    print("=" * 60)
    print()
    print("Same as V4 experimental but:")
    print("  - Random parent selection (not fitness-based)")
    print("  - Random mutation (no market feedback)")
    print("  - Same market, clients, retirement, death rules")
    print()

    db = Database("celula_madre_v4_control.db")

    existing_agents = db.get_all_agents()
    completed_txs = db.get_transaction_count_total()

    if existing_agents and completed_txs > 0:
        print(f"[RESUME] {completed_txs} txs done, {len(existing_agents)} agents")
        agents = [SimpleAgent(ac) for ac in existing_agents if ac.status == "active"]
        print(f"[RESUME] Loaded {len(agents)} active agents")
        start_tx = completed_txs
    else:
        print("[Setup] Creating initial population (IDENTICAL to V4 experimental)...")
        # SAME initial prompts as V4
        initial_prompts = [
            "Write Python in under 20 lines. No comments, no docstrings, no fluff. "
            "One function, minimal imports, return the result. Brevity is everything.",
            
            "Every function gets a docstring with Args/Returns/Example. Every block gets a comment. "
            "Use type hints on all parameters and returns. Documentation is the product.",
            
            "For every function, write at least 3 test functions using assert. "
            "Test edge cases, empty inputs, and normal cases. Tests are more important than the code itself.",
            
            "Write simple, working Python. Use try/except for error handling. "
            "Keep it under 25 lines. No fancy patterns, just code that parses and runs correctly.",
        ]

        agents = []
        specialist_names = ["minimalist", "documenter", "tester", "pragmatist"]
        for i, (prompt, name) in enumerate(zip(initial_prompts, specialist_names)):
            config = AgentConfig(
                agent_id=f"ctrl_gen0_{name}",
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
    evolution = EvolutionV4Control()  # RANDOM evolution

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
            
            # RANDOM evolution: pick 2 random active parents, crossover + random mutate
            try:
                active = [a for a in agents if a.config.status == "active"]
                marketplace.agents = active
                
                if len(active) >= 2 and len(active) < 8:
                    # RANDOM parent selection (key difference from V4!)
                    parent1, parent2 = random.sample(active, 2)
                    
                    gen = max(parent1.config.generation, parent2.config.generation) + 1
                    new_id = f"ctrl_gen{gen}_tx{i+1}"
                    
                    new_prompt = evolution.random_crossover_and_mutate(
                        parent1.config.system_prompt,
                        parent2.config.system_prompt
                    )
                    
                    if new_prompt:
                        new_config = AgentConfig(
                            agent_id=new_id,
                            generation=gen,
                            parent_id=f"{parent1.config.agent_id}+{parent2.config.agent_id}",
                            system_prompt=new_prompt
                        )
                        new_agent = SimpleAgent(new_config)
                        db.save_agent(new_config)
                        agents.append(new_agent)
                        active = [a for a in agents if a.config.status == "active"]
                        marketplace.agents = active
                        
                        print(f"  🎲 BORN (RANDOM): {new_id} (Gen{gen})")
                        print(f"     Parents: {parent1.config.agent_id} + {parent2.config.agent_id}")
                        print(f"     Prompt: {new_prompt[:80]}...")
            except Exception as e:
                print(f"  🎲 RANDOM EVOLUTION ERROR: {e}")

            # Retirement by lifespan/bankruptcy (SAME as V4)
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
                print(f"     {a.config.agent_id:25s} gen{a.config.generation} "
                      f"{a.config.transaction_count:2d}txs ${avg:5.2f}/tx")
            
            print("-" * 60)

    # === RESULTS ===
    print("\n" + "=" * 60)
    print("CONTROL GROUP RESULTS")
    print("=" * 60)

    all_agents = db.get_all_agents()
    
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
            print(f"CONTROL GROUP (Random Evolution):")
            print(f"Gen 0 avg:     ${gen0_avg:.2f}/tx")
            print(f"Evolved avg:   ${ev_avg:.2f}/tx")
            print(f"Delta:         {delta:+.1f}%")
            
            if delta > 5:
                print(f"\n⚠️  Random evolution ALSO improved — market selection alone may explain it")
            elif delta > -5:
                print(f"\n📊 Neutral — random evolution didn't help or hurt")
            else:
                print(f"\n📉 Random evolution degraded performance")

    print(f"\nTransaction Distribution:")
    total = sum(d['txs'] for d in gen_data.values())
    for g in sorted(gen_data.keys()):
        d = gen_data[g]
        pct = (d['txs'] / total) * 100 if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  Gen {g}: {d['txs']:3d} txs ({pct:4.1f}%) {bar}")

    print(f"\n{'=' * 60}")
    print("Control group complete!")
    print("Compare with V4 experimental (celula_madre_v4_results.db)")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
