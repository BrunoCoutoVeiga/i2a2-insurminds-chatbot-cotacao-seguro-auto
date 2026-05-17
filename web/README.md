# InsurMind — UI Next.js

Frontend do chatbot **InsurMind** (Porto Inseguro fictícia, curso I2A2 InsurMinds). Caminho paralelo à UI Streamlit em [`../src/insurmind/ui.py`](../src/insurmind/ui.py) — **não a substitui**. Construída pra demo visual mais polida e pra viabilizar deploy cloud.

Consome o backend FastAPI em [`../src/insurmind/api.py`](../src/insurmind/api.py) via Server-Sent Events.

## Stack

- **Next.js 16.2.6** (Turbopack) + **React 19.2** + **TypeScript 5**
- **Tailwind CSS v4** + **shadcn/ui** (componentes pre-built)
- **React Flow v12** (`@xyflow/react`) — diagrama animado do Modo Debug com nodes customizados e edges bidirecionais
- **Inter** (sans) + **JetBrains Mono** (mono) via `next/font/google`

## Setup

### 1. Pré-requisitos

- Node.js 20+ (`winget install OpenJS.NodeJS.LTS` no Windows)
- Backend FastAPI rodando em `http://localhost:8000` — sem ele, a UI sobe mas o chat falha com "Backend indisponível".

### 2. Instalar deps e rodar dev server

```powershell
cd web
npm install            # primeira vez
npm run dev            # dev server em http://localhost:3000
```

### 3. Subir o backend (outro terminal)

```powershell
# Na raiz do repo (não em web/)
.\.venv\Scripts\Activate.ps1
uvicorn insurmind.api:app --port 8000 --reload
```

O backend lê `.env` da raiz — configurar `INSURMIND_LLM` (`anthropic_api` recomendado pra desenvolvimento da UI) + chave da API correspondente.

## Comandos úteis

```powershell
npm run dev            # dev server com hot reload (Turbopack)
npm run build          # production build + type check
npm run start          # serve o build de produção
npm run lint           # ESLint
```

## Arquitetura

### Estrutura

```
web/
├── app/
│   ├── layout.tsx              # root layout, fonts (Inter + JetBrains Mono)
│   ├── page.tsx                # client component — chat + painel debug lado a lado
│   └── globals.css             # Tailwind v4 + shadcn theme tokens
├── components/
│   ├── chat/
│   │   ├── ChatMessages.tsx    # lista de mensagens + welcome card
│   │   └── ChatInput.tsx       # input + Enviar + toggle Modo Debug inline
│   ├── debug/
│   │   ├── DebugPanel.tsx      # container: diagrama (topo) + timeline (corpo) + nav (rodapé)
│   │   ├── AgentDiagram.tsx    # React Flow: nodes, edges bidirecionais, ativação por passo
│   │   ├── AgentNode.tsx       # custom node Agent — 6 handles nomeados
│   │   ├── ToolNode.tsx        # custom node Tools/KB — 4 handles bidirecionais
│   │   ├── RagBadgeNode.tsx    # decorativo — zona RAG visual (retrieve_kb + ChromaDB)
│   │   └── EventCard.tsx       # card por evento — auto-scroll + auto-collapse
│   └── ui/                     # shadcn primitives (Button, Card, Input, Switch, Badge...)
├── lib/
│   ├── api.ts                  # parser SSE custom (POST /api/chat, regex CRLF-tolerant)
│   ├── types.ts                # tipos espelhando AgentEvent do backend
│   └── utils.ts                # cn() helper do shadcn
└── public/
    └── porto-inseguro-logo.jpg # logo fictícia da seguradora
```

### Fluxo de uma mensagem (Modo Debug ON)

```
User digita "O que é franquia?" + clica Enviar
       │
       ▼
app/page.tsx::sendMessage()
       │
       │ POST /api/chat com {messages: [...]}
       ▼
lib/api.ts::streamChat()       ← parser SSE custom
       │
       │ Recebe N eventos AgentEvent (8 no caso de FAQ com tool)
       ▼
collected[] preenche, finalText extraído do agent_delivering_answer_to_user
       │
       │ Resposta vai no chat (hidden até user revelar todos os passos)
       │ Eventos ficam disponíveis no painel debug pra navegação manual
       ▼
DebugPanel renderiza:
  - AgentDiagram acende nodes/edges do evento[stepIndex]
  - EventCard expandido pro evento atual (anteriores colapsam)
  - Botão "▶ Passo N+1: ..." pra avançar
```

