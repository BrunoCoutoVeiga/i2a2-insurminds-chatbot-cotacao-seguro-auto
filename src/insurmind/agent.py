"""Agente InsurMind — orquestrador agnóstico ao motor de inferência.

A escolha do motor (Claude Code local, Anthropic API, Ollama, Gemini) é feita
via env var `INSURMIND_LLM` pela factory em `insurmind.llm.make_provider`.

Uso CLI (single-shot, sem histórico):
    python -m insurmind.agent "O que é franquia?"
    INSURMIND_LLM=gemini python -m insurmind.agent "..."

Uso programático (multi-turno, com histórico):
    from insurmind.agent import chat_stream
    async for chunk in chat_stream(messages=[{"role": "user", "content": "..."}, ...]):
        if isinstance(chunk, TextDelta):
            print(chunk.text, end="", flush=True)
"""

from __future__ import annotations

import asyncio
import io
import sys
from typing import AsyncIterator

from dotenv import load_dotenv

from .events import AgentEvent
from .llm import Block, TextDelta, ToolCall, ToolResult, make_provider
from .prompts import SYSTEM_PROMPT
from .tools import ALL_TOOLS


async def chat_stream(messages: list[dict]) -> AsyncIterator[Block]:
    """Envia o histórico completo e devolve um stream de blocos (texto + tool calls).

    `messages` no formato `[{"role": "user"|"assistant", "content": str}, ...]`
    contendo o histórico do diálogo até a mensagem atual do usuário inclusive.

    Yields `TextDelta` (pedaços de texto), `ToolCall` (pedido) e `ToolResult`
    (resultado, só providers manuais como `gemini`). O cliente concatena os
    `TextDelta` pra montar a resposta final.
    """
    provider = make_provider()
    async for block in provider.chat(
        system_prompt=SYSTEM_PROMPT,
        messages=messages,
        tools=ALL_TOOLS,
    ):
        yield block


async def chat_stream_events(messages: list[dict]) -> AsyncIterator[AgentEvent]:
    """Versão rica do `chat_stream` que envelopa Blocks em AgentEvents.

    Pra UI debug step-by-step: cada operação interna do agente vira um event
    estruturado (tipo + payload + timestamp). Emite no fim um `final_answer`
    com o texto completo concatenado.

    Limitação: providers com autodispatch (`claude_code`) não emitem `ToolResult`
    — a sequência pra cada tool fica `tool_call_requested` → (próximo `llm_text`).
    Pra debug com `tool_result` granular, use `INSURMIND_LLM=gemini`.
    """
    # Evento inicial — descreve o que está sendo enviado à LLM
    yield AgentEvent(
        type="llm_call_start",
        payload={
            "system_prompt_preview": SYSTEM_PROMPT[:300] + "...",
            "system_prompt_full": SYSTEM_PROMPT,
            "user_message": messages[-1]["content"] if messages else "",
            "history_length": len(messages),
            "tools_available": [
                {"name": t.name, "description": t.description[:100]}
                for t in ALL_TOOLS
            ],
        },
    )

    pieces: list[str] = []
    async for block in chat_stream(messages):
        if isinstance(block, TextDelta):
            pieces.append(block.text)
            yield AgentEvent(
                type="llm_text",
                payload={"text": block.text},
            )
        elif isinstance(block, ToolCall):
            yield AgentEvent(
                type="tool_call_requested",
                payload={"name": block.name, "args": dict(block.args)},
            )
        elif isinstance(block, ToolResult):
            yield AgentEvent(
                type="tool_result",
                payload={
                    "name": block.name,
                    "result_preview": block.result[:500] + ("..." if len(block.result) > 500 else ""),
                    "result_full": block.result,
                },
            )

    yield AgentEvent(
        type="final_answer",
        payload={"text": "".join(pieces)},
    )


async def chat_once(user_message: str) -> str:
    """Single-shot: 1 mensagem do usuário, retorna a resposta concatenada.

    Wrapper sobre `chat_stream` pra retrocompatibilidade com a CLI atual.
    """
    pieces: list[str] = []
    messages = [{"role": "user", "content": user_message}]
    async for block in chat_stream(messages):
        if isinstance(block, TextDelta):
            pieces.append(block.text)
        elif isinstance(block, ToolCall):
            print(f"[debug] tool call: {block.name}({block.args})", file=sys.stderr)
        # ToolResult não printa (rapidamente vira ruído na CLI; use `chat_stream_events` se quiser ver tudo)
    return "".join(pieces)


def main() -> int:
    load_dotenv()
    if sys.platform == "win32" and isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("uso: python -m insurmind.agent <mensagem>")
        return 1
    user_message = " ".join(sys.argv[1:])
    answer = asyncio.run(chat_once(user_message))
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
