"""Contrato agnóstico ao motor de inferência (LLM).

Define os tipos comuns que `agent.py` e `tools.py` consomem, sem amarração
com nenhum SDK específico. Cada provider em `llm/<motor>.py` traduz entre
estes tipos e o formato nativo do motor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable, Protocol


@dataclass(frozen=True)
class Tool:
    """Descrição agnóstica de uma tool exposta ao agente.

    `parameters_schema` é JSON Schema (denominador comum entre Claude, Gemini,
    OpenAI e Ollama). `handler` é a função Python pura executada quando o
    motor decide chamar a tool — recebe os args validados e retorna um dict
    com pelo menos a chave `text` (resposta serializada para o motor).
    """

    name: str
    description: str
    parameters_schema: dict
    handler: Callable[[dict], Awaitable[dict[str, Any]]]


@dataclass
class TextDelta:
    """Pedaço de texto humano-legível emitido pelo motor."""

    text: str


@dataclass
class ToolCall:
    """Pedido de chamada de tool emitido pelo motor.

    A execução do handler acontece dentro do provider; o agente vê este
    bloco apenas para fins de logging/debug.
    """

    name: str
    args: dict


@dataclass
class ToolResult:
    """Resultado da execução de uma tool, emitido pelos providers que
    controlam o loop manualmente (ex.: `gemini`). Providers com autodispatch
    (ex.: `claude_code`) não emitem este bloco — o agent.py converte os
    blocks em eventos genéricos e degrada graciosamente quando ausente.
    """

    name: str
    result: str        # texto retornado pelo handler (já serializado)


Block = TextDelta | ToolCall | ToolResult


class LLMProvider(Protocol):
    """Contrato de qualquer motor de LLM utilizável pelo agente.

    Implementações vivem em `llm/<motor>.py` (ex.: `claude_code`, `ollama`,
    `gemini`, `anthropic_api`). A factory em `llm/__init__.py` escolhe qual
    instanciar via env var `INSURMIND_LLM`.
    """

    def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        """Envia a conversa ao motor e devolve um stream de blocos.

        - `system_prompt`: texto de instrução de mais alta prioridade.
        - `messages`: histórico no formato `[{"role": "user"|"assistant",
          "content": str}, ...]`.
        - `tools`: lista de tools que o motor pode invocar; o provider é
          responsável por traduzi-las ao formato nativo e por executar o
          loop de tool calls (autodispatch ou manual) sem expor essa
          complexidade ao chamador.

        Retorna um async iterator de `TextDelta` e (opcionalmente) `ToolCall`.
        """
        ...
