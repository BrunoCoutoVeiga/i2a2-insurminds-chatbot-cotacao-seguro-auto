"""Registry de tools do agente InsurMind.

3 tools registradas (todas em formato agnóstico — `insurmind.llm.base.Tool`):

- `consultar_porto_inseguro` — busca semântica tieirizada na KB (Porto primária → SUSEP/FENACOR fallback)
- `cotar_seguro_auto`        — cotação com 10 campos → 3 opções variando franquia
- `encaminhar_atendimento`   — devolve mensagem padrão de encaminhamento (pra fora-do-produto)

Os providers em `insurmind.llm.<motor>` traduzem essas tools pro formato nativo
do motor (Claude SDK: MCP tools; Anthropic API: tool_use blocks; etc.).
"""

from __future__ import annotations

import logging

from .llm import Tool
from .quote import QuoteInput, QuoteUnavailableError, compute_quote
from .quote_tables import (
    FATOR_BONUS, FATOR_IDADE, FATOR_MODELO_POR_CHAVE,
    FATOR_REGIAO, FATOR_USO, VALOR_ASSISTENCIA,
)
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


async def _handler_consultar_porto_inseguro(args: dict) -> dict:
    consulta = args["consulta"]
    logger.info("TOOL consultar_porto_inseguro invocada pela LLM com consulta=%r", consulta)
    chunks = await retrieve_kb(consulta, k=5)
    if not chunks:
        logger.warning("TOOL consultar_porto_inseguro: 0 chunks retornados")
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
        "TOOL consultar_porto_inseguro devolvendo: %d chunks, %d chars de texto pra LLM",
        len(chunks), len(result_text),
    )
    return {"text": result_text}


# Nome neutro/genérico (sem revelar "kb"/"retrieve"/arquitetura interna).
# Descrição foca no comportamento funcional sem mencionar:
# - InsurMind (nome do sistema interno)
# - SUSEP/FENACOR (fallback — implementação)
# - "tieirizado"/"vetorial" (arquitetura)
# A LLM ainda recebe trechos com `Fonte:` label, então cita fontes na resposta.
consultar_porto_inseguro_tool = Tool(
    name="consultar_porto_inseguro",
    description=(
        "Busca informações oficiais sobre seguro auto Porto Inseguro. Use SEMPRE "
        "antes de afirmar qualquer fato sobre coberturas, franquias, sinistro, "
        "regras de apólice, glossário ou conceitos de seguro auto. Nunca invente — "
        "se não houver fontes relevantes, encaminhe pra atendimento humano."
    ),
    parameters_schema=_RETRIEVE_KB_SCHEMA,
    handler=_handler_consultar_porto_inseguro,
)


# =============================================================================
# Tool 2 — compute_quote_mock
# =============================================================================

# Enums extraídos das tabelas geradas a partir da planilha v2.0 — fonte única de verdade.
_MODELOS_ENUM = list(FATOR_MODELO_POR_CHAVE.keys())  # 16 chaves
_CAPITAIS_ENUM = list(FATOR_REGIAO.keys())            # 6 capitais
_FAIXAS_ETARIAS_ENUM = list(FATOR_IDADE.keys())       # 6 faixas
_USOS_ENUM = list(FATOR_USO.keys())                   # 4 categorias
_CLASSES_BONUS_ENUM = list(FATOR_BONUS.keys())        # 11 classes
_ASSISTENCIA_ENUM = list(VALOR_ASSISTENCIA.keys())    # Básica/Ampliada

_COMPUTE_QUOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "modelo_versao": {
            "type": "string",
            "enum": _MODELOS_ENUM,
            "description": "Modelo+versão do veículo. Se o usuário disser só 'Polo' ou 'Onix', pergunte qual versão (entrada ou topo) antes de chamar.",
        },
        "ano": {
            "type": "string",
            "enum": ["0km", "2026", "2025", "2024", "2023"],
            "description": "Ano do veículo. '0km' para veículo novo a sair da concessionária.",
        },
        "capital": {
            "type": "string",
            "enum": _CAPITAIS_ENUM,
            "description": "Capital onde o veículo pernoita. Se o usuário disser uma cidade que não é capital ou está fora da lista, ofereça a capital mais próxima como aproximação.",
        },
        "faixa_etaria": {
            "type": "string",
            "enum": _FAIXAS_ETARIAS_ENUM,
            "description": "Faixa etária do condutor principal. Calcule pela idade que o usuário informou.",
        },
        "sexo": {
            "type": "string",
            "enum": ["Masculino", "Feminino"],
        },
        "uso": {
            "type": "string",
            "enum": _USOS_ENUM,
            "description": "Uso primário do veículo. 'Particular - lazer/trabalho' até ~30km/dia, 'Particular - alta rodagem' acima de 60km/dia, 'Comercial - representante' para viagens de trabalho, 'App (Uber/99)' para motoristas de aplicativo.",
        },
        "pernoite": {
            "type": "string",
            "enum": ["Sim - garagem fechada", "Sim - estacionamento", "Não - rua"],
            "description": "Onde o carro fica à noite. Em caso de ambiguidade, interprete a favor do segurado (escolha a opção que reduz o prêmio).",
        },
        "classe_bonus": {
            "type": "string",
            "enum": _CLASSES_BONUS_ENUM,
            "description": "Classe de bônus. 'Classe 0' = seguro novo (sem histórico). 'Classe N' = N anos consecutivos sem sinistro avisado. 'Classe 10' = 10+ anos.",
        },
        "cobertura": {
            "type": "string",
            "enum": ["Compreensiva", "RF+Inc+RCF-V", "Só RCF-V"],
            "description": "Tipo de cobertura. 'Compreensiva' = mais completa (colisão + roubo + incêndio + terceiros + APP). 'RF+Inc+RCF-V' = só roubo, furto, incêndio + terceiros. 'Só RCF-V' = só danos a terceiros, sem casco.",
        },
        "assistencia": {
            "type": "string",
            "enum": _ASSISTENCIA_ENUM,
            "description": "Nível da assistência 24h. 'Básica' = guincho 100km + chaveiro + pneu + pane seca (R$ 180/ano). 'Ampliada' = guincho ilimitado + carro reserva 15 dias + hospedagem (R$ 360/ano).",
        },
    },
    "required": [
        "modelo_versao", "ano", "capital", "faixa_etaria", "sexo", "uso",
        "pernoite", "classe_bonus", "cobertura", "assistencia",
    ],
}


