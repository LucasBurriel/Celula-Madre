"""
AG News data pipeline for Célula Madre V6.
Downloads AG News, creates fixed splits for reproducible experiments.
"""

import json
import random
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "ag_news"
LABELS = ["World", "Sports", "Business", "Sci/Tech"]
LABEL_MAP = {0: "World", 1: "Sports", 2: "Business", 3: "Sci/Tech"}

SPLIT_SIZES = {
    "dev": 100,     # fitness evaluation during evolution
    "val": 100,     # gating: child must beat parent
    "test": 200,    # final evaluation, never seen during evolution
}
SEED = 42


def download_ag_news():
    """Download AG News test set from HuggingFace datasets."""
    from datasets import load_dataset
    ds = load_dataset("ag_news", split="test")
    return ds


def prepare_splits(force=False):
    """Create fixed dev/val/test splits. Returns dict of splits."""
    splits_file = DATA_DIR / "splits.json"
    
    if splits_file.exists() and not force:
        with open(splits_file) as f:
            return json.load(f)
    
    print("Downloading AG News...")
    ds = download_ag_news()
    
    # Convert to list of dicts
    examples = [{"text": row["text"], "label": LABELS[row["label"]]} for row in ds]
    
    # Shuffle deterministically
    random.seed(SEED)
    random.shuffle(examples)
    
    # Split
    splits = {}
    offset = 0
    for name, size in SPLIT_SIZES.items():
        splits[name] = examples[offset:offset + size]
        offset += size
    
    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(splits_file, "w") as f:
        json.dump(splits, f, indent=2)
    
    # Print stats
    for name, data in splits.items():
        label_dist = {}
        for ex in data:
            label_dist[ex["label"]] = label_dist.get(ex["label"], 0) + 1
        print(f"{name}: {len(data)} examples, distribution: {label_dist}")
    
    return splits


def load_splits():
    """Load pre-computed splits."""
    splits_file = DATA_DIR / "splits.json"
    if not splits_file.exists():
        return prepare_splits()
    with open(splits_file) as f:
        return json.load(f)


def evaluate_agent(agent_prompt: str, examples: list, llm_fn) -> dict:
    """
    Evaluate an agent's prompt on a set of examples.
    
    Args:
        agent_prompt: The system prompt for the agent
        examples: List of {"text": ..., "label": ...}
        llm_fn: Function(system_prompt, user_message) -> str
    
    Returns:
        {"accuracy": float, "correct": int, "total": int, 
         "per_class": {label: {"correct": int, "total": int, "accuracy": float}},
         "errors": list of misclassified examples}
    """
    correct = 0
    total = len(examples)
    per_class = {l: {"correct": 0, "total": 0} for l in LABELS}
    errors = []
    
    for ex in examples:
        user_msg = f"Classify this news article:\n\n{ex['text']}\n\nRespond with ONLY one of: World, Sports, Business, Sci/Tech"
        
        response = llm_fn(agent_prompt, user_msg)
        predicted = parse_label(response)
        true_label = ex["label"]
        
        per_class[true_label]["total"] += 1
        
        if predicted == true_label:
            correct += 1
            per_class[true_label]["correct"] += 1
        else:
            errors.append({
                "text": ex["text"][:200],
                "true": true_label,
                "predicted": predicted,
                "raw_response": response[:100]
            })
    
    # Calculate per-class accuracy
    for l in LABELS:
        t = per_class[l]["total"]
        per_class[l]["accuracy"] = per_class[l]["correct"] / t if t > 0 else 0.0
    
    return {
        "accuracy": correct / total if total > 0 else 0.0,
        "correct": correct,
        "total": total,
        "per_class": per_class,
        "errors": errors[:10]  # keep top 10 for mutation analysis
    }


def parse_label(response: str) -> str:
    """Parse LLM response to extract a label."""
    response = response.strip()
    
    # Direct match
    for label in LABELS:
        if response.lower() == label.lower():
            return label
    
    # Check if label appears in response
    found = []
    for label in LABELS:
        if label.lower() in response.lower():
            found.append(label)
    
    if len(found) == 1:
        return found[0]
    
    # Check for "Sci/Tech" variations
    sci_variants = ["sci/tech", "science", "technology", "sci-tech", "scitech"]
    for v in sci_variants:
        if v in response.lower():
            return "Sci/Tech"
    
    # Last resort: first label mentioned
    for label in LABELS:
        if label.lower() in response.lower():
            return label
    
    return "Unknown"


if __name__ == "__main__":
    splits = prepare_splits(force=True)
    print(f"\nTotal examples prepared: {sum(len(v) for v in splits.values())}")
    print(f"Labels: {LABELS}")
