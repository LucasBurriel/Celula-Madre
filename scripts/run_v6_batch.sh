#!/bin/bash
# V6 Batch Runner — all remaining runs
cd /home/ubuntu/.openclaw/workspace/Celula-Madre
LOG="results/v6/batch_$(date +%Y%m%d_%H%M).log"

echo "=== V6 Batch Runner — Started $(date) ===" | tee "$LOG"

declare -a RUNS=(
  "reflective 2"
  "reflective 3"
  "random 1"
  "random 2"
  "random 3"
  "static 1"
  "static 2"
  "static 3"
)

for entry in "${RUNS[@]}"; do
  mode=$(echo $entry | cut -d' ' -f1)
  run=$(echo $entry | cut -d' ' -f2)
  
  # Skip if already has results
  if [ -f "results/v6/$mode/run_$run/results.json" ]; then
    echo "SKIP $mode run_$run (results.json exists)" | tee -a "$LOG"
    continue
  fi
  
  echo "START $mode run_$run at $(date)" | tee -a "$LOG"
  python3 scripts/run_v6.py --mode "$mode" --run "$run" --resume 2>&1 | tee -a "$LOG"
  echo "DONE $mode run_$run at $(date)" | tee -a "$LOG"
  echo "---" | tee -a "$LOG"
done

echo "=== ALL RUNS COMPLETE at $(date) ===" | tee -a "$LOG"
