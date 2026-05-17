"""Camada de provider de LLM, agnóstica ao motor de inferência.

Uso típico:

    from insurmind.llm import make_provider
    from insurmind.tools import ALL_TOOLS

    provider = make_provider()
    async for block in provider.chat(system_prompt, messages, ALL_TOOLS):
        ...

A factory `make_provider` lê a env var `INSURMIND_LLM` (default: `claude_code`).
Imports dos providers são preguiçosos — cada um traz suas dependências só
quando selecionado.
"""

from __future__ import annotations

import os

from .base import Block, LLMProvider, TextDelta, Tool, ToolCall, ToolResult

__all__ = [
    "Block",
    "LLMProvider",
    "TextDelta",
    "Tool",
    "ToolCall",
    "ToolResult",
    "make_provider",
]


def make_provider() -> LLMProvider:
    name = os.environ.get("INSURMIND_LLM", "claude_code").lower()
    if name == "claude_code":
        from .claude_code import ClaudeCodeProvider
        return ClaudeCodeProvider()
    if name == "anthropic_api":
        from .anthropic_api import AnthropicAPIProvider
        return AnthropicAPIProvider()
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider()
    if name == "gemini":
        from .gemini import GeminiProvider
        return GeminiProvider()
    raise ValueError(
        f"Provider '{name}' desconhecido. "
        f"Opções: claude_code | anthropic_api | ollama | gemini."
    )
