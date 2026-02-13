"""
Multi-domain sentiment data pipeline for Célula Madre V8.
Downloads SST-2, Amazon Reviews, Yelp Reviews, and TweetEval.
Creates balanced, domain-labeled splits for market selection experiments.
"""

import json
import random
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "sentiment"
DOMAINS = ["movies", "products", "restaurants", "social"]
LABELS = ["negative", "positive"]

# Per-domain counts for each split
PER_DOMAIN = {
    "dev": 25,
    "val": 25,
    "test": 50,
}
SEED = 42


def download_all_domains():
    """Download all 4 sentiment datasets. Returns dict of domain -> list of {text, label}."""
    from datasets import load_dataset

    domains = {}

    # 1. SST-2 (movies) — binary sentiment
    print("Downloading SST-2 (movies)...")
    sst = load_dataset("glue", "sst2", split="validation")
    movies = [
        {"text": row["sentence"], "label": LABELS[row["label"]], "domain": "movies"}
        for row in sst
    ]
    domains["movies"] = movies
    print(f"  → {len(movies)} examples")

    # 2. Amazon Reviews (products) — binary polarity
    print("Downloading Amazon Reviews (products)...")
    amazon = load_dataset("amazon_polarity", split="test", streaming=True)
    products = []
    for row in amazon:
        text = row["content"] if row["content"] else row["title"]
        if not text or len(text.strip()) < 10:
            continue
        label = "negative" if row["label"] == 0 else "positive"
        products.append({"text": text[:500], "label": label, "domain": "products"})
        if len(products) >= 2000:  # only need a subset
            break
    domains["products"] = products
    print(f"  → {len(products)} examples")

    # 3. Yelp Reviews (restaurants) — binary polarity
    print("Downloading Yelp Reviews (restaurants)...")
    yelp = load_dataset("yelp_polarity", split="test", streaming=True)
    restaurants = []
    for row in yelp:
        text = row["text"]
        if not text or len(text.strip()) < 10:
            continue
        label = "negative" if row["label"] == 0 else "positive"
        restaurants.append({"text": text[:500], "label": label, "domain": "restaurants"})
        if len(restaurants) >= 2000:
            break
    domains["restaurants"] = restaurants
    print(f"  → {len(restaurants)} examples")

    # 4. TweetEval (social) — filter to binary (skip neutral)
    print("Downloading TweetEval (social)...")
    tweets = load_dataset("tweet_eval", "sentiment", split="test")
    label_map = {0: "negative", 2: "positive"}  # skip 1=neutral
    social = [
        {"text": row["text"], "label": label_map[row["label"]], "domain": "social"}
        for row in tweets
        if row["label"] in label_map
    ]
    domains["social"] = social
    print(f"  → {len(social)} examples (binary only, neutral filtered)")

    return domains


def prepare_splits(force=False):
    """Create fixed dev/val/test splits balanced across domains and labels.
    Returns dict: {split_name: [{text, label, domain}, ...]}
    """
    splits_file = DATA_DIR / "splits.json"

    if splits_file.exists() and not force:
        with open(splits_file) as f:
            return json.load(f)

    raw = download_all_domains()

    random.seed(SEED)
    splits = {"dev": [], "val": [], "test": []}

    for domain in DOMAINS:
        examples = raw[domain]
        random.shuffle(examples)

        # Split by label for balancing
        pos = [e for e in examples if e["label"] == "positive"]
        neg = [e for e in examples if e["label"] == "negative"]
        print(f"{domain}: {len(pos)} positive, {len(neg)} negative")

        for split_name, per_domain in PER_DOMAIN.items():
            half = per_domain // 2
            # Take half positive, half negative (+ 1 extra if odd)
            extra = per_domain - 2 * half
            selected = pos[:half + extra] + neg[:half]
            pos = pos[half + extra:]
            neg = neg[half:]
            random.shuffle(selected)
            splits[split_name].extend(selected)

    # Shuffle each split
    for split_name in splits:
        random.shuffle(splits[split_name])

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(splits_file, "w") as f:
        json.dump(splits, f, indent=2)

    # Print stats
    for split_name, examples in splits.items():
        domain_counts = {}
        label_counts = {}
        for e in examples:
            domain_counts[e["domain"]] = domain_counts.get(e["domain"], 0) + 1
            label_counts[e["label"]] = label_counts.get(e["label"], 0) + 1
        print(f"\n{split_name} ({len(examples)} total):")
        print(f"  Domains: {domain_counts}")
        print(f"  Labels: {label_counts}")

    print(f"\nSaved to {splits_file}")
    return splits