### Decisão técnica — POST + SSE em vez de WebSocket ou GET + EventSource

| Opção | Tradeoffs | Escolha |
|---|---|---|
| `EventSource` nativo (GET only) | Não permite body — teria que serializar histórico na URL | ❌ |
| WebSocket | Overkill pro caso (one-shot turn-based), exige protocolo custom | ❌ |
| POST + SSE custom parser | Body limpo, SSE no return é nativo no `sse-starlette` | ✅ |

Parser em [lib/api.ts](lib/api.ts): `fetch` + `ReadableStream` + decoder UTF-8 + regex `/\r?\n\r?\n/` (sse-starlette usa CRLF; sem essa tolerância, todos os eventos vinham concatenados num único `data:`).

### Custom nodes do React Flow — por quê

Default nodes do `@xyflow/react` têm 1 source + 1 target handle. O Agent precisa conectar **bidirecionalmente em 3 lados** (User à esquerda, LLM em cima, Tools à direita) — não dá com defaults. Custom nodes:

- **`AgentNode`** — 6 handles: `from-user`, `to-user`, `to-llm`, `from-llm`, `to-tools`, `from-tools`.
- **`ToolNode`** — 4 handles: `from-agent`, `to-agent`, `to-kb`, `from-kb`. Reutilizado pro ChromaDB (os handles right ficam sem uso).
- **`RagBadgeNode`** — decorativo, sem handles. Renderiza retângulo tracejado com etiqueta "🧠 RAG" envolvendo retrieve_kb + ChromaDB. Acende em âmbar nos passos do retrieve.

### Edges bidirecionais

Cada par conectado tem 2 edges (forward + reverse). A forward sempre desenhada cinza-faded; a reverse só visível quando o passo atual aciona aquela direção. Resultado: **a seta sempre aponta no sentido REAL do fluxo daquele passo**.

| Passo | Direção da seta acesa |
|---|---|
| 1. `agent_received_user_input` | User → Agent |
| 2. `agent_sending_to_llm` | Agent → LLM |
| 3. `agent_received_tool_request_from_llm` | LLM → Agent |
| 4. `agent_executing_tool` | Agent → Tool (+ Retrieve → ChromaDB se RAG) |
| 5. `agent_received_tool_result` | Tool → Agent (+ ChromaDB → Retrieve se RAG) |
| 6. `agent_sending_tool_result_to_llm` | Agent → LLM |
| 7. `agent_received_text_from_llm` | LLM → Agent |
| 8. `agent_delivering_answer_to_user` | Agent → User |

## UX features didáticas do Modo Debug

- **Replay determinístico**: agente roda inteiro até o fim ANTES da UI replayar. Por isso o painel sabe "N passos restantes" com certeza.
- **Auto-scroll com `requestAnimationFrame`**: quando o passo atual muda, o card novo entra no campo de visão alinhado pelo topo. `rAF` garante que o reflow do layout (após expansão do card) já aconteceu.
- **Auto-collapse**: o card do passo anterior fecha automaticamente ao avançar.
- **Foco automático no input**: cursor já no campo no carregamento e quando o input destrava (após resposta).
- **Modo Debug ON por default**: é a feature didática central.
- **Toggle compacto no `ChatInput`**: libera espaço no header pro painel debug estender mais pra cima.

## Troubleshooting

**"Backend indisponível: Failed to fetch"**
Uvicorn não está rodando ou está em outra porta. Subir backend e F5.

**"CLIConnectionError: Failed to start Claude Code"**
O provider `claude_code` tentou spawnar `claude.exe` e falhou. Trocar pra `anthropic_api` no `.env` da raiz e restartar uvicorn — esse provider chama a API HTTPS direta, sem CLI.

**Header mostra `claude_code` mas o `.env` foi alterado**
Uvicorn não reiniciou. `Ctrl+C` no terminal do uvicorn e relançar; ele lê `.env` na importação do módulo `api.py`.

**Diagrama vazio ou sem animação**
Verificar que o backend está emitindo eventos via SSE: `curl -N -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"oi"}]}'` deve mostrar stream `event: ...\ndata: ...`.

## Deploy (Fase 4)

Backend → **Render** (free tier). Frontend → **Vercel** (free tier). Ambos integrados ao GitHub: `git push` na branch `main` → redeploy automático.

### Pré-requisitos