async def _handler_cotar_seguro_auto(args: dict) -> dict:
    logger.info(
        "TOOL cotar_seguro_auto invocada: %s %s, %s, %s/%s, %s, %s",
        args.get("modelo_versao"), args.get("ano"), args.get("capital"),
        args.get("sexo"), args.get("faixa_etaria"),
        args.get("cobertura"), args.get("assistencia"),
    )
    try:
        qin = QuoteInput(**args)
        opcoes = compute_quote(qin)
    except QuoteUnavailableError as e:
        logger.warning("TOOL cotar_seguro_auto: combinação indisponível — %s", e)
        return {
            "text": (
                f"Não tenho cotação para {e.modelo_versao} no ano {e.ano}. "
                f"Anos disponíveis para esse modelo: {', '.join(e.anos_disponiveis)}. "
                "Peça ao usuário pra escolher um ano disponível ou outro modelo."
            )
        }
    except (KeyError, ValueError) as e:
        logger.warning("TOOL cotar_seguro_auto: argumento inválido — %s", e)
        return {"text": f"Argumento inválido na cotação: {e}. Reconfirme os dados com o usuário."}

    logger.info(
        "TOOL cotar_seguro_auto devolvendo 3 opções: %s",
        ", ".join(f"{o.nivel_franquia}=R${o.premio_anual:,.2f}" for o in opcoes),
    )

    parts: list[str] = [
        f"Cotação — {qin.modelo_versao} {qin.ano} | {qin.capital} | "
        f"condutor {qin.sexo} {qin.faixa_etaria} | "
        f"Cobertura {qin.cobertura} | Assistência {qin.assistencia} | "
        f"Bônus {qin.classe_bonus}\n",
    ]
    for o in opcoes:
        franq = (
            f"franquia em sinistro R$ {o.valor_franquia:,.2f}"
            if o.valor_franquia is not None
            else "sem casco (franquia N/A)"
        )
        parts.append(
            f"\n• Franquia {o.nivel_franquia.upper()}: "
            f"prêmio anual R$ {o.premio_anual:,.2f} "
            f"(mensal R$ {o.premio_mensal:,.2f}) — {franq}"
        )
    parts.append("\n\nCoberturas inclusas (idênticas nas 3 opções; varia só franquia):")
    for c in opcoes[0].coberturas:
        parts.append(f"\n  - {c}")
    parts.append("\n\nAvisos obrigatórios:")
    for a in opcoes[0].avisos:
        parts.append(f"\n  - {a}")

    return {"text": "".join(parts)}


cotar_seguro_auto_tool = Tool(
    name="cotar_seguro_auto",
    description=(
        "Calcula uma cotação de seguro auto Porto Inseguro. Devolve 3 opções "
        "variando a franquia (Reduzida, Normal e Aumentada) — todas no tipo de "
        "cobertura escolhido pelo usuário. Antes de chamar, colete TODOS os 10 "
        "campos abaixo conversando naturalmente com o usuário (NÃO liste os "
        "nomes técnicos dos campos pra ele). Se algum estiver faltando, pergunte."
    ),
    parameters_schema=_COMPUTE_QUOTE_SCHEMA,
    handler=_handler_cotar_seguro_auto,
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


async def _handler_encaminhar_atendimento(args: dict) -> dict:
    motivo = args.get("motivo", "(motivo não informado)")
    logger.info("TOOL encaminhar_atendimento invocada: motivo=%r", motivo)
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


encaminhar_atendimento_tool = Tool(
    name="encaminhar_atendimento",
    description=(
        "Encaminha o usuário pro atendimento humano da Porto Inseguro. Use quando "
        "o pedido for sobre OUTRO produto (vida, residencial, frota, saúde, viagem, "
        "náutico, pet, moto, previdência) OU exigir ação que só humano pode fazer "
        "(alterar apólice, aprovar reembolso, cancelar contrato, registrar "
        "reclamação formal). NÃO use pra perguntas fora do domínio de seguros "
        "(história, clima, código, opinião) — pra essas, responda direto que você "
        "não trata o tema, sem chamar tool."
    ),
    parameters_schema=_ESCALAR_HUMANO_SCHEMA,
    handler=_handler_encaminhar_atendimento,
)


# =============================================================================
# Lista exposta ao agent
# =============================================================================

ALL_TOOLS: list[Tool] = [
    consultar_porto_inseguro_tool,
    cotar_seguro_auto_tool,
    encaminhar_atendimento_tool,
]
