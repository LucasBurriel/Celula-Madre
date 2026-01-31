# MVP-2 Implementation Plan: Generational Lifecycle & Austrian Economics

**Date**: 2026-01-04
**Goal**: Enable creative destruction through generational death + Austrian cost/reputation mechanisms

---

## Problem Statement

MVP-1.1 showed that Client Choice creates perfect market segmentation, but pure greedy selection causes a "frozen market":
- Gen0 agents monopolize all transactions
- Gen1-2 agents (18 created) received 0 transactions
- No innovation opportunities despite better prompts potentially existing

---

## Solution: Four Austrian Mechanisms

### 1. Generational Death (PRIORITY 1) ⭐
**Mechanism**: Agents retire after reaching lifespan limit, forcing clients to discover new agents

**Implementation**:
```python
# Retirement policies
MAX_AGENT_LIFESPAN_TXS = 40  # Max transactions before retirement
MAX_GENERATION_GAP = 3       # Max generations behind current

class Marketplace:
    def retire_old_agents(self, current_generation: int):
        """Remove agents that are too old or have too many transactions"""
        active = []
        retired = []

        for agent in self.agents:
            # Retirement conditions
            too_many_txs = agent.config.transaction_count >= MAX_AGENT_LIFESPAN_TXS
            too_old = (current_generation - agent.config.generation) > MAX_GENERATION_GAP

            if too_many_txs or too_old:
                retired.append(agent)
                agent.config.status = "retired"  # NEW FIELD
                db.update_agent_status(agent.config.agent_id, "retired")
            else:
                active.append(agent)

        self.agents = active
        return retired
```

**Effects**:
- Forces clients to try new agents when favorites retire
- Natural succession: Gen1 inherits Gen0's clients
- Preserves historical data for CMP calculations
- Mimics real business lifecycle

### 2. Token-Based Costs (PRIORITY 2)
**Mechanism**: Agents pay for API usage, reducing net profit

**Implementation**:
```python
@dataclass
class AgentConfig:
    # ... existing fields
    total_revenue: float = 0.0
    total_costs: float = 0.0      # NEW
    net_profit: float = 0.0        # NEW

@dataclass
class Transaction:
    # ... existing fields
    tokens_used: int = 0           # NEW
    api_cost: float = 0.0          # NEW

# In agent.solve_request():
response = self.client.messages.create(...)
tokens_used = response.usage.input_tokens + response.usage.output_tokens

# Haiku pricing: $1/MTok input, $5/MTok output
input_cost = (response.usage.input_tokens / 1_000_000) * 1.00
output_cost = (response.usage.output_tokens / 1_000_000) * 5.00
api_cost = input_cost + output_cost

self.config.total_costs += api_cost
self.config.net_profit = self.config.total_revenue - self.config.total_costs

return code, tokens_used, api_cost
```

**Effects**:
- Rewards efficiency (low token usage)
- Penalizes verbosity (high costs)
- Net profit becomes true fitness metric

### 3. Reputation System (PRIORITY 3)
**Mechanism**: Track success rate as reputation score for client decisions

**Implementation**:
```python
# In Database class
def get_reputation(self, agent_id: str) -> float:
    """
    Reputation = success_rate * experience_factor

    Experience factor: min(tx_count / 10, 1.0)
    - New agents start low even with 100% success (low sample size)
    - Reputation caps at 10 transactions
    """
    success_rate = self.get_success_rate(agent_id)
    tx_count = self.get_transaction_count(agent_id)

    experience_factor = min(tx_count / 10.0, 1.0)
    reputation = success_rate * experience_factor

    return reputation

# Clients can use reputation in scoring
def select_agent(self, agents, db):
    scores = []
    for agent in agents:
        # Example: Combine reputation with specific preferences
        reputation = db.get_reputation(agent.config.agent_id)
        specific_score = calculate_client_specific_score(agent, db)

        # Weight: 50% reputation, 50% client preferences
        total_score = 0.5 * reputation + 0.5 * specific_score
        scores.append(total_score)

    return agents[scores.index(max(scores))]
```

**Effects**:
- New agents can build reputation quickly
- Low sample size doesn't over-reward lucky agents
- Clients have simple heuristic for quality

### 4. Epsilon-Greedy Exploration (OPTIONAL)
**Mechanism**: 20% random selection to give new agents opportunities

**Implementation**:
```python
EXPLORATION_RATE = 0.2

def select_agent(self, agents, db):
    if random.random() < EXPLORATION_RATE:
        # Exploration: Random selection
        return random.choice(agents)
    else:
        # Exploitation: Greedy selection
        return greedy_selection_with_reputation(agents, db)
```

**Effects**:
- Guarantees new agents get opportunities
- Allows discovery of better agents
- Trade-off: 20% of transactions are "wasteful"

---

## Changes Required

