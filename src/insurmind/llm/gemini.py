"""Provider Gemini — usa a Google GenAI API direta com controle MANUAL do loop
de tool calls. Pré-requisito do Modo Debug (que precisa pausar entre passos).

Diferente do `claude_code` provider (que faz autodispatch das tools internamente
via MCP), aqui controlamos cada etapa: enviamos pra LLM, recebemos resposta,
executamos tool nós mesmos, mandamos resultado de volta, continuamos o loop.
Isso permite emitir eventos granulares (e, na Etapa C, pausar entre eles).

Configuração:
    export GEMINI_API_KEY=...        # obtenha em https://aistudio.google.com/apikey
    INSURMIND_LLM=gemini python -m insurmind.agent "..."

Modelo default: `gemini-2.5-flash` (econômico, free tier generoso, multimodal,
suporta function calling). Sobrescreva via env `GEMINI_MODEL`.
"""

from __future__ import annotations

import os
from typing import AsyncIterator

from .base import Block, TextDelta, Tool, ToolCall, ToolResult

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_TOOL_ROUNDS = 10  # proteção contra loops infinitos


def _to_gemini_tool_declarations(tools: list[Tool]):
    """Traduz Tool agnóstica → FunctionDeclaration do Gemini.

    Gemini usa OpenAPI Schema (subconjunto do JSON Schema). Pra schemas simples
    o nosso JSON Schema já é compatível — types `object`/`string`/`integer`/
    `boolean`/`array` + `properties` + `required` + `enum` funcionam diretos.
    """
    from google.genai import types as gtypes

    decls = []
    for t in tools:
        decls.append(gtypes.FunctionDeclaration(
            name=t.name,
            description=t.description,
            parameters=t.parameters_schema,
        ))
    return [gtypes.Tool(function_declarations=decls)]


def _to_gemini_contents(messages: list[dict]):
    """Traduz nosso histórico → list[Content] do Gemini.

    Gemini usa roles `"user"` e `"model"` (não `"assistant"`).
    """
    from google.genai import types as gtypes

    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(gtypes.Content(
            role=role,
            parts=[gtypes.Part.from_text(text=m["content"])],
        ))
    return contents


class GeminiProvider:
    """Adapter pra Google GenAI SDK com loop manual de tool calls."""

    def __init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Obtenha em "
                "https://aistudio.google.com/apikey e configure em `.env` "
                "(ou export GEMINI_API_KEY=...)."
            )
        # Import preguiçoso pra que o stub anterior não exija o SDK instalado
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model_name = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        from google.genai import types as gtypes

        tools_by_name = {t.name: t for t in tools}
        gemini_tools = _to_gemini_tool_declarations(tools) if tools else None
        contents = _to_gemini_contents(messages)

        config = gtypes.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=gemini_tools,
            # Desabilita autodispatch — queremos controle manual pra emitir eventos
            automatic_function_calling=gtypes.AutomaticFunctionCallingConfig(disable=True),
        )

        for _ in range(MAX_TOOL_ROUNDS):
            # Chamada à LLM (assíncrona)
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=config,
            )

            # Coleta texto e function_calls da resposta
            function_calls = []
            text_parts = []
            for cand in (response.candidates or []):
                if not cand.content or not cand.content.parts:
                    continue
                for part in cand.content.parts:
                    if getattr(part, "text", None):
                        text_parts.append(part.text)
                    fc = getattr(part, "function_call", None)
                    if fc is not None:
                        function_calls.append(fc)

            # Emite TextDelta pra cada pedaço de texto
            for txt in text_parts:
                yield TextDelta(text=txt)

            # Se não pediu tool, a conversa terminou
            if not function_calls:
                return

            # Para cada tool pedida: emite ToolCall, executa handler, alimenta resultado
            # de volta como nova mensagem (com Part.from_function_response).
            # Primeiro, adiciona a resposta do modelo ao histórico (pra próximo round).
            model_parts = []
            for txt in text_parts:
                model_parts.append(gtypes.Part.from_text(text=txt))
            for fc in function_calls:
                model_parts.append(gtypes.Part(function_call=fc))
            contents.append(gtypes.Content(role="model", parts=model_parts))

            tool_result_parts = []
            for fc in function_calls:
                fc_args = dict(fc.args) if fc.args else {}
                yield ToolCall(name=fc.name, args=fc_args)

                tool = tools_by_name.get(fc.name)
                if tool is None:
                    result_text = f"ERRO: tool desconhecida '{fc.name}'"
                else:
                    try:
                        result = await tool.handler(fc_args)
                        result_text = (
                            result["text"]
                            if isinstance(result, dict) and "text" in result
                            else str(result)
                        )
                    except Exception as e:
                        result_text = f"ERRO ao executar {fc.name}: {type(e).__name__}: {e}"

                # Emite o resultado pra agente/UI verem (pré-requisito do Modo Debug)
                yield ToolResult(name=fc.name, result=result_text)

                tool_result_parts.append(gtypes.Part.from_function_response(
                    name=fc.name,
                    response={"result": result_text},
                ))

            # Devolve os resultados pra LLM (role="user" no formato Gemini pra function responses)
            contents.append(gtypes.Content(role="user", parts=tool_result_parts))

        # Se ultrapassou MAX_TOOL_ROUNDS, encerra com aviso
        yield TextDelta(text="\n\n[Aviso: limite de rounds de tool calls atingido.]")
