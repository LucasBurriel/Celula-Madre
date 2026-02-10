#!/bin/bash
# Run all V6 experiments sequentially
set -e
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1

echo "=== V6 Experiment Suite Started: $(date) ==="

# 3 runs per mode
for mode in reflective random static; do
  for run in 1 2 3; do
    echo ">>> Starting $mode run $run at $(date)"
    python3 -u scripts/run_v6.py --mode "$mode" --run "$run" --resume
    echo "<<< Finished $mode run $run at $(date)"
  done
done

echo "=== V6 Experiment Suite Complete: $(date) ==="
