"""Motor de cotação do seguro auto — InsurMind / Porto Inseguro.

Replica EXATAMENTE a aba CÁLCULO da planilha
`Precificador_Seguro_Automóvel_v2.0.xlsx` (João Carlos + Adriele, 2026-05-22).

Contrato `QuoteInput` -> `list[QuoteOption]` com 3 opções variando franquia
(Reduzida / Normal / Aumentada), todas no tipo de cobertura escolhido pelo
usuário. O usuário NÃO escolhe franquia — variamos as 3 internamente pra
cumprir o DoD do João Carlos ("3 opções de preço com franquia").

Tabelas em `quote_tables.py` (geradas por `scripts/import_precificador.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from .quote_tables import (
    FIPE_POR_CHAVE_ANO, FATOR_MODELO_POR_CHAVE,
    TAXA_CASCO, TAXA_RCFV, TAXA_APP, LMI_RCFV, LMI_APP,
    FATOR_COBERTURA_CASCO, FATOR_COBERTURA_APP, FATOR_FRANQUIA,
    FATOR_IDADE, FATOR_SEXO, FATOR_USO, FATOR_GARAGEM, FATOR_BONUS,
    VALOR_ASSISTENCIA, CARREGAMENTO, IOF, FATOR_REGIAO,
)


# =============================================================================
# Tipos do contrato
# =============================================================================

Ano = Literal["0km", "2026", "2025", "2024", "2023"]
Sexo = Literal["Masculino", "Feminino"]
Cobertura = Literal["Compreensiva", "RF+Inc+RCF-V", "Só RCF-V"]
Pernoite = Literal["Sim - garagem fechada", "Sim - estacionamento", "Não - rua"]
Assistencia = Literal["Básica", "Ampliada"]
Franquia = Literal["Reduzida", "Normal", "Aumentada"]
FaixaEtaria = Literal["18-25", "26-30", "31-40", "41-55", "56-65", "66+"]


@dataclass(frozen=True)
class QuoteInput:
    """10 campos do precificador v2.0. Franquia NÃO entra — variamos 3x internamente."""
    modelo_versao: str       # uma das 16 chaves de FATOR_MODELO_POR_CHAVE
    ano: Ano
    capital: str             # uma das 6 chaves de FATOR_REGIAO
    faixa_etaria: FaixaEtaria
    sexo: Sexo
    uso: str                 # uma das 4 chaves de FATOR_USO
    pernoite: Pernoite
    classe_bonus: str        # uma das 11 chaves de FATOR_BONUS
    cobertura: Cobertura
    assistencia: Assistencia


@dataclass(frozen=True)
class QuoteOption:
    nivel_franquia: Franquia
    valor_franquia: Decimal | None   # None se cobertura = "Só RCF-V" (sem casco)
    premio_anual: Decimal
    premio_mensal: Decimal
    coberturas: list[str]
    avisos: list[str] = field(default_factory=list)


class QuoteUnavailableError(Exception):
    """Combinação modelo×ano inexistente na planilha (FIPE = '-')."""
    def __init__(self, modelo_versao: str, ano: str, anos_disponiveis: list[str]):
        self.modelo_versao = modelo_versao
        self.ano = ano
        self.anos_disponiveis = anos_disponiveis
        super().__init__(
            f"{modelo_versao!r} não tem valor FIPE para {ano!r}. "
            f"Anos disponíveis: {', '.join(anos_disponiveis)}."
        )


# =============================================================================
# Constantes auxiliares
# =============================================================================

# Franquia em sinistro de casco como % do FIPE. A planilha não explicita o valor
# em R$ — só os fatores que afetam o prêmio. Adoto razão 1:2:4 que a LEIA-ME
# da planilha declara: "Reduzida = 50% da normal" e "Aumentada = 200% da normal".
# Base 4% = típico de mercado pra carros nesta faixa de valor.
PCT_FRANQUIA: dict[Franquia, Decimal] = {
    "Reduzida":  Decimal("0.02"),  # 2% do FIPE
    "Normal":    Decimal("0.04"),  # 4% do FIPE
    "Aumentada": Decimal("0.08"),  # 8% do FIPE
}

COBERTURAS_INCLUSAS: dict[Cobertura, list[str]] = {
    "Compreensiva": [
        "Casco — colisão, incêndio, roubo/furto, danos da natureza",
        f"RCF-V — danos a terceiros (LMI R$ {int(LMI_RCFV):,})".replace(",", "."),
        f"APP — acidentes pessoais de passageiros (LMI R$ {int(LMI_APP):,})".replace(",", "."),
        "Assistência 24h (conforme nível escolhido)",
    ],
    "RF+Inc+RCF-V": [
        "Casco SOMENTE para roubo, furto e incêndio (sem colisão)",
        f"RCF-V — danos a terceiros (LMI R$ {int(LMI_RCFV):,})".replace(",", "."),
        "Assistência 24h (conforme nível escolhido)",
    ],
    "Só RCF-V": [
        f"RCF-V — danos a terceiros (LMI R$ {int(LMI_RCFV):,})".replace(",", "."),
        "Sem casco e sem APP",
    ],
}

AVISOS_PADRAO = [
    "⚠️ Valores simulados para fins acadêmicos — trabalho do curso I2A2 InsurMinds.",
    "Não constituem oferta vinculante da Porto Inseguro (empresa fictícia).",
    "Para uma cotação real, consulte um corretor de seguros habilitado pela SUSEP.",
]


# =============================================================================
# Cálculo (espelho fiel da aba CÁLCULO da planilha v2.0)
# =============================================================================

def _arred(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _resolver_is_fipe(modelo_versao: str, ano: str) -> Decimal:
    """Lookup IS_FIPE. Levanta QuoteUnavailableError se par ausente."""
    if modelo_versao not in FATOR_MODELO_POR_CHAVE:
        raise ValueError(
            f"Modelo {modelo_versao!r} não está no catálogo. Modelos válidos: "
            f"{list(FATOR_MODELO_POR_CHAVE.keys())}"
        )
    if (modelo_versao, ano) not in FIPE_POR_CHAVE_ANO:
        anos = sorted(a for (m, a) in FIPE_POR_CHAVE_ANO if m == modelo_versao)
        raise QuoteUnavailableError(modelo_versao, ano, anos)
    return FIPE_POR_CHAVE_ANO[(modelo_versao, ano)]


def _premio_uma_franquia(input: QuoteInput, franquia: Franquia) -> tuple[Decimal, Decimal | None]:
    """Calcula prêmio total anual + valor da franquia em sinistro para UMA franquia.

    Replica as células B17:B25 da aba CÁLCULO (planilha v2.0).
    Retorna (premio_total_anual, valor_franquia_sinistro).
    """
    is_fipe = _resolver_is_fipe(input.modelo_versao, input.ano)

    # Lookups de fatores (espelhando INDEX/MATCH e VLOOKUP da planilha)
    f_modelo    = FATOR_MODELO_POR_CHAVE[input.modelo_versao]
    f_regiao    = FATOR_REGIAO[input.capital]
    f_idade     = FATOR_IDADE[input.faixa_etaria]
    f_sexo      = FATOR_SEXO[input.sexo]
    f_uso       = FATOR_USO[input.uso]
    f_garagem   = FATOR_GARAGEM[input.pernoite]
    f_bonus     = FATOR_BONUS[input.classe_bonus]
    f_cob_casco = FATOR_COBERTURA_CASCO[input.cobertura]
    f_cob_app   = FATOR_COBERTURA_APP[input.cobertura]
    f_franquia  = FATOR_FRANQUIA[franquia]
    val_assist  = VALOR_ASSISTENCIA[input.assistencia]

    # Casco (B17) — fator zero se cobertura = "Só RCF-V"
    premio_casco = (
        is_fipe * TAXA_CASCO * f_modelo * f_regiao * f_cob_casco * f_franquia
        * f_idade * f_sexo * f_uso * f_garagem * f_bonus
    )

    # RCF-V (B18) — F_Cobertura_RCFV é sempre 1, então omitido. F_Sexo e F_Garagem aplicados.
    premio_rcfv = LMI_RCFV * TAXA_RCFV * f_idade * f_sexo * f_uso * f_garagem * f_bonus

    # APP (B19) — só na Compreensiva (f_cob_app=0 nas outras zera). Sem F_Sexo nem F_Garagem.
    premio_app = LMI_APP * TAXA_APP * f_cob_app * f_idade * f_uso * f_bonus

    # Assistência 24h (B20) — valor fixo, sem aplicação de fatores
    premio_assist = val_assist

    # Prêmio puro total (B21)
    premio_puro = premio_casco + premio_rcfv + premio_app + premio_assist

    # Carregamento (B22) e líquido (B23): premio_puro / (1 - 0.35)
    premio_liquido = premio_puro / (Decimal("1") - CARREGAMENTO)

    # IOF (B24) e prêmio total anual (B25)
    premio_total = premio_liquido * (Decimal("1") + IOF)

    # Valor da franquia em sinistro de casco (% do FIPE). N/A se cobertura sem casco.
    valor_franquia = None
    if input.cobertura != "Só RCF-V":
        valor_franquia = _arred(is_fipe * PCT_FRANQUIA[franquia])

    return _arred(premio_total), valor_franquia


def compute_quote(input: QuoteInput) -> list[QuoteOption]:
    """Devolve 3 opções de franquia (Reduzida/Normal/Aumentada) pro tipo de
    cobertura escolhido. Determinístico.

    Levanta `QuoteUnavailableError` se o par (modelo, ano) não existe na planilha.
    """
    opcoes: list[QuoteOption] = []
    for nivel in ("Reduzida", "Normal", "Aumentada"):
        premio_total, valor_franquia = _premio_uma_franquia(input, nivel)
        opcoes.append(QuoteOption(
            nivel_franquia=nivel,
            valor_franquia=valor_franquia,
            premio_anual=premio_total,
            premio_mensal=_arred(premio_total / Decimal("12")),
            coberturas=COBERTURAS_INCLUSAS[input.cobertura],
            avisos=AVISOS_PADRAO,
        ))
    return opcoes


# =============================================================================
# Smoke test — replica o exemplo da própria planilha v2.0
# =============================================================================

if __name__ == "__main__":
    # Exemplo da planilha (CÁLCULO B4:B14): VW Polo Highline TSI 2026, SP,
    # 41-55, Masculino, Particular lazer/trabalho, garagem fechada, Classe 4,
    # Compreensiva, FRANQUIA Reduzida, Assistência Ampliada → R$ 6.974,66/ano.
    sample = QuoteInput(
        modelo_versao="VW Polo - Highline TSI",
        ano="2026",
        capital="São Paulo",
        faixa_etaria="41-55",
        sexo="Masculino",
        uso="Particular - lazer/trabalho",
        pernoite="Sim - garagem fechada",
        classe_bonus="Classe 4",
        cobertura="Compreensiva",
        assistencia="Ampliada",
    )
    opcoes = compute_quote(sample)
    print(f"Cotação {sample.modelo_versao} {sample.ano} | {sample.capital} | "
          f"{sample.sexo} {sample.faixa_etaria} | {sample.cobertura} | "
          f"Assistência {sample.assistencia}\n")
    for o in opcoes:
        franq = f"R$ {o.valor_franquia:>10,.2f}" if o.valor_franquia else "N/A (sem casco)"
        print(f"  Franquia {o.nivel_franquia:>10}:  "
              f"prêmio anual R$ {o.premio_anual:>10,.2f}  "
              f"(mensal R$ {o.premio_mensal:>8,.2f})  "
              f"franquia em sinistro {franq}")
    print(f"\nReferência da planilha (CÁLCULO B25, franquia Reduzida): R$ 6.974,66/ano")
    print(f"Computado pelo código (franquia Reduzida):                R$ {opcoes[0].premio_anual:,.2f}/ano")
