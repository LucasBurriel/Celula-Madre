#!/bin/bash
# Run all remaining V6 experiments sequentially
# Each run takes ~5h with Qwen3-30B
# Total: ~40h for 8 remaining runs

cd "$(dirname "$0")/.."
LOG="results/v6/batch_remaining.log"

echo "=== V6 Batch Runner — Started $(date) ===" | tee -a "$LOG"

for mode in reflective random static; do
  for run in 1 2 3; do
    RESULTS_FILE="results/v6/$mode/run_$run/results.json"
    RECOVERED="results/v6/$mode/run_$run/results_recovered.json"
    
    # Skip if already completed
    if [ -f "$RESULTS_FILE" ] || [ -f "$RECOVERED" ]; then
      echo "SKIP $mode run_$run (already done)" | tee -a "$LOG"
      continue
    fi
    
    echo "START $mode run_$run at $(date)" | tee -a "$LOG"
    python3 scripts/run_v6.py --mode "$mode" --run "$run" --resume 2>&1 | tee -a "results/v6/${mode}_run${run}.log"
    echo "DONE $mode run_$run at $(date)" | tee -a "$LOG"
  done
done

echo "=== V6 Batch Runner — Finished $(date) ===" | tee -a "$LOG"
