from src.database import Database

db = Database('celula_madre.db')
print('Total transactions:', db.get_transaction_count_total())

# Get last few transactions directly from database
cursor = db.conn.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 5")
txs = cursor.fetchall()
if txs:
    print("\nLast 5 transactions:")
    for tx in reversed(txs):  # Show oldest first
        print(f'Agent: {tx["agent_id"]} | Price: ${tx["price_paid"]:.2f} | Client: {tx["client_name"]} | Feedback: {tx["feedback"]}')

agents = db.get_all_agents()
print(f"\nAgents: {len(agents)} total")
for agent in agents:
    avg_price = agent.total_revenue / max(1, agent.transaction_count) if agent.transaction_count > 0 else 0
    print(f'  {agent.agent_id} (Gen {agent.generation}): {agent.transaction_count} txs, ${agent.total_revenue:.2f} revenue, ${avg_price:.2f} avg')

db.close()