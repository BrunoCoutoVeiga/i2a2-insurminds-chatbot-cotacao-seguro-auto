# Aula 05 — Trechos sobre o trabalho (complementos)

Fonte: [transcricoes/aula-05.srt](../transcricoes/aula-05.srt).

A aula 05 começa **reforçando** as regras do trabalho dadas na aula 04 e dá orientações complementares de implementação.

## Reforços (`00:00:07 → 00:04:12`)

- *"Tarefa no final desse conjunto de blocos é obrigatória e eliminatória"* — `00:00:35 → 00:00:53`.
- *"Pode ser feito em grupo"* (não obriga grupo; entrega individual é OK).
- *"Não é um problema complexo, mas vocês vão ter trabalho pra conseguir organizar tudo"* — `00:01:17 → 00:01:34`.
- *"Espero que vocês já tenham aproveitado o feriado de 1º de Maio (Dia do Trabalho) para fazer o trabalho"* — `00:01:22 → 00:01:34`. (Indica que a aula 05 ocorreu **após** 01/05.)
- *"Não fez a entrega, não vai conseguir passar para as próximas etapas e nem vai fazer jus ao certificado"* — `00:01:57 → 00:02:05`.

## Resposta a perguntas dos alunos sobre o trabalho

### Peterson — "treinar com fine-tuning?" (`00:02:33 → 00:02:53`)

> *"Treinar ferramentas significa fine-tuning ou RAG com base de conhecimento. **No caso de vocês, Peterson, vocês vão trabalhar com o RAG. Fazer fine-tuning de modelo não acho que seja algo viável e possível de ser feito**."*

**Implicação direta:** o caminho oficial é **RAG**, não fine-tuning.

### Dados (`00:02:43 → 00:02:53`)

> *"Os dados vocês podem criar, não tem problema nenhum"*.

**Implicação:** dataset sintético ou montado à mão é aceito.

### Avaliação (`00:02:53 → 00:03:15`)

> *"A gente vai olhar o que você está entregando, o relatório, os entregáveis, o código, vamos olhar tudo isso e obviamente ver se as coisas fazem sentido. Se não fizerem sentido, eu não posso dar como entregue."*

**Critérios efetivos:** coerência, completude, evidência de funcionamento.

### Plataforma (`00:03:15 → 00:03:36`)

> *"Não tem restrição nenhuma de plataforma, vocês podem usar o que vocês quiserem. Pode usar Azure com Copilot, pode usar Amazon, pode usar Google, o AI Studio, Vertex, enfim. O Antigravity para desenvolver código, para quem for escrever código, fiquem à vontade."*

## Conteúdo técnico da aula 05 aplicável ao trabalho

O foco da aula 05 é **ferramentas e agentes**, com ênfase em **low-code / no-code**:

- **N8N** (orquestração de fluxos) — `01:08:09 → 01:16:31`. Self-hosted em Docker. Modelo de cobrança por execução; versão paga ~R$200/mês na mais simples; **self-hosted gratuito**. Professor mostra rodando localmente em `01:58:51 → 02:02:23`.
- **Langflow** — visual para construir fluxos com LLM.
- **Bubble / Lovable** — construção de aplicações sem código, com workflows e DB nativos. Pode chamar API da OpenAI dentro do workflow (`01:33:02 → 01:33:08`).
- **PipeDream** — alternativa ao N8N (`01:05:42 → 01:05:53`).
- **Combinação Langflow + N8N** mencionada como caminho para chatbot (`01:46:20 → 01:46:32`).

### Sobre o chatbot (`00:53:43 → 00:53:54`)

> *"Construir um chatbot e um chatbot que vai buscar informações específicas. Então, é um chatbot que provavelmente vocês vão ter que fazer RAG ou vão ter que buscar informação na..."*

### Fluxo de RAG no N8N (`02:08:46 → 02:08:59`)

> *"Para vocês que esperam trabalhar com RAG. Ele já tem aqui um primeiro fluxo de RAG."*

(O professor demonstra um fluxo de RAG já construído no N8N para servir de **base** para o trabalho.)

### Compatibilidade código ↔ no-code

- Antônio perguntou sobre rodar LangChain dentro do N8N — o professor responde que sim, dá pra subir outro container Python no mesmo `docker-compose` do N8N e expor APIs (`01:15:41 → 01:16:05`).
- Tradeoff: no-code é **mais rápido** (meses → dias), mas resulta em **código mais frágil** e potencialmente menos adequado para produção corporativa (`00:18:04 → 00:18:30`).

### Conceito de "agente" reforçado (`00:08:26 → 00:13:22`)

Anatomia do agente que o professor quer ver:

1. **Percepção** — coleta info via sensores/API/prompt/contexto.
2. **Raciocínio** — LLM processa (planejamento + objetivos).
3. **Ação** — invoca ferramentas (funções) que alteram o ambiente.
4. **Loop** — coleta resultado e decide se finaliza ou tenta outra rota.

Diagrama mental: LLM = "processador/cérebro" + ferramentas = "mãos" + ambiente = "mundo".

## Implicação para o trabalho do Bruno

O professor está claramente dando duas trilhas de implementação viáveis:

| Trilha | Stack sugerida | Quando preferir |
|---|---|---|
| **No-code** | N8N self-hosted + Langflow + Bubble (front) | Velocidade, valida ideia, exige menos código |
| **Code** | LangChain / LangGraph + Python + qualquer LLM API + front próprio | Controle, robustez, demonstrar competência de engenharia |

Bruno é desenvolvedor — provavelmente a **trilha code** mostra mais maturidade técnica, mas pode-se hibridizar (N8N orquestrando + serviço Python para o RAG).
