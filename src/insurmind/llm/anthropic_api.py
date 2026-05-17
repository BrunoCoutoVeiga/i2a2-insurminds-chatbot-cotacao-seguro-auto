"""Provider Anthropic API — usa a API HTTPS direta da Anthropic via SDK
`anthropic`, com controle MANUAL do loop de tool calls.

Diferente do `claude_code` provider (que spawna a CLI local do Claude Code e
faz autodispatch via MCP), aqui falamos direto com a API:

- Sem subprocess — não depende do binário `claude.exe` estar no PATH.
- Loop de tool calls manual — emite ToolCall + ToolResult granularmente
  (mesmas garantias do `gemini.py`, pré-requisito do Modo Debug step-by-step
  com os 8 passos completos, incluindo passos 5+6).
- Funciona em deploy (Render/Vercel) onde não há `claude.exe` instalado.

Configuração:
    export ANTHROPIC_API_KEY=sk-ant-...   # https://console.anthropic.com
    INSURMIND_LLM=anthropic_api python -m insurmind.agent "..."

Modelo default: `claude-sonnet-4-5` (boa relação custo/qualidade). Sobrescreva
via env `ANTHROPIC_MODEL` (ex.: `claude-opus-4-5` para tarefas mais pesadas).
"""

from __future__ import annotations

import logging
import os
from typing import AsyncIterator

from .base import Block, TextDelta, Tool, ToolCall, ToolResult

DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4096
MAX_TOOL_ROUNDS = 10  # proteção contra loops infinitos

logger = logging.getLogger(__name__)


def _to_anthropic_tools(tools: list[Tool]) -> list[dict]:
    """Traduz Tool agnóstica → formato `tools=[...]` da Anthropic API.

    O campo `input_schema` da Anthropic aceita JSON Schema direto; nosso
    `parameters_schema` já está nesse formato.
    """
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.parameters_schema,
        }
        for t in tools
    ]


class AnthropicAPIProvider:
    """Adapter pra Anthropic Messages API com loop manual de tool calls."""

    def __init__(self) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY não configurada. Obtenha em "
                "https://console.anthropic.com e configure em `.env` "
                "(ou export ANTHROPIC_API_KEY=...)."
            )
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        tools_by_name = {t.name: t for t in tools}
        anth_tools = _to_anthropic_tools(tools) if tools else []

        logger.info(
            "PROVIDER anthropic_api: iniciando turno (model=%s, %d msgs hist, %d tools)",
            self._model, len(messages), len(anth_tools),
        )

        # Trabalhamos com cópia do histórico — vamos adicionar mensagens do
        # assistant (com tool_use) e do user (com tool_result) entre os rounds.
        conv: list[dict] = [dict(m) for m in messages]

        for round_idx in range(MAX_TOOL_ROUNDS):
            logger.info("LLM round %d: chamando Anthropic API...", round_idx + 1)
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=anth_tools,
                messages=conv,
            )

            # Resposta vem com lista de blocks (TextBlock, ToolUseBlock).
            text_pieces: list[str] = []
            tool_uses: list = []
            block_summary: list[str] = []
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    text_pieces.append(block.text)
                    block_summary.append(f"text({len(block.text)} chars)")
                elif btype == "tool_use":
                    tool_uses.append(block)
                    block_summary.append(f"tool_use({block.name})")

            usage = getattr(response, "usage", None)
            tokens_info = (
                f"in={usage.input_tokens}, out={usage.output_tokens}"
                if usage else "?"
            )
            logger.info(
                "  → resposta da LLM: stop_reason=%s, blocks=[%s], tokens=%s",
                response.stop_reason,
                ", ".join(block_summary) if block_summary else "vazio",
                tokens_info,
            )

            for txt in text_pieces:
                yield TextDelta(text=txt)

            # Se LLM não pediu tool, conversa terminou
            if not tool_uses:
                logger.info(
                    "LLM terminou (sem tool_use) — encerrando loop após round %d",
                    round_idx + 1,
                )
                return

            # Reconstrói content do assistant como dicts (mais robusto que
            # passar os blocks crus do SDK pra próximo create()).
            assistant_content: list[dict] = []
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif btype == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
            conv.append({"role": "assistant", "content": assistant_content})

            # Executa cada tool pedida e monta lista de tool_results
            tool_results: list[dict] = []
            for tu in tool_uses:
                args = dict(tu.input) if tu.input else {}
                yield ToolCall(name=tu.name, args=args)

                tool = tools_by_name.get(tu.name)
                if tool is None:
                    result_text = f"ERRO: tool desconhecida '{tu.name}'"
                else:
                    try:
                        result = await tool.handler(args)
                        result_text = (
                            result["text"]
                            if isinstance(result, dict) and "text" in result
                            else str(result)
                        )
                    except Exception as e:
                        result_text = f"ERRO ao executar {tu.name}: {type(e).__name__}: {e}"

                yield ToolResult(name=tu.name, result=result_text)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": result_text,
                })

            # Devolve resultados pra LLM no próximo round (role=user com
            # content=list de tool_result blocks — formato Anthropic).
            conv.append({"role": "user", "content": tool_results})

        # Saiu do for sem return → loop estourou
        logger.warning(
            "LLM estourou MAX_TOOL_ROUNDS=%d — possível loop infinito",
            MAX_TOOL_ROUNDS,
        )
        yield TextDelta(text="\n\n[Aviso: limite de rounds de tool calls atingido.]")
