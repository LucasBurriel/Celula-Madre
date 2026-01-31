# Célula Madre MVP

**Price-Driven Evolution of AI Coding Agents**

An experimental system where AI coding agents evolve based on market price signals rather than traditional benchmarks.

## Concept

Instead of optimizing agents against fixed benchmarks, Célula Madre uses a simulated marketplace where:
- Agents generate code for client requests
- Bot clients evaluate code and pay based on their preferences (brevity, documentation, tests, etc.)
- Higher-earning agents are more likely to "reproduce" (have their prompts evolved)
- Claude mutates agent prompts based on market feedback

## MVP Scope

This MVP validates the core hypothesis: **Can price signals guide agent evolution better than random mutation?**

**Includes:**
- ✅ Simple agents with variable system prompts (only mutation)
- ✅ 4 bot clients with different preferences
- ✅ Greedy + epsilon-random selection (80/20)
- ✅ Small population (3-8 agents)
- ✅ SQLite persistence
- ✅ Evolution tracking

**Not included** (deferred to MVP-2):
- Clade-Metaproductivity (CMP) selection
- Multiple LLM models
- Full AP2 protocol
- Web UI

## Installation

### Prerequisites
- Python 3.10+
- Anthropic API key

### Setup

```bash
# Clone or navigate to project
cd Celula-Madre

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

## Usage

### Run the experiment

```bash
python main.py
```

This will:
1. Create 3 initial agents with different system prompts
2. Run 50 simulated transactions
3. Evolve agents every 10 transactions
4. Display results and statistics

### Run tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific component tests
pytest tests/test_database.py -v
pytest tests/test_agent.py -v
pytest tests/test_clients.py -v
pytest tests/test_marketplace.py -v
pytest tests/test_evolution.py -v
```

## Project Structure

```
celula-madre-mvp/
├── src/
│   ├── agent.py          # SimpleAgent (code generation with Claude)
│   ├── clients.py        # Bot clients (evaluators)
│   ├── marketplace.py    # Request generation and processing
│   ├── evolution.py      # Evolutionary engine
│   └── database.py       # SQLite persistence
├── tests/
│   ├── test_agent.py
│   ├── test_clients.py
│   ├── test_marketplace.py
│   ├── test_evolution.py
│   └── test_database.py
├── main.py               # Main execution script
├── schema.sql            # Database schema
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## How It Works

### 1. Agent Population
- Starts with 3 agents, each with different system prompts
- Agents use Claude Sonnet to generate code

### 2. Marketplace
- Generates random coding requests
- Assigns requests to agents (random in MVP)
- Bot clients evaluate generated code and pay accordingly

### 3. Bot Clients
Four types of clients with different preferences:

- **MinimalistClient**: Pays more for concise code (< 20 lines)
- **DocumenterClient**: Pays more for good documentation
- **TesterClient**: Pays more for comprehensive tests
- **PragmaticClient**: Pays more for simple, working code

### 4. Evolution
- Every 10 transactions, creates a new agent
- Selects parent using greedy + epsilon strategy (80% best, 20% random)
- Uses Claude to evolve the parent's system prompt based on market feedback
- New agent joins the population

### 5. Results
- Tracks total revenue and average price per agent
- Compares evolved agents (gen > 0) vs initial agents (gen 0)
- Success = evolved agents earn more on average

## Success Criteria

After 50 transactions, the MVP is successful if:

1. ✅ Average revenue increases between generations (Gen 5 > Gen 0)
2. ✅ Variation exists between agents (some earn more than others)
3. ✅ Prompts evolve in interpretable ways
4. ✅ Evolution guided > random mutation (control experiment)

## Example Output

```
[Tx 1] Agent: agent_gen0_0    | Price: $12.00 | Client: DocumenterClient    | Feedback: Good documentation
[Tx 2] Agent: agent_gen0_1    | Price: $15.00 | Client: MinimalistClient    | Feedback: Excellent brevity
...
🧬 EVOLUTION: New agent created!
   ID: agent_gen1_5472
   Generation: 1
   Parent: agent_gen0_1
   Prompt (first 80 chars): You are a concise Python expert focusing on minimal, clear solutions...

FINAL RESULTS
================================================================
Agent: agent_gen1_5472
  Generation: 1
  Parent: agent_gen0_1
  Total Revenue: $68.50
  Transactions: 5
  Avg Price: $13.70
...

SUMMARY STATISTICS
================================================================
Generation 0 (baseline):
  Avg Revenue: $45.00
  Avg Price per Transaction: $10.20

Evolved Agents (gen > 0):
  Avg Revenue: $62.30
  Avg Price per Transaction: $12.85

✅ Improvement: +26.0% avg price (evolution working!)
```

## Technical Details

- **Database**: SQLite (`celula_madre.db`)
- **LLM**: Claude 3.5 Sonnet via Anthropic API
- **Selection**: Greedy (80%) + Epsilon-random (20%)
- **Mutation**: Claude-driven prompt evolution
- **Population**: 3-8 agents (grows by 1 every 10 transactions)

## Next Steps (Post-MVP)

If the hypothesis is validated:

**MVP-2**:
- Clade-Metaproductivity (CMP) selection
- Revenue-weighted agent assignment
- More sophisticated bot clients

**MVP-3**:
- Multiple LLM models (Opus, Sonnet, Haiku)
- PostgreSQL
- Basic web dashboard

**Full Vision**:
- Variable MCP servers
- Configurable tools
- Real AP2 protocol
- Public marketplace

## References

- **Austrian Economics**: Hayek's price signals vs central planning
- **AP2 Protocol**: Agent Payments Protocol (Google)
- **DGM**: Darwin Gödel Machine (self-evolving code)

## License

[Your license here]

## Contributing

This is an experimental research project. Feedback and contributions welcome!
