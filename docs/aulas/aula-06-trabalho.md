# Aula 06 — Trechos sobre o trabalho e Vibe Code

Fonte: [transcricoes/aula-06.srt](../transcricoes/aula-06.srt).

**Quem ministrou**: professor convidado **Onelio Ceabra** (ex-aluno I2A2), com participação do professor Celso na abertura. Foco da aula: **Vibe Code** — desenvolvimento por linguagem natural com LLM.

## TL;DR para o trabalho

- **Sem mudança de escopo nem de deadline.** Continua chatbot de seguros, deadline 29/05.
- **Landing page** foi exibida como exemplo de output do Vibe Code, **não é entregável adicional**.
- **Concept de "guardrails" ("guarde-reio")** introduzido — pedem que o chatbot tenha limites explícitos. Útil para fortalecer o `system_prompt` e documentar no relatório.
- **Padrão conversacional sugerido** (Ceabra mostrou via exemplo de seguro saúde): _identificar assunto → solicitar dados mínimos → consultar / simular → oferecer protocolo → encaminhar humano se necessário_.
- **Validação do nosso paradigma de implementação**: LLM + tools externas = agente. Confirmação explícita de Ceabra.

## Reforço de prazo (`00:01:10 → 00:01:27`)

> *"Não deixem para a última hora a montagem dos grupos para fazer a tarefa que eu passei na aula 4 para vocês. A gente já está no meio do mês, no final do mês é o prazo final de vocês, e aí não entregou, dançou."* — professor Celso

Deadline confirmado: 29/05/2026.

## Conceito-chave: Vibe Code (`00:36:00 → 00:43:00`)

> *"A atividade que os senhores terão que entregar é a construção de um bot, de um chatbot utilizando IA"* — `00:36:38`.

Vibe Code é o ciclo: **ideia → prompt (linguagem natural) → IA gera código → testa → ajusta → repete**. Ceabra coloca isso como o método recomendado para a entrega.

**Implicação para nós**: já estamos fazendo Vibe Code — o Claude Code está escrevendo todo o código do chatbot. Para o relatório final, dá para citar isso explicitamente como método aplicado.

> *"Aqueles que já têm um background de programação fica muito mais fácil escrever o que precisa, que são os chamados requisitos, o que precisa de fato para que a máquina faça tudo aquilo que ele queira ali de fato."* — `00:37:02`

## Checklist obrigatório antes de pedir para a IA construir (`00:59:21 → 00:59:44`)

> *"O problema está claro no meu prompt, o usuário foi definido, as funcionalidades que o sistema precisa ter foram listadas, as regras de negócio foram descritas, os limites do chatbot foram definidos."*

Mapeamento para o nosso entregável (já cobertos no [plano](../../../Users/Bruno/.claude/plans/eu-perdi-o-v-deo-quirky-pinwheel.md), reforçar no `RELATORIO.md`):

| Item do checklist | Onde está cumprido no nosso trabalho |
|---|---|
| Problema claro | Cotação de seguros de auto em PT-BR com IA |
| Usuário definido | Pessoa interessada em cotar; conhece seu carro mas não necessariamente termos técnicos |
| Funcionalidades listadas | `retrieve_kb`, `compute_quote`, `list_coverages` |
| Regras de negócio descritas | KB (coberturas, regras de elegibilidade, fatores de cotação) |
| **Limites do chatbot definidos** | **Falta consolidar** — ver seção "Guardrails" abaixo |

## Guardrails ("guarde-reio") — novo requisito implícito (`00:59:44 → 01:00:41`)

> *"Os senhores têm que montar um guarde-reio para o modelo dos senhores, de forma que justamente o modelo de vocês, por ter acesso a uma base de dados, a um banco de dados ali, ele simplesmente não faça uma besteira (...) coisa que era para estar justamente o chatbot de vocês."*

Exemplo dado: o chatbot **não** pode aprovar reembolso de R$ 500 mil só porque o usuário pediu.

**Como aplicar no nosso chatbot**:

1. **Restringir escopo** no system prompt: só seguro auto, não vida/saúde/residencial. (Já feito.)
2. **Não inventar valores**: forçar uso de `retrieve_kb` antes de afirmar coberturas/franquias. (Já feito.)
3. **Não executar transações reais**: deixar claro que `compute_quote` é **simulação** — não emite apólice, não cobra, não transfere dados a terceiros.
4. **Validar inputs**: `compute_quote` deve rejeitar idade < 18, classe de bônus > 10, UF inválida, ano de veículo > ano atual ou < 1990.
5. **Sempre exibir disclaimer didático** ao apresentar cotação. (Já no system prompt.)

Os pontos 3 e 4 precisam virar **validações no código** (tools.py + quote.py) e parágrafos explícitos no system prompt. Vou incorporar quando codarmos a Fase 2.

## Padrão conversacional sugerido pelo Ceabra (`00:55:51 → 00:57:01`)

Ordem das ações do chatbot ao receber um pedido:

1. **Identificar o assunto** ("quero cotar" / "o que é franquia" / etc.).
2. **Solicitar dados mínimos** (modelo, ano, idade, UF...).
3. **Consultar** (KB via RAG ou tabela de cotação).
4. **Informar estado simulado** (com disclaimer).
5. **Oferecer protocolo** (no nosso caso: número de simulação, ou opção de "salvar essa cotação").
6. **Encaminhar humano** se sair do escopo (no nosso caso: redirecionar a sugerir "procure um corretor").

Esse fluxo pode ser explicitado no system prompt como "Política de Atendimento".

## Confirmação direta do paradigma agent + tools (`00:57:32 → 00:57:49`)

> *"Quando eu tenho justamente um modelo onde esse modelo tem possibilidade de acesso a ferramentas externas, nós temos justamente um conceito de agentes."*

Validação explícita de que nossa arquitetura (`ClaudeSDKClient` + tools via MCP) é o caminho certo. Citar no relatório.

## Vibe Code com Claude — citação direta (`01:39:04 → 01:39:18`)

> *"Aqui é o código criado lá pelo nosso amigo Claude. Então pode verificar aqui também. Poderia melhorar aqui um pouco, mas uma página realmente muito boa ali."*

O próprio Ceabra usa Claude. Reforço de que nossa escolha de stack está alinhada.

## Mudanças aplicáveis ao plano

| Onde | Mudança |
|---|---|
| `chatbot/src/insurmind/prompts.py` | Acrescentar seção "Política de Atendimento" (passos 1-6 acima) e seção "Guardrails" enumerando o que **não** pode (não emite apólice, não cobra, não acessa dados externos) |
| `chatbot/src/insurmind/quote.py` | Validações de input (idade ≥ 18, ano do veículo válido, UF válida, classe bônus 0-10) — sair com `ValueError` legível |
| `chatbot/src/insurmind/tools.py` | A tool `compute_quote` envelopa o erro de validação e devolve uma mensagem que o agente sabe transmitir ao usuário |
| `chatbot/RELATORIO.md` | Seção "Método: Vibe Code" + seção "Guardrails aplicados" citando timestamps desta aula |
| Plano (cronograma) | Sem mudança de datas — só explicita os ajustes acima na entrega do Dia 6-8 (cotação + tools) |

Nenhum desses ajustes adiciona tempo significativo ao cronograma — são incrementos pequenos a artefatos já planejados.
