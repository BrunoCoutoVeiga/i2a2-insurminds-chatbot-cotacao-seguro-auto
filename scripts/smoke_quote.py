"""Smoke tests do motor de cotação — feliz + adversariais.

Pra rodar antes de cada deploy. Não substitui suite completa de testes; serve
pra pegar regressões grossas em <1s. Histórico:

- 2026-05-26: criado após descoberta em prod de fallback silencioso do mock
  antigo (`Fiat Estilo IE 2007` retornava cotação calculada pela média dos 8
  modelos do mock, sem aviso). Hoje o schema da tool tem `enum` fechado e o
  motor levanta `ValueError` / `QuoteUnavailableError` em vez de inventar.
  Detalhes em RELATORIO.md sessão "2026-05-26 (tarde) — QA adversarial".

Uso:
    .\\.venv\\Scripts\\python.exe scripts/smoke_quote.py
    # Exit code 0 se tudo passou; 1 se algum caso quebrou.
"""
from __future__ import annotations

import asyncio
import sys
import traceback

from insurmind.quote import compute_quote, QuoteInput, QuoteUnavailableError
from insurmind.tools import cotar_seguro_auto_tool

# Cores ANSI pra terminal Windows moderno
GREEN, RED, RESET = "\033[92m", "\033[91m", "\033[0m"


PASSED: list[str] = []
FAILED: list[tuple[str, str]] = []


def expect(label: str, cond: bool, detail: str = ""):
    """Imprime e registra resultado de uma asserção."""
    if cond:
        print(f"  {GREEN}OK{RESET}  {label}")
        PASSED.append(label)
    else:
        print(f"  {RED}FAIL{RESET} {label}  -- {detail}")
        FAILED.append((label, detail))


# =============================================================================
# Caso 1 — Feliz: bate ao centavo com o exemplo da CÁLCULO da planilha
# =============================================================================

def caso_planilha_exemplo():
    print("\n[1] Replica exemplo da planilha (CÁLCULO B25, franquia Reduzida)")
    qin = QuoteInput(
        modelo_versao="VW Polo - Highline TSI", ano="2026", capital="São Paulo",
        faixa_etaria="41-55", sexo="Masculino", uso="Particular - lazer/trabalho",
        pernoite="Sim - garagem fechada", classe_bonus="Classe 4",
        cobertura="Compreensiva", assistencia="Ampliada",
    )
    opcoes = compute_quote(qin)
    expect("3 opções devolvidas", len(opcoes) == 3, f"got {len(opcoes)}")
    expect("Reduzida = R$ 6.974,66 (planilha)",
           str(opcoes[0].premio_anual) == "6974.66",
           f"got {opcoes[0].premio_anual}")
    expect("Reduzida > Normal > Aumentada (ordem decrescente do prêmio)",
           opcoes[0].premio_anual > opcoes[1].premio_anual > opcoes[2].premio_anual)
    expect("Reduzida < Normal < Aumentada (ordem crescente da franquia)",
           opcoes[0].valor_franquia < opcoes[1].valor_franquia < opcoes[2].valor_franquia)


# =============================================================================
# Caso 2 — Adversarial: modelo fora do catálogo
# =============================================================================

def caso_modelo_inexistente():
    print("\n[2] Modelo fora do catálogo deve levantar ValueError (não inventar cotação)")
    qin = QuoteInput(
        modelo_versao="Fiat Estilo IE", ano="2026", capital="São Paulo",
        faixa_etaria="31-40", sexo="Masculino", uso="Particular - lazer/trabalho",
        pernoite="Sim - garagem fechada", classe_bonus="Classe 0",
        cobertura="Compreensiva", assistencia="Básica",
    )
    try:
        result = compute_quote(qin)
        expect("compute_quote levanta ValueError", False,
               f"NÃO levantou — devolveu {result}")
    except ValueError as e:
        expect("compute_quote levanta ValueError",
               "Modelo" in str(e) and "catálogo" in str(e),
               f"mensagem foi {e!r}")
    except Exception as e:
        expect("compute_quote levanta ValueError", False,
               f"levantou {type(e).__name__} em vez de ValueError: {e}")


# =============================================================================
# Caso 3 — Adversarial: combinação modelo×ano sem FIPE na planilha
# =============================================================================

def caso_ano_indisponivel():
    print("\n[3] Modelo válido mas ano sem FIPE → QuoteUnavailableError com anos_disponiveis")
    qin = QuoteInput(
        modelo_versao="Renault Kwid - Iconic", ano="2023", capital="São Paulo",
        faixa_etaria="31-40", sexo="Feminino", uso="Particular - lazer/trabalho",
        pernoite="Sim - garagem fechada", classe_bonus="Classe 5",
        cobertura="Compreensiva", assistencia="Básica",
    )
    try:
        compute_quote(qin)
        expect("levanta QuoteUnavailableError", False, "não levantou")
    except QuoteUnavailableError as e:
        expect("levanta QuoteUnavailableError", True)
        expect("anos_disponiveis preenchido",
               len(e.anos_disponiveis) > 0,
               f"got {e.anos_disponiveis}")
        expect("modelo + ano expostos na exceção",
               e.modelo_versao == "Renault Kwid - Iconic" and e.ano == "2023")