def load_splits():
    """Load pre-prepared splits. Raises if not prepared yet."""
    splits_file = DATA_DIR / "splits.json"
    if not splits_file.exists():
        raise FileNotFoundError(
            f"Splits not found at {splits_file}. Run prepare_splits() first."
        )
    with open(splits_file) as f:
        return json.load(f)


def evaluate_agent(llm_fn, system_prompt, examples, domain_filter=None):
    """Evaluate an agent on sentiment classification examples.
    
    Args:
        llm_fn: callable(system_prompt, user_prompt) -> str
        system_prompt: agent's system prompt
        examples: list of {text, label, domain}
        domain_filter: optional domain name to filter examples
    
    Returns:
        dict with overall and per-domain accuracy
    """
    if domain_filter:
        examples = [e for e in examples if e["domain"] == domain_filter]

    correct = 0
    total = 0
    domain_stats = {d: {"correct": 0, "total": 0} for d in DOMAINS}

    for ex in examples:
        user_prompt = f"Classify the sentiment of the following text as exactly 'positive' or 'negative'. Reply with ONLY the label.\n\nText: {ex['text']}"
        try:
            response = llm_fn(system_prompt, user_prompt)
            prediction = parse_sentiment(response)
            is_correct = prediction == ex["label"]
            if is_correct:
                correct += 1
                domain_stats[ex["domain"]]["correct"] += 1
            total += 1
            domain_stats[ex["domain"]]["total"] += 1
        except Exception as e:
            total += 1
            domain_stats[ex["domain"]]["total"] += 1

    result = {
        "accuracy": correct / total if total > 0 else 0.0,
        "correct": correct,
        "total": total,
        "per_domain": {},
    }
    for d in DOMAINS:
        s = domain_stats[d]
        result["per_domain"][d] = {
            "accuracy": s["correct"] / s["total"] if s["total"] > 0 else 0.0,
            "correct": s["correct"],
            "total": s["total"],
        }
    return result


def parse_sentiment(response):
    """Parse LLM response to extract sentiment label."""
    response = response.strip().lower()
    # Direct match
    if response in ("positive", "negative"):
        return response
    # Look for label in response
    if "positive" in response and "negative" not in response:
        return "positive"
    if "negative" in response and "positive" not in response:
        return "negative"
    # First word
    first = response.split()[0].strip(".,!:;") if response else ""
    if first in ("positive", "negative"):
        return first
    return "unknown"


# Seed strategies for V8
SEED_STRATEGIES = [
    # 1. Generalist
    "You are a sentiment classifier. Analyze the text and determine if the overall sentiment is positive or negative. Consider the tone, word choice, and context.",
    # 2. Formal review analyzer
    "You are a sentiment classifier specialized in formal reviews. Look for evaluative adjectives, comparative language, and overall recommendation signals. Star ratings map to sentiment: 1-2 = negative, 4-5 = positive.",
    # 3. Slang/informal decoder
    "You are a sentiment classifier for informal text. Decode slang, abbreviations, hashtags, emojis, and internet speak. 'lol', 'smh', 'ngl' and similar terms carry sentiment signals.",
    # 4. Sarcasm detector
    "You are a sentiment classifier with sarcasm awareness. Look for irony markers: exaggeration, contradictions between stated and implied meaning, 'oh great' used negatively, praise that's actually criticism.",
    # 5. Keyword-based
    "You are a sentiment classifier using keyword signals. Positive indicators: great, excellent, love, amazing, wonderful, best, perfect. Negative indicators: terrible, awful, worst, hate, horrible, disappointing, waste.",
    # 6. Context reader
    "You are a sentiment classifier focused on contextual understanding. Pay attention to qualifiers ('but', 'however', 'although'), negations ('not bad' = positive), and overall narrative arc. The conclusion often reveals true sentiment.",
    # 7. Emotion mapper
    "You are a sentiment classifier that maps emotions to sentiment. Joy, satisfaction, gratitude, excitement → positive. Anger, frustration, disappointment, sadness → negative. Focus on the emotional state expressed.",
    # 8. Minimalist
    "Classify sentiment as positive or negative. Focus on: does the author like or dislike the subject? Like = positive, dislike = negative.",
]


if __name__ == "__main__":
    splits = prepare_splits()
