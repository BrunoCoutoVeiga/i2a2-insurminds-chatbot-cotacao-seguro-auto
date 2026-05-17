# Aula 04 — Trechos sobre o trabalho (Atividade Obrigatória 2 / "InsurMind")

Fonte: [transcricoes/aula-04.srt](../transcricoes/aula-04.srt). Timestamps citados são do vídeo original.

## Resumo executivo

**Trabalho:** construir um **chatbot para o domínio de seguros** ("InsurMind Atividade Obrigatória 2"), com base de conhecimento (FAQ + documentos públicos) consumida via **RAG**. Entrega obrigatória e **eliminatória**.

**Deadline:** 29/05/2026. Resultados (aprovação para fase 3) anunciados até 01/06/2026.

**Modalidade:** em grupo de até 5 pessoas; Bruno fará solo (premissa do projeto).

## Escopo técnico exigido

### Obrigatório (em ordem do que o professor disse, ~01:22:00–01:26:00):

1. **Mapear e categorizar perguntas frequentes** do domínio de seguros (FAQ).
2. **Compor uma base de conhecimento** consumível pela IA — não é treino de modelo, é montar dados que a LLM consulta.
3. **Definir qual LLM** será usada.
4. **Usar RAG** para enriquecer o contexto ("provavelmente vão ter que usar"). Citação: *"vocês vão ter que fazer Hague pra enriquecer o contexto"* — `01:24:59 → 01:25:10`.
5. **Construir o chatbot funcional**: pergunta → resposta com contexto.

### Opcional:

- Integração com CRM ou tickets de suporte anonimizados (`01:25:32 → 01:25:46`).
- Personalização por perfil (assegurado vs corretor).
- Especialização num ramo específico de seguros (ex.: automóveis) — *"Pode ser especializado em um tipo de seguros, por exemplo, automóveis, não tem problema nenhum"* — `01:34:36`.

### Fontes de dados sugeridas pelo professor:

- Sites de seguradoras (informações públicas).
- Bases no **Kaggle**.
- Sites de **órgãos de classe** (modelos de apólice, documentação pública).
- *"No pior das hipóteses, você pode inventar algumas informações"* — `01:23:41 → 01:23:49`.

## Entregáveis (e-mail)

Citação consolidada de `01:29:00 → 01:31:30`:

- **Destinatário:** `challenges@i2a2.academy` (o professor menciona `challenges-2a2.academy` — provável transcrição de `challenges@i2a2.academy`).
- **Remetente:** o **representante do grupo** envia, com **todos os integrantes em cópia** (protocolo de entrega).
- **Assunto (literal):** `InsurMinds atividade obrigatória 2` (sem aspas, sem variações — *"O assunto tem que ser instruments, atividade obrigatória 2"* — `01:29:32`; "instruments" é erro da transcrição para "InsurMinds").
- **Corpo do e-mail:**
  - Nome do grupo.
  - Lista de integrantes: **nome completo, e-mail, celular**.
  - Link para versão executável do chatbot (se houver) — pode ser repositório no GitHub (`01:32:25 → 01:32:31`).
- **Anexos:**
  - Código-fonte.
  - Documentação.
  - Base de dados.
  - Diagramas.
  - **Relatório** descrevendo o processo: como foi a criação, problemas enfrentados, decisões.
  - **Print screens** evidenciando o chatbot funcionando (pergunta → resposta).

## Avaliação

Critérios mencionados (`00:02:53 → 00:03:15` da aula-05, complementa aula-04):

- O que é entregue: relatório, entregáveis, código.
- *"Se não fizerem sentido, eu não posso dar como entregue"* — coerência conta.
- Sem restrição de plataforma: Azure/OpenAI, AWS, Google AI Studio/Vertex, etc. Pode usar IDE/agente de código (Antigravity, Cursor, Claude Code) à vontade.

## Penalidades

- **Eliminatória**: se o grupo (mesmo que de 5) não entregar, **todos os 5 são eliminados** — `01:31:58 → 01:32:15`.
- Sem entrega → sem certificado → sem fase 3.
- *"Não deixem pra última hora"* (mencionado 3x na aula). Caso real citado: aluno tentou entregar Atividade 1 no fim da sexta, faltou luz, não entregou, foi eliminado — `01:33:01 → 01:33:18`.

## Framework recomendado pelo professor

Aula 04 dedica ~1h ensinando um **ciclo de vida de 7 etapas para soluções de IA generativa** (`00:28:48 → 00:29:24`):

1. **Definição do problema** (a mais importante — ótica de negócio, critérios de sucesso claros).
2. **Investigação dos dados** (que insumos existem? RAG? APIs? bancos?).
3. **Preparação dos dados** (limpeza, estruturação).
4. **Desenvolvimento**.
5. **Avaliação**.
6. **Implantação**.
7. **Monitoramento e melhoria**.

O ciclo é **iterativo** — voltar a etapas anteriores é esperado.

Inspirado em: PDCA, DMAIC (Six Sigma), Scrum (Product Backlog → Sprint Backlog → entrega → repete), CrispDM.

Citação central: *"ao final desse mês vocês vão ter que me entregar uma solução baseada em IA generativa. Então é importante que a gente tenha um framework para ajudar a organizar as ideias"* — `00:28:41 → 00:29:00`.

## Dicas práticas do professor

- *"Não é um problema complexo, mas vocês vão ter trabalho pra conseguir organizar tudo"* (aula 05 `00:01:17`).
- *"Sejam criativos na busca da solução"* — `01:29:00`.
- Dividir tarefas no grupo: um cuida da fonte de dados, outro do RAG, outro da LLM, outro da interface — `01:28:21 → 01:28:52`. (Como Bruno é solo, ele assume tudo, mas a estrutura serve para organizar fases.)
- Grupos de >5 normalmente não funcionam (2-3 fazem tudo, resto observa).

## Resumo para Bruno (solo)

Mesmo entregando individualmente, o e-mail e o subject **devem** seguir o protocolo de grupo (nome do "grupo" = Bruno, integrantes = 1 pessoa). Vale validar com o professor se isso é aceito, mas o curso permite explicitamente entrega individual com solução pensada em grupo (`00:16:01 → 00:16:07`).