# =============================================================================
# Caso 4 — Adversarial: cobertura "Só RCF-V" sem casco
# =============================================================================

def caso_so_rcfv_sem_franquia():
    print("\n[4] Cobertura Só RCF-V → valor_franquia=None (sem casco, sem franquia)")
    qin = QuoteInput(
        modelo_versao="Fiat Argo - 1.0", ano="2024", capital="Curitiba",
        faixa_etaria="31-40", sexo="Feminino", uso="Particular - lazer/trabalho",
        pernoite="Sim - garagem fechada", classe_bonus="Classe 0",
        cobertura="Só RCF-V", assistencia="Básica",
    )
    opcoes = compute_quote(qin)
    expect("3 opções mesmo sem casco", len(opcoes) == 3)
    expect("valor_franquia é None nas 3 opções",
           all(o.valor_franquia is None for o in opcoes))
    expect("prêmios das 3 são IDÊNTICOS (fator franquia não afeta sem casco)",
           opcoes[0].premio_anual == opcoes[1].premio_anual == opcoes[2].premio_anual)


# =============================================================================
# Caso 5 — Handler da tool: modelo inválido devolve mensagem amigável,
#                          NÃO crasha o agent
# =============================================================================

def caso_handler_tool_fallback():
    print("\n[5] Handler da tool com modelo inválido → mensagem amigável (não crash)")
    args = {
        "modelo_versao": "Fiat Estilo IE",  # fora do catálogo
        "ano": "2026", "capital": "São Paulo", "faixa_etaria": "31-40",
        "sexo": "Masculino", "uso": "Particular - lazer/trabalho",
        "pernoite": "Sim - garagem fechada", "classe_bonus": "Classe 0",
        "cobertura": "Compreensiva", "assistencia": "Básica",
    }
    result = asyncio.run(cotar_seguro_auto_tool.handler(args))
    text = result.get("text", "")
    expect("handler devolveu dict com 'text'", "text" in result and bool(text))
    expect("texto menciona 'inválido' ou 'indisponível' (não vaza R$ inventado)",
           "inválido" in text.lower() or "indisponível" in text.lower() or "não tenho cotação" in text.lower(),
           f"texto foi: {text[:200]!r}")
    expect("texto NÃO contém valor monetário inventado (R$ X,YY)",
           "R$ " not in text or "0,00" in text,
           f"texto suspeito: {text[:200]!r}")


# =============================================================================
# Caso 6 — Sanidade do schema enum (a LLM não pode passar valor fora dos enums)
# =============================================================================

def caso_schema_enum_fechado():
    print("\n[6] Schema da tool tem enums fechados (LLM não pode passar valor livre)")
    schema = cotar_seguro_auto_tool.parameters_schema
    props = schema["properties"]
    for campo in ("modelo_versao", "ano", "capital", "faixa_etaria",
                  "sexo", "uso", "pernoite", "classe_bonus",
                  "cobertura", "assistencia"):
        expect(f"{campo} tem enum fechado",
               "enum" in props[campo] and len(props[campo]["enum"]) > 0,
               f"props[{campo}] = {props[campo]}")
    expect("modelo_versao tem exatamente 16 SKUs",
           len(props["modelo_versao"]["enum"]) == 16,
           f"got {len(props['modelo_versao']['enum'])}")
    expect("'Fiat Estilo IE' NÃO está no enum modelo_versao",
           "Fiat Estilo IE" not in props["modelo_versao"]["enum"])


# =============================================================================
# Runner
# =============================================================================

def main():
    print("="*72)
    print("SMOKE TESTS — motor de cotação (feliz + adversariais)")
    print("="*72)

    for caso in (caso_planilha_exemplo, caso_modelo_inexistente,
                 caso_ano_indisponivel, caso_so_rcfv_sem_franquia,
                 caso_handler_tool_fallback, caso_schema_enum_fechado):
        try:
            caso()
        except Exception:
            print(f"  {RED}CRASH{RESET} em {caso.__name__}:")
            traceback.print_exc()
            FAILED.append((caso.__name__, "crashou — ver traceback"))

    print("\n" + "="*72)
    print(f"RESUMO: {GREEN}{len(PASSED)} OK{RESET}, {RED}{len(FAILED)} FAIL{RESET}")
    print("="*72)
    if FAILED:
        for label, detail in FAILED:
            print(f"  - {label}: {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
