# DESIGN-V7: DGM Replication + Incentive Swap

## Philosophy
First replicate DGM's approach (code self-improvement with benchmark fitness).
Verify it works. Then swap the incentive mechanism from benchmarks to market signals.

## Phase 1: Replicate DGM Core Loop

### Architecture (from DGM paper/code)
```
Population Archive (all agents that compile + pass gating)
    │
    ├─ Select parent (score_child_prop: sigmoid(score) × 1/(1+children))
    │
    ├─ Diagnose: LLM analyzes parent's failures on a task
    │   → Structured JSON: log_summary, potential_improvements, 
    │     improvement_proposal, implementation_suggestion, problem_description
    │
    ├─ Implement: Coding LLM modifies parent's code based on diagnosis
    │   → Produces a diff/patch
    │
    ├─ Evaluate: Run modified agent on benchmark tasks
    │   → accuracy_score, resolved/unresolved task lists
    │
    ├─ Gate: Does it compile? Does it pass minimum threshold?
    │
    └─ Archive: If passes gating → add to population archive
```

### Key DGM Mechanisms to Replicate
1. **score_child_prop selection**: sigmoid(score) × 1/(1+children_count)
2. **Separated diagnosis/implementation**: One LLM diagnoses, another implements
3. **Infinite archive**: Never discard, let selection handle it
4. **Docker sandbox**: Code runs in isolation
5. **Structured diagnosis prompts**: Different prompts for different failure types

### Simplifications for V7
- Use Qwen3-30B (local) for both diagnosis and implementation
- Use Polyglot benchmark (simpler than SWE-bench, multi-language)
- Start with small subset (10-20 tasks) for fast iteration
- If Qwen can't handle it, fall back to Claude API for diagnosis only

### Task: Polyglot Benchmark
- Multi-language coding tasks (Python, JS, Go, Rust, Java, C++)
- Clear pass/fail evaluation
- Already supported by DGM codebase
- Subset selection: pick easiest 10-20 for initial validation

## Phase 2: Verify It Works
- Run 10-20 generations
- Track: accuracy_score per generation, number of compiled patches, improvement rate
- Success criterion: monotonic improvement in archive best score
- Compare against baseline (no evolution, just initial agent)

## Phase 3: Swap Incentive (Célula Madre Thesis)
Once DGM loop is verified working:
- Keep: code mutation, archive, selection mechanism
- Replace: benchmark fitness → market/price signal
  - Instead of "does it pass tests?" → "do clients choose this agent?"
  - Clients = different task profiles with preferences
  - Revenue = fitness signal
- Compare: same architecture, different selection pressure
  - Group A: benchmark selection (DGM original)
  - Group B: market selection (Célula Madre)
  - Hypothesis: market selection produces more diverse, robust agents

## Implementation Plan

### Files to Create
- `src/dgm_loop.py` — Main DGM evolution loop
- `src/dgm_diagnose.py` — Diagnosis prompts and logic
- `src/dgm_agent.py` — Coding agent (tool-using LLM)
- `src/dgm_evaluate.py` — Benchmark evaluation
- `src/dgm_selection.py` — Parent selection (score_child_prop)
- `src/dgm_archive.py` — Archive management
- `scripts/run_dgm.py` — CLI runner

### LLM Configuration
```python
# Diagnosis model (needs reasoning)
DIAGNOSE_MODEL = "qwen3-coder-30b-a3b-instruct"  # with thinking
DIAGNOSE_ENDPOINT = "http://172.17.0.1:1234/v1"

# Coding model (needs tool use)  
CODING_MODEL = "qwen3-coder-30b-a3b-instruct"  # without thinking for speed
CODING_ENDPOINT = "http://172.17.0.1:1234/v1"
```

### Evaluation
- Docker sandbox for code execution (like DGM)
- Or simpler: subprocess with timeout (sufficient for Polyglot)
- Pass/fail on test suite

## Success Metrics
- Phase 1: DGM loop runs without errors, produces patches
- Phase 2: Archive best score improves over generations
- Phase 3: Statistical comparison of benchmark vs market selection

## References
- DGM repo: research/celula-madre/dgm-reference/
- DGM paper: arxiv.org/abs/2505.22954
- Key files: DGM_outer.py, self_improve_step.py, prompts/
