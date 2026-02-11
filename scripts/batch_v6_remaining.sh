#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/Celula-Madre
LOG=results/v6/batch_$(date +%Y%m%d_%H%M).log
echo "=== V6 Batch — $(date) ===" | tee -a "$LOG"

for mode in reflective random static; do
  for run in 1 2 3; do
    RESFILE="results/v6/${mode}/run_${run}/results.json"
    if [ -f "$RESFILE" ]; then
      echo "SKIP $mode run_$run (results.json exists)" | tee -a "$LOG"
      continue
    fi
    echo "START $mode run_$run at $(date)" | tee -a "$LOG"
    python3 -u scripts/run_v6.py --mode "$mode" --run "$run" --resume 2>&1 | tee -a "$LOG"
    echo "DONE $mode run_$run at $(date)" | tee -a "$LOG"
  done
done
echo "=== ALL DONE $(date) ===" | tee -a "$LOG"
