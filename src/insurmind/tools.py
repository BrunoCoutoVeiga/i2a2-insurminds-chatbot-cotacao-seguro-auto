"""Registry de tools do agente InsurMind.

3 tools registradas (todas em formato agnóstico — `insurmind.llm.base.Tool`):

- `retrieve_kb`         — busca semântica tieirizada na KB (Porto primária → SUSEP/FENACOR fallback)
- `compute_quote_mock`  — cotação simulada com 13 campos de input → 3 opções de franquia
- `escalar_humano`      — devolve mensagem padrão de encaminhamento (pra fora-do-produto)

Os providers em `insurmind.llm.<motor>` traduzem essas tools pro formato nativo
do motor (Claude SDK: MCP tools; Anthropic API: tool_use blocks; etc.).
"""

from __future__ import annotations

import logging

from .llm import Tool
from .quote import QuoteInput, compute_quote_mock
from .rag import retrieve_kb

logger = logging.getLogger(__name__)


# =============================================================================
# Tool 1 — retrieve_kb
# =============================================================================

_RETRIEVE_KB_SCHEMA = {
    "type": "object",
    "properties": {
        "consulta": {
            "type": "string",
            "description": (
                "A pergunta ou termo a buscar na base de conhecimento, em português. "
                "Pode ser reformulada para captar melhor o sentido (ex.: 'o que é franquia' → "
                "'franquia em seguro auto Porto Inseguro')."
            ),
        }
    },
    "required": ["consulta"],
}


async def _handler_retrieve_kb(args: dict) -> dict:
    consulta = args["consulta"]
    logger.info("TOOL retrieve_kb invocada pela LLM com consulta=%r", consulta)
    chunks = await retrieve_kb(consulta, k=5)
    if not chunks:
        logger.warning("TOOL retrieve_kb: 0 chunks retornados")
        return {"text": "Nenhum trecho relevante encontrado na base de conhecimento."}

    parts: list[str] = [f"Trechos relevantes para a consulta: {consulta!r}\n"]
    for i, c in enumerate(chunks, start=1):
        page = f", página {c.page}" if c.page else ""
        parts.append(
            f"\n[{i}] Fonte: {c.source} ({c.file}{page}) — seção \"{c.section[:80]}\"\n"
            f"{c.text}\n"
        )
    parts.append(
        "\nInstruções para o agente: use estes trechos como fonte primária da "
        "resposta ao usuário. CITE a fonte (formato: \"Fonte: {source} ({file}\")"
    )
    result_text = "".join(parts)
    logger.info(
        "TOOL retrieve_kb devolvendo: %d chunks, %d chars de texto pra LLM",
        len(chunks), len(result_text),
    )
    return {"text": result_text}


retrieve_kb_tool = Tool(
    name="retrieve_kb",
    description=(
        "Busca trechos relevantes na base de conhecimento do InsurMind — Condições "
        "Gerais e FAQ da Porto Inseguro (primárias), com fallback automático para "
        "glossários SUSEP e FENACOR quando a Porto não tem a informação. Use SEMPRE "
        "antes de afirmar qualquer fato sobre coberturas, franquias, sinistro, "
        "regras de apólice, glossário ou conceitos de seguro auto."
    ),
    parameters_schema=_RETRIEVE_KB_SCHEMA,
    handler=_handler_retrieve_kb,
)


# =============================================================================
# Tool 2 — compute_quote_mock
# =============================================================================

_COMPUTE_QUOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "modelo":                 {"type": "string", "description": "Modelo do veículo (ex.: 'Polo', 'Onix', 'Argo')"},
        "versao":                 {"type": "string", "description": "Versão (ex.: 'entrada', 'Highline', 'GTS')"},
        "ano":                    {"type": "integer", "description": "Ano do veículo (ex.: 2026)"},
        "cep_pernoite":           {"type": "string", "description": "CEP onde o carro fica à noite (8 dígitos, ex.: '01310-100')"},
        "data_nascimento":        {"type": "string", "description": "Data de nascimento do principal condutor (formato 'DD/MM/AAAA')"},
        "sexo":                   {"type": "string", "enum": ["M", "F"]},
        "estado_civil":           {"type": "string", "enum": ["solteiro", "casado", "divorciado", "viuvo", "uniao_estavel"]},
        "uso":                    {"type": "string", "enum": ["particular", "trabalho", "aplicativo"], "description": "Uso primário do veículo"},
        "garagem_casa":           {"type": "boolean", "description": "Carro fica em garagem fechada quando está em casa?"},
        "garagem_trabalho":       {"type": "boolean", "description": "Carro fica em garagem fechada quando está no trabalho?"},
        "garagem_fim_de_semana":  {"type": "boolean", "description": "Carro fica em garagem nos fins de semana?"},
        "ha_condutor_menor_25":   {"type": "boolean", "description": "Algum condutor adicional com menos de 25 anos usa o veículo?"},
        "tipo_cobertura":         {"type": "string", "enum": ["compreensiva", "roubo_furto", "basica_terceiros"], "description": "Tipo de cobertura desejada"},
    },
    "required": [
        "modelo", "versao", "ano", "cep_pernoite", "data_nascimento", "sexo",
        "estado_civil", "uso", "garagem_casa", "garagem_trabalho", "garagem_fim_de_semana",
        "ha_condutor_menor_25", "tipo_cobertura",
    ],
}


