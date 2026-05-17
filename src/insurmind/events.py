"""Eventos estruturados emitidos pelo agente — base do Modo Debug da UI.

O agente envelopa os `Block` brutos do provider de LLM em `AgentEvent`s ricos
(com tipo, payload estruturado e timestamp) que a UI debug consome pra
mostrar passo a passo o que está acontecendo por baixo dos panos.

Tipos de eventos (na ordem típica de uma conversa):

1. `llm_call_start`      — agente preparou a chamada e está enviando à LLM
2. `llm_text`            — LLM emitiu pedaço de texto (resposta direta)
3. `tool_call_requested` — LLM pediu execução de uma tool
4. `tool_result`         — handler da tool retornou (só providers manuais; Claude SDK não emite)
5. `final_answer`        — fim do ciclo; cadeia completa pronta

Os botões do Modo Debug derivam-se desses tipos (`docs/visao-geral-do-chatbot.md` §7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

EventType = Literal[
    "llm_call_start",
    "llm_text",
    "tool_call_requested",
    "tool_result",
    "final_answer",
]


@dataclass(frozen=True)
class AgentEvent:
    type: EventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def short_description(self) -> str:
        """Texto curto pra exibir como label no botão 'Próximo passo' da UI debug."""
        match self.type:
            case "llm_call_start":
                return "Enviar pergunta à LLM (com system prompt e tools)"
            case "llm_text":
                return "Receber texto da LLM"
            case "tool_call_requested":
                name = self.payload.get("name", "?")
                return f"Executar a tool `{name}` pedida pela LLM"
            case "tool_result":
                name = self.payload.get("name", "?")
                return f"Devolver resultado da tool `{name}` à LLM"
            case "final_answer":
                return "Mostrar resposta final ao usuário"
            case _:
                return self.type
