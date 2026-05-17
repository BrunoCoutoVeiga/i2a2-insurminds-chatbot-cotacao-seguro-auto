"""Stub: provider para LLM local via Ollama (`http://localhost:11434`).

Para implementar: usar `httpx.AsyncClient` para chamar `/api/chat` com
`stream=True`; consumir NDJSON; quando o modelo emitir `tool_calls`, executar
o handler localmente e devolver o resultado como mensagem `tool` na próxima
chamada (loop manual).

Modelos recomendados (todos suportam tool calling):
- `llama3.1:8b-instruct` — leve, roda em CPU.
- `qwen2.5:7b-instruct` — bom em PT-BR.
- `mistral-nemo:12b` — qualidade superior, exige GPU/RAM mais robusta.
"""

from __future__ import annotations

from typing import AsyncIterator

from .base import Block, Tool


class OllamaProvider:
    def __init__(self, model: str = "llama3.1:8b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        raise NotImplementedError(
            "OllamaProvider ainda não implementado. "
            "Use INSURMIND_LLM=claude_code por enquanto."
        )
        yield  # pragma: no cover