- Conta no GitHub (já existe — repo `BrunoCoutoVeiga/insurmind-chatbot`)
- Conta gratuita no Render (https://render.com — login via GitHub)
- Conta gratuita no Vercel (https://vercel.com — login via GitHub)
- Chave Anthropic API válida em `console.anthropic.com`

### Passo 1 — Deploy do backend no Render

O arquivo `render.yaml` na raiz do repo declara toda a config. Duas formas:

**Forma A (recomendada) — via Blueprint:**

1. Em https://dashboard.render.com, clique **"New +"** → **"Blueprint"**.
2. Selecione o repo `BrunoCoutoVeiga/insurmind-chatbot` (Render pede pra autorizar acesso via GitHub).
3. Render lê o `render.yaml` automaticamente e propõe a config — confirme.
4. Aguarde o **primeiro build** (~3-5 min — baixa o modelo e5-base e gera o índice ChromaDB).
5. O serviço falhará na primeira tentativa porque as secrets não foram configuradas. Vá em **"Environment"** e preencha:
   - `ANTHROPIC_API_KEY` → sua chave (cola em https://console.anthropic.com/settings/keys se ainda não tem)
   - `INSURMIND_CORS_ORIGINS` → deixar vazio por agora; preencher após o passo 2.
6. Em **"Manual Deploy"** → **"Deploy latest commit"** pra aplicar as secrets.
7. Quando o status virar **"Live"** (~2 min), copie a URL pública (formato: `https://insurmind-api-xxxx.onrender.com`).

**Forma B (manual) — sem Blueprint:** "New +" → "Web Service" e preencha cada campo conforme `render.yaml` indica (build/start commands, env vars).

**Validação:** abra `https://insurmind-api-xxxx.onrender.com/api/health` no browser. Deve retornar JSON `{"status":"ok","provider":"anthropic_api","tools_count":3}`.

**Cold start:** após 15min de inatividade, o serviço dorme. Primeira requisição depois disso demora ~30-60s pra acordar. Aceitável pra demo acadêmica.

### Passo 2 — Deploy do frontend no Vercel

1. Em https://vercel.com/dashboard, clique **"Add New..."** → **"Project"**.
2. Importe o repo `BrunoCoutoVeiga/insurmind-chatbot` (Vercel pede pra autorizar GitHub).
3. Configure:
   - **Framework Preset:** Next.js (auto-detectado)
   - **Root Directory:** `web` (importante! o repo tem outras pastas que não são Next.js)
   - **Build Command:** deixa o padrão (`next build`)
   - **Environment Variables:**
     - `NEXT_PUBLIC_API_BASE` = URL do Render do passo 1 (ex.: `https://insurmind-api-xxxx.onrender.com`)
4. Clique **"Deploy"** e aguarde (~2 min).
5. Quando concluído, Vercel mostra a URL pública (formato: `https://insurmind-chatbot-xxxx.vercel.app`).

### Passo 3 — Conectar os dois (configurar CORS)

O backend tem que permitir requisições vindas do Vercel. De volta ao Render:

1. Vá no serviço `insurmind-api` → **"Environment"**.
2. Edite `INSURMIND_CORS_ORIGINS` e cole a URL do Vercel (sem barra no final):
   ```
   https://insurmind-chatbot-xxxx.vercel.app
   ```
3. Salvar → Render reinicia automaticamente o serviço (~1 min).

### Passo 4 — Smoke test em produção

1. Abra a URL do Vercel no browser.
2. Aguarde 30-60s no primeiro request (cold start do Render).
3. Faça uma pergunta: "o que é prêmio?".
4. Verifique:
   - Resposta aparece com citação de fonte
   - Modo Debug mostra os passos do agente
   - Diagrama anima com setas direcionais
5. No Render → **"Logs"**, deve aparecer o logging estruturado (RAG, tools, anthropic_api).

### Limites e proteções recomendadas

- **Limite de gasto na Anthropic**: configure em `console.anthropic.com/settings/limits`. Sem isso, alguém que descobrir sua URL pode esgotar sua chave. Recomendado: $5-10/mês como teto.
- **URL "obscura"**: a URL do Vercel é pseudo-aleatória e difícil de descobrir, mas qualquer um com o link consegue usar. Sem auth implementada.
- **CORS** já protege contra sites maliciosos chamarem seu backend — só o domínio do Vercel é permitido.
- **Free tier limits**: Render = 750h/mês (1 serviço cabe folgado). Vercel = 100GB bandwidth/mês (consumo típico de demo é < 1GB).
