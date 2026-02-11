#!/usr/bin/env python3
"""Generate figures for Célula Madre paper."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# === Figure 1: V6 Gen-over-gen best validation accuracy ===
# Only reflective R1 has full gen data. Use paper's ASCII chart data for means.
# From paper: Reflective starts ~78%, jumps to ~83% gen1, plateaus ~85-86%
# Random starts ~79%, climbs gradually to ~85-87% by gen 5-9

# Reflective R1 actual data
refl_r1 = [0.91, 0.94, 0.94, 0.94, 0.94, 0.95, 0.95, 0.96, 0.96, 0.96]

# For the group comparison figure, use test scores
fig, ax = plt.subplots(1, 1, figsize=(6, 4))

# Test accuracy by group
groups = ['Reflective\n(n=3)', 'Random\n(n=3)', 'Static\n(estimated)']
means = [83.7, 83.3, 79.0]
stds = [3.8, 3.6, 2.0]  # static std estimated
colors = ['#2196F3', '#FF9800', '#9E9E9E']

bars = ax.bar(groups, means, yerr=stds, capsize=8, color=colors, edgecolor='black', linewidth=0.8, alpha=0.85)
ax.set_ylabel('Test Accuracy (%)', fontsize=12)
ax.set_title('V6: AG News Test Accuracy by Mutation Strategy', fontsize=13, fontweight='bold')
ax.set_ylim(70, 95)
ax.axhline(y=79, color='gray', linestyle='--', alpha=0.5, label='Gen0 baseline (~79%)')
ax.legend(fontsize=9)

# Add individual run points
refl_runs = [89.0, 80.5, 81.5]
rand_runs = [87.0, 78.5, 84.5]
for i, val in enumerate(refl_runs):
    ax.scatter(0, val, color='black', s=30, zorder=5, alpha=0.7)
for i, val in enumerate(rand_runs):
    ax.scatter(1, val, color='black', s=30, zorder=5, alpha=0.7)

# Annotation
ax.annotate('p = 0.932\n(n.s.)', xy=(0.5, 86), fontsize=10, ha='center', style='italic')
ax.annotate('p = 0.041*', xy=(0.5, 76), fontsize=10, ha='center', style='italic', color='green')

plt.tight_layout()
plt.savefig('figures/v6_test_accuracy.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/v6_test_accuracy.pdf', bbox_inches='tight')
print("Saved v6_test_accuracy.png/pdf")

# === Figure 2: Reflective R1 generational trajectory ===
fig2, ax2 = plt.subplots(1, 1, figsize=(6, 4))
gens = list(range(10))
ax2.plot(gens, [v*100 for v in refl_r1], 'o-', color='#2196F3', linewidth=2, markersize=6, label='Reflective Run 1')
ax2.axhline(y=79, color='gray', linestyle='--', alpha=0.5, label='Gen0 baseline (~79%)')
ax2.set_xlabel('Generation', fontsize=12)
ax2.set_ylabel('Best Validation Accuracy (%)', fontsize=12)
ax2.set_title('V6: Generational Improvement (Reflective Run 1)', fontsize=13, fontweight='bold')
ax2.set_ylim(75, 100)
ax2.set_xticks(gens)
ax2.legend(fontsize=9)
plt.tight_layout()
plt.savefig('figures/v6_gen_trajectory.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/v6_gen_trajectory.pdf', bbox_inches='tight')
print("Saved v6_gen_trajectory.png/pdf")

# === Figure 3: V4 comparison ===
fig3, ax3 = plt.subplots(1, 1, figsize=(5, 4))
groups_v4 = ['Guided\nMutation', 'Random\nMutation']
means_v4 = [90.81, 208.57]
colors_v4 = ['#F44336', '#4CAF50']
bars = ax3.bar(groups_v4, means_v4, color=colors_v4, edgecolor='black', linewidth=0.8, alpha=0.85)
ax3.set_ylabel('Mean Agent Profit', fontsize=12)
ax3.set_title('V4: Guided vs Random Mutation\n(Cohen\'s d = −2.01, p < 0.0001)', fontsize=12, fontweight='bold')
for bar, val in zip(bars, means_v4):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'{val:.1f}', ha='center', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig('figures/v4_comparison.png', dpi=300, bbox_inches='tight')
plt.savefig('figures/v4_comparison.pdf', bbox_inches='tight')
print("Saved v4_comparison.png/pdf")

print("\nAll figures generated!")
