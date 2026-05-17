"""Motor de cotação simulado (mock) — InsurMind / Porto Inseguro.

Contrato `QuoteInput` -> `list[QuoteOption]` com 3 opções variando franquia
(reduzida / normal / aumentada), todas no tipo de cobertura escolhido pelo
usuário. Especificação completa em `docs/visao-geral-do-chatbot.md` §6 e em
`RELATORIO.md` ("2026-05-16 — Especificação do mock de cotação").

**Interface estável**: quando a planilha real do João Carlos + Adriele chegar,
**substitua apenas o miolo de `compute_quote_mock`** mantendo a assinatura
idêntica. Toda a cadeia acima (LLM, agent, UI, testes) permanece igual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


# =============================================================================
# Tipos do contrato
# =============================================================================

EstadoCivil = Literal["solteiro", "casado", "divorciado", "viuvo", "uniao_estavel"]
Sexo = Literal["M", "F"]
Uso = Literal["particular", "trabalho", "aplicativo"]
TipoCobertura = Literal["compreensiva", "roubo_furto", "basica_terceiros"]
NivelFranquia = Literal["reduzida", "normal", "aumentada"]


@dataclass(frozen=True)
class QuoteInput:
    """8 perguntas da especificação Adriele (2026-05-16). 13 campos no total."""
    # Veículo
    modelo: str                          # ex.: "Polo", "Onix"
    versao: str                          # ex.: "Highline", "entrada"
    ano: int                             # ex.: 2026

    # Localização
    cep_pernoite: str                    # 8 dígitos (com ou sem hífen)

    # Condutor principal
    data_nascimento: str                 # "DD/MM/YYYY"
    sexo: Sexo
    estado_civil: EstadoCivil

    # Uso e proteção
    uso: Uso
    garagem_casa: bool
    garagem_trabalho: bool
    garagem_fim_de_semana: bool

    # Outros condutores
    ha_condutor_menor_25: bool

    # Tipo de cobertura escolhida
    tipo_cobertura: TipoCobertura


@dataclass(frozen=True)
class QuoteOption:
    nivel_franquia: NivelFranquia
    valor_franquia: Decimal
    premio_anual: Decimal
    coberturas: list[str]
    avisos: list[str] = field(default_factory=list)


# =============================================================================
# Tabelas do tarifador mock (calibradas a mão por Bruno em 2026-05-16,
# refletindo ordem de grandeza realista; serão substituídas pela planilha
# do grupo quando estiver pronta).
#
# **Valores in-memory, didáticos, NÃO refletem mercado real.**
# =============================================================================

# Valor médio zero-km dos 8 modelos mais vendidos no Brasil
MODELOS_VALOR_FIPE: dict[str, Decimal] = {
    "polo":    Decimal("95000"),
    "argo":    Decimal("78000"),
    "onix":    Decimal("88000"),
    "t-cross": Decimal("140000"),
    "creta":   Decimal("135000"),
    "dolphin": Decimal("160000"),  # BYD elétrico
    "hb20":    Decimal("85000"),
    "kwid":    Decimal("68000"),
}

# Percentual base do prêmio anual sobre o valor FIPE, por tipo de cobertura
PREMIO_BASE_PCT: dict[TipoCobertura, Decimal] = {
    "compreensiva":     Decimal("0.045"),  # 4.5% — cobre tudo
    "roubo_furto":      Decimal("0.028"),  # 2.8% — só roubo/furto/incêndio + RCF-V
    "basica_terceiros": Decimal("0.012"),  # 1.2% — só RCF-V (terceiros)
}

# Fatores multiplicativos sobre o prêmio base
FATOR_SEXO: dict[Sexo, Decimal] = {
    "M": Decimal("1.05"),
    "F": Decimal("0.95"),
}

FATOR_ESTADO_CIVIL: dict[EstadoCivil, Decimal] = {
    "solteiro":      Decimal("1.05"),
    "casado":        Decimal("0.95"),
    "uniao_estavel": Decimal("0.95"),
    "divorciado":    Decimal("1.00"),
    "viuvo":         Decimal("1.00"),
}

FATOR_USO: dict[Uso, Decimal] = {
    "particular": Decimal("1.00"),
    "trabalho":   Decimal("1.15"),
    "aplicativo": Decimal("1.40"),
}

# Fator por idade (faixas)
def _fator_idade(idade: int) -> Decimal:
    if idade < 25:   return Decimal("1.45")
    if idade < 30:   return Decimal("1.15")
    if idade < 40:   return Decimal("1.00")
    if idade < 50:   return Decimal("0.92")
    if idade < 65:   return Decimal("0.88")
    return Decimal("0.95")  # idosos: leve aumento

# Fator por nº de "garagem sim" (0 a 3)
_FATOR_GARAGEM = {
    0: Decimal("1.20"),
    1: Decimal("1.05"),
    2: Decimal("0.95"),
    3: Decimal("0.88"),
}

FATOR_MENOR_25 = Decimal("1.25")  # se ha_condutor_menor_25 = True

# Fator por região (2 primeiros dígitos do CEP). Cobertura simplificada:
# capitais SP/RJ caras, sul/SC/PR baratos, NE médio.
def _fator_regiao(cep: str) -> Decimal:
    digits = "".join(c for c in cep if c.isdigit())
    if len(digits) < 2:
        return Decimal("1.00")
    prefix = int(digits[:2])
    # SP capital + grande SP
    if 1 <= prefix <= 9:    return Decimal("1.25")
    if 10 <= prefix <= 19:  return Decimal("1.15")
    # RJ capital + interior
    if 20 <= prefix <= 23:  return Decimal("1.20")
    if 24 <= prefix <= 28:  return Decimal("1.05")
    # MG
    if 30 <= prefix <= 39:  return Decimal("0.98")
    # BA / SE
    if 40 <= prefix <= 49:  return Decimal("1.05")
    # NE (PE, AL, PB, RN, CE, PI, MA)
    if 50 <= prefix <= 65:  return Decimal("1.08")
    # Norte (PA, AM, AC, RR, RO, AP, TO)
    if 66 <= prefix <= 77:  return Decimal("1.12")
    # Centro-oeste (DF, GO, MT, MS)
    if 70 <= prefix <= 79:  return Decimal("1.02")
    # Sul (PR, SC, RS) — historicamente menor sinistralidade
    if 80 <= prefix <= 99:  return Decimal("0.92")
    return Decimal("1.00")

# Configuração das franquias (% do valor do veículo + ajuste do prêmio)
FRANQUIA_CONFIG: dict[NivelFranquia, tuple[Decimal, Decimal]] = {
    # nivel: (pct_franquia_sobre_fipe, ajuste_premio)
    "reduzida":  (Decimal("0.020"), Decimal("1.18")),   # franquia 2% / prêmio +18%
    "normal":    (Decimal("0.035"), Decimal("1.00")),   # franquia 3.5% / prêmio base
    "aumentada": (Decimal("0.055"), Decimal("0.85")),   # franquia 5.5% / prêmio -15%
}

# Lista de coberturas incluídas por tipo
COBERTURAS_POR_TIPO: dict[TipoCobertura, list[str]] = {
    "compreensiva": [
        "Casco (colisão, incêndio, roubo/furto)",
        "RCF-V Danos Materiais a terceiros (LMI R$ 100.000)",
        "RCF-V Danos Corporais a terceiros (LMI R$ 100.000)",
        "APP — Acidentes Pessoais a Passageiros (LMI R$ 20.000)",
        "Assistência 24h básica (guincho até 300km, chaveiro, pane seca)",
    ],
    "roubo_furto": [
        "Casco apenas para roubo, furto e incêndio (sem colisão)",
        "RCF-V Danos Materiais a terceiros (LMI R$ 100.000)",
        "RCF-V Danos Corporais a terceiros (LMI R$ 100.000)",
        "Assistência 24h básica (guincho até 300km, chaveiro)",
    ],
    "basica_terceiros": [
        "RCF-V Danos Materiais a terceiros (LMI R$ 50.000)",
        "RCF-V Danos Corporais a terceiros (LMI R$ 50.000)",
    ],
}

# Carregamento (despesas + comissão) e tributo
CARREGAMENTO = Decimal("1.30")   # 30% sobre o prêmio puro
IOF = Decimal("1.0738")          # 7.38% sobre o prêmio líquido

AVISOS_PADRAO = [
    "⚠️ Valores simulados para fins acadêmicos — trabalho do curso I2A2 InsurMinds.",
    "Não constituem oferta vinculante da Porto Inseguro (empresa fictícia).",
    "Para uma cotação real, consulte um corretor de seguros habilitado pela SUSEP.",
]


# =============================================================================
# Cálculos auxiliares
# =============================================================================

def _idade_do_condutor(data_nascimento: str, hoje: date | None = None) -> int:
    """Calcula idade em anos completos. `hoje` permite testes determinísticos."""
    hoje = hoje or date.today()
    nasc = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
    idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
    return max(0, idade)


def _valor_fipe(modelo: str) -> Decimal:
    """Busca o valor FIPE do modelo (case-insensitive); fallback didático se desconhecido."""
    key = modelo.strip().lower()
    if key in MODELOS_VALOR_FIPE:
        return MODELOS_VALOR_FIPE[key]
    # Fallback: média dos 8 modelos. O agente também pode escalar humano nesses casos.
    media = sum(MODELOS_VALOR_FIPE.values(), Decimal("0")) / Decimal(len(MODELOS_VALOR_FIPE))
    return media.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _arred(v: Decimal) -> Decimal:
    """Arredonda pra 2 casas decimais (centavos)."""
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =============================================================================
# Função principal
# =============================================================================

def compute_quote_mock(input: QuoteInput, _hoje: date | None = None) -> list[QuoteOption]:
    """Devolve 3 opções de franquia (reduzida/normal/aumentada) para o tipo
    de cobertura escolhido pelo usuário. Determinístico — sem aleatoriedade.

    `_hoje` é injetável apenas pra testes; em uso normal usa `date.today()`.
    """
    valor_fipe = _valor_fipe(input.modelo)
    idade = _idade_do_condutor(input.data_nascimento, _hoje)

    # Prêmio puro = valor × pct base × cadeia de fatores
    premio_puro = valor_fipe * PREMIO_BASE_PCT[input.tipo_cobertura]
    premio_puro *= _fator_idade(idade)
    premio_puro *= FATOR_SEXO[input.sexo]
    premio_puro *= FATOR_ESTADO_CIVIL[input.estado_civil]
    premio_puro *= FATOR_USO[input.uso]
    premio_puro *= _FATOR_GARAGEM[
        sum([input.garagem_casa, input.garagem_trabalho, input.garagem_fim_de_semana])
    ]
    if input.ha_condutor_menor_25:
        premio_puro *= FATOR_MENOR_25
    premio_puro *= _fator_regiao(input.cep_pernoite)

    # Aplicar carregamento e IOF
    premio_liquido = premio_puro * CARREGAMENTO
    premio_final_base = premio_liquido * IOF

    coberturas = COBERTURAS_POR_TIPO[input.tipo_cobertura]
    opcoes: list[QuoteOption] = []

    for nivel in ("reduzida", "normal", "aumentada"):
        pct_franquia, ajuste = FRANQUIA_CONFIG[nivel]
        opcoes.append(QuoteOption(
            nivel_franquia=nivel,
            valor_franquia=_arred(valor_fipe * pct_franquia),
            premio_anual=_arred(premio_final_base * ajuste),
            coberturas=coberturas,
            avisos=AVISOS_PADRAO,
        ))

    return opcoes


# =============================================================================
# Smoke test mínimo — `python -m insurmind.quote` roda um exemplo determinístico
# =============================================================================

if __name__ == "__main__":
    # Exemplo da spec da Adriele: Polo Highline 2026, condutor 35 anos casado em SP,
    # garagem casa+trabalho, sem condutor jovem, cobertura compreensiva.
    sample = QuoteInput(
        modelo="Polo",
        versao="Highline",
        ano=2026,
        cep_pernoite="01310-100",
        data_nascimento="15/03/1990",
        sexo="M",
        estado_civil="casado",
        uso="particular",
        garagem_casa=True,
        garagem_trabalho=True,
        garagem_fim_de_semana=False,
        ha_condutor_menor_25=False,
        tipo_cobertura="compreensiva",
    )
    # Usa data fixa pra determinismo
    opcoes = compute_quote_mock(sample, _hoje=date(2026, 5, 16))

    print(f"Cotação Polo Highline 2026, cobertura compreensiva, SP:")
    for o in opcoes:
        print(f"  [{o.nivel_franquia:>10}]  prêmio anual R$ {o.premio_anual:>10,.2f}  "
              f"franquia R$ {o.valor_franquia:>10,.2f}")
    print(f"\nCoberturas inclusas ({len(opcoes[0].coberturas)}):")
    for c in opcoes[0].coberturas:
        print(f"  • {c}")
