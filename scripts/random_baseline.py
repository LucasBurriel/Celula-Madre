"""Random baseline: measure what random UP/DOWN achieves on test set."""
import sys, os, json, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.market_data import create_examples, split_examples

examples = create_examples("data/btc_daily_365.json", asset="BTC")
_, _, test = split_examples(examples)

N_RUNS = 10000
accs = []
for _ in range(N_RUNS):
    correct = sum(1 for ex in test if random.choice(["UP","DOWN"]) == ex.direction)
    accs.append(correct / len(test))

accs = np.array(accs)
print(f"Random baseline on {len(test)} test examples ({N_RUNS} runs):")
print(f"  Mean: {accs.mean():.4f}")
print(f"  Std:  {accs.std():.4f}")
print(f"  95% CI: [{np.percentile(accs, 2.5):.4f}, {np.percentile(accs, 97.5):.4f}]")

# Also check class balance
up = sum(1 for ex in test if ex.direction == "UP")
print(f"\nClass balance: UP={up}/{len(test)} ({up/len(test):.1%}), DOWN={len(test)-up}/{len(test)} ({(len(test)-up)/len(test):.1%})")
print(f"Always-UP baseline: {up/len(test):.4f}")
print(f"Always-DOWN baseline: {(len(test)-up)/len(test):.4f}")
