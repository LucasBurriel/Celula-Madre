"""
Parent selection for DGM - implements score_child_prop from Sakana's DGM.
"""
import math
import random


def score_child_prop(archive, k=1):
    """
    Select k parents from archive using score_child_prop method.
    
    Each candidate's probability is proportional to:
        sigmoid(score) * 1/(1 + children_count)
    
    This favors high-scoring agents that haven't been selected much yet.
    
    archive: list of dicts with {id, score, children_count}
    Returns: list of k selected parent IDs
    """
    if not archive:
        return []
    
    candidates = [a for a in archive if a.get("score") is not None]
    if not candidates:
        return random.choices([a["id"] for a in archive], k=k)
    
    # Calculate selection probabilities
    scores = [_sigmoid(c["score"]) for c in candidates]
    children_factors = [1.0 / (1 + c.get("children_count", 0)) for c in candidates]
    
    raw_probs = [s * cf for s, cf in zip(scores, children_factors)]
    total = sum(raw_probs)
    
    if total == 0:
        probs = [1.0 / len(candidates)] * len(candidates)
    else:
        probs = [p / total for p in raw_probs]
    
    selected_indices = random.choices(range(len(candidates)), weights=probs, k=k)
    return [candidates[i]["id"] for i in selected_indices]


def _sigmoid(x, scale=10, center=0.5):
    """Sigmoid function centered at `center` with given scale."""
    return 1.0 / (1 + math.exp(-scale * (x - center)))


def random_selection(archive, k=1):
    """Random parent selection (baseline)."""
    if not archive:
        return []
    return random.choices([a["id"] for a in archive], k=k)


def best_selection(archive, k=1):
    """Select the best-scoring parents."""
    if not archive:
        return []
    sorted_archive = sorted(archive, key=lambda a: a.get("score", 0), reverse=True)
    parents = [a["id"] for a in sorted_archive[:k]]
    # If not enough, repeat
    while len(parents) < k:
        parents.extend(parents[:k - len(parents)])
    return parents[:k]
