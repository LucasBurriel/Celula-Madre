"""Célula Madre — Multi-provider LLM abstraction.

Supports:
  - Local LM Studio (OpenAI-compatible)
  - Groq (fast, cheap)
  - OpenRouter (access to many models)
  - Together.ai
  - Any OpenAI-compatible endpoint

Usage:
    from src.llm_providers import create_llm_fn, LLMConfig

    # Local LM Studio
    llm = create_llm_fn(LLMConfig(provider="lmstudio"))

    # Groq
    llm = create_llm_fn(LLMConfig(provider="groq", api_key="gsk_..."))

    # OpenRouter
    llm = create_llm_fn(LLMConfig(provider="openrouter", api_key="sk-or-..."))

    # Use it
    response = llm("You are a helper.", "What is 2+2?")

    # Async version
    import asyncio
    allm = create_async_llm_fn(LLMConfig(provider="groq", api_key="gsk_..."))
    response = asyncio.run(allm("system", "user"))
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import requests

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


# ── Provider Configs ────────────────────────────────────────────────

PROVIDERS = {
    "lmstudio": {
        "base_url": "http://172.17.0.1:1234",
        "default_model": "qwen3-coder-30b-a3b-instruct",
        "extra_body": {"no_think": True},
        "needs_key": False,
    },
    "groq": {
        "base_url": "https://api.groq.com/openai",
        "default_model": "llama-3.3-70b-versatile",
        "extra_body": {},
        "needs_key": True,
        "env_key": "GROQ_API_KEY",
        "rpm_limit": 30,
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "default_model": "qwen/qwen3-coder:free",
        "extra_body": {},
        "needs_key": True,
        "env_key": "OPENROUTER_API_KEY",
        "rpm_limit": 20,  # Free tier conservative limit
    },
    "together": {
        "base_url": "https://api.together.xyz",
        "default_model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "extra_body": {},
        "needs_key": True,
        "env_key": "TOGETHER_API_KEY",
    },
    "xai": {
        "base_url": "https://api.x.ai",
        "default_model": "grok-3-mini-fast",
        "extra_body": {},
        "needs_key": True,
        "env_key": "XAI_API_KEY",
        "rpm_limit": 1400,  # 1450 actual, conservative
    },
    "custom": {
        "base_url": "",
        "default_model": "",
        "extra_body": {},
        "needs_key": False,
    },
}


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str = "lmstudio"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 300
    retries: int = 3
    timeout: int = 30
    # Rate limiting
    rpm_limit: Optional[int] = None  # requests per minute
    _last_call: float = field(default=0.0, repr=False)

    def __post_init__(self):
        prov = PROVIDERS.get(self.provider, PROVIDERS["custom"])
        if self.base_url is None:
            self.base_url = prov["base_url"]
        if self.model is None:
            self.model = prov["default_model"]
        if self.api_key is None and prov.get("needs_key"):
            env_key = prov.get("env_key", "")
            self.api_key = os.environ.get(env_key, "")
        if self.rpm_limit is None and "rpm_limit" in prov:
            self.rpm_limit = prov["rpm_limit"]


# ── Sync LLM Call ───────────────────────────────────────────────────

def create_llm_fn(config: LLMConfig) -> Callable:
    """Create a synchronous LLM function: (system, user) -> str."""
    prov = PROVIDERS.get(config.provider, PROVIDERS["custom"])
    extra_body = prov.get("extra_body", {})

    def llm_fn(system_prompt: str, user_prompt: str) -> str:
        # Rate limiting
        if config.rpm_limit:
            min_interval = 60.0 / config.rpm_limit
            elapsed = time.time() - config._last_call
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        body = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            **extra_body,
        }

        for attempt in range(config.retries):
            try:
                r = requests.post(
                    f"{config.base_url}/v1/chat/completions",
                    json=body,
                    headers=headers,
                    timeout=config.timeout,
                )
                r.raise_for_status()
                config._last_call = time.time()
                return r.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                if attempt == config.retries - 1:
                    raise
                wait = 2 ** attempt
                # Groq 429 → wait longer
                if hasattr(e, 'response') and getattr(e.response, 'status_code', 0) == 429:
                    wait = max(wait, 10)
                time.sleep(wait)
        return ""

    return llm_fn


# ── Async LLM Call ──────────────────────────────────────────────────

def create_async_llm_fn(config: LLMConfig) -> Callable:
    """Create an async LLM function: async (system, user) -> str.
    
    Requires aiohttp: pip install aiohttp
    """
    if not HAS_AIOHTTP:
        raise ImportError("aiohttp required for async LLM calls: pip install aiohttp")

    prov = PROVIDERS.get(config.provider, PROVIDERS["custom"])
    extra_body = prov.get("extra_body", {})
    # Semaphore for rate limiting
    sem = asyncio.Semaphore(config.rpm_limit or 50)

    async def allm_fn(system_prompt: str, user_prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"

        body = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            **extra_body,
        }

        async with sem:
            for attempt in range(config.retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{config.base_url}/v1/chat/completions",
                            json=body,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=config.timeout),
                        ) as resp:
                            resp.raise_for_status()
                            data = await resp.json()
                            return data["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    if attempt == config.retries - 1:
                        raise
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
        return ""

    return allm_fn


# ── Async Batch Evaluation ──────────────────────────────────────────

async def async_evaluate_batch(
    agent_prompt: str,
    scenarios: list,
    opponent_prompt: str,
    config: LLMConfig,
    max_turns: int = 5,
    max_concurrent: int = 5,
) -> list:
    """Evaluate agent on multiple scenarios concurrently.
    
    Returns list of (scenario_id, normalized_score, agreed).
    Uses semaphore to limit concurrency.
    """
    from src.negotiation import run_negotiation, FIXED_OPPONENT_PROMPT

    if opponent_prompt is None:
        opponent_prompt = FIXED_OPPONENT_PROMPT

    allm = create_async_llm_fn(config)
    sem = asyncio.Semaphore(max_concurrent)

    async def eval_one(scenario):
        async with sem:
            # run_negotiation is sync; run in executor
            loop = asyncio.get_event_loop()
            llm_sync = create_llm_fn(config)
            deal, dialogue = await loop.run_in_executor(
                None,
                lambda: run_negotiation(
                    agent_prompt, opponent_prompt, scenario,
                    max_turns=max_turns, llm_fn=llm_sync,
                ),
            )
            return {
                "scenario_id": scenario.id,
                "score": deal.normalized_agent_score(scenario),
                "agreed": deal.agreed,
            }

    tasks = [eval_one(s) for s in scenarios]
    return await asyncio.gather(*tasks, return_exceptions=True)


# ── Convenience ─────────────────────────────────────────────────────

def check_provider(config: LLMConfig) -> dict:
    """Quick health check for a provider. Returns {ok, model, latency_ms, error}."""
    try:
        llm = create_llm_fn(config)
        t0 = time.time()
        resp = llm("You are a test.", "Say 'ok' and nothing else.")
        latency = (time.time() - t0) * 1000
        return {"ok": True, "model": config.model, "latency_ms": round(latency), "response": resp}
    except Exception as e:
        return {"ok": False, "model": config.model, "error": str(e)}
