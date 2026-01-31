"""Quick script to check MVP-2 experiment progress."""
import sqlite3
import os

db_path = "celula_madre.db"

if not os.path.exists(db_path):
    print("❌ Database not found. Experiment hasn't started yet.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get transaction count
tx_count = cursor.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]

# Get agent stats
agents = cursor.execute('''
    SELECT agent_id, generation, transaction_count, total_revenue,
           total_costs, net_profit, status
    FROM agents
    ORDER BY generation, agent_id
''').fetchall()

# Get generation distribution
gen_dist = {}
for agent in agents:
    gen = agent[1]
    txs = agent[2]
    gen_dist[gen] = gen_dist.get(gen, 0) + txs

print("=" * 60)
print(f"MVP-2 PROGRESS: {tx_count}/200 transactions")
print("=" * 60)

print(f"\nAgents: {len(agents)} total")
active = [a for a in agents if a[6] == 'active']
retired = [a for a in agents if a[6] == 'retired']
print(f"  Active: {len(active)}, Retired: {len(retired)}")

print("\nTransaction Distribution by Generation:")
for gen in sorted(gen_dist.keys()):
    count = gen_dist[gen]
    pct = (count / tx_count * 100) if tx_count > 0 else 0
    print(f"  Gen {gen}: {count} txs ({pct:.1f}%)")

print("\nTop 3 Agents by Net Profit:")
top_agents = sorted(agents, key=lambda a: a[5], reverse=True)[:3]
for agent in top_agents:
    agent_id, gen, tx_count, revenue, costs, profit, status = agent
    print(f"  {agent_id} (Gen {gen}, {status}): ${profit:.2f} profit ({tx_count} txs)")

# Get recent transactions
recent = cursor.execute('''
    SELECT agent_id, client_name, price_paid, feedback, api_cost
    FROM transactions
    ORDER BY created_at DESC
    LIMIT 5
''').fetchall()

print("\nLast 5 Transactions:")
for tx in recent:
    agent_id, client, price, feedback, cost = tx
    print(f"  {agent_id[:15]:15s} | {client:18s} | ${price:5.2f} | Cost: ${cost:.4f} | {feedback}")

conn.close()
print("\n" + "=" * 60)
