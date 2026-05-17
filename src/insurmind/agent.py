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

    Todos os eventos são narrados na perspectiva do Agente — ele é o ator
    central. Sequência típica (FAQ com tool):

      1. agent_received_user_input
      2. agent_sending_to_llm
      3. agent_received_tool_request_from_llm
      4. agent_executing_tool
      5. agent_received_tool_result
      6. agent_sending_tool_result_to_llm
      7. agent_received_text_from_llm
      8. agent_delivering_answer_to_user

    Off-domain (LLM responde direto): só passos 1, 2, 7, 8.

    Limitação: providers com autodispatch (`claude_code`) NÃO emitem
    `ToolResult` — pulam direto pro próximo `llm_text`. Resultado: os passos
    5 e 6 (`agent_received_tool_result` + `agent_sending_tool_result_to_llm`)
    não aparecem. Pra debug com todos os 8 passos, use
    `INSURMIND_LLM=gemini`.
    """
    user_msg = messages[-1]["content"] if messages and messages[-1]["role"] == "user" else ""

    # Passo 1: Agente recebeu o input do usuário e está preparando o contexto
    yield AgentEvent(
        type="agent_received_user_input",
        payload={
            "user_message": user_msg,
            "history_length": len(messages),
        },
    )

    # Passo 2: Agente vai enviar pra LLM (com system prompt + tools)
    yield AgentEvent(
        type="agent_sending_to_llm",
        payload={
            "system_prompt_preview": SYSTEM_PROMPT[:300] + "...",
            "system_prompt_full": SYSTEM_PROMPT,
            "user_message": user_msg,
            "history_length": len(messages),
            "tools_available": [
                {"name": t.name, "description": t.description[:100]}
                for t in ALL_TOOLS
            ],
        },
    )

    # `round_pieces` acumula o texto do round ATUAL da LLM. Cada resposta da LLM
    # é uma mensagem com blocos `[text?, tool_use?]`. Quando aparece um ToolCall,
    # "fechamos" o round e flushamos o texto pré-tool como uma entrega ao usuário
    # — assim a UI mostra "Ótima pergunta, deixa eu buscar..." como bolha
    # separada da resposta final, em vez de grudar tudo no fim. Ao fim do loop,
    # flushamos o último round (texto da resposta final).
    round_pieces: list[str] = []
    delivered_anything = False

    async for block in chat_stream(messages):
        if isinstance(block, TextDelta):
            round_pieces.append(block.text)
            # Passo 7 (genérico): Agente recebeu texto da LLM
            yield AgentEvent(
                type="agent_received_text_from_llm",
                payload={"text": block.text},
            )
        elif isinstance(block, ToolCall):
            # Ordem cuidadosamente escolhida pra refletir a REALIDADE da API:
            # quando a LLM responde com `[text, tool_use]` num MESMO message,
            # os 2 blocos chegam adjacentes no nosso stream. Se a gente
            # "entregasse" o texto ao usuário ANTES de emitir o tool_request,
            # o painel debug pareceria mostrar "LLM mandou texto → agente
            # entregou ao user → LLM mandou tool_request do nada", sugerindo
            # uma 2ª chamada que não existiu.
            #
            # Por isso:
            #   1. Primeiro emite tool_request (vizinho do text event — mesma
            #      resposta da LLM, sem nada falso entre eles).
            #   2. Só depois flusha a entrega do texto (agora está claro que é
            #      o AGENTE decidindo apresentar o texto ao usuário, não a LLM
            #      "mandando" de novo).
            #   3. Por fim, executa a tool.
            args_dict = dict(block.args)
            yield AgentEvent(
                type="agent_received_tool_request_from_llm",
                payload={"name": block.name, "args": args_dict},
            )
            if round_pieces:
                yield AgentEvent(
                    type="agent_delivering_answer_to_user",
                    payload={"text": "".join(round_pieces)},
                )
                delivered_anything = True
                round_pieces = []
            yield AgentEvent(
                type="agent_executing_tool",
                payload={"name": block.name, "args": args_dict},
            )
        elif isinstance(block, ToolResult):
            # Passo 5: Agente recebeu o resultado da tool
            yield AgentEvent(
                type="agent_received_tool_result",
                payload={
                    "name": block.name,
                    "result_preview": block.result[:500] + ("..." if len(block.result) > 500 else ""),
                    "result_full": block.result,
                },
            )
            # Passo 6: Agente devolvendo resultado à LLM (ela vai formular resposta)
            yield AgentEvent(
                type="agent_sending_tool_result_to_llm",
                payload={"name": block.name},
            )

    # Passo 8: Agente apresentando a resposta final ao usuário (texto do último
    # round, depois da LLM ter visto os tool_results). Sempre emitimos pelo
    # menos uma entrega — se não houve nenhuma anterior nem texto agora, vai
    # vazia mas marca o fim do turno (a UI usa esse evento como sinal).
    if round_pieces or not delivered_anything:
        yield AgentEvent(
            type="agent_delivering_answer_to_user",
            payload={"text": "".join(round_pieces)},
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
