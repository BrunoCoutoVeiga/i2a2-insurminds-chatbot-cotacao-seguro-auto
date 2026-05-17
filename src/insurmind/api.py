"""Backend HTTP da nova UI Next.js (Fase 1 da Sprint 3).

Expõe o agente InsurMind via API REST + Server-Sent Events (SSE). Mantém o
contrato `chat_stream_events` (AsyncIterator de AgentEvent) — apenas serializa
cada evento como SSE pra Next.js consumir via `EventSource`.

**Não substitui** a UI Streamlit em `ui.py` — é um caminho paralelo.

Endpoints:
- `GET  /api/health`             — sanity check
- `POST /api/chat`               — SSE stream de eventos do agente
- `GET  /api/info`               — metadados (provider atual, tools disponíveis)

Uso (dev):
    uvicorn insurmind.api:app --reload --port 8000
"""
from __future__ import annotations

import json
import os
import sys
from typing import AsyncIterator, Literal

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from insurmind.agent import chat_stream_events
from insurmind.tools import ALL_TOOLS

load_dotenv()

# Encoding fix Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# =============================================================================
# App + CORS
# =============================================================================

app = FastAPI(
    title="InsurMind API",
    description=(
        "Backend HTTP da UI Next.js do chatbot InsurMind (Porto Inseguro, fictícia). "
        "Expõe o agente via SSE stream de eventos pra UI poder renderizar o Modo "
        "Debug em tempo real."
    ),
    version="0.1.0",
)

# Dev: Next em localhost:3000 chama backend em localhost:8000
# Prod: ajustar conforme deploy (Vercel front + Render back)
ALLOWED_ORIGINS = os.environ.get(
    "INSURMIND_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Modelos Pydantic
# =============================================================================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(
        description="Histórico completo do diálogo, incluindo a última mensagem do usuário.",
        min_length=1,
    )


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    provider: str
    tools_count: int


class ToolInfo(BaseModel):
    name: str
    description: str


class InfoResponse(BaseModel):
    provider: str
    tools: list[ToolInfo]
    cors_origins: list[str]


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Sanity check — confirma que o backend subiu e quais provider/tools estão ativos."""
    return HealthResponse(
        provider=os.environ.get("INSURMIND_LLM", "claude_code"),
        tools_count=len(ALL_TOOLS),
    )


@app.get("/api/info", response_model=InfoResponse)
async def info() -> InfoResponse:
    """Metadados pra UI mostrar config corrente (provider, tools, CORS)."""
    return InfoResponse(
        provider=os.environ.get("INSURMIND_LLM", "claude_code"),
        tools=[ToolInfo(name=t.name, description=t.description[:200]) for t in ALL_TOOLS],
        cors_origins=ALLOWED_ORIGINS,
    )


@app.post("/api/chat")
async def chat(payload: ChatRequest):
    """Roda 1 turno do agente e devolve SSE stream de AgentEvents.

    Formato do stream (cada evento é uma linha SSE `event: <type>\\ndata: <json>\\n\\n`):

        event: llm_call_start
        data: {"type": "llm_call_start", "payload": {...}, "timestamp": "..."}

        event: tool_call_requested
        data: {"type": "tool_call_requested", "payload": {...}, "timestamp": "..."}

        ...

        event: final_answer
        data: {"type": "final_answer", "payload": {"text": "..."}, "timestamp": "..."}

    O cliente Next.js consome via `EventSource` e renderiza no painel debug.
    """
    messages_dicts = [m.model_dump() for m in payload.messages]

    async def event_stream() -> AsyncIterator[dict]:
        try:
            async for ev in chat_stream_events(messages_dicts):
                data = {
                    "type": ev.type,
                    "payload": ev.payload,
                    "timestamp": ev.timestamp.isoformat(),
                }
                yield {
                    "event": ev.type,
                    "data": json.dumps(data, ensure_ascii=False),
                }
        except Exception as e:
            # Em vez de quebrar o stream, emite evento de erro pra UI exibir
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "error",
                    "payload": {"message": f"{type(e).__name__}: {e}"},
                }, ensure_ascii=False),
            }

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    # `python -m insurmind.api` pra rodar em dev (alternativa a `uvicorn ...`)
    import uvicorn
    uvicorn.run("insurmind.api:app", host="127.0.0.1", port=8000, reload=True)
