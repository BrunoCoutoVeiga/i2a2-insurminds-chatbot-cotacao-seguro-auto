# InsurMind Chatbot

Chatbot conversacional de **atendimento ao segurado de automóveis** em PT-BR — três fluxos: tirar dúvidas (RAG), cotação simulada e encaminhamento humano. Entrega do curso de **Agentes de IA da I2A2 — turma InsurMinds** (Atividade Obrigatória 2).

**Equipe (5 membros):** Bruno (técnica), João Carlos (técnica + planejamento), Adriele (especialista em seguros), Victor (criou o repo do grupo), + 1 membro não nomeado.
**Deadline:** 2026-05-29 (entrega obrigatória, eliminatória).
**Resultados:** anunciados até 2026-06-01.

## Origem deste repositório

Extraído em 2026-05-14 do projeto `transcribe_yt` (em `C:\Bruno\OneDrive - Rede D'Or\05.Pessoal\Projetos\transcribe_yt`), que ficou responsável apenas pelo pipeline de transcrição de videoaulas.

As **análises das aulas** que motivaram o escopo deste produto foram copiadas para [docs/aulas/](docs/aulas/) como referência imutável.

O **plano técnico aprovado por Bruno** vive em `C:\Users\Bruno\.claude\plans\eu-perdi-o-v-deo-quirky-pinwheel.md`. O **plano de planejamento do grupo** (escrito pelo João pós-reunião 14/05) está em [meetings/Sugestão de Planejamento - Desafio II - feedback da reunião de 14.05.pdf](<meetings/Sugestão de Planejamento - Desafio II - feedback da reunião de 14.05.pdf>) — esse plano lista 5 frentes, propõe stack alternativa (rejeitada — ver "Stack" abaixo) e fixa as 3 sprints.

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
- **Reunião do grupo em 14/05** consolidou o escopo (3 fluxos), validou Opção A (Python), e dividiu frentes. Transcrição em [meetings/20260514.txt](meetings/20260514.txt).

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

- **Python 3.12**.
- **Agente**: `claude-agent-sdk` (Claude Code local — apenas a primeira implementação; o agente é **agnóstico ao motor**).
- **Vector store**: ChromaDB local.
- **Embeddings**: `intfloat/multilingual-e5-base` via `sentence-transformers` (PT-BR-friendly, sem custo, local).
- **UI**: Streamlit.

**Stack proposta pelo João descartada explicitamente:** OpenAI `gpt-4o-mini` + `text-embedding-3-small` (OpenAI) + **LangChain**. Por quê:

- A arquitetura agnóstica do Bruno (factory de providers) já cobre o objetivo de "trocar de LLM sem reescrever" — LangChain seria uma camada **competidora** de abstração, não complementar.
- LangChain adiciona ~200 dependências, quebra API entre versões, esconde comportamento.
- `gpt-4o-mini` tem custo e requer API key OpenAI — `claude-agent-sdk` local é gratuito durante desenvolvimento.
- `text-embedding-3-small` é OpenAI (custo + cloud); `e5-base` é local, free, e melhor em PT-BR.

Trocar de motor de inferência (Claude → OpenAI → Gemini → Ollama) é uma mudança localizada (1 arquivo em `src/insurmind/llm/`), preservando todo o resto do código.

## Arquitetura agnóstica (decisão central)

O agente **não pode ficar acoplado** ao Claude Agent SDK. A escolha do motor é feita via env var `INSURMIND_LLM` pela factory em `src/insurmind/llm/__init__.py`. Implementações ficam em `src/insurmind/llm/<motor>.py`:

