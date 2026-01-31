-- Célula Madre MVP - Database Schema

CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    generation INTEGER NOT NULL,
    parent_id TEXT,
    system_prompt TEXT NOT NULL,
    total_revenue REAL DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    total_costs REAL DEFAULT 0,
    net_profit REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (DATETIME('now', 'subsec')),
    FOREIGN KEY (parent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    code_generated TEXT NOT NULL,
    price_paid REAL NOT NULL,
    client_name TEXT NOT NULL,
    feedback TEXT,
    tokens_used INTEGER DEFAULT 0,
    api_cost REAL DEFAULT 0,
    created_at TEXT DEFAULT (DATETIME('now', 'subsec')),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_revenue ON agents(total_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_agent ON transactions(agent_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at DESC);
