"""Provider que usa o `claude-agent-sdk` com a sessão local do Claude Code CLI.

Este é o adapter padrão (`INSURMIND_LLM=claude_code`). A SDK do Claude resolve
internamente o loop de tool calls — basta registrar as tools como MCP server
local que o autodispatch acontece sozinho.
"""

from __future__ import annotations

from typing import AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

from .base import Block, TextDelta, Tool, ToolCall

MCP_NAMESPACE = "insurmind"


def _wrap_tool(t: Tool):
    """Embrulha uma `Tool` agnóstica como tool nativa do Claude Agent SDK.

    O SDK aceita JSON Schema diretamente no terceiro argumento de `@tool`.
    O resultado do handler é normalizado para o formato esperado:
    `{"content": [{"type": "text", "text": "..."}]}`.
    """

    @tool(t.name, t.description, t.parameters_schema)
    async def sdk_handler(args: dict):
        result = await t.handler(args)
        text = result["text"] if isinstance(result, dict) and "text" in result else str(result)
        return {"content": [{"type": "text", "text": text}]}

    return sdk_handler


class ClaudeCodeProvider:
    """Adapter para `claude-agent-sdk` (Claude Code CLI local)."""

    async def chat(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[Tool],
    ) -> AsyncIterator[Block]:
        sdk_tools = [_wrap_tool(t) for t in tools]

        options_kwargs: dict = {"system_prompt": system_prompt}
        if sdk_tools:
            server = create_sdk_mcp_server(MCP_NAMESPACE, "1.0.0", tools=sdk_tools)
            options_kwargs["mcp_servers"] = {MCP_NAMESPACE: server}
            options_kwargs["allowed_tools"] = [
                f"mcp__{MCP_NAMESPACE}__{t.name}" for t in tools
            ]

        options = ClaudeAgentOptions(**options_kwargs)

        # Pra multi-turno: como o ClaudeSDKClient é session-based e abrimos uma
        # sessão nova a cada chat(), formatamos o histórico inteiro como texto
        # estruturado na primeira query. A LLM lê e entende o contexto.
        # Limitação: ineficiente em conversas longas (re-envia tudo); resolvido
        # se/quando migrarmos pro provider gemini (que aceita messages array nativo).
        if len(messages) == 1 and messages[0]["role"] == "user":
            query_text = messages[0]["content"]
        else:
            lines: list[str] = ["[Diálogo anterior:]"]
            for m in messages[:-1]:
                role = "Usuário" if m["role"] == "user" else "InsurMind"
                lines.append(f"{role}: {m['content']}")
            current_user = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                "",
            )
            lines.append(f"\n[Mensagem atual do usuário:]\n{current_user}")
            query_text = "\n".join(lines)

        async with ClaudeSDKClient(options=options) as client:
            await client.query(query_text)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield TextDelta(text=block.text)
                        elif isinstance(block, ToolUseBlock):
                            yield ToolCall(name=block.name, args=block.input)
