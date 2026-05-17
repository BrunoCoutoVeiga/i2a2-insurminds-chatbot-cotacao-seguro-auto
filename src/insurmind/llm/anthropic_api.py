"""Stub: provider que falaria direto com a API da Anthropic via SDK `anthropic`.

Diferenças vs `ClaudeCodeProvider`:
- Sem subprocess do Claude Code CLI; chamada HTTPS direta.
- Loop de tool call **manual** (a Anthropic API não autodispatch como o SDK do
  Claude Code faz).
- Requer `ANTHROPIC_API_KEY` válido em variável de ambiente.

Para implementar: usar `anthropic.AsyncAnthropic`, montar `tools=[...]` no
`messages.create`, ler `response.content` por bloco, executar o handler em
`ToolUseBlock`, devolver `tool_result` na próxima chamada, repetir até obter
texto final.
"""

from __future__ import annotations

from typing import AsyncIterator

from .base import Block, Tool


class AnthropicAPIProvider:
    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        raise NotImplementedError(
            "AnthropicAPIProvider ainda não implementado. "
            "Use INSURMIND_LLM=claude_code por enquanto."
        )
        yield  # pragma: no cover  # mantém função como async generator
