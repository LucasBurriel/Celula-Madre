"""
Agent module for Célula Madre MVP.
Code-generating agents with variable system prompts.
Supports: local (LM Studio/OpenAI-compatible), Anthropic Claude, Google Gemini.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from src.database import AgentConfig

# Provider config
PROVIDER = os.environ.get("CELULA_PROVIDER", "local")  # "local", "anthropic", or "gemini"
LOCAL_BASE_URL = os.environ.get("LOCAL_BASE_URL", "http://172.17.0.1:1234/v1")
LOCAL_MODEL = os.environ.get("LOCAL_MODEL", "qwen3-coder-30b-a3b-instruct")


class SimpleAgent:
    """AI agent that generates code using an LLM with a configurable prompt."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.provider = PROVIDER

        if self.provider == "local":
            self.client = OpenAI(base_url=LOCAL_BASE_URL, api_key="lm-studio")
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic()
        else:
            from google import genai
            self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    def solve_request(self, description: str) -> tuple[str, int, float]:
        """Generate code for a request. Returns (code, tokens_used, api_cost)."""
        user_prompt = (
            f"Generate Python code for: {description}\n\n"
            f"Include tests and docstrings.\n\n"
            f"IMPORTANT: Return ONLY executable Python code. "
            f"No markdown formatting, no backticks, no code block delimiters."
        )

        if self.provider == "local":
            return self._solve_local(user_prompt)
        elif self.provider == "anthropic":
            return self._solve_anthropic(user_prompt)
        else:
            return self._solve_gemini(user_prompt)

    def _solve_local(self, user_prompt: str) -> tuple[str, int, float]:
        """Generate code using local LM Studio model (OpenAI-compatible API)."""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=LOCAL_MODEL,
                    messages=[
                        {"role": "system", "content": self.config.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.7
                )

                text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                api_cost = 0.0  # Local = free

                # Retry on empty response
                if not text or not text.strip():
                    if attempt < max_retries - 1:
                        print(f"  [RETRY] Empty response from {self.config.agent_id}, attempt {attempt + 2}/{max_retries}")
                        time.sleep(2)
                        continue
                    else:
                        text = "# Empty response from model\npass"

                # Clean markdown wrappers
                if text.startswith("```python"):
                    text = text[len("```python"):].strip()
                if text.startswith("```"):
                    text = text[3:].strip()
                if text.endswith("```"):
                    text = text[:-3].strip()

                return text, tokens_used, api_cost

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  [RETRY] Error from {self.config.agent_id}: {e}, attempt {attempt + 2}/{max_retries}")
                    time.sleep(2)
                    continue
                raise RuntimeError(
                    f"Agent {self.config.agent_id} failed (local): {str(e)}"
                ) from e

    def _solve_anthropic(self, user_prompt: str) -> tuple[str, int, float]:
        """Generate code using Anthropic Claude."""
        from anthropic import APIError
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                system=self.config.system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=2048
            )

            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            input_cost = (response.usage.input_tokens / 1_000_000) * 1.00
            output_cost = (response.usage.output_tokens / 1_000_000) * 5.00
            api_cost = input_cost + output_cost

            return response.content[0].text, tokens_used, api_cost

        except APIError as e:
            raise RuntimeError(
                f"Agent {self.config.agent_id} failed (Anthropic): {str(e)}"
            ) from e

    def _solve_gemini(self, user_prompt: str) -> tuple[str, int, float]:
        """Generate code using Google Gemini with retry on rate limits."""
        import time
        try:
            full_prompt = f"{self.config.system_prompt}\n\n{user_prompt}"

            for attempt in range(5):
                try:
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=full_prompt
                    )
                    break
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        wait = (2 ** attempt) + 1
                        time.sleep(wait)
                        if attempt == 4:
                            raise
                    else:
                        raise

            usage = getattr(response, 'usage_metadata', None)
            if usage:
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
            else:
                input_tokens = len(full_prompt) // 4
                output_tokens = len(response.text) // 4

            tokens_used = input_tokens + output_tokens
            input_cost = (input_tokens / 1_000_000) * 0.075
            output_cost = (output_tokens / 1_000_000) * 0.30
            api_cost = input_cost + output_cost

            text = response.text
            if text.startswith("```python"):
                text = text[len("```python"):].strip()
            if text.startswith("```"):
                text = text[3:].strip()
            if text.endswith("```"):
                text = text[:-3].strip()

            return text, tokens_used, api_cost

        except Exception as e:
            raise RuntimeError(
                f"Agent {self.config.agent_id} failed (Gemini): {str(e)}"
            ) from e
