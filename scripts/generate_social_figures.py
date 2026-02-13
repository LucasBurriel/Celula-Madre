#!/usr/bin/env python3
"""Generate social-media-optimized figures for Célula Madre Twitter/blog."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = 'research/paper/figures/social'
os.makedirs(OUT, exist_ok=True)

# Dark style
DARK = {
    'font.size': 18, 'axes.titlesize': 24, 'axes.labelsize': 18,
    'xtick.labelsize': 16, 'ytick.labelsize': 16,
    'legend.fontsize': 15, 'figure.facecolor': '#0d1117',
    'axes.facecolor': '#161b22', 'text.color': '#e6edf3',
    'axes.labelcolor': '#e6edf3', 'xtick.color': '#8b949e',
    'ytick.color': '#8b949e', 'axes.edgecolor': '#30363d',
    'legend.facecolor': '#161b22', 'legend.edgecolor': '#30363d',
}
plt.rcParams.update(DARK)

# ===== FIGURE 1: V6 Bar Chart =====
fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

groups = ['Reflective\nMutation', 'Random\nMutation', 'Static\n(No Evolution)']
means = [83.7, 83.3, 79.0]
stds = [3.8, 3.6, 0]
colors = ['#58a6ff', '#f0883e', '#8b949e']
individual = {'Reflective': [89.0, 80.5, 81.5], 'Random': [87.0, 78.5, 84.5], 'Static': [79.0]}

bars = ax.bar(groups, means, yerr=stds, color=colors, edgecolor='white', linewidth=0.5,
              capsize=10, error_kw={'color': '#e6edf3', 'linewidth': 2.5})

for i, (group, runs) in enumerate(individual.items()):
    for r in runs:
        ax.scatter(i, r, color='white', s=80, zorder=5, alpha=0.9, edgecolors='#0d1117', linewidths=1)

ax.set_ylabel('Test Accuracy (%)')
ax.set_title('Evolution works.\nHow you mutate doesn\'t matter.', fontweight='bold', pad=15, fontsize=22)
ax.set_ylim(70, 95)
ax.axhline(y=79, color='#8b949e', linestyle='--', alpha=0.5)

# Bracket between reflective & random
ax.annotate('', xy=(0, 90.5), xytext=(1, 90.5),
            arrowprops=dict(arrowstyle='-', color='#e6edf3', lw=1.5))
ax.plot([0, 0], [90, 90.5], color='#e6edf3', lw=1.5)
ax.plot([1, 1], [90, 90.5], color='#e6edf3', lw=1.5)
ax.text(0.5, 91, 'p = 0.93 (no difference)', ha='center', fontsize=14, color='#f0883e', fontweight='bold')

# Evolution vs static
ax.annotate('', xy=(0.5, 76), xytext=(2, 76),
            arrowprops=dict(arrowstyle='-', color='#e6edf3', lw=1.5))
ax.plot([0.5, 0.5], [75.5, 76], color='#e6edf3', lw=1.5)
ax.plot([2, 2], [75.5, 76], color='#e6edf3', lw=1.5)
ax.text(1.25, 73.5, 'p = 0.041* (evolution works!)', ha='center', fontsize=14, color='#58a6ff', fontweight='bold')

# n labels
for i, n in enumerate([3, 3, 1]):
    ax.text(i, 72, f'n={n}', ha='center', fontsize=13, color='#8b949e')

ax.text(0.02, 0.02, 'Error bars: ±1 SD  •  Dots: individual runs', transform=ax.transAxes,
        fontsize=11, color='#8b949e', alpha=0.7)

fig.tight_layout()
fig.savefig(f'{OUT}/v6_bar_chart.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Figure 1: V6 bar chart")

# ===== FIGURE 2: Gen-over-Gen Trajectory =====
fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

gens = list(range(10))
refl = [78.5, 83.5, 85.5, 85.5, 85.0, 85.5, 84.5, 84.0, 85.0, 85.5]
rand = [79.0, 82.0, 82.0, 82.7, 84.3, 85.7, 86.3, 86.3, 85.0, 85.7]

ax.plot(gens, refl, 'o-', color='#58a6ff', linewidth=3, markersize=10, label='Reflective mutation', zorder=3)
ax.plot(gens, rand, 's-', color='#f0883e', linewidth=3, markersize=10, label='Random mutation', zorder=3)
ax.axhline(y=79, color='#8b949e', linestyle='--', alpha=0.5, linewidth=2, label='No evolution (~79%)')

ax.set_xlabel('Generation')
ax.set_ylabel('Best Validation Accuracy (%)')
ax.set_title('Prompts evolve from 79% → 86% in 10 generations', fontweight='bold', pad=15, fontsize=22)
ax.set_ylim(75, 90)
ax.set_xticks(gens)
ax.legend(loc='lower right', fontsize=15)

# Direct label
ax.annotate('+7pp', xy=(9, 85.7), xytext=(9.3, 88), fontsize=16, fontweight='bold',
            color='#f0883e', arrowprops=dict(arrowstyle='->', color='#f0883e', lw=2))

ax.text(0.02, 0.02, 'AG News 4-class classification  •  Qwen3-30B  •  Pop=8', transform=ax.transAxes,
        fontsize=12, color='#8b949e', alpha=0.7)

fig.tight_layout()
fig.savefig(f'{OUT}/v6_gen_trajectory.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Figure 2: Gen-over-gen trajectory")

# ===== FIGURE 3: Market Dynamics (V6.5) =====
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), dpi=300)

mgens = [1, 2, 3, 4, 5, 6]
gini = [0.099, 0.142, 0.171, 0.137, 0.177, 0.152]
hhi = [0.130, 0.133, 0.137, 0.133, 0.139, 0.134]
val_acc = [93, 91, 91, 92, 92, 92]

ax1.plot(mgens, gini, 'o-', color='#f778ba', linewidth=3, markersize=10, label='Gini (inequality)')
ax1.plot(mgens, hhi, 's-', color='#7ee787', linewidth=3, markersize=10, label='HHI (concentration)')
ax1.axhline(y=0.15, color='#8b949e', linestyle='--', alpha=0.4, linewidth=1.5)
ax1.text(1.1, 0.155, 'Competitive threshold', fontsize=12, color='#8b949e')
ax1.set_xlabel('Generation')
ax1.set_ylabel('Index Value')
ax1.set_title('Market stays competitive', fontweight='bold', fontsize=20)
ax1.set_ylim(0.05, 0.25)
ax1.legend(loc='upper left', fontsize=13)

ax2.plot(mgens, val_acc, 'D-', color='#d2a8ff', linewidth=3, markersize=12)
ax2.set_xlabel('Generation')
ax2.set_ylabel('Best Validation Accuracy (%)')
ax2.set_title('Accuracy stays high', fontweight='bold', fontsize=20)
ax2.set_ylim(85, 96)
ax2.axhline(y=84, color='#f0883e', linestyle='--', alpha=0.5, linewidth=1.5)
ax2.text(1.1, 84.5, 'V6 tournament mean (84%)', fontsize=13, color='#f0883e')

# Key callout
ax2.annotate('93% peak\n(beats all V6 runs)', xy=(1, 93), xytext=(3, 95),
            fontsize=14, fontweight='bold', color='#d2a8ff',
            arrowprops=dict(arrowstyle='->', color='#d2a8ff', lw=2))

fig.suptitle('Agents competing in a free market\n(Hayek meets AI)', fontweight='bold', fontsize=22, y=1.04)
fig.tight_layout()
fig.savefig(f'{OUT}/v65_market_dynamics.png', dpi=300, bbox_inches='tight')
plt.close()
print("✅ Figure 3: Market dynamics")

print(f"\n📁 All figures saved to {OUT}/")
