"""
Agent module for Célula Madre MVP.
Code-generating agents with variable system prompts.
"""

from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic, APIError
from src.database import AgentConfig


class SimpleAgent:
    """AI agent that generates code using Claude with a configurable prompt."""

    def __init__(self, config: AgentConfig):
        """
        Initialize agent with configuration.

        Args:
            config: Agent configuration including system prompt
        """
        self.config = config
        self.client = Anthropic()

    def solve_request(self, description: str) -> tuple[str, int, float]:
        """
        Generate code based on client description.

        Args:
            description: Natural language description of code to generate

        Returns:
            Tuple of (code, tokens_used, api_cost)

        Raises:
            RuntimeError: If Anthropic API call fails (wraps APIError)
        """
        try:
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                system=self.config.system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Generate Python code for: {description}\n\nInclude tests and docstrings.\n\nIMPORTANT: Return ONLY executable Python code. No markdown formatting, no backticks, no code block delimiters."
                }],
                max_tokens=2048
            )

            # Calculate API cost (Haiku pricing)
            # Input: $1.00 per million tokens
            # Output: $5.00 per million tokens
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            input_cost = (response.usage.input_tokens / 1_000_000) * 1.00
            output_cost = (response.usage.output_tokens / 1_000_000) * 5.00
            api_cost = input_cost + output_cost

            return response.content[0].text, tokens_used, api_cost

        except APIError as e:
            # Log error and re-raise with context for debugging
            raise RuntimeError(
                f"Agent {self.config.agent_id} failed to generate code: {str(e)}"
            ) from e
