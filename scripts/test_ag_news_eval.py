"""Quick test: evaluate 1 agent on 5 AG News examples via LM Studio."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ag_news_data import load_splits, evaluate_agent
import requests

LLM_URL = "http://172.17.0.1:1234/v1/chat/completions"

def llm_fn(system_prompt, user_message):
    try:
        r = requests.post(LLM_URL, json={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1,
            "max_tokens": 50,
        }, timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"LLM error: {e}")
        return "Unknown"

# Test with vanilla prompt on 5 dev examples
splits = load_splits()
agent_prompt = "You are a news classifier. Classify articles into exactly one category: World, Sports, Business, or Sci/Tech. Respond with ONLY the category name."

result = evaluate_agent(agent_prompt, splits["dev"][:5], llm_fn)
print(f"Accuracy: {result['accuracy']:.0%} ({result['correct']}/{result['total']})")
print(f"Per-class: {result['per_class']}")
if result['errors']:
    print(f"\nErrors:")
    for e in result['errors']:
        print(f"  True={e['true']}, Predicted={e['predicted']}, Response={e['raw_response'][:50]}")
