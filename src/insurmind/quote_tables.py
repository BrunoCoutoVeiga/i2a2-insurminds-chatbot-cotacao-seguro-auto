"""Tabelas do tarifador, geradas a partir de `Precificador_Seguro_Automóvel_v2.0.xlsx`.

**NÃO EDITAR À MÃO.** Regerar com `python scripts/import_precificador.py`
quando o grupo (João Carlos + Adriele) entregar uma versão nova da planilha.

Fonte: planilha v2.0 (modificada em 2026-05-22), criada por João Carlos Mendonça.
Importada em: gerada automaticamente — ver topo do arquivo gerado.

Inconsistências da planilha tratadas:
- SKUs com FIPE = '-' em algum ano são omitidas do índice
  `FIPE_POR_CHAVE_ANO`. Em runtime, levanta QuoteUnavailableError.
- Fórmula da LEIA-ME (A13) consolida F_Idade/F_Uso/F_Bônus aplicados
  ao prêmio puro total; as CÉLULAS aplicam por componente. As células
  são a verdade canônica — replicamos exatamente, inclusive a não-aplicação
  de F_Sexo e F_Garagem no APP (atuarialmente: APP indeniza passageiros,
  não depende do condutor).
"""
from __future__ import annotations

from decimal import Decimal


# 16 SKUs (8 modelos × 2 versões) — cada um com FIPE por ano + fator_modelo.
MODELOS: list[dict] = [
    {"sku": 'M01', "chave": 'VW Polo - Track 1.0', "marca": 'VW', "modelo": 'Polo', "versao": 'Track 1.0', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.05"), "observacao": 'Versão de entrada - alto volume'},
    {"sku": 'M02', "chave": 'VW Polo - Highline TSI', "marca": 'VW', "modelo": 'Polo', "versao": 'Highline TSI', "tipo": 'Hatch', "motor": '1.0 TSI AT', "fator_modelo": Decimal("1.1"), "observacao": 'Topo de linha - valores baseados em FIPE real'},
    {"sku": 'M03', "chave": 'Fiat Argo - 1.0', "marca": 'Fiat', "modelo": 'Argo', "versao": '1.0', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.08"), "observacao": 'Hatch popular - frequência alta de roubo'},
    {"sku": 'M04', "chave": 'Fiat Argo - Trekking 1.3 CVT', "marca": 'Fiat', "modelo": 'Argo', "versao": 'Trekking 1.3 CVT', "tipo": 'Hatch', "motor": '1.3 CVT', "fator_modelo": Decimal("1.1"), "observacao": 'Topo Trekking - câmbio CVT'},
    {"sku": 'M05', "chave": 'GM - Chevrolet Onix - 1.0 MT', "marca": 'GM - Chevrolet', "modelo": 'Onix', "versao": '1.0 MT', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.07"), "observacao": 'Líder de vendas - modelo muito visado'},
    {"sku": 'M06', "chave": 'GM - Chevrolet Onix - RS Turbo AT', "marca": 'GM - Chevrolet', "modelo": 'Onix', "versao": 'RS Turbo AT', "tipo": 'Hatch', "motor": '1.0 Turbo AT', "fator_modelo": Decimal("1.12"), "observacao": 'Topo RS - perfil esportivo'},
    {"sku": 'M07', "chave": 'VW T-Cross - Sense 200 TSI', "marca": 'VW', "modelo": 'T-Cross', "versao": 'Sense 200 TSI', "tipo": 'SUV', "motor": '1.0 TSI AT', "fator_modelo": Decimal("0.98"), "observacao": 'SUV entrada - depreciação menor'},
    {"sku": 'M08', "chave": 'VW T-Cross - Highline 250 TSI', "marca": 'VW', "modelo": 'T-Cross', "versao": 'Highline 250 TSI', "tipo": 'SUV', "motor": '1.4 TSI AT', "fator_modelo": Decimal("1.02"), "observacao": 'Topo Extreme - IS alta'},
    {"sku": 'M09', "chave": 'Hyundai Creta - Comfort', "marca": 'Hyundai', "modelo": 'Creta', "versao": 'Comfort', "tipo": 'SUV', "motor": '1.0 TGDi AT', "fator_modelo": Decimal("0.96"), "observacao": 'SUV entrada - boa retenção de valor'},
    {"sku": 'M10', "chave": 'Hyundai Creta - Platinum', "marca": 'Hyundai', "modelo": 'Creta', "versao": 'Platinum', "tipo": 'SUV', "motor": '1.0 TGDi AT', "fator_modelo": Decimal("1.0"), "observacao": 'Topo Ultimate'},
    {"sku": 'M11', "chave": 'BYD Dolphin Mini - Mini', "marca": 'BYD', "modelo": 'Dolphin Mini', "versao": 'Mini', "tipo": 'Hatch EV', "motor": 'Elétrico', "fator_modelo": Decimal("1.15"), "observacao": 'Elétrico - depreciação acelerada'},
    {"sku": 'M12', "chave": 'BYD Dolphin Mini - Plus/EV', "marca": 'BYD', "modelo": 'Dolphin Mini', "versao": 'Plus/EV', "tipo": 'Hatch EV', "motor": 'Elétrico', "fator_modelo": Decimal("1.18"), "observacao": 'Elétrico topo'},
    {"sku": 'M13', "chave": 'Hyundai HB20 - Comfort 1.0', "marca": 'Hyundai', "modelo": 'HB20', "versao": 'Comfort 1.0', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.06"), "observacao": 'Hatch popular'},
    {"sku": 'M14', "chave": 'Hyundai HB20 - Platinum TGDi', "marca": 'Hyundai', "modelo": 'HB20', "versao": 'Platinum TGDi', "tipo": 'Hatch', "motor": '1.0 Turbo AT', "fator_modelo": Decimal("1.1"), "observacao": 'Topo Platinum'},
    {"sku": 'M15', "chave": 'Renault Kwid - Zen', "marca": 'Renault', "modelo": 'Kwid', "versao": 'Zen', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.12"), "observacao": 'Subcompacto - depreciação mais alta'},
    {"sku": 'M16', "chave": 'Renault Kwid - Iconic', "marca": 'Renault', "modelo": 'Kwid', "versao": 'Iconic', "tipo": 'Hatch', "motor": '1.0 MT', "fator_modelo": Decimal("1.1"), "observacao": 'Topo Iconic'},
]

FATOR_MODELO_POR_CHAVE: dict[str, Decimal] = {
    'VW Polo - Track 1.0': Decimal("1.05"),
    'VW Polo - Highline TSI': Decimal("1.1"),
    'Fiat Argo - 1.0': Decimal("1.08"),
    'Fiat Argo - Trekking 1.3 CVT': Decimal("1.1"),
    'GM - Chevrolet Onix - 1.0 MT': Decimal("1.07"),
    'GM - Chevrolet Onix - RS Turbo AT': Decimal("1.12"),
    'VW T-Cross - Sense 200 TSI': Decimal("0.98"),
    'VW T-Cross - Highline 250 TSI': Decimal("1.02"),
    'Hyundai Creta - Comfort': Decimal("0.96"),
    'Hyundai Creta - Platinum': Decimal("1.0"),
    'BYD Dolphin Mini - Mini': Decimal("1.15"),
    'BYD Dolphin Mini - Plus/EV': Decimal("1.18"),
    'Hyundai HB20 - Comfort 1.0': Decimal("1.06"),
    'Hyundai HB20 - Platinum TGDi': Decimal("1.1"),
    'Renault Kwid - Zen': Decimal("1.12"),
    'Renault Kwid - Iconic': Decimal("1.1"),
}

# FIPE por (chave, ano). Pares ausentes = SKU não existe naquele ano (foi '-' na planilha).
FIPE_POR_CHAVE_ANO: dict[tuple[str, str], Decimal] = {
    ('VW Polo - Track 1.0', '0km'): Decimal("91637.0"),
    ('VW Polo - Track 1.0', '2026'): Decimal("81509.0"),
    ('VW Polo - Track 1.0', '2025'): Decimal("75922.0"),
    ('VW Polo - Track 1.0', '2024'): Decimal("69975.0"),
    ('VW Polo - Track 1.0', '2023'): Decimal("65939.0"),
    ('VW Polo - Highline TSI', '0km'): Decimal("125260.0"),
    ('VW Polo - Highline TSI', '2026'): Decimal("111559.0"),
    ('VW Polo - Highline TSI', '2025'): Decimal("106281.0"),
    ('VW Polo - Highline TSI', '2024'): Decimal("97330.0"),
    ('VW Polo - Highline TSI', '2023'): Decimal("93468.0"),
    ('Fiat Argo - 1.0', '0km'): Decimal("87010.0"),
    ('Fiat Argo - 1.0', '2026'): Decimal("77032.0"),
    ('Fiat Argo - 1.0', '2025'): Decimal("71478.0"),
    ('Fiat Argo - 1.0', '2024'): Decimal("65889.0"),
    ('Fiat Argo - 1.0', '2023'): Decimal("62570.0"),
    ('Fiat Argo - Trekking 1.3 CVT', '0km'): Decimal("110019.0"),
    ('Fiat Argo - Trekking 1.3 CVT', '2026'): Decimal("97295.0"),
    ('Fiat Argo - Trekking 1.3 CVT', '2025'): Decimal("88958.0"),
    ('Fiat Argo - Trekking 1.3 CVT', '2024'): Decimal("86368.0"),
    ('Fiat Argo - Trekking 1.3 CVT', '2023'): Decimal("81274.0"),
    ('GM - Chevrolet Onix - 1.0 MT', '0km'): Decimal("92576.0"),
    ('GM - Chevrolet Onix - 1.0 MT', '2026'): Decimal("82413.0"),
    ('GM - Chevrolet Onix - 1.0 MT', '2025'): Decimal("71220.0"),
    ('GM - Chevrolet Onix - 1.0 MT', '2024'): Decimal("69348.0"),
    ('GM - Chevrolet Onix - 1.0 MT', '2023'): Decimal("67522.0"),
    ('GM - Chevrolet Onix - RS Turbo AT', '0km'): Decimal("122949.0"),
    ('GM - Chevrolet Onix - RS Turbo AT', '2026'): Decimal("112204.0"),
    ('GM - Chevrolet Onix - RS Turbo AT', '2025'): Decimal("100121.0"),
    ('GM - Chevrolet Onix - RS Turbo AT', '2024'): Decimal("88902.0"),
    ('GM - Chevrolet Onix - RS Turbo AT', '2023'): Decimal("81113.0"),
    ('VW T-Cross - Sense 200 TSI', '0km'): Decimal("119277.0"),
    ('VW T-Cross - Sense 200 TSI', '2026'): Decimal("112021.0"),
    ('VW T-Cross - Sense 200 TSI', '2025'): Decimal("108541.0"),
    ('VW T-Cross - Sense 200 TSI', '2024'): Decimal("101750.0"),
    ('VW T-Cross - Sense 200 TSI', '2023'): Decimal("95631.0"),
    ('VW T-Cross - Highline 250 TSI', '0km'): Decimal("177138.0"),
    ('VW T-Cross - Highline 250 TSI', '2026'): Decimal("160967.0"),
    ('VW T-Cross - Highline 250 TSI', '2025'): Decimal("143595.0"),
    ('VW T-Cross - Highline 250 TSI', '2024'): Decimal("131448.0"),
    ('VW T-Cross - Highline 250 TSI', '2023'): Decimal("124531.0"),
    ('Hyundai Creta - Comfort', '0km'): Decimal("147707.0"),
    ('Hyundai Creta - Comfort', '2026'): Decimal("132243.0"),
    ('Hyundai Creta - Comfort', '2025'): Decimal("122969.0"),
    ('Hyundai Creta - Comfort', '2024'): Decimal("112337.0"),
    ('Hyundai Creta - Comfort', '2023'): Decimal("109302.0"),
    ('Hyundai Creta - Platinum', '0km'): Decimal("181554.0"),
    ('Hyundai Creta - Platinum', '2026'): Decimal("163718.0"),
    ('Hyundai Creta - Platinum', '2025'): Decimal("144866.0"),
    ('Hyundai Creta - Platinum', '2024'): Decimal("133244.0"),
    ('Hyundai Creta - Platinum', '2023'): Decimal("120719.0"),
    ('BYD Dolphin Mini - Mini', '0km'): Decimal("120463.0"),
    ('BYD Dolphin Mini - Mini', '2026'): Decimal("109084.0"),
    ('BYD Dolphin Mini - Mini', '2025'): Decimal("105621.0"),
    ('BYD Dolphin Mini - Mini', '2024'): Decimal("98322.0"),
    ('BYD Dolphin Mini - Plus/EV', '0km'): Decimal("184800.0"),
    ('BYD Dolphin Mini - Plus/EV', '2026'): Decimal("184800.0"),
    ('BYD Dolphin Mini - Plus/EV', '2025'): Decimal("151591.0"),
    ('BYD Dolphin Mini - Plus/EV', '2024'): Decimal("141745.0"),
    ('Hyundai HB20 - Comfort 1.0', '0km'): Decimal("89525.0"),
    ('Hyundai HB20 - Comfort 1.0', '2026'): Decimal("81733.0"),
    ('Hyundai HB20 - Comfort 1.0', '2024'): Decimal("70005.0"),
    ('Hyundai HB20 - Comfort 1.0', '2023'): Decimal("64274.0"),
    ('Hyundai HB20 - Platinum TGDi', '0km'): Decimal("131126.0"),
    ('Hyundai HB20 - Platinum TGDi', '2026'): Decimal("114281.0"),
    ('Hyundai HB20 - Platinum TGDi', '2024'): Decimal("97078.0"),
    ('Hyundai HB20 - Platinum TGDi', '2023'): Decimal("90891.0"),
    ('Renault Kwid - Zen', '0km'): Decimal("69396.0"),
    ('Renault Kwid - Zen', '2026'): Decimal("62834.0"),
    ('Renault Kwid - Zen', '2025'): Decimal("56737.0"),
    ('Renault Kwid - Zen', '2024'): Decimal("52585.0"),
    ('Renault Kwid - Zen', '2023'): Decimal("49655.0"),
    ('Renault Kwid - Iconic', '0km'): Decimal("75837.0"),
    ('Renault Kwid - Iconic', '2026'): Decimal("70009.0"),
}

# Taxas-base por componente (sobre IS_FIPE / LMI_RCFV / LMI_APP).
TAXA_CASCO = Decimal("0.03")
TAXA_RCFV  = Decimal("0.008")
TAXA_APP   = Decimal("0.003")

LMI_RCFV   = Decimal("100000.0")
LMI_APP    = Decimal("20000.0")

FATOR_COBERTURA_CASCO: dict[str, Decimal] = {
    'Compreensiva': Decimal("1.0"),
    'RF+Inc+RCF-V': Decimal("0.45"),
    'Só RCF-V': Decimal("0.0"),
}

FATOR_COBERTURA_RCFV: dict[str, Decimal] = {
    'Compreensiva': Decimal("1.0"),
    'RF+Inc+RCF-V': Decimal("1.0"),
    'Só RCF-V': Decimal("1.0"),
}

FATOR_COBERTURA_APP: dict[str, Decimal] = {
    'Compreensiva': Decimal("1.0"),
    'RF+Inc+RCF-V': Decimal("0.0"),
    'Só RCF-V': Decimal("0.0"),
}

FATOR_FRANQUIA: dict[str, Decimal] = {
    'Reduzida': Decimal("1.2"),
    'Normal': Decimal("1.0"),
    'Aumentada': Decimal("0.8"),
}

FATOR_IDADE: dict[str, Decimal] = {
    '18-25': Decimal("1.8"),
    '26-30': Decimal("1.3"),
    '31-40': Decimal("1.0"),
    '41-55': Decimal("0.85"),
    '56-65': Decimal("0.95"),
    '66+': Decimal("1.15"),
}

FATOR_SEXO: dict[str, Decimal] = {
    'Masculino': Decimal("1.1"),
    'Feminino': Decimal("0.95"),
}

FATOR_USO: dict[str, Decimal] = {
    'Particular - lazer/trabalho': Decimal("1.0"),
    'Particular - alta rodagem': Decimal("1.15"),
    'Comercial - representante': Decimal("1.25"),
    'App (Uber/99)': Decimal("1.5"),
}

FATOR_GARAGEM: dict[str, Decimal] = {
    'Sim - garagem fechada': Decimal("0.92"),
    'Sim - estacionamento': Decimal("0.98"),
    'Não - rua': Decimal("1.15"),
}

FATOR_BONUS: dict[str, Decimal] = {
    'Classe 0': Decimal("1.0"),
    'Classe 1': Decimal("0.9"),
    'Classe 2': Decimal("0.82"),
    'Classe 3': Decimal("0.75"),
    'Classe 4': Decimal("0.68"),
    'Classe 5': Decimal("0.62"),
    'Classe 6': Decimal("0.58"),
    'Classe 7': Decimal("0.55"),
    'Classe 8': Decimal("0.53"),
    'Classe 9': Decimal("0.52"),
    'Classe 10': Decimal("0.5"),
}

VALOR_ASSISTENCIA: dict[str, Decimal] = {
    'Básica': Decimal("180.0"),
    'Ampliada': Decimal("360.0"),
}

CARREGAMENTO = Decimal("0.35")  # 35%: corretagem + admin + margem
IOF          = Decimal("0.0738")  # 7.38% sobre o prêmio líquido

FATOR_REGIAO: dict[str, Decimal] = {
    'São Paulo': Decimal("1.3"),
    'Rio de Janeiro': Decimal("1.45"),
    'Belo Horizonte': Decimal("1.1"),
    'Porto Alegre': Decimal("1.05"),
    'Curitiba': Decimal("1.0"),
    'Brasília': Decimal("0.95"),
}

