"""
Evolution V4 Control — Random mutations without market feedback.

Key difference from EvolutionV4:
- Mutations are generic/random, NOT guided by market performance
- Crossover combines prompts randomly, not based on niche/fitness
- This isolates the effect of price signals on evolution quality
"""

import os
import random
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

from src.agent import PROVIDER


class EvolutionV4Control:
    """Random evolutionary engine (control group)."""

    def __init__(self):
        self.provider = PROVIDER

        if self.provider == "local":
            from openai import OpenAI
            from src.agent import LOCAL_BASE_URL, LOCAL_MODEL
            self.client = OpenAI(base_url=LOCAL_BASE_URL, api_key="lm-studio")
            self.local_model = LOCAL_MODEL
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
        else:
            from google import genai
            self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    def _llm_generate(self, prompt: str, temperature: float = 0.9) -> str:
        """Generate text with high temperature for randomness."""
        if self.provider == "local":
            response = self.client.chat.completions.create(
                model=self.local_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=min(temperature, 1.0)
            )
            return response.content[0].text.strip()
        else:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()

    def random_crossover_and_mutate(
        self,
        prompt_a: str,
        prompt_b: str
    ) -> Optional[str]:
        """
        Combine two prompts and mutate WITHOUT any market feedback.
        
        The mutation prompt is deliberately generic — it doesn't know:
        - What clients want
        - What prices agents earned
        - Which strategies worked
        
        This is the null hypothesis: random variation + selection pressure
        from the market (clients still choose and pay), but NO guided mutation.
        """
        # Random crossover strategy (no intelligence)
        strategies = [
            "merge",      # Mix both
            "take_a",     # Mostly A with random changes  
            "take_b",     # Mostly B with random changes
            "scramble",   # Random pieces from both
        ]
        strategy = random.choice(strategies)

        mutation_prompt = f"""You are a prompt editor. Combine and modify these two coding agent prompts into a NEW prompt.

PROMPT A:
{prompt_a}

PROMPT B:
{prompt_b}

Strategy: {strategy}

Rules:
- Create a NEW system prompt for a Python coding agent
- Make random changes — add something new, remove something, change emphasis
- Do NOT optimize for anything specific — just make it different
- Keep it 2-4 sentences long
- Output ONLY the new prompt, nothing else"""

        try:
            result = self._llm_generate(mutation_prompt, temperature=0.9)
            # Clean up
            result = result.strip().strip('"').strip("'")
            if len(result) < 20 or len(result) > 500:
                return None
            return result
        except Exception as e:
            print(f"[CONTROL MUTATION ERROR] {e}")
            return None
