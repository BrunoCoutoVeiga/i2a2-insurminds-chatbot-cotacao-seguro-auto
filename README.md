---
title: InsurMind API
emoji: 🚗
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Backend FastAPI do chatbot acadêmico InsurMind (seguro auto)
---

# InsurMind — Chatbot de Atendimento ao Segurado Auto

> Chatbot conversacional em PT-BR que combina **RAG**, **tool calling** e **modo debug visual** pra demonstrar arquitetura de agentes LLM. Entrega da **Atividade Obrigatória 2** do curso de Agentes de IA da [I2A2 Academy](https://i2a2.academy) — turma InsurMinds.

## 🌐 Demo ao vivo

**[https://insurminds-chatbot.vercel.app](https://insurminds-chatbot.vercel.app)**

> ⚠️ Primeira pergunta com RAG pode demorar 30-60s (cold start do modelo de embedding). Depois fica instantâneo.

## O que ele faz

Atende **3 tipos de pergunta** de um segurado de seguro auto:

1. **Dúvidas factuais** sobre o produto (franquia, cobertura, sinistro, prazos) — responde com base na KB oficial, **citando fonte** sempre.
2. **Cotação simulada** — coleta 13 informações em 4 turnos conversacionais e devolve 3 opções de franquia (reduzida / normal / aumentada).
3. **Encaminhamento humano** — questões fora de escopo (outros produtos de seguros, alterações contratuais, reclamações formais) viram protocolo de atendimento.

E pra perguntas **fora do domínio de seguros** (clima, código, opinião) — refuse educado, sem inventar.

> 🎭 **A seguradora "Porto Inseguro" é fictícia.** Toda a base de conhecimento foi sistematicamente anonimizada a partir de materiais públicos de uma seguradora brasileira real. O CG, FAQ, telefones, CNPJ e URLs foram substituídos por placeholders. Detalhes em [`scripts/anonymize_porto.py`](scripts/anonymize_porto.py).

## 🪲 Modo Debug — diferencial técnico

A UI tem um **painel de debug step-by-step** que mostra cada decisão do agente em tempo real:

- **Diagrama animado** (React Flow) com User → Agente → LLM → Tools → ChromaDB
- **Setas direcionais** acendem na direção real do fluxo a cada passo (LLM→Agente quando recebendo resposta, Agente→Tool quando executando, etc.)
- **8 eventos agent-centric** narrados em gerúndio (`agent_received_user_input`, `agent_sending_to_llm`, `agent_executing_tool`, etc.)
- **Zona RAG** destacada visualmente com retângulo tracejado em `consultar_porto_inseguro` + `ChromaDB`
- **JSON cru de cada evento** acessível pra inspeção técnica

Pedagogicamente alinhado com a aula 6 do curso (Prof. Onelio Ceabra) sobre observabilidade de agentes.

## 🏗️ Arquitetura

```
[Usuário]
   ↓
[Frontend Next.js (Vercel)]
   ↓ HTTPS POST + SSE stream
[Backend FastAPI (HuggingFace Spaces, Docker)]
   ↓
[Agente — orquestrador]
   ├─→ [Anthropic API] (claude-sonnet-4-5, loop manual de tool calls)
   ├─→ [consultar_porto_inseguro] — RAG tieirizado
   │      └─→ [ChromaDB] (312 chunks com embeddings e5-base fp16)
   │            ├─ tier primary: porto-glossario + porto-cg + porto-faq
   │            └─ tier fallback: SUSEP-glossario + SUSEP-cartilha + FENACOR
   ├─→ [cotar_seguro_auto] — mock de cotação (3 opções de franquia)
   └─→ [encaminhar_atendimento] — protocolo pra atendimento humano
```

## 🧱 Stack técnica

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 16 + React 19 + TypeScript 5 + Tailwind v4 + shadcn/ui + React Flow v12 |
| Backend | Python 3.12 + FastAPI + uvicorn + sse-starlette |
| LLM | Anthropic API (`claude-sonnet-4-5`) com 3 providers agnósticos (`anthropic_api`, `gemini`, `claude_code`) |
| RAG | ChromaDB + `intfloat/multilingual-e5-base` (fp16) + retrieval tieirizado próprio |
| Deploy | Vercel (frontend) + HuggingFace Spaces (backend Docker, 16GB RAM free tier) |

## 🚀 Como rodar localmente

> 💡 **Setup do zero em máquina nova?** Veja o guia detalhado em **[docs/setup-new-machine.md](docs/setup-new-machine.md)** — passo-a-passo completo desde instalação de Python/Node/Git até primeira execução, com troubleshooting.

### Pré-requisitos

- Python 3.12+
- Node.js 20+ (LTS)
- Chave da Anthropic API ([console.anthropic.com](https://console.anthropic.com/settings/keys))

### Setup

```powershell
# 1. Clonar
git clone https://github.com/BrunoCoutoVeiga/i2a2-insurminds-chatbot-cotacao-seguro-auto.git
cd i2a2-insurminds-chatbot-cotacao-seguro-auto

# 2. Backend Python
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # (macOS/Linux: source .venv/bin/activate)
pip install -e .

# 3. Configurar .env
cp .env.example .env
# Edite .env e cole sua ANTHROPIC_API_KEY

# 4. Ingerir a base vetorial (1x, ~3-5 min na primeira execução pra baixar modelo)
python scripts/ingest_kb.py

# 5. Subir o backend (porta 8000)
uvicorn insurmind.api:app --port 8000 --reload
```

Em outro terminal:

```powershell
# 6. Frontend Next.js (porta 3000)
cd web
npm install
npm run dev
```

Aí abre `http://localhost:3000` no browser.

### Smoke test sem UI

```powershell
python -m insurmind.agent "O que é franquia?"
```

## 📁 Estrutura do repositório

```
chatbot/
├── README.md                       # Este arquivo
├── RELATORIO.md                    # Log detalhado de desenvolvimento (entregável avaliado)
├── CLAUDE.md                       # Instruções internas do projeto pra o Claude Code
├── LICENSE                         # MIT
├── Dockerfile                      # Build do backend pro HuggingFace Spaces
├── pyproject.toml                  # Dependências Python
│
├── src/insurmind/                  # Código do backend
│   ├── agent.py                    # Orquestrador agente-centric (8 eventos em gerúndio)
│   ├── api.py                      # FastAPI + SSE
│   ├── prompts.py                  # System prompt (persona, escopo, guardrails)
│   ├── tools.py                    # 3 tools: consultar_porto_inseguro, cotar_seguro_auto, encaminhar_atendimento
│   ├── rag.py                      # Retrieval tieirizado em Chroma
│   ├── quote.py                    # Motor mock de cotação (13 campos → 3 opções)
│   ├── events.py                   # AgentEvent dataclass (8 EventTypes)
│   ├── ui.py                       # UI Streamlit alternativa (legacy)
│   └── llm/                        # Camada de providers agnósticos
│       ├── anthropic_api.py        # Provider default em produção
│       ├── claude_code.py          # Provider dev local (sem custo)
│       └── gemini.py               # Provider alternativo (free tier generoso)
│
├── web/                            # Frontend Next.js
│   ├── app/page.tsx                # Chat + painel debug
│   └── components/
│       ├── chat/                   # Bolhas, input, mensagens
│       └── debug/                  # Diagrama React Flow + timeline de eventos
│
├── data/
│   ├── kb/                         # Base de conhecimento curada (markdown anonimizado)
│   │   ├── 08-porto-condicoes-gerais.md       # Porto Inseguro CG142
│   │   ├── 09-porto-faq.md                    # FAQ Porto Inseguro Auto (97 Q&A)
│   │   ├── 10-porto-glossario.md              # Glossário próprio (12 termos centrais)
│   │   ├── 07-cartilha-susep.md               # Cartilha SUSEP 2006
│   │   ├── 02-glossario.md                    # Glossário SUSEP
│   │   └── 06-fenacor-glossario.md            # Glossário FENACOR
│   └── raw/                        # Texto bruto antes da anonimização (audit trail)
│
├── scripts/
│   ├── ingest_kb.py                # Chunk + embed + carga no Chroma
│   ├── fetch_porto_faq.py          # Pipeline de scraping FAQ (uso 1x)
│   ├── build_porto_faq_md.py       # Parser HTML → markdown
│   └── anonymize_porto.py          # Anonimização Porto Seguro → Porto Inseguro
│
└── docs/
    ├── visao-geral-do-chatbot.md   # Apresentação pro grupo (não-técnica)
    └── aulas/                      # Análises das aulas 4, 5, 6 do curso
```

## 👥 Equipe

- **Bruno Couto Veiga** — frente técnica (este repositório)
- **João Carlos** — planejamento + tarifador
- **Adriele** — especialista em seguros (consultoria sobre regras realistas)
- **Victor (vicTmm)** — repositório paralelo do grupo
- **+ 1 membro do grupo**

## 📚 Documentação detalhada

- **[RELATORIO.md](RELATORIO.md)** — log completo de desenvolvimento com decisões, opções consideradas, tradeoffs e justificativas (entregável principal pro professor)
- **[docs/visao-geral-do-chatbot.md](docs/visao-geral-do-chatbot.md)** — visão não-técnica pro grupo
- **[docs/setup-new-machine.md](docs/setup-new-machine.md)** — guia completo pra setup do projeto em máquina nova (do zero, com tudo a instalar)
- **[CLAUDE.md](CLAUDE.md)** — instruções internas pra desenvolvedores (assistentes de IA)
- **[web/README.md](web/README.md)** — setup específico do frontend

## ⚖️ Licença

MIT — ver [LICENSE](LICENSE).

## 🔗 Links importantes

- **Demo ao vivo (UI)**: https://insurminds-chatbot.vercel.app
- **Backend ao vivo (API)**: https://bveiga-insurminds-api.hf.space
- **Healthcheck**: https://bveiga-insurminds-api.hf.space/api/health
- **HF Space (Docker source)**: https://huggingface.co/spaces/bveiga/insurminds-api
