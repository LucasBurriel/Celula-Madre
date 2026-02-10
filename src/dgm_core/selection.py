"""
Parent selection for DGM - implements score_child_prop from Sakana's DGM.
"""
import math
import random


def score_child_prop(archive, k=1):
    """
    Select k parents using DGM's score_child_prop method.
    P(parent) ∝ sigmoid(score) × 1/(1 + children_count)
    """
    if not archive:
        return []

    candidates = [a for a in archive if a.get("score") is not None]
    if not candidates:
        return random.choices([a["id"] for a in archive], k=k)

    scores = [1.0 / (1 + math.exp(-10 * (c["score"] - 0.5))) for c in candidates]
    child_factors = [1.0 / (1 + c.get("children_count", 0)) for c in candidates]

    raw_probs = [s * cf for s, cf in zip(scores, child_factors)]
    total = sum(raw_probs)

    if total == 0:
        probs = [1.0 / len(candidates)] * len(candidates)
    else:
        probs = [p / total for p in raw_probs]

    selected = random.choices(range(len(candidates)), weights=probs, k=k)
    return [candidates[i]["id"] for i in selected]


def random_selection(archive, k=1):
    if not archive:
        return []
    return random.choices([a["id"] for a in archive], k=k)
