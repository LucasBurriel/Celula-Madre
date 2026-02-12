# Gating Problem Analysis & Fix

## Problem
In V6 and V6.5, mutations almost never pass gating. All 8 agents in V6.5 Market Run 1 are still gen-0 seeds after 4 generations. V6 had the same pattern — only rare mutations passed.

## Root Cause
**Strict gating (`child_acc >= parent_acc`) on noisy evaluations.**

With 100 validation examples, accuracy has a standard error of ~√(p(1-p)/n) ≈ 3% for p=0.9. A mutation that's equally good as its parent will be rejected ~50% of the time purely by noise. A slightly better mutation (1% improvement) still gets rejected ~40% of the time.

For a parent at 91% accuracy on 100 examples:
- Child at 91% (equally good): 50% chance of rejection
- Child at 92% (1pp better): ~40% chance of rejection  
- Child at 88% (3pp worse): ~90% chance of rejection (correctly rejected)

## Fix: Tolerance-Based Gating
Accept child if `child_acc >= parent_acc - tolerance` where tolerance defaults to 3%.

**Why 3%?** It's approximately 1 standard error for binomial noise on 100 examples. This means:
- Equally good mutations: ~85% acceptance rate (was ~50%)
- 1pp better: ~90% acceptance rate (was ~60%)
- 3pp worse: ~50% acceptance rate (correctly more likely to be rejected)
- 5pp worse: ~15% acceptance rate (almost always rejected)

This lets evolution explore more while still rejecting clearly bad mutations. The selection pressure (market or tournament) handles the rest — bad agents that sneak through gating will be eliminated by competitive pressure.

## Implementation
- Added `gating_tolerance: float = 0.03` to V6Config and V65Config
- Changed gating condition from `>=` to `>= parent - tolerance`
- Added delta reporting in logs (✓ for improvement, ≈ for within tolerance)
- Backwards compatible — existing checkpoints work, tolerance applies on resume

## Theoretical Justification
In Austrian economics terms: strict gating is like requiring a new entrant to immediately outperform incumbents. Real markets allow entry with "good enough" products — the market itself determines winners over time. The tolerance mirrors a market entry barrier that's realistic rather than prohibitive.
