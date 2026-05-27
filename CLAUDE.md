# InsurMind Chatbot

Chatbot conversacional de **atendimento ao segurado de automóveis** em PT-BR — três fluxos: tirar dúvidas (RAG), cotação simulada e encaminhamento humano. Entrega do curso de **Agentes de IA da I2A2 — turma InsurMinds** (Atividade Obrigatória 2).

**Equipe (5 membros):** Bruno (técnica), João Carlos (técnica + planejamento), Adriele (especialista em seguros), Victor (criou o repo do grupo), + 1 membro não nomeado.
**Deadline:** 2026-05-29 (entrega obrigatória, eliminatória).
**Resultados:** anunciados até 2026-06-01.

---

## 🚀 PRIMEIRA EXECUÇÃO NESTA MÁQUINA? Leia isto antes.

> Esta seção é direcionada a você, **Claude Code**, ao ser executado pela primeira vez nesta cópia do projeto. Bruno está provavelmente migrando o projeto pra esta máquina e espera que VOCÊ conduza o setup a partir daqui.

### 1. Checagem rápida do estado do ambiente local

Rode esses comandos pra detectar se o setup já foi feito ou se a máquina está virgem:

```powershell
# Diretório atual deve ser a raiz do projeto (tem CLAUDE.md, pyproject.toml, etc.)
ls CLAUDE.md pyproject.toml Dockerfile          # confirma que clonou certo

# Esses 4 indicam setup completo. Se algum NÃO existir, é máquina nova.
ls .venv                                        # virtualenv Python
ls .chroma                                      # base vetorial ChromaDB
ls .env                                         # secrets (ANTHROPIC_API_KEY etc.)
ls web\node_modules                             # deps do frontend Next.js
```

### 2. Se a máquina está virgem (algum dos 4 acima faltou)

Existem **2 cenários** dependendo de quais arquivos sobreviveram:

**Cenário A — `.env` E `.chroma/` faltam (clone limpo do GitHub)**