### Database Schema Updates
```sql
-- Add new fields to agents table
ALTER TABLE agents ADD COLUMN total_costs REAL DEFAULT 0.0;
ALTER TABLE agents ADD COLUMN net_profit REAL DEFAULT 0.0;
ALTER TABLE agents ADD COLUMN status TEXT DEFAULT 'active';  -- 'active' or 'retired'

-- Add new fields to transactions table
ALTER TABLE transactions ADD COLUMN tokens_used INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN api_cost REAL DEFAULT 0.0;
```

### File Changes
1. **schema.sql**: Add new columns
2. **src/database.py**:
   - Add `get_reputation()`, `get_transaction_count()`, `update_agent_status()`
   - Update `save_agent()`, `save_transaction()`, `update_agent_revenue()` for new fields
3. **src/agent.py**:
   - Return `(code, tokens_used, api_cost)` from `solve_request()`
4. **src/marketplace.py**:
   - Add `retire_old_agents()` method
   - Update `process_request()` to track costs
5. **src/clients.py** (optional):
   - Add epsilon-greedy exploration to each `select_agent()`
6. **main.py**:
   - Call `marketplace.retire_old_agents()` after each evolution
   - Track and display cost metrics

---

## Experimental Design

### Variables
- **Independent Variables**:
  - Retirement enabled (True/False)
  - Epsilon-greedy rate (0.0, 0.1, 0.2)
  - Cost tracking (True/False)

- **Dependent Variables**:
  - Gen1+ transaction rate
  - Number of unique agents with txs > 0
  - Average price over time
  - Net profit distribution

### Test Runs
1. **Control**: No retirement, no epsilon, no costs (MVP-1.1 baseline)
2. **Treatment 1**: Retirement only
3. **Treatment 2**: Retirement + epsilon=0.2
4. **Treatment 3**: Retirement + epsilon=0.2 + costs

### Success Criteria
- Gen1+ agents receive > 20% of transactions (vs 0% in MVP-1.1)
- At least 5 unique agents with txs > 0 (vs 3 in MVP-1.1)
- Market diversity: No agent has > 60% market share in final 50 txs

---

## Implementation Steps

1. **Update Schema**:
   - Add new columns to `schema.sql`
   - Create migration script for existing DBs

2. **Implement Cost Tracking**:
   - Modify `AgentConfig` dataclass
   - Update `agent.solve_request()` to return costs
   - Update `marketplace.process_request()` to record costs

3. **Implement Retirement Mechanism**:
   - Add `retire_old_agents()` to `Marketplace`
   - Add `update_agent_status()` to `Database`
   - Call after each evolution in `main.py`

4. **Implement Reputation System**:
   - Add `get_reputation()` to `Database`
   - Update client selection logic (optional)

5. **Add Epsilon-Greedy** (optional):
   - Modify each client's `select_agent()` method

6. **Update Main Script**:
   - Add retirement calls
   - Display cost/profit metrics
   - Track generation diversity

7. **Run Experiments**:
   - Control + 3 treatments
   - 200 transactions each
   - Compare results

---

## Expected Outcomes

### With Retirement Only
- Gen1 agents start getting transactions after Gen0 retirements
- Market turnover creates opportunities
- Some agents may never get opportunities if Gen0 doesn't retire fast enough

### With Retirement + Epsilon-Greedy
- Gen1 agents get opportunities immediately (20% of txs)
- Faster discovery of better prompts
- Some waste from random selection

### With Retirement + Epsilon + Costs
- Efficient agents (low token usage) rise to top
- Verbose agents penalized by net profit
- True Austrian competition: revenue - costs

---

## Timeline

1. Schema + Database updates: 30 min
2. Cost tracking implementation: 30 min
3. Retirement mechanism: 30 min
4. Reputation system: 20 min
5. Epsilon-greedy (optional): 20 min
6. Testing + experiments: 1-2 hours

**Total**: ~3-4 hours

---

## Risks & Mitigations

**Risk 1**: Retirement too aggressive → all agents die
- **Mitigation**: Ensure `MAX_LIFESPAN_TXS` is reasonable (40 txs allows participation)

**Risk 2**: Epsilon too high → too much waste
- **Mitigation**: Start with 0.2, can tune down to 0.1 if needed

**Risk 3**: Costs dominate revenue → all agents unprofitable
- **Mitigation**: Haiku is very cheap (~$0.003 per tx), should be fine

**Risk 4**: Reputation favors lucky agents
- **Mitigation**: Experience factor caps reputation until 10 txs

---

## Conclusion

MVP-2 implements the missing piece from MVP-1.1: **generational lifecycle management**. By adding retirement, costs, and reputation, we create a true Austrian market:
- Creative destruction (retirement)
- Production costs (token usage)
- Information aggregation (reputation)
- Discovery process (epsilon-greedy)

This should unlock the frozen market and allow genuine evolution to occur.
