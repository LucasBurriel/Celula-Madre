"""
Visualization script for Célula Madre evolution tree.
Generates a tree diagram showing agent lineage and performance.
"""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Dict, List, Tuple


def load_agents_from_db(db_path: str = "celula_madre.db") -> List[Dict]:
    """Load all agents from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    agents = conn.execute("""
        SELECT agent_id, generation, parent_id, total_revenue, transaction_count
        FROM agents
        ORDER BY generation, agent_id
    """).fetchall()

    conn.close()
    return [dict(agent) for agent in agents]


def build_tree_structure(agents: List[Dict]) -> Dict:
    """Build hierarchical tree structure from flat agent list."""
    tree = {}

    # Index agents by ID for quick lookup
    agents_by_id = {a['agent_id']: a for a in agents}

    # Group by generation
    by_generation = {}
    for agent in agents:
        gen = agent['generation']
        if gen not in by_generation:
            by_generation[gen] = []
        by_generation[gen].append(agent)

    # Build parent-child relationships
    for agent in agents:
        agent['children'] = [
            a for a in agents
            if a['parent_id'] == agent['agent_id']
        ]

    return by_generation, agents_by_id


def calculate_positions(by_generation: Dict, agents_by_id: Dict) -> Dict[str, Tuple[float, float]]:
    """Calculate x, y positions for each agent in the tree."""
    positions = {}
    max_gen = max(by_generation.keys())

    # Y position based on generation (inverted for tree top-down)
    y_spacing = 1.0

    # X position based on sibling order within generation
    for gen, gen_agents in by_generation.items():
        y = max_gen - gen  # Invert so Gen0 is at top

        # Sort by parent for better visual grouping
        gen_agents_sorted = sorted(gen_agents, key=lambda a: (a['parent_id'] or '', a['agent_id']))

        # Space agents evenly across X axis
        num_agents = len(gen_agents_sorted)
        x_spacing = 2.0

        for i, agent in enumerate(gen_agents_sorted):
            x = i * x_spacing - (num_agents - 1) * x_spacing / 2
            positions[agent['agent_id']] = (x, y * y_spacing)

    return positions


def visualize_evolution_tree(db_path: str = "celula_madre.db", save_path: str = "evolution_tree.png"):
    """
    Create and save visualization of evolution tree.

    Args:
        db_path: Path to SQLite database
        save_path: Path to save output PNG
    """
    # Load data
    agents = load_agents_from_db(db_path)

    if not agents:
        print("No agents found in database!")
        return

    by_generation, agents_by_id = build_tree_structure(agents)
    positions = calculate_positions(by_generation, agents_by_id)

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_aspect('equal')

    # Draw edges (parent-child connections)
    for agent in agents:
        if agent['parent_id'] and agent['parent_id'] in positions:
            x1, y1 = positions[agent['parent_id']]
            x2, y2 = positions[agent['agent_id']]

            ax.plot([x1, x2], [y1, y2], 'k-', alpha=0.3, linewidth=1)

    # Draw nodes
    for agent in agents:
        x, y = positions[agent['agent_id']]

        # Color based on revenue
        revenue = agent['total_revenue']
        avg_price = revenue / max(1, agent['transaction_count'])

        # Color scale: red (low) -> yellow -> green (high)
        if avg_price < 8:
            color = '#ff6b6b'  # Red
        elif avg_price < 12:
            color = '#ffd93d'  # Yellow
        else:
            color = '#6bcf7f'  # Green

        # Draw node
        circle = mpatches.Circle((x, y), 0.3, color=color, ec='black', linewidth=2, zorder=10)
        ax.add_patch(circle)

        # Label with agent info
        short_id = agent['agent_id'].split('_')[-1]  # Just the number
        gen = agent['generation']
        txs = agent['transaction_count']

        label = f"{short_id}\nG{gen}\n${revenue:.0f}\n({txs}tx)"

        ax.text(x, y, label, ha='center', va='center', fontsize=7, weight='bold', zorder=11)

    # Legend
    legend_elements = [
        mpatches.Patch(color='#6bcf7f', label='High Performer (avg ≥ $12)'),
        mpatches.Patch(color='#ffd93d', label='Medium Performer ($8-12)'),
        mpatches.Patch(color='#ff6b6b', label='Low Performer (< $8)'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # Title and labels
    total_agents = len(agents)
    max_gen = max(a['generation'] for a in agents)
    total_revenue = sum(a['total_revenue'] for a in agents)

    ax.set_title(
        f"Célula Madre Evolution Tree\n"
        f"{total_agents} agents across {max_gen + 1} generations | "
        f"Total Revenue: ${total_revenue:.2f}",
        fontsize=14,
        weight='bold',
        pad=20
    )

    ax.set_xlabel("Agent Lineage", fontsize=12)
    ax.set_ylabel("Generation (Gen 0 = top)", fontsize=12)

    # Remove axes ticks
    ax.set_xticks([])
    ax.set_yticks([])

    # Set limits with padding
    all_x = [p[0] for p in positions.values()]
    all_y = [p[1] for p in positions.values()]
    x_margin = 1.5
    y_margin = 0.5

    ax.set_xlim(min(all_x) - x_margin, max(all_x) + x_margin)
    ax.set_ylim(min(all_y) - y_margin, max(all_y) + y_margin)

    # Invert y-axis so Gen 0 is at top
    ax.invert_yaxis()

    # Grid
    ax.grid(True, alpha=0.1)

    # Save
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Evolution tree saved to: {save_path}")

    # Show
    plt.show()


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "celula_madre.db"
    save_path = sys.argv[2] if len(sys.argv) > 2 else "evolution_tree.png"

    visualize_evolution_tree(db_path, save_path)
