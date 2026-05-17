"""Eventos estruturados emitidos pelo agente — base do Modo Debug da UI.

Todos os eventos são narrados na **perspectiva do Agente** (o ator central do
sistema), em gerúndio, didáticos. O Agente é o componente que estamos
desenvolvendo; LLM e tools são recursos que ele orquestra.

Sequência típica pra uma pergunta de FAQ que dispara `retrieve_kb`:

  1. agent_received_user_input            — recebeu a pergunta
  2. agent_sending_to_llm                  — vai enviar contexto à LLM
  3. agent_received_tool_request_from_llm  — LLM pediu execução de tool
  4. agent_executing_tool                  — está rodando a tool
  5. agent_received_tool_result            — tool terminou
  6. agent_sending_tool_result_to_llm      — devolve resultado à LLM
  7. agent_received_text_from_llm          — LLM gerou texto final
  8. agent_delivering_answer_to_user       — apresenta no chat

Para pergunta off-domain (LLM responde direto sem chamar tool), só os passos
1, 2, 7, 8 ocorrem. Para cotação multi-turno, a sequência se repete a cada
turno de coleta de dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

EventType = Literal[
    "agent_received_user_input",
    "agent_sending_to_llm",
    "agent_received_tool_request_from_llm",
    "agent_executing_tool",
    "agent_received_tool_result",
    "agent_sending_tool_result_to_llm",
    "agent_received_text_from_llm",
    "agent_delivering_answer_to_user",
    "error",
]


@dataclass(frozen=True)
class AgentEvent:
    type: EventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def short_description(self) -> str:
        """Texto curto pro botão 'Próximo passo' da UI. Sempre em gerúndio,
        agente como sujeito ativo."""
        match self.type:
            case "agent_received_user_input":
                return "Agente recebendo pergunta do usuário"
            case "agent_sending_to_llm":
                return "Agente enviando contexto à LLM"
            case "agent_received_tool_request_from_llm":
                return "Agente recebeu pedido de tool da LLM"
            case "agent_executing_tool":
                name = self.payload.get("name", "?")
                return f"Agente executando a tool `{name}`"
            case "agent_received_tool_result":
                name = self.payload.get("name", "?")
                return f"Agente recebeu resultado da tool `{name}`"
            case "agent_sending_tool_result_to_llm":
                return "Agente devolvendo resultado à LLM"
            case "agent_received_text_from_llm":
                return "Agente recebeu texto da LLM"
            case "agent_delivering_answer_to_user":
                return "Agente apresentando resposta ao usuário"
            case "error":
                return "Erro durante a execução"
            case _:
                return self.type
