#!/usr/bin/env python3
"""Generate market dynamics figure for paper (Gini + HHI over generations)."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# V6.5 Market Run 1 data (gens 1-6, gen 0 has no market stats)
gens = [1, 2, 3, 4, 5, 6]
gini = [0.099, 0.142, 0.171, 0.137, 0.177, 0.152]
hhi = [0.130, 0.133, 0.137, 0.133, 0.139, 0.134]
best_val = [93, 91, 91, 92, 92, 92]
mutations_accepted = [4, 3, 2, 4, 2, 0]  # out of attempts
mutations_total = [4, 3, 2, 5, 5, 1]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# Left: Market concentration metrics
ax1.plot(gens, gini, 'o-', color='#2196F3', linewidth=2, markersize=6, label='Gini coefficient')
ax1.plot(gens, hhi, 's-', color='#FF9800', linewidth=2, markersize=6, label='HHI')
ax1.axhline(y=0.15, color='gray', linestyle='--', alpha=0.5, label='HHI unconcentrated threshold')
ax1.set_xlabel('Generation', fontsize=11)
ax1.set_ylabel('Index value', fontsize=11)
ax1.set_title('Market Concentration Dynamics', fontsize=12)
ax1.legend(fontsize=9)
ax1.set_ylim(0, 0.25)
ax1.set_xticks(gens)
ax1.grid(True, alpha=0.3)

# Right: Val accuracy + mutation acceptance
ax2b = ax2.twinx()
ax2.plot(gens, best_val, 'o-', color='#4CAF50', linewidth=2, markersize=6, label='Best val accuracy')
acceptance_rate = [a/t*100 if t > 0 else 0 for a, t in zip(mutations_accepted, mutations_total)]
ax2b.bar(gens, acceptance_rate, alpha=0.3, color='#9C27B0', width=0.6, label='Mutation acceptance %')
ax2.set_xlabel('Generation', fontsize=11)
ax2.set_ylabel('Validation accuracy (%)', fontsize=11, color='#4CAF50')
ax2b.set_ylabel('Mutation acceptance (%)', fontsize=11, color='#9C27B0')
ax2.set_title('Performance & Mutation Flow', fontsize=12)
ax2.set_ylim(85, 95)
ax2b.set_ylim(0, 110)
ax2.set_xticks(gens)
ax2.grid(True, alpha=0.3)

# Combined legend
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2b.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='lower left')

plt.tight_layout()
plt.savefig('research/paper/latex/figures/v65_market_dynamics.pdf', dpi=300, bbox_inches='tight')
plt.savefig('research/paper/latex/figures/v65_market_dynamics.png', dpi=150, bbox_inches='tight')
print("Saved market dynamics figure")