- `claude_code.py` — implementação default (Claude Code SDK local, autodispatch de tools via MCP).
- `gemini.py` — implementação Gemini API (Google GenAI SDK) com controle MANUAL do loop de tool calls. Pré-requisito do Modo Debug pra ter pause real entre passos. Requer `GEMINI_API_KEY` em `.env` (free tier em https://aistudio.google.com/apikey). Default model: `gemini-2.5-flash`.
- `anthropic_api.py`, `ollama.py` — stubs com `NotImplementedError` (sinalizam o contrato).

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
│   │   └── 09-porto-faq.md         # ✅ FAQ Porto Auto, 97 Q&A em 6 categorias — FONTE PRIMÁRIA
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
├── meetings/                       # transcrições e materiais das reuniões
│   ├── 20260514.txt                # ✅ transcrição reunião 14/05
│   ├── CG142-Porto-Oficial-3402.pdf       # ✅ Condições Gerais Porto (fonte primária KB)
│   ├── CG142-Porto-Oficial-3402-raw.txt   # ✅ extração textual pypdf
│   ├── Sugestão de Planejamento ...pdf    # ✅ plano do João Carlos
│   ├── porto-faq-titulos.txt              # ✅ lista bruta dos títulos da FAQ Porto (auditável)
│   ├── porto-faq-html/                    # ✅ HTML cru de cada FAQ Porto (98 arquivos)
│   ├── porto-faq-fetch-log.json           # ✅ log do fetch (status por URL)
│   └── porto-faq-parsed.json              # ✅ debug do parser
├── src/insurmind/
│   ├── __init__.py
│   ├── agent.py                    # ✅ orquestrador agnóstico
│   ├── prompts.py                  # ✅ system prompt
│   ├── tools.py                    # ✅ 3 tools: retrieve_kb, compute_quote_mock, escalar_humano
│   ├── llm/                        # ✅ camada agnóstica
│   │   ├── base.py
│   │   ├── claude_code.py          # ✅ default — autodispatch de tools via MCP
│   │   ├── gemini.py               # ✅ controle manual de tool calls (necessário pro Modo Debug)
│   │   ├── anthropic_api.py        # stub
│   │   └── ollama.py               # stub
│   ├── rag.py                      # ✅ retrieval tieirizado em Chroma (primary Porto / fallback SUSEP+FENACOR)
│   ├── quote.py                    # ✅ motor mock com 13 campos → 3 opções de franquia
│   ├── events.py                   # ✅ AgentEvent dataclass (base do Modo Debug step-by-step)
│   └── ui.py                       # ✅ Streamlit chat multi-turno + Modo Debug step-by-step funcional
├── scripts/                        # data prep + pipelines
│   ├── fetch_porto_faq.py          # ✅ baixa HTMLs da FAQ Porto Auto
│   ├── build_porto_faq_md.py       # ✅ parseia HTML, categoriza, gera 09-porto-faq.md
│   ├── anonymize_porto.py          # ✅ anonimiza Porto Inseguro → Porto Inseguro (idempotente)
│   └── ingest_kb.py                # ✅ chunk + embed e5-base + carga Chroma (298 chunks)
└── tests/                          # ⏳ a criar
    ├── test_quote.py
    └── test_rag.py
```

## Anonimização da seguradora

**Atenção, futuras sessões / quem ler este repo:** a base de conhecimento usa o nome fictício **"Porto Inseguro"** em todos os arquivos `data/kb/`, em `RELATORIO.md`, em `docs/`, e neste `CLAUDE.md`. O conteúdo foi extraído de materiais públicos de uma seguradora brasileira real e **sistematicamente anonimizado** (nome, telefones, CNPJ, URLs, endereços, diretor) para fins acadêmicos.

- Script idempotente: `scripts/anonymize_porto.py` (rode `--include-docs` pra processar também os docs além de `data/kb/`).
- O que NÃO é anonimizado: pasta `meetings/` (PDF Porto original, HTMLs baixados, logs de fetch) — mantida como evidência de auditoria do processo de coleta.
- Cidades brasileiras com "Porto" no nome (Porto Alegre, Porto Belo, Porto Real, Senhora do Porto, etc.) são **preservadas** pelo script via lista explícita.
- Filenames com prefixo `porto-` (`08-porto-condicoes-gerais.md`, `09-porto-faq.md`, `scripts/fetch_porto_faq.py`) **não foram renomeados** — o "porto" no nome é a abreviação genérica usada nas convenções internas; o conteúdo é Porto Inseguro.

## Estratégia da Knowledge Base (RAG)

KB organizada em camadas — **Porto Inseguro é a fonte primária**, SUSEP/FENACOR/cartilha são fallback:

| Arquivo | Fonte | Etiqueta no texto | Uso |
|---|---|---|---|
| [08-porto-condicoes-gerais.md](data/kb/08-porto-condicoes-gerais.md) | Porto Inseguro CG142 (PDF oficial 01/05/2026, 174 pgs) | implícito (todo o arquivo é Porto) | **PRIMÁRIA** — consulta primeiro |
| [09-porto-faq.md](data/kb/09-porto-faq.md) | [Porto Inseguro FAQ Auto](https://www.portoinseguro.com.br/canal-de-ajuda/categorias/faqs/auto), 97 Q&A em 6 categorias | implícito | **PRIMÁRIA** — consulta primeiro |
| [07-cartilha-susep.md](data/kb/07-cartilha-susep.md) | Cartilha SUSEP 2006 | `[SUSEP]` | Fallback (regras gerais do setor) |
| [02-glossario.md](data/kb/02-glossario.md) | SUSEP (página Auto) + sintético | `[SUSEP]` / `[Sintético]` | Fallback (termos regulatórios) |
| [06-fenacor-glossario.md](data/kb/06-fenacor-glossario.md) | FENACOR | `[FENACOR]` | Fallback (termos de mercado) |

**Lógica de retrieval (a implementar em `rag.py`):**

1. Buscar primeiro nos chunks com `source` ∈ {`porto-cg`, `porto-faq`}.
2. Se score abaixo do threshold ou nenhum chunk relevante → buscar em SUSEP/FENACOR.
3. Sempre retornar fonte citada na resposta final.

**Por que essa ordem:** o glossário do produto (Porto) é específico do contrato do usuário — mais assertivo. SUSEP/FENACOR são definições genéricas do setor (úteis quando o termo não está no produto). Decisão validada pela Adriele na reunião.

**Cotação:**

- **Sem fetch FIPE/AUTOSEG** (descartado em 14/05). AUTOSEG não é publicado desde 2021; FIPE+AUTOSEG via API daria um dataset gigante e ruidoso.
- **Tarifador curado a mão** por João Carlos + Adriele. Bruno construiu um MVP em Excel (8 modelos zero-km mais vendidos: Polo, Argo, Onix, T-Cross, Creta, Dolphin, HB20, Kwid). O grupo refina e devolve.
- **8 campos coletados do usuário** (especificação Adriele em 2026-05-16): modelo+versão+ano do veículo, CEP de pernoite, data de nascimento + sexo + estado civil do principal condutor, uso (particular/trabalho/aplicativo), garagem em casa/trabalho/fim de semana (3 booleans), há condutor menor de 25 anos, tipo de cobertura desejada (compreensiva / roubo-furto / básica com terceiros).
- **Saída:** `compute_quote_mock` devolve **3 opções variando a franquia** (reduzida/normal/aumentada) — todas do tipo escolhido pelo usuário. Casa com o critério "3 opções de preço com franquia" do plano do João + respeita a escolha de tipo do usuário.
- Contrato técnico completo (dataclasses `QuoteInput` / `QuoteOption`) na memória `project_mock_quote_interface.md` e em `RELATORIO.md` sessão "2026-05-16 — Especificação do mock de cotação".

## Próximos passos (em ordem — Sprint 1)

1. **Implementar tools agnósticas** (`retrieve_kb`, `compute_quote_mock`, `escalar_humano`) em `src/insurmind/tools.py`. **Interface estável** — quando a planilha do João Carlos + Adriele chegar, só a implementação interna de `compute_quote_mock` muda. Contrato em `src/insurmind/quote.py` com `dataclass QuoteInput` (13 campos = 8 perguntas da Adriele) / `QuoteOption` (3 opções variando franquia reduzida/normal/aumentada, todas no tipo de cobertura escolhido pelo usuário). **Agente construído como event-stream desde o início** (`AsyncIterator` de eventos: `llm_call`, `llm_response_text`, `llm_response_tool_use`, `tool_call`, `tool_result`, `final_answer`) — pré-requisito da feature de modo debug planejada pra Sprint 2.
2. **Pipeline `scripts/ingest_kb.py`** — chunk (500-800 tokens, overlap 100) + embedding e5-base + carga no Chroma com metadata (`source`, `file`, `page` quando disponível).
3. **Retriever** com filtro por fonte e score threshold (priorizar Porto, fallback SUSEP/FENACOR) → `src/insurmind/rag.py`.
4. **Receber tarifador refinado** (João Carlos + Adriele) → substituir implementação interna de `compute_quote_mock` mantendo assinatura idêntica.
5. **UI Streamlit** em `src/insurmind/ui.py` — `st.chat_message`/`st.chat_input`, histórico em `st.session_state`, card pra cotação, botão "falar com atendente".
6. ~~**Marco 21/05:** demo interna — chat responde 1 FAQ via RAG + 1 cotação mock.~~ ✅ **ATINGIDO em 2026-05-16** (5 dias antes do prazo). 4/4 cenários funcionando via CLI (`python -m insurmind.agent "..."`): FAQ → `retrieve_kb`, off-product → `escalar_humano`, off-domain → refuse direto sem tool, cotação completa → `compute_quote_mock` com 3 opções de franquia. Detalhes em `RELATORIO.md` sessão "2026-05-16 — Sprint 1 implementação".
7. ~~**Sprint 2 (22-27/05):** refino de prompt, ajuste de retrieval, validações, deploy Streamlit Community Cloud, + painel "Modo Debug" na UI.~~ ✅ **Antecipada em 11 dias.** UI Streamlit multi-turno + provider Gemini + Modo Debug step-by-step funcional. Restante da Sprint 2 (deploy Community Cloud + ajustes de retrieval/prompt) opcional — pode rolar paralelo com Sprint 3.
8. **Sprint 3 (28-29/05):** QA, doc técnica final, slides, ensaio, entrega.

## Princípios de trabalho

- **Vibe Code** explícito: Claude Code escreve o código mediante linguagem natural; ciclo curto de iteração. Citar no relatório (validado pelo prof. Onelio Ceabra na aula 6).
- **Guardrails** explícitos no system prompt e em validações no código (aula 6 — exemplo do prof: chatbot não pode aprovar reembolso só porque o usuário pediu).
- **Padrão conversacional** sugerido pelo prof. Ceabra: identificar → coletar dados → simular → oferecer protocolo → encaminhar humano se necessário.
- **Disclaimer didático** em todas as cotações: valores e regras são fictícios e não constituem oferta vinculante da Porto Inseguro ou qualquer outra seguradora.
- **Heurística "a favor do segurado":** quando o input do usuário for ambíguo (ex.: "minha tia mora ao lado e às vezes meu primo põe o carro na garagem dela" — tem ou não garagem?), interpretar a favor do segurado para concessão de desconto/cobertura. Princípio reforçado pela Adriele na reunião de 14/05.
- **Registrar decisões substancias** no `RELATORIO.md` no formato *Opções consideradas → Tradeoffs → Escolha → Justificativa* — o relatório é entregável avaliado pelos professores e essas seções demonstram raciocínio de engenharia.
- **Auditabilidade de citações:** quando um artefato (decisão, princípio, exemplo) for derivado de fala específica do professor numa aula, citar o timestamp da transcrição (formato `aula-NN @ HH:MM:SS`). Os `.srt` originais ficam em `transcribe_yt/transcricoes/` (ver "Origem deste repositório"). Para citações da reunião do grupo, citar [meetings/20260514.txt](meetings/20260514.txt).
- **Anti-alucinação no RAG:** prompt do sistema exige citação de fonte para toda resposta factual; threshold de similaridade no retriever; se nenhum chunk passar o threshold, responder "não encontrei essa informação" e oferecer encaminhamento humano.
- **Interface-first para integrações que ainda virão do grupo:** a planilha de tarifador está sendo construída por João Carlos + Adriele. Implementamos `compute_quote_mock` com **interface estável** (`QuoteInput`/`QuoteOption` dataclasses) e implementação interna em dict in-memory. Quando a planilha chegar, **só a implementação interna muda** — assinatura da função, system prompt, UI, testes permanecem.
- **Agente como event-stream, não black box:** `agent.run()` é um `AsyncIterator` que emite eventos (`llm_call`, `llm_response_text`, `llm_response_tool_use`, `tool_call`, `tool_result`, `final_answer`). UI normal consome o stream silenciosamente; modo debug consome o mesmo stream, mostra cada evento e pausa entre eles. **Nenhum código duplicado** — debug é "grátis" se o agente for desenhado certo desde o início.

## Comandos úteis

```powershell
# Ativar venv
.\.venv\Scripts\Activate.ps1

# Instalar deps + data-prep deps (pra re-extrair PDFs em outra máquina)
pip install -e .[dev,dataprep]

# Smoke test do agente
python -m insurmind.agent "O que é franquia?"

# Trocar motor (quando implementado)
$env:INSURMIND_LLM = "ollama"
python -m insurmind.agent "..."
```