async def _handler_compute_quote(args: dict) -> dict:
    logger.info(
        "TOOL compute_quote_mock invocada: %s %s %s, CEP=%s, cobertura=%s",
        args.get("modelo"), args.get("versao"), args.get("ano"),
        args.get("cep_pernoite"), args.get("tipo_cobertura"),
    )
    qin = QuoteInput(**args)
    opcoes = compute_quote_mock(qin)
    logger.info(
        "TOOL compute_quote_mock devolvendo 3 opções: %s",
        ", ".join(f"{o.nivel_franquia}=R${o.premio_anual:,.2f}" for o in opcoes),
    )

    cob_label = {
        "compreensiva": "Compreensiva",
        "roubo_furto": "Roubo/Furto/Incêndio + RCF-V",
        "basica_terceiros": "Básica (terceiros)",
    }[qin.tipo_cobertura]

    parts: list[str] = [
        f"Cotação simulada — {qin.modelo} {qin.versao} {qin.ano}, "
        f"cobertura {cob_label}, CEP {qin.cep_pernoite}, "
        f"condutor {qin.sexo}/{qin.estado_civil} nascido em {qin.data_nascimento}.\n",
    ]
    for o in opcoes:
        parts.append(
            f"\n• Franquia {o.nivel_franquia.upper()}: "
            f"prêmio anual R$ {o.premio_anual:,.2f} / "
            f"franquia em sinistro R$ {o.valor_franquia:,.2f}"
        )
    parts.append(f"\n\nCoberturas inclusas (mesmas nas 3 opções, varia só franquia):")
    for c in opcoes[0].coberturas:
        parts.append(f"\n  - {c}")
    parts.append("\n\nAvisos obrigatórios:")
    for a in opcoes[0].avisos:
        parts.append(f"\n  - {a}")

    return {"text": "".join(parts)}


compute_quote_mock_tool = Tool(
    name="compute_quote_mock",
    description=(
        "Calcula uma cotação SIMULADA (mock didático) de seguro auto Porto Inseguro. "
        "Devolve 3 opções de franquia (reduzida/normal/aumentada) — todas no tipo de "
        "cobertura escolhido pelo usuário. Exige TODOS os 13 campos preenchidos antes "
        "de chamar — pergunte ao usuário o que estiver faltando. Os campos seguem a "
        "especificação da Adriele (especialista do grupo). A resposta inclui o "
        "disclaimer obrigatório de simulação didática."
    ),
    parameters_schema=_COMPUTE_QUOTE_SCHEMA,
    handler=_handler_compute_quote,
)


# =============================================================================
# Tool 3 — escalar_humano
# =============================================================================

_ESCALAR_HUMANO_SCHEMA = {
    "type": "object",
    "properties": {
        "motivo": {
            "type": "string",
            "description": (
                "Descrição curta do que o usuário pediu e por que está fora do escopo "
                "(ex.: 'seguro de vida — fora do escopo deste chatbot, que cobre apenas auto'; "
                "'aprovar reembolso — requer atendente humano')."
            ),
        }
    },
    "required": ["motivo"],
}


async def _handler_escalar_humano(args: dict) -> dict:
    motivo = args.get("motivo", "(motivo não informado)")
    logger.info("TOOL escalar_humano invocada: motivo=%r", motivo)
    text = (
        f"Encaminhamento ao atendimento humano. Motivo: {motivo}\n\n"
        "Mensagem padrão a apresentar ao usuário:\n\n"
        "    Para este atendimento específico, recomendo entrar em contato direto com a "
        "Porto Inseguro:\n"
        "    📱 WhatsApp: (11) 0000-0001\n"
        "    📞 Capitais e grandes centros: (11) 0000-0005\n"
        "    📞 Outras localidades: 0300 0000-0001\n"
        "    🌐 portoinseguro.com.br\n"
        "    \n"
        "    Posso te ajudar com mais alguma dúvida sobre seguro auto?\n"
    )
    return {"text": text}


escalar_humano_tool = Tool(
    name="escalar_humano",
    description=(
        "Use quando o pedido do usuário for sobre OUTRO produto de seguros (vida, "
        "residencial, frota grande, saúde, viagem) OU exigir ação de humano (alterar "
        "apólice real, aprovar reembolso, cancelar contrato, registrar reclamação "
        "formal). NÃO use para perguntas fora do domínio de seguros (história, clima, "
        "código, opinião) — para essas, responda direto que você não trata o tema, "
        "sem chamar tool nenhuma."
    ),
    parameters_schema=_ESCALAR_HUMANO_SCHEMA,
    handler=_handler_escalar_humano,
)


# =============================================================================
# Lista exposta ao agent
# =============================================================================

ALL_TOOLS: list[Tool] = [
    retrieve_kb_tool,
    compute_quote_mock_tool,
    escalar_humano_tool,
]
