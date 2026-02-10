#!/bin/bash
# Run V6 experiments sequentially in background
# Usage: nohup bash scripts/run_v6_batch.sh > logs/v6_batch.log 2>&1 &

set -e
cd "$(dirname "$0")/.."

echo "=== V6 Batch Run Started: $(date) ==="

for mode in reflective random static; do
  for run in 1 2 3; do
    echo ""
    echo ">>> Starting $mode run $run at $(date)"
    python3 scripts/run_v6.py --mode $mode --run $run --resume 2>&1 | tee -a logs/v6_${mode}_run${run}.log
    echo ">>> Finished $mode run $run at $(date)"
  done
done

echo ""
echo "=== V6 Batch Run Complete: $(date) ==="