Bruno fez `git clone` numa máquina virgem. **Conduza-o pelo `docs/setup-new-machine.md` → "Caminho A"** (~60-90 min: instalar Git/Python/Node via winget, configurar `.env`, rodar `ingest_kb.py`, validar). Detalhes a ressaltar:
- O `.env` precisa ser **recriado manualmente** com `ANTHROPIC_API_KEY` (gera em https://console.anthropic.com/settings/keys se Bruno não tiver salva).
- O remote `hf` **não vem do clone** do GitHub: `git remote add hf https://huggingface.co/spaces/bveiga/insurminds-api`.

**Cenário B — `.env` e `.chroma/` EXISTEM, mas `.venv/` ou `web/node_modules/` faltam (cópia via rede)**

Bruno copiou a pasta inteira da máquina antiga via rede/USB e deletou as pastas que não migram bem (paths hardcoded). **Conduza-o pelo `docs/setup-new-machine.md` → "Caminho B"** (~15-20 min: só recriar `.venv` + `node_modules`).

Confira nesse cenário:
- `git remote -v` deve mostrar `origin` (GitHub) e `hf` (HF Space) — vieram do `.git/` copiado.
- `.env` deve estar preenchido (veio da cópia).
- `.chroma/` deve ter os 312 chunks ingeridos (não precisa re-rodar `ingest_kb.py`).

**Em ambos os cenários**:
- Esta máquina tem **RTX 5060 Ti 16GB**. O setup default usa CPU+fp16 (funciona, mas embedding lento ~10-15s na primeira query). Há uma seção "Bônus — Sua RTX 5060 Ti" em `docs/setup-new-machine.md` mostrando como ativar PyTorch CUDA pra ~10x mais velocidade — **mas só aplique DEPOIS do setup CPU básico validado**.

### 3. Se a máquina já está pronta (os 4 itens existem)

Bruno provavelmente quer **continuar o desenvolvimento de onde parou**. Diagnóstico:

```powershell
git status                # mudanças pendentes?
git log --oneline -5      # últimos commits (referência do estado)
git remote -v             # confirma origin (GitHub) e hf (HuggingFace Space)
```

Pergunte ao Bruno o que ele quer fazer. URLs importantes pra contexto:
- **Demo ao vivo (UI)**: https://insurminds-chatbot.vercel.app
- **Backend ao vivo (API)**: https://bveiga-insurminds-api.hf.space
- **Repo público (entrega)**: https://github.com/BrunoCoutoVeiga/i2a2-insurminds-chatbot-cotacao-seguro-auto
- **Repo HF Space (Docker source)**: https://huggingface.co/spaces/bveiga/insurminds-api

### 4. Estado de entrega (snapshot 2026-05-19)

O trabalho está **considerado concluído** pra entrega ao professor. Sumário detalhado em `RELATORIO.md` seção "3. Estado de entrega". TL;DR:
- ✅ Todos os 6 critérios de "pronto" do plano original atingidos
- ✅ Deploy ativo: frontend Vercel + backend HuggingFace Spaces
- ✅ Anti-prompt-injection (renomeação de tools + regra no system prompt)
- ✅ Anonimização Porto Seguro → Porto Inseguro 100% (verificado com grep adversarial)
- ✅ **Tarifador real do grupo integrado em 2026-05-26** (`Precificador_Seguro_Automóvel_v2.0.xlsx`). Compilado pra `src/insurmind/quote_tables.py` via `scripts/import_precificador.py`. Contrato passou de 13 → 10 campos. Smoke test bate ao centavo com a planilha (R$ 6.974,66/ano).

Se Bruno estiver continuando dev, prováveis frentes ainda em aberto:
- QA conversacional adicional (10 FAQs do DoD + cenários novos da cotação real)
- Slides de apresentação (10-12 slides — feito fora do repo)
- Melhorias técnicas pós-entrega: ativar GPU, ONNX, embeddings via API externa, etc.

---

## Origem deste repositório

Extraído em 2026-05-14 do projeto `transcribe_yt` (em `C:\Bruno\OneDrive - Rede D'Or\05.Pessoal\Projetos\transcribe_yt`), que ficou responsável apenas pelo pipeline de transcrição de videoaulas.

As **análises das aulas** que motivaram o escopo deste produto foram copiadas para [docs/aulas/](docs/aulas/) como referência imutável.

O **plano técnico aprovado por Bruno** vive em `C:\Users\Bruno\.claude\plans\eu-perdi-o-v-deo-quirky-pinwheel.md`. O **plano de planejamento do grupo** (escrito pelo João pós-reunião 14/05) listava 5 frentes, propunha stack alternativa (rejeitada — ver "Stack" abaixo) e fixava as 3 sprints. O PDF original ficava em `meetings/` mas foi removido em 2026-05-19 na limpeza pré-entrega (conteúdo proprietário não cabe em repo público).

**Workflow com `transcribe_yt`:** quando uma aula nova for liberada → rodar `transcribe-yt one aula-NN` no repo `transcribe_yt`, copiar a análise resultante para [docs/aulas/](docs/aulas/) aqui e atualizar este `CLAUDE.md` se mudar o escopo. Para auditoria de citação ("o prof. disse X"), o `.srt` com timestamps está em `transcribe_yt/transcricoes/`.

## Equipe e repositórios

- **Bruno** (este repo) — codificação + arquitetura. Toda a frente F2 (RAG & Backend LLM) fica com Bruno, com apoio do Claude Code.
- **João Carlos** — escreve o planejamento do grupo, trabalha no tarifador junto com Adriele. Frentes F1, F3, F5 (compartilhadas).
- **Adriele** — especialista em seguros (trabalha em corretora). Define junto com João Carlos os fatores realistas do tarifador (modelos, faixas etárias, taxas, fatores de agravamento).
- **Victor (vicTmm)** — criou um repo grupal em [github.com/vicTmm/i2a2-chatbot-seguro-auto](https://github.com/vicTmm/i2a2-chatbot-seguro-auto). **Decisão atual:** Bruno continua trabalhando neste repo local; se o repo do Victor virar a melhor opção mais à frente, migra-se. Por enquanto não há push pra lá.
- **Quinto membro** — papel não definido na ata.

Comunicação do grupo: **WhatsApp** (canal não-versionado).

## Cronograma (do plano do João)

| Sprint | Datas | Marco |
|---|---|---|
| Sprint 0 | 13-14/05 | Alinhamento — concluída |
| **Sprint 1** | **15-21/05** | **Em curso.** Marco: 1 FAQ via RAG + 1 cotação mock funcionando até 21/05. |
| Sprint 2 | 22-27/05 | Integração e polimento. **Feature freeze 27/05.** |
| Sprint 3 | 28-29/05 | QA, doc final, ensaio. **Entrega 29/05.** |

**Hoje é 2026-05-16** — Sprint 1, dia 2 de 7.

## Como colaborar com Bruno

Bruno é desenvolvedor experiente; pede explicações didáticas quando o conceito é novo (RAG, system prompt, tool calling, embeddings). Quando isso acontecer, explicar **concretamente no contexto deste projeto**, não em abstrato — apontar arquivos, fluxo de dados, decisões já tomadas.

**Preferências de execução:**

- **Executar diretamente** em vez de criar scaffolding/prompts pra outra LLM rodar depois. O Claude Code já é a LLM — qualquer camada de indireção é desnecessária.
- Não criar pasta `prompts/` no repositório. Ler insumos, produzir artefatos finais inline.
- Atualizar artefatos versionados (`RELATORIO.md`, `data/kb/`, `src/`, `CLAUDE.md`) à medida que decisões são tomadas, sem pedir confirmação repetida.
- **Espelhar memória durável neste `CLAUDE.md`**: ao salvar ou atualizar uma memória, avaliar se o conteúdo é princípio durável do projeto (decisão técnica, workflow, regra de engenharia → sim, promover ao `CLAUDE.md` com redação adaptada) ou preferência puramente conversacional (tom/brevidade → memória basta). Memória é fonte interna; `CLAUDE.md` é a versão pública e sobrevive a troca de máquina.

**Contexto temporal do curso:**

- A **Atividade 1** já foi entregue (anterior a este trabalho).
- Esta **Atividade 2** foi apresentada pelo professor nas **aulas 4 e 5** e reforçada na **aula 6** (com o convidado **Onelio Ceabra**, que validou o método Vibe Code e enfatizou guardrails + padrão conversacional).
- **Reunião do grupo em 14/05** consolidou o escopo (3 fluxos), validou Opção A (Python), e dividiu frentes. Transcrição originalmente em `meetings/20260514.txt` — pasta removida na limpeza pré-entrega (audit trail interno fora do repo público).

## Escopo do chatbot (3 fluxos)

O chatbot é **de atendimento ao segurado**, não apenas cotação. Três fluxos:

```
Usuário → [ Chat UI Streamlit ] → [ Agente / Router de intent ]
                                    ├── intent = FAQ / dúvida    → [ RAG: Chroma + e5-base ] → [ LLM ] → resposta
                                    ├── intent = cotação         → [ Coleta progressiva de dados ] → [ tool compute_quote ] → resposta
                                    └── intent = fora de escopo  → mensagem de encaminhamento humano
```

**Critérios de "pronto" (do plano do João):**

1. Bot responde 10 perguntas de FAQ com **fonte citada** e sem alucinar.
2. Bot completa fluxo de cotação coletando todos os dados e devolve **3 opções de preço com franquia**.
3. Bot encaminha pergunta fora de escopo com mensagem clara.
4. Repo público com README executável por terceiro.
5. Doc técnica e slides revisados pelos 5 e versionados.
6. Demo ao vivo (ou vídeo) funciona do início ao fim sem intervenção manual.

**Fora de escopo (não fazer):**

- Integração real com API de seguradora ou cotador de mercado.
- Integração com CRM, histórico anonimizado de tickets (opcionais do PDF — descartados).
- Multi-ramo. Apenas auto neste MVP.
- Autenticação, persistência entre sessões, banco transacional. Contexto só dentro da sessão.

## Stack

**Backend (Python 3.12):**
- **Agente**: arquitetura agnóstica — 3 providers implementados:
  - `claude_code` (default em CLI) — `claude-agent-sdk` spawna a CLI local do Claude Code. Autodispatch de tools via MCP (pula passos 5+6 do Modo Debug).
  - `anthropic_api` — SDK `anthropic` chamando a API HTTPS direta, loop manual de tool calls. Sem dependência de binário CLI → único viável pra deploy cloud.
  - `gemini` — Google GenAI SDK, loop manual de tool calls.
- **Vector store**: ChromaDB local.
- **Embeddings**: `intfloat/multilingual-e5-base` via `sentence-transformers` (PT-BR-friendly, sem custo, local).
- **API HTTP**: FastAPI + sse-starlette (Server-Sent Events pra streamar eventos do agente).

**UIs (duas, em paralelo — Streamlit não foi descontinuada):**
- **Streamlit** (`src/insurmind/ui.py`) — UI didática integrada ao pacote Python, ideal pra demo standalone (`streamlit run`).
- **Next.js 16 + React 19 + Tailwind v4 + shadcn/ui** (`web/`) — UI moderna com diagrama animado React Flow do Modo Debug. Consome o backend FastAPI via SSE.

**Stack proposta pelo João descartada explicitamente:** OpenAI `gpt-4o-mini` + `text-embedding-3-small` (OpenAI) + **LangChain**. Por quê:

- A arquitetura agnóstica do Bruno (factory de providers) já cobre o objetivo de "trocar de LLM sem reescrever" — LangChain seria uma camada **competidora** de abstração, não complementar.
- LangChain adiciona ~200 dependências, quebra API entre versões, esconde comportamento.
- `gpt-4o-mini` tem custo e requer API key OpenAI — `claude-agent-sdk` local é gratuito durante desenvolvimento.
- `text-embedding-3-small` é OpenAI (custo + cloud); `e5-base` é local, free, e melhor em PT-BR.

Trocar de motor de inferência (Claude → OpenAI → Gemini → Ollama) é uma mudança localizada (1 arquivo em `src/insurmind/llm/`), preservando todo o resto do código.

## Arquitetura agnóstica (decisão central)

O agente **não pode ficar acoplado** ao Claude Agent SDK. A escolha do motor é feita via env var `INSURMIND_LLM` pela factory em `src/insurmind/llm/__init__.py`. Implementações ficam em `src/insurmind/llm/<motor>.py`:

- `claude_code.py` — default em CLI. Claude Code SDK local, autodispatch de tools via MCP. **Limitação**: requer `claude.exe` no PATH e faz autodispatch — pula passos 5+6 do Modo Debug.
- `anthropic_api.py` — Anthropic API direta via SDK `anthropic`. Loop manual de tool calls. Sem CLI → funciona em deploy cloud. Requer `ANTHROPIC_API_KEY` em `.env`. Default model: `claude-sonnet-4-5` (override via `ANTHROPIC_MODEL`).
- `gemini.py` — Google Gemini API. Loop manual de tool calls. Requer `GEMINI_API_KEY` em `.env` (free tier em https://aistudio.google.com/apikey: 15 req/min, 1500 req/dia). Default model: `gemini-2.5-flash`.
- `ollama.py` — stub com `NotImplementedError` (sinaliza o contrato pra implementação futura).

**Default em produção (web)**: `anthropic_api`. Default na CLI Python: `claude_code` (gratuito durante dev se o usuário tiver Claude Code instalado e logado).

Tools são definidas em formato agnóstico (`Tool` dataclass em `src/insurmind/llm/base.py`) — `name`, `description`, `parameters_schema` (JSON Schema), `handler` async. Cada provider traduz para o formato nativo do motor (no Claude SDK: `@tool` + `create_sdk_mcp_server`).

**Sem LangChain ou LiteLLM**, decisão deliberada. A camada própria em `src/insurmind/llm/` tem ~150 linhas, é explícita e auditável. Para banca, "Vibe Code visível" é vantagem; para evolução, troca de provider é 1 arquivo.

**Como estender:**
- Para uma nova tool: registrar em `tools.py` como `Tool` agnóstico — `ClaudeCodeProvider` traduz automaticamente.
- Para um novo provider: implementar `chat()` no formato `AsyncIterator[TextDelta | ToolCall]` e adicionar branch em `make_provider()`.

## Estrutura

```
chatbot/
├── README.md                       # uso, setup, screenshots (TODO)
├── RELATORIO.md                    # log de trabalho + relatório de entrega
├── DIAGRAMA.md                     # arquitetura em Mermaid (TODO)
├── pyproject.toml
├── .env.example
├── data/
│   ├── kb/                         # corpus (markdown) consumido pelo RAG
│   │   ├── 02-glossario.md         # ✅ SUSEP verbatim + sintético (fallback)
│   │   ├── 06-fenacor-glossario.md # ✅ FENACOR ~85 termos (fallback)
│   │   ├── 07-cartilha-susep.md    # ✅ Cartilha SUSEP 2006 (fallback)
│   │   ├── 08-porto-condicoes-gerais.md  # ✅ Porto Inseguro CG142 — FONTE PRIMÁRIA
│   │   ├── 09-porto-faq.md         # ✅ FAQ Porto Auto, 97 Q&A em 6 categorias — FONTE PRIMÁRIA
│   │   └── 10-porto-glossario.md   # ✅ 12 termos centrais definidos no estilo Porto (criado 2026-05-17 pra resolver "Porto tem o conceito mas não tem a DEFINIÇÃO")
│   ├── raw/                        # arquivos brutos baixados
│   │   ├── 06-fenacor-glossario.txt
│   │   ├── 07-cartilha-susep.pdf
│   │   └── 07-cartilha-susep-raw.txt
│   └── tarifador/                  # ⏳ Excel do João Carlos + Adriele (a integrar)
├── docs/
│   ├── visao-geral-do-chatbot.md   # ✅ apresentação ao grupo (não-técnica, 2026-05-16)
│   └── aulas/                      # análises das aulas (snapshot)
│       ├── aula-04-trabalho.md
│       ├── aula-05-trabalho.md
│       └── aula-06-trabalho.md
# (pasta meetings/ removida em 2026-05-19 — continha material proprietário
#  Porto Seguro real + transcrições internas do grupo. Repo público não deve
#  hospedar isso. Conteúdo migrado pra audit local fora do repo.)
├── src/insurmind/
│   ├── __init__.py
│   ├── agent.py                    # ✅ orquestrador agnóstico (chat_stream_events emite 8 eventos agent-centric)
│   ├── api.py                      # ✅ FastAPI + SSE — backend HTTP da UI Next.js
│   ├── prompts.py                  # ✅ system prompt
│   ├── tools.py                    # ✅ 3 tools: consultar_porto_inseguro, cotar_seguro_auto, encaminhar_atendimento (nomes neutros desde 2026-05-18 — antes eram retrieve_kb / compute_quote_mock / escalar_humano, renomeados após descoberta de info disclosure via meta-pergunta)
│   ├── llm/                        # ✅ camada agnóstica
│   │   ├── base.py
│   │   ├── claude_code.py          # ✅ autodispatch via MCP (default CLI; limitação: pula passos 5+6 do debug)
│   │   ├── anthropic_api.py        # ✅ API direta, loop manual (default web; funciona em deploy cloud)
│   │   ├── gemini.py               # ✅ free tier, loop manual (alternativa free pra debug completo)
│   │   └── ollama.py               # stub
│   ├── rag.py                      # ✅ retrieval tieirizado em Chroma (primary Porto / fallback SUSEP+FENACOR)
│   ├── quote.py                    # ✅ motor real (tarifador v2.0 do grupo, integrado 2026-05-26) com 10 campos → 3 opções variando franquia
│   ├── quote_tables.py             # ✅ tabelas geradas a partir de Precificador_Seguro_Automóvel_v2.0.xlsx (NÃO EDITAR — regerar via scripts/import_precificador.py)
│   ├── events.py                   # ✅ AgentEvent — 8 EventTypes agent-centric (gerúndio, agente como sujeito)
│   └── ui.py                       # ✅ Streamlit chat multi-turno + Modo Debug step-by-step funcional
├── web/                            # ✅ UI Next.js 16 (paralela à Streamlit)
│   ├── app/page.tsx                # ✅ chat + painel debug lado a lado
│   ├── components/
│   │   ├── chat/                   # ✅ ChatMessages, ChatInput (com toggle Modo Debug inline)
│   │   └── debug/                  # ✅ DebugPanel, EventCard (auto-scroll + auto-collapse),
│   │                               #     AgentDiagram (React Flow com edges bidirecionais),
│   │                               #     AgentNode/ToolNode (custom nodes, 4+ handles),
│   │                               #     RagBadgeNode (zona RAG visual didática)
│   ├── lib/{api,types,utils}.ts    # ✅ parser SSE (com fix CRLF), types espelhando backend
│   └── public/porto-inseguro-logo.jpg
├── scripts/                        # data prep + pipelines
│   ├── fetch_porto_faq.py          # ✅ baixa HTMLs da FAQ Porto Auto
│   ├── build_porto_faq_md.py       # ✅ parseia HTML, categoriza, gera 09-porto-faq.md
│   ├── anonymize_porto.py          # ✅ anonimiza Porto Inseguro → Porto Inseguro (idempotente)
│   ├── ingest_kb.py                # ✅ chunk + embed e5-base + carga Chroma (312 chunks)
│   └── import_precificador.py      # ✅ compila Precificador_Seguro_Automóvel_v2.0.xlsx → src/insurmind/quote_tables.py
```
# (pasta tests/ não foi criada — projeto acadêmico priorizou smoke test
#  manual em produção sobre TDD por restrição de tempo. Quando precisar
#  escalar pra cobertura automatizada: test_quote.py pra cotação +
#  test_rag.py pra retrieval. Hoje, validação é via demo ao vivo.)

## Anonimização da seguradora

**Atenção, futuras sessões / quem ler este repo:** a base de conhecimento usa o nome fictício **"Porto Inseguro"** em todos os arquivos `data/kb/`, em `RELATORIO.md`, em `docs/`, e neste `CLAUDE.md`. O conteúdo foi extraído de materiais públicos de uma seguradora brasileira real e **sistematicamente anonimizado** (nome, telefones, CNPJ, URLs, endereços, diretor) para fins acadêmicos.

- Script idempotente: `scripts/anonymize_porto.py` (rode `--include-docs` pra processar também os docs além de `data/kb/`).
- Audit trail original (PDFs Porto, HTMLs baixados, logs de fetch) ficava em `meetings/` mas foi removida em 2026-05-19 na limpeza pré-entrega — repo agora é público (curso exige), conteúdo proprietário não cabe. Em backup local fora do git.
- Cidades brasileiras com "Porto" no nome (Porto Alegre, Porto Belo, Porto Real, Senhora do Porto, etc.) são **preservadas** pelo script via lista explícita.
- Filenames com prefixo `porto-` (`08-porto-condicoes-gerais.md`, `09-porto-faq.md`, `scripts/fetch_porto_faq.py`) **não foram renomeados** — o "porto" no nome é a abreviação genérica usada nas convenções internas; o conteúdo é Porto Inseguro.

## Estratégia da Knowledge Base (RAG)

KB organizada em camadas — **Porto Inseguro é a fonte primária**, SUSEP/FENACOR/cartilha são fallback:

| Arquivo | Fonte | Tier | Uso |
|---|---|---|---|
| [10-porto-glossario.md](data/kb/10-porto-glossario.md) | **Glossário próprio** (criado 2026-05-17), 12 termos centrais no estilo Porto | `primary` (`porto-glossario`) | **PRIMÁRIA** — pega definições conceituais em 1 round |
| [08-porto-condicoes-gerais.md](data/kb/08-porto-condicoes-gerais.md) | Porto Inseguro CG142 (PDF oficial 01/05/2026, 174 pgs) | `primary` (`porto-cg`) | **PRIMÁRIA** — regras detalhadas e procedimentais |
| [09-porto-faq.md](data/kb/09-porto-faq.md) | Porto Inseguro FAQ Auto, 97 Q&A em 6 categorias | `primary` (`porto-faq`) | **PRIMÁRIA** — perguntas frequentes do cliente |
| [07-cartilha-susep.md](data/kb/07-cartilha-susep.md) | Cartilha SUSEP 2006 | `fallback` (`susep-cartilha`) | Fallback (regras gerais do setor) |
| [02-glossario.md](data/kb/02-glossario.md) | SUSEP (página Auto) + sintético | `fallback` (`susep-glossario`) | Fallback (termos regulatórios) |
| [06-fenacor-glossario.md](data/kb/06-fenacor-glossario.md) | FENACOR | `fallback` (`fenacor`) | Fallback (termos de mercado) |

**Total**: 312 chunks (244 primary + 68 fallback), persistidos em `.chroma/` via `python scripts/ingest_kb.py`.

**Lógica de retrieval (em [rag.py](src/insurmind/rag.py)):**

1. Sempre faz query no Chroma com `where={'tier':'primary'}` — exclui SUSEP/FENACOR da disputa.
2. Se a melhor distância retornada estiver **≤ `SCORE_THRESHOLD = 0.40`** → primary satisfaz, retorna só esses chunks.
3. Caso contrário → faz segunda query com `where={'tier':'fallback'}` e mescla os resultados ordenados por distância.
4. A LLM recebe os 5 chunks finais com source label visível ("Fonte: porto-glossario", "Fonte: fenacor" etc.) — é assim que ela "sabe" de onde veio.

**Calibração empírica do threshold** (2026-05-17): valor inicial era 1.30 (placeholder). Logs revelaram que e5-base nesse domínio comprime distâncias em 0.2-0.4 — threshold 1.30 nunca disparava fallback. Re-calibrado pra 0.40 com base em distâncias reais observadas:
- Porto-perfect (in-scope com glossário): ~0.20 → no fallback ✓
- Off-product mas seguros: ~0.32 → no fallback ✓
- Off-domain absoluto ("brigadeiro"): ~0.40+ → **dispara fallback** ✓

**Por que essa ordem:** o glossário do produto (Porto) é específico do contrato do usuário — mais assertivo. SUSEP/FENACOR são definições genéricas do setor (úteis quando o termo não está no produto). Decisão validada pela Adriele na reunião.

**Cotação (motor real do grupo, integrado em 2026-05-26):**

- **Fonte de verdade**: `Precificador_Seguro_Automóvel_v2.0.xlsx` (João Carlos Mendonça, modificada em 2026-05-22). 5 sheets: LEIA-ME, MODELOS (16 SKUs × 5 anos com FIPE real), FATORES (taxas, fatores idade/sexo/uso/garagem/bônus/cobertura/franquia/assistência, carregamento 35%, IOF 7.38%), CAPITAIS (6 capitais com fator regional), CÁLCULO (formulário operacional).
- **Excel é spec, não fonte runtime**. Compilado via `scripts/import_precificador.py` → `src/insurmind/quote_tables.py` (17 estruturas Python literais). Em prod só roda Python — sem dep `openpyxl`, sem leitura de disco.
- **10 campos coletados** do usuário em 4 turnos (sem CEP — usa Capital de 6 opções; sem data de nascimento — usa Faixa Etária de 6 categorias; sem estado civil — não entra no cálculo; sem 3 booleans de garagem — usa Pernoite de 3 categorias; sem flag de condutor menor 25; **inclui** Classe de Bônus 0-10 e Assistência 24h Básica/Ampliada).
- **Fórmula**: `Casco_Prêmio = IS_FIPE × 0.03 × F_Modelo × F_Região × F_Cobertura × F_Franquia × F_Idade × F_Sexo × F_Uso × F_Garagem × F_Bônus`. RCF-V usa LMI fixo R$ 100k × 0.8%. APP usa LMI fixo R$ 20k × 0.3% (só na Compreensiva). Assistência valor fixo. Total final aplica carregamento 35% + IOF 7.38%. Replica fielmente as células B17:B25 da aba CÁLCULO.
- **Saída**: `cotar_seguro_auto` devolve **3 opções variando a franquia** (Reduzida/Normal/Aumentada — fatores 1.20/1.00/0.80 sobre o prêmio de casco; valor da franquia em sinistro de 2%/4%/8% do FIPE), todas no tipo de cobertura escolhido. Casa com o DoD do João ("3 opções de preço com franquia").
- **Edge case**: 7 de 80 combinações modelo×ano não têm valor FIPE na planilha (Dolphin sem 2023, HB20 sem 2025, Kwid Iconic só 0km+2026). `QuoteUnavailableError` é levantado e o handler da tool transmite ao usuário com a lista de anos disponíveis.
- **Inconsistências resolvidas localmente** (sem voltar a perguntar pro grupo): (i) fórmula consolidada da LEIA-ME vs aplicação por componente nas células — adotadas as células (verdade canônica). (ii) APP omite F_Sexo e F_Garagem nas células — mantido (atuarialmente defensável: APP indeniza passageiros, não depende do condutor). Detalhes na sessão "2026-05-26 — Integração do tarifador real" no RELATORIO.md.
- **Validação numérica**: smoke test `python -m insurmind.quote` reproduz exemplo do CÁLCULO da planilha (Polo Highline TSI 2026 / SP / 41-55 / M / Particular / fechada / Classe 4 / Compreensiva / Reduzida / Ampliada) → R$ 6.974,66/ano. **Bate ao centavo**.

## Próximos passos (em ordem — Sprint 1)

1. **Implementar tools agnósticas** (`consultar_porto_inseguro`, `cotar_seguro_auto`, `encaminhar_atendimento`) em `src/insurmind/tools.py`. **Interface estável** — quando a planilha do João Carlos + Adriele chegar, só a implementação interna de `cotar_seguro_auto` muda. Contrato em `src/insurmind/quote.py` com `dataclass QuoteInput` (13 campos = 8 perguntas da Adriele) / `QuoteOption` (3 opções variando franquia reduzida/normal/aumentada, todas no tipo de cobertura escolhido pelo usuário). **Agente construído como event-stream desde o início** (`AsyncIterator` de eventos: `llm_call`, `llm_response_text`, `llm_response_tool_use`, `tool_call`, `tool_result`, `final_answer`) — pré-requisito da feature de modo debug planejada pra Sprint 2.
2. **Pipeline `scripts/ingest_kb.py`** — chunk (500-800 tokens, overlap 100) + embedding e5-base + carga no Chroma com metadata (`source`, `file`, `page` quando disponível).
3. **Retriever** com filtro por fonte e score threshold (priorizar Porto, fallback SUSEP/FENACOR) → `src/insurmind/rag.py`.
4. **Receber tarifador refinado** (João Carlos + Adriele) → substituir implementação interna de `cotar_seguro_auto` mantendo assinatura idêntica.
5. **UI Streamlit** em `src/insurmind/ui.py` — `st.chat_message`/`st.chat_input`, histórico em `st.session_state`, card pra cotação, botão "falar com atendente".
6. ~~**Marco 21/05:** demo interna — chat responde 1 FAQ via RAG + 1 cotação mock.~~ ✅ **ATINGIDO em 2026-05-16** (5 dias antes do prazo). 4/4 cenários funcionando via CLI (`python -m insurmind.agent "..."`): FAQ → `consultar_porto_inseguro`, off-product → `encaminhar_atendimento`, off-domain → refuse direto sem tool, cotação completa → `cotar_seguro_auto` com 3 opções de franquia. Detalhes em `RELATORIO.md` sessão "2026-05-16 — Sprint 1 implementação".
7. ~~**Sprint 2 (22-27/05):** refino de prompt, ajuste de retrieval, validações, deploy Streamlit Community Cloud, + painel "Modo Debug" na UI.~~ ✅ **Antecipada em 11 dias.** UI Streamlit multi-turno + provider Gemini + Modo Debug step-by-step funcional.
8. ~~**Sprint 3 (28-29/05):** UI Next.js + Modo Debug v2 com diagrama animado + provider Anthropic API.~~ ✅ **Antecipada em 11 dias (executada em 2026-05-17).** Entregas:
   - **Fase 1**: backend FastAPI + SSE (`src/insurmind/api.py`) expondo `chat_stream_events` via Server-Sent Events.
   - **Fase 2**: scaffold Next.js 16 (Turbopack) + chat funcional + painel debug (timeline + JSON cru).
   - **Fase 3**: diagrama animado React Flow no painel debug, com edges bidirecionais e custom nodes (AgentNode/ToolNode com handles nomeados).
   - **Refator agent-centric**: 8 eventos em gerúndio com agente como sujeito, em vez de 5 system-centric ambíguos. Direção das setas no diagrama segue o sentido REAL do fluxo em cada passo.
   - **Provider `anthropic_api`**: API direta da Anthropic via SDK `anthropic`, loop manual. Desbloqueia deploy cloud (não depende do `claude.exe`).
   - **UX polishes do Modo Debug**: auto-scroll com `requestAnimationFrame`, auto-collapse de passos anteriores, header slim com Modo Debug movido pro ChatInput, ratio 2/5 chat / 3/5 debug, fonte Inter, RAG zone visual, foco automático no input, logo da Porto Inseguro.
9. ~~**Frente A — Calibração RAG (2026-05-17 tarde)**~~ ✅ Concluída. Adicionado [data/kb/10-porto-glossario.md](data/kb/10-porto-glossario.md) (12 termos centrais no estilo Porto), threshold recalibrado de 1.30 → 0.40 com base em distâncias empíricas, **logging interno detalhado** (`INSURMIND_LOG_LEVEL` env var → rag.py + tools.py + anthropic_api.py). KB: 298 → **312 chunks**. Impacto: caso "o que é prêmio?" caiu de **5 rounds/60K tokens (~$0.20)** pra **1 round/~5K tokens (~$0.02)** — 90% redução de custo. Mudança de entregas no chat (`agent_delivering_answer_to_user` agora pode emitir múltiplas vezes por turno — bolhas separadas). Detalhes em RELATORIO.md sessão "2026-05-17 (tarde) — Frente A".
10. **Frente B / Fase 4 (a executar):** deploy + materiais de entrega:
    - Backend FastAPI → Render (free tier, container Python). Cuidado com `.chroma/` (~50MB): bundlar no image ou rebuild no startup.
    - Frontend Next.js → Vercel (free tier, integração direta com GitHub)
    - QA conversacional (10 FAQs do DoD do João + edge cases + jailbreak attempts). Cenário recomendado pra demonstrar multi-RAG: *"Se eu emprestar meu carro pro meu primo de 22 anos e ele bater, o seguro cobre? E muda alguma coisa se eu não tiver declarado ele como condutor?"* (mistura 3 conceitos → força 2-3 rodadas de consultar_porto_inseguro).
    - Slides de apresentação (~10-12) destacando RAG tieirizado + Modo Debug como diferencial técnico
    - ~~Receber tarifador real do João + Adriele e substituir miolo de `cotar_seguro_auto` (interface estável)~~ ✅ Concluído em 2026-05-26 — ver sessão "2026-05-26 — Integração do tarifador real" no RELATORIO.md

## Princípios de trabalho

- **Vibe Code** explícito: Claude Code escreve o código mediante linguagem natural; ciclo curto de iteração. Citar no relatório (validado pelo prof. Onelio Ceabra na aula 6).
- **Guardrails** explícitos no system prompt e em validações no código (aula 6 — exemplo do prof: chatbot não pode aprovar reembolso só porque o usuário pediu).
- **Padrão conversacional** sugerido pelo prof. Ceabra: identificar → coletar dados → simular → oferecer protocolo → encaminhar humano se necessário.
- **Disclaimer didático** em todas as cotações: valores e regras são fictícios e não constituem oferta vinculante da Porto Inseguro ou qualquer outra seguradora.
- **Heurística "a favor do segurado":** quando o input do usuário for ambíguo (ex.: "minha tia mora ao lado e às vezes meu primo põe o carro na garagem dela" — tem ou não garagem?), interpretar a favor do segurado para concessão de desconto/cobertura. Princípio reforçado pela Adriele na reunião de 14/05.
- **Registrar decisões substancias** no `RELATORIO.md` no formato *Opções consideradas → Tradeoffs → Escolha → Justificativa* — o relatório é entregável avaliado pelos professores e essas seções demonstram raciocínio de engenharia.
- **Auditabilidade de citações:** quando um artefato (decisão, princípio, exemplo) for derivado de fala específica do professor numa aula, citar o timestamp da transcrição (formato `aula-NN @ HH:MM:SS`). Os `.srt` originais ficam em `transcribe_yt/transcricoes/` (ver "Origem deste repositório"). Citações da reunião do grupo ficavam em `meetings/20260514.txt` mas a pasta foi removida no cleanup pré-entrega (manter backup local se precisar verificar).
- **Anti-alucinação no RAG:** prompt do sistema exige citação de fonte para toda resposta factual; threshold de similaridade no retriever; se nenhum chunk passar o threshold, responder "não encontrei essa informação" e oferecer encaminhamento humano.
- **Interface-first para integrações que ainda virão do grupo:** a planilha de tarifador está sendo construída por João Carlos + Adriele. Implementamos `cotar_seguro_auto` com **interface estável** (`QuoteInput`/`QuoteOption` dataclasses) e implementação interna em dict in-memory. Quando a planilha chegar, **só a implementação interna muda** — assinatura da função, system prompt, UI, testes permanecem.
- **Agente como event-stream, não black box:** `agent.chat_stream_events()` é um `AsyncIterator[AgentEvent]` que emite **8 eventos agent-centric narrados em gerúndio** (refator 2026-05-17 — antes eram 5 sem perspectiva clara). Sequência canônica (FAQ com tool): `agent_received_user_input` → `agent_sending_to_llm` → `agent_received_tool_request_from_llm` → `agent_executing_tool` → `agent_received_tool_result` → `agent_sending_tool_result_to_llm` → `agent_received_text_from_llm` → `agent_delivering_answer_to_user`. Off-domain (LLM responde direto): só passos 1, 2, 7, 8. UI normal consome o stream silenciosamente; Modo Debug consome o MESMO stream, mostra cada evento e pausa entre eles. **Nenhum código duplicado**. Agente é sempre o sujeito ativo do evento — não "tool_called" mas "agent_executing_tool"; foco didático no orquestrador.
- **Modo Debug com replay completo do turno:** o agente roda inteiro até `agent_delivering_answer_to_user`, **depois** a UI replaya passo-a-passo (não é narração ao vivo). Por isso o painel sabe com certeza quantos passos faltam ("Rodar até o final (N passos restantes)") — N é determinístico no momento do replay. Decisão deliberada: permite pause real entre passos sem segurar a LLM no meio do call.
- **Diagrama animado como complemento didático:** [web/components/debug/AgentDiagram.tsx](web/components/debug/AgentDiagram.tsx) renderiza grafo React Flow com nodes (User, Agent, LLM, 3 tools, ChromaDB) e edges **bidirecionais** que acendem na direção certa por passo (passo 3 acende `LLM → Agent`, passo 4 acende `Agent → Tool`, etc.). Inclui **RagBadgeNode** — retângulo tracejado envolvendo `consultar_porto_inseguro` + `ChromaDB` com etiqueta "🧠 RAG", acende nos passos 4-5 do retrieve. Objetivo pedagógico: alunos perguntam "onde está o RAG" — visualmente delimitado.
- **Multi-deliveries por turno (refator 2026-05-17 tarde):** quando a LLM responde com `[text, tool_use]` na mesma mensagem (anúncio antes de chamar tool), o agente emite **2 eventos `agent_delivering_answer_to_user` separados** no mesmo turno — um após o texto pré-tool e outro após o texto final pós-tool. A UI mostra como bolhas distintas no chat. Razão: a LLM "fala 2 vezes" ao usuário (anúncio + resposta final), e essas duas mensagens devem aparecer **separadas pelo tempo de execução da tool**, não grudadas no fim. Em Modo Debug, push progressivo conforme o usuário avança no `stepIndex` (`pushedDeliveriesRef` no [web/app/page.tsx](web/app/page.tsx) rastreia índices já empurrados).
- **Logging interno como fonte de verdade do sistema:** `INSURMIND_LOG_LEVEL` (default INFO) configura logger em [api.py](src/insurmind/api.py). Loggers granulares em `insurmind.rag` (queries, decisões de tier, distâncias, source labels), `insurmind.tools` (invocações + tamanho do resultado), `insurmind.llm.anthropic_api` (rounds + stop_reason + tokens). Razão: a narração da LLM ao usuário expressa **intenções**, não eventos do sistema — *log estruturado é a única fonte real do que aconteceu*. Em produção: UI mostra narração da LLM (humana, fluida); log estruturado serve auditoria/debug interno. Não conflite as duas fontes.
- **Threshold do RAG calibrado empiricamente, não chutado:** `SCORE_THRESHOLD = 0.40` em [rag.py](src/insurmind/rag.py) foi escolhido após observar distâncias reais nos logs. Valor inicial era 1.30 (placeholder) que NUNCA disparava fallback. e5-base nesse domínio comprime distâncias em 0.2-0.4. Princípio: **antes de calibrar parâmetros, instrumente. Antes de instrumentar, suspeite das suposições**. O caso prêmio (5 rounds desnecessários antes de descobrir que fallback nunca tinha rodado) virou estudo de caso desse princípio.
- **Fallback silencioso é anti-pattern em motor de cotação:** descoberto em produção em 2026-05-26 via QA adversarial — o mock antigo `_valor_fipe` retornava "média dos 8 modelos" pra qualquer modelo desconhecido, sem avisar. Combinado com schema sem `enum`, a LLM mandou "Fiat Estilo IE 2007" e o sistema inventou cotação plausível por 9 dias antes de ser detectado. Lições: (i) lookups fora do domínio devem **levantar exceção**, nunca retornar "razoável"; (ii) **restrição estrutural** (enum no JSON Schema) sempre vence restrição textual (prompt instruindo a LLM); (iii) smokes precisam cobrir adversarial além do feliz — `scripts/smoke_quote.py` agora roda 6 casos (26 asserções) antes de cada commit que toca em quote.py/tools.py. Detalhes em RELATORIO.md sessão "2026-05-26 (tarde) — QA adversarial".
- **System prompt + tool descriptions são LEAKY por default:** a LLM tem acesso integral ao próprio system prompt e ao parâmetro `tools=[...]` (nomes + descrições). Quando o usuário pergunta meta-coisas ("qual o nome da tool de cotação?"), a LLM revela. Descoberto em 2026-05-18 via teste adversarial — vazamento de `compute_quote_mock` + os 13 campos exatos. Mitigação aplicada: (A) regra de confidencialidade explícita no system prompt + (B) renomeação dos tools pra nomes neutros sem jargão técnico (`consultar_porto_inseguro`, `cotar_seguro_auto`, `encaminhar_atendimento`). Princípio: **nomes de tools são UX, não identificadores internos** — eles aparecem em logs, debug panel, e podem vazar. Tratar como nomes de feature. Detalhes da descoberta em RELATORIO.md sessão "Hardening anti-prompt-injection".

## URLs de produção

- **Frontend (Next.js)**: https://insurminds-chatbot.vercel.app — Vercel Hobby free
- **Backend (FastAPI Docker)**: https://bveiga-insurminds-api.hf.space — HuggingFace Spaces free (16GB RAM)
- **Repo público (entrega do curso)**: https://github.com/BrunoCoutoVeiga/i2a2-insurminds-chatbot-cotacao-seguro-auto
- **Repo HF Space**: https://huggingface.co/spaces/bveiga/insurminds-api

A tentativa inicial de deploy foi no Render mas abandonada por OOM no free tier (512MB). Migração pra HF Spaces (16GB) resolveu sem mudar código de aplicação. `render.yaml` removido em 2026-05-19 na limpeza pré-entrega — histórico no RELATORIO.md sessão "2026-05-17 (noite) — Frente B".

## Comandos úteis

```powershell
# === Backend Python ===

# Ativar venv
.\.venv\Scripts\Activate.ps1

# Instalar deps + data-prep (pra re-extrair PDFs em outra máquina)
pip install -e .[dev,dataprep]

# Smoke test do agente via CLI
python -m insurmind.agent "O que é franquia?"

# Trocar motor de inferência
$env:INSURMIND_LLM = "anthropic_api"  # ou "gemini", "claude_code"
python -m insurmind.agent "..."

# UI Streamlit standalone
streamlit run src/insurmind/ui.py

# Backend FastAPI (porta 8000) — pré-requisito da UI Next.js
uvicorn insurmind.api:app --port 8000 --reload

# === Frontend Next.js (em outro terminal) ===

cd web
npm install         # primeira vez
npm run dev         # dev server em http://localhost:3000 (espera backend em :8000)
npm run build       # production build + type check
```

**Setup completo numa máquina nova:**
1. Python: `python -m venv .venv && pip install -e .[dev,dataprep]`
2. Node: `winget install OpenJS.NodeJS.LTS` (Windows) ou `brew install node` (Mac)
3. Copiar `.env.example` → `.env` e preencher `ANTHROPIC_API_KEY` (ou `GEMINI_API_KEY`)
4. Ingerir KB: `python scripts/ingest_kb.py` (gera Chroma local)
5. Backend: `uvicorn insurmind.api:app --port 8000 --reload`
6. Frontend: `cd web && npm install && npm run dev`
