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

# InsurMind Chatbot

Chatbot conversacional de **atendimento ao segurado de automóveis** em PT-BR — entrega da **Atividade Obrigatória 2** do curso de **Agentes de IA da I2A2 (turma InsurMinds)**.

> ⚠️ A seguradora **"Porto Inseguro"** é **fictícia**. Conteúdo da base de conhecimento foi anonimizado a partir de materiais públicos de uma seguradora real brasileira, para fins exclusivamente acadêmicos.

## Sobre este Space

Este HuggingFace Space hospeda o **backend FastAPI** do chatbot. O frontend Next.js fica em [Vercel](https://insurmind-chatbot.vercel.app).

### Endpoints públicos

- `GET /api/health` — healthcheck (retorna `{status, provider, tools_count}`)
- `GET /api/info` — metadados (provider ativo, tools disponíveis, CORS origins)
- `POST /api/chat` — stream SSE de eventos do agente (consumido pelo frontend)

### Arquitetura

```
[Vercel Next.js UI] ←─SSE─→ [HF Spaces FastAPI] ←─→ [Anthropic API]
                                    ↓
                            [retrieve_kb tool]
                                    ↓
                            [ChromaDB local + e5-base]
                                    ↓
                            [KB Porto Inseguro tiered:
                             porto-glossario (primary)
                             porto-cg + porto-faq (primary)
                             SUSEP + FENACOR (fallback)]
```

3 tools registradas:
- `retrieve_kb` — busca semântica tieirizada na KB (Porto primary, SUSEP/FENACOR fallback)
- `compute_quote_mock` — cotação simulada com 13 campos
- `escalar_humano` — encaminhamento humano para questões fora de escopo

### Secrets necessários (configurar no painel do Space)

| Variável | Descrição |
|---|---|
| `ANTHROPIC_API_KEY` | Chave da Anthropic API (obtém em [console.anthropic.com](https://console.anthropic.com/settings/keys)) |
| `INSURMIND_CORS_ORIGINS` | URL do frontend (ex.: `https://insurmind-chatbot.vercel.app`) |

### Stack técnica

- **Python 3.12**, FastAPI, uvicorn, sse-starlette
- **Anthropic API** (modelo `claude-sonnet-4-5`) com loop manual de tool calls
- **ChromaDB** + `intfloat/multilingual-e5-base` em fp16 pra retrieval semântico
- **8 eventos agent-centric** em gerúndio narrando cada passo (`agent_received_user_input`, `agent_sending_to_llm`, etc.) — base do Modo Debug step-by-step da UI

### Código-fonte

Repositório completo no GitHub: [BrunoCoutoVeiga/insurmind-chatbot](https://github.com/BrunoCoutoVeiga/insurmind-chatbot)

Detalhes técnicos, decisões de arquitetura e log de desenvolvimento em [RELATORIO.md](https://github.com/BrunoCoutoVeiga/insurmind-chatbot/blob/main/RELATORIO.md).
