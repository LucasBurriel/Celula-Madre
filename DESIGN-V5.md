# Célula Madre V5 — Market-Driven Prompt Evolution

## Core Idea
Agents predict BTC/ETH direction using real historical data.
Evolution uses GEPA-style reflective mutation + Pareto selection.
The market IS the fitness function — no simulated scores.

## Architecture

### Market Environment
- Historical BTC/ETH data (OHLCV + news headlines)
- Each "round": agent sees last N candles + recent news
- Agent predicts: UP or DOWN for next period
- Ground truth: actual price movement
- Fitness = accuracy over multiple rounds

### Agent = System Prompt
- Each agent is a system prompt that defines a trading strategy
- The LLM (Qwen3 local) executes the strategy given market context
- Prompt contains: analysis methodology, risk rules, indicators to watch

### Evolution Loop (per generation)
1. **Evaluate**: Run each agent on dev set (subset of historical data)
2. **Collect trajectories**: What the agent reasoned, what it predicted, why
3. **Reflect**: LLM sees failures + trajectories → proposes improved prompt
4. **Gate**: Only accept if new prompt doesn't degrade on dev set
5. **Validate**: Score on held-out val set
6. **Pareto update**: Track who's best at what (bull markets, crashes, sideways)
7. **Merge**: Combine complementary strategies (e.g., one good at crashes + one good at rallies)

### Key Difference from V4
- V4: Simulated clients with random preferences → noise
- V5: Real historical prices → deterministic ground truth
- V4: Random mutation → no learning from failures  
- V5: Reflective mutation → learns WHY it failed
- V4: Single "best" metric → premature convergence
- V5: Pareto frontier → preserves diverse strategies

## Data Pipeline
1. Fetch BTC/ETH daily OHLCV from free API (CoinGecko/Binance)
2. Fetch historical news headlines (optional, phase 2)
3. Split into train (dev+val) and test sets
4. Each "example" = {context: last 30 days, question: "direction next 24h?", answer: actual}

## Metrics
- Primary: direction accuracy (% correct UP/DOWN)
- Secondary: confidence-weighted accuracy (high confidence + correct = bonus)
- Tertiary: max drawdown avoidance (penalize wrong calls on big moves)

## Evolution Parameters (from GEPA)
- Population: 8 agents
- Generations: 10-20
- Mutation rate: 0.5 (50% mutate, 50% carry forward)
- Dev/val split: 50/50
- Merge: enabled, max 5 per generation
- Gating: child >= parent on dev set

## LLM Usage
- Agent execution: Qwen3-30B local (free)
- Reflection/mutation: Qwen3-30B local (free)
- Total cost: $0 (all local)
