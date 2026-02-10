"""
LLM client for DGM - uses OpenAI-compatible API (LM Studio / Qwen3-30B)
"""
import json
import re
import os
from openai import OpenAI

DEFAULT_ENDPOINT = os.environ.get("DGM_LLM_ENDPOINT", "http://172.17.0.1:1234/v1")
DEFAULT_MODEL = os.environ.get("DGM_LLM_MODEL", "qwen3-coder-30b-a3b-instruct")
MAX_TOKENS = 8192


def create_client(endpoint=None, model=None):
    endpoint = endpoint or DEFAULT_ENDPOINT
    model = model or DEFAULT_MODEL
    client = OpenAI(base_url=endpoint, api_key="not-needed")
    return client, model


def chat(client, model, system_message, user_message, temperature=0.7, max_tokens=None):
    """Simple chat completion."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens or MAX_TOKENS,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return response.choices[0].message.content


def chat_with_tools(client, model, system_message, messages, tools, max_iterations=15,
                    tool_executor=None, temperature=0.7):
    """
    Chat with tool use loop.
    tools: list of tool definitions (OpenAI format)
    tool_executor: function(tool_name, tool_args) -> str
    Returns: final message history
    """
    full_messages = [{"role": "system", "content": system_message}] + list(messages)

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            tools=tools,
            temperature=temperature,
            max_tokens=MAX_TOKENS,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )

        choice = response.choices[0]
        msg = choice.message

        # Add assistant message
        full_messages.append(msg.model_dump())

        # Check if there are tool calls
        if not msg.tool_calls:
            break

        # Execute each tool call
        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}

            if tool_executor:
                result = tool_executor(fn_name, fn_args)
            else:
                result = f"Error: no tool executor configured for {fn_name}"

            full_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)[:10000],
            })

    return full_messages


def extract_json(text):
    """Extract JSON from LLM output (handles ```json blocks)."""
    pattern = r'```json\s*\n(.*?)\n\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[0])
        except json.JSONDecodeError:
            pass

    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, text, re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except json.JSONDecodeError:
            continue

    return None
