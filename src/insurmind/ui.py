"""Interface Streamlit do InsurMind — chat + Modo Debug step-by-step.

Chat conversacional com histórico multi-turno, streaming da resposta, disclaimer
didático e toggle "🪲 Modo Debug" que abre painel lateral mostrando passo a
passo o que o agente faz (preparar chamada à LLM → executar tools → mostrar
resposta), com botão "Próximo passo" pra avançar manualmente.

**Observação técnica**: o agente executa a conversa **inteira** ao receber a
mensagem (chamadas à LLM acontecem todas de uma vez). O Modo Debug **pausa a
visualização** dos eventos coletados — o usuário "replaya" o que aconteceu.
Isso é uma limitação prática do modelo de execução do Streamlit (re-roda o
script a cada interação). A UX final é idêntica a "pause real": o usuário
clica e vê cada passo aparecer.

Uso:
    streamlit run src/insurmind/ui.py

Pre-requisitos:
    python scripts/ingest_kb.py        # popula Chroma
    # opcional pra usar Gemini (recomendado pro debug com tool_result granular):
    # configurar GEMINI_API_KEY no .env e INSURMIND_LLM=gemini
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Permite rodar `streamlit run src/insurmind/ui.py` direto sem pip install -e
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
from dotenv import load_dotenv

from insurmind.agent import chat_stream_events
from insurmind.events import AgentEvent

load_dotenv()

st.set_page_config(
    page_title="InsurMind — Chatbot Porto Inseguro",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# Estado de sessão
# =============================================================================

def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []          # histórico do chat (role/content)
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    if "debug_events" not in st.session_state:
        st.session_state.debug_events = []      # lista de AgentEvent do último turno
    if "debug_step_index" not in st.session_state:
        st.session_state.debug_step_index = 0   # quantos events já foram revelados


_init_state()


# =============================================================================
# Header + controles
# =============================================================================

col_title, col_clear, col_debug = st.columns([6, 2, 2])

with col_title:
    st.title("🚗 InsurMind — Porto Inseguro")
    st.caption(
        "Chatbot acadêmico de seguro auto — curso I2A2 InsurMinds (Atividade Obrigatória 2). "
        "**Porto Inseguro** é uma seguradora **fictícia**."
    )

with col_clear:
    st.write(""); st.write("")
    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.messages = []
        st.session_state.debug_events = []
        st.session_state.debug_step_index = 0
        st.rerun()

with col_debug:
    st.write(""); st.write("")
    new_debug = st.toggle(
        "🪲 Modo Debug",
        value=st.session_state.debug_mode,
        help=(
            "Mostra o que acontece por baixo dos panos — chamadas à LLM, tools "
            "executadas, resultados. Para ver `tool_result` granular, use "
            "`INSURMIND_LLM=gemini` no .env (com `claude_code` autodispatch "
            "executa internamente sem expor o resultado intermediário)."
        ),
    )
    if new_debug != st.session_state.debug_mode:
        st.session_state.debug_mode = new_debug
        st.session_state.debug_step_index = 0
        st.rerun()

st.divider()


# =============================================================================
# Layout — chat à esquerda, debug à direita (quando ON)
# =============================================================================

if st.session_state.debug_mode:
    col_chat, col_debug_panel = st.columns([3, 2])
else:
    col_chat = st.container()
    col_debug_panel = None


# =============================================================================
# Helpers de renderização
# =============================================================================

def _render_event(idx: int, ev: AgentEvent, is_current: bool) -> None:
    """Renderiza um AgentEvent no painel debug, com nível de detalhe didático."""
    icon = "🟡" if is_current else "✅"
    label_short = ev.short_description()
    with st.expander(f"{icon} Passo {idx+1} — {label_short}", expanded=is_current):
        if ev.type == "llm_call_start":
            p = ev.payload
            st.markdown(f"**Mensagem do usuário:** {p['user_message']!r}")
            st.markdown(f"**Tamanho do histórico:** {p['history_length']} mensagens")
            st.markdown("**Tools disponíveis:**")
            for t in p["tools_available"]:
                st.markdown(f"- `{t['name']}` — {t['description']}")
            with st.expander("🔍 ver system prompt completo (técnico)"):
                st.code(p["system_prompt_full"], language="text")

        elif ev.type == "llm_text":
            st.markdown("LLM gerou texto (parte da resposta final):")
            st.code(ev.payload["text"][:500] + ("..." if len(ev.payload["text"]) > 500 else ""), language="text")

        elif ev.type == "tool_call_requested":
            st.markdown(f"**Tool:** `{ev.payload['name']}`")
            st.markdown("**Parâmetros pedidos pela LLM:**")
            for k, v in ev.payload["args"].items():
                st.markdown(f"- `{k}` = `{v!r}`")
            with st.expander("🔍 ver formato técnico (JSON)"):
                st.code(json.dumps({
                    "tool_call": ev.payload["name"],
                    "args": ev.payload["args"],
                }, indent=2, ensure_ascii=False), language="json")

        elif ev.type == "tool_result":
            st.markdown(f"**Resultado da tool `{ev.payload['name']}`:**")
            st.code(ev.payload["result_preview"], language="text")
            if ev.payload.get("result_full") and len(ev.payload["result_full"]) > 500:
                with st.expander("🔍 ver resultado completo"):
                    st.code(ev.payload["result_full"], language="text")

        elif ev.type == "final_answer":
            st.success("Resposta final pronta — será mostrada no chat.")
            st.markdown(ev.payload["text"][:300] + ("..." if len(ev.payload["text"]) > 300 else ""))

        st.caption(f"⏱️ {ev.timestamp.strftime('%H:%M:%S.%f')[:-3]}  |  evento: `{ev.type}`")


# =============================================================================
# Render chat — mensagens passadas
# =============================================================================

with col_chat:
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🚗"):
            st.markdown(
                "Olá! Eu sou o **InsurMind**, assistente da **Porto Inseguro** "
                "(seguradora fictícia) especializado em **seguro auto**. Posso te ajudar com:\n\n"
                "- 📚 **Dúvidas** sobre cobertura, franquia, sinistro, condições da apólice\n"
                "- 💰 **Cotação simulada** do seu seguro auto (preciso de alguns dados do veículo e do condutor)\n"
                "- 📞 **Encaminhamento** pra atendimento humano se for outro produto\n\n"
                "Como posso te ajudar hoje?"
            )

    # Histórico completo
    for i, m in enumerate(st.session_state.messages):
        avatar = "🚗" if m["role"] == "assistant" else None
        with st.chat_message(m["role"], avatar=avatar):
            # No modo debug, a última msg do assistant só aparece quando o usuário
            # avançou TODOS os steps. `remaining_steps == 0` significa que o passo
            # atual é o último (final_answer) e a resposta pode aparecer no chat.
            remaining_steps = (
                len(st.session_state.debug_events)
                - st.session_state.debug_step_index
                - 1
            )
            should_hide = (
                st.session_state.debug_mode
                and m["role"] == "assistant"
                and i == len(st.session_state.messages) - 1
                and remaining_steps > 0
            )
            if should_hide:
                st.info(
                    "📍 Modo Debug ativo — clique em **Próximo passo** no painel "
                    "lateral pra ver a resposta aparecer."
                )
            else:
                st.markdown(m["content"])


# =============================================================================
# Render painel debug — timeline step-by-step
# =============================================================================

if col_debug_panel is not None:
    with col_debug_panel:
        st.markdown("### 🪲 Painel Debug — passo a passo")
        st.caption(
            "Cada passo do agente é mostrado conforme você clica em **Próximo "
            "passo**. Use **Rodar até o fim** pra revelar todos de uma vez."
        )

        events = st.session_state.debug_events
        step_idx = st.session_state.debug_step_index

        if not events:
            st.info(
                "Faça uma pergunta no chat ao lado e os passos do agente "
                "aparecerão aqui."
            )
        else:
            # Renderiza eventos já revelados (verde) + atual (amarelo).
            # Quando o usuário já chegou ao último passo, NÃO há "atual" —
            # tudo é "concluído" (todos verdes).
            all_revealed = (step_idx >= len(events) - 1)
            for i, ev in enumerate(events[:step_idx + 1]):
                is_current = (i == step_idx) and not all_revealed
                _render_event(i, ev, is_current=is_current)

            # Botões de avanço
            remaining = len(events) - step_idx - 1
            if remaining > 0:
                next_ev = events[step_idx + 1] if step_idx + 1 < len(events) else None
                if next_ev:
                    label = f"▶ Passo {step_idx + 2}: {next_ev.short_description()}"
                    if st.button(label, key="btn_next", use_container_width=True):
                        st.session_state.debug_step_index += 1
                        st.rerun()
                if st.button(
                    f"⏩ Rodar até o final ({remaining} passos restantes)",
                    key="btn_skip",
                    use_container_width=True,
                ):
                    st.session_state.debug_step_index = len(events) - 1
                    st.rerun()
            else:
                st.success("✅ Conversa nesse turno concluída — pronto pra próxima pergunta.")


# =============================================================================
# Input do chat + execução
# =============================================================================

async def _run_turn(user_text: str) -> tuple[str, list[AgentEvent]]:
    """Roda o agente, coleta todos os events, devolve (resposta_final, events)."""
    history = st.session_state.messages + [{"role": "user", "content": user_text}]
    events: list[AgentEvent] = []
    final_text = ""
    async for ev in chat_stream_events(history):
        events.append(ev)
        if ev.type == "final_answer":
            final_text = ev.payload["text"]
    return final_text, events


if user_input := st.chat_input("Pergunte sobre seu seguro auto..."):
    # Mostra mensagem do usuário imediatamente
    with col_chat:
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant", avatar="🚗"):
            with st.spinner("InsurMind pensando..."):
                response_text, events = asyncio.run(_run_turn(user_input))

    # Salva no histórico + no debug log
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.session_state.debug_events = events
    # No modo debug, começa revelando só o primeiro passo; no modo normal, revela todos
    if st.session_state.debug_mode:
        st.session_state.debug_step_index = 0
    else:
        st.session_state.debug_step_index = len(events) - 1
    st.rerun()


# =============================================================================
# Rodapé
# =============================================================================

st.divider()
st.caption(
    "⚠️ **Disclaimer:** valores, regras e exemplos são simulados para fins acadêmicos "
    "(curso I2A2 InsurMinds, Atividade Obrigatória 2). **Porto Inseguro** é uma "
    "seguradora **fictícia** — o conteúdo da KB foi anonimizado a partir de "
    "materiais públicos de uma seguradora real."
)
