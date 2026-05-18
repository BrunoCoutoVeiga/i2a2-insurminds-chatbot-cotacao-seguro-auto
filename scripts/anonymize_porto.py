"""
Anonimiza referências à Porto Seguro (empresa real) na base de conhecimento
(`data/kb/*.md`), substituindo por "Porto Inseguro" (fictícia, didática).

Motivo: a Atividade Obrigatória 2 do curso I2A2 InsurMinds é um trabalho
acadêmico. Para evitar conflito de marca, direitos autorais ou aparência
de endosso comercial, todo o conteúdo que vai ao RAG/chatbot é anonimizado.

O que é substituído:
- Nome da empresa em todas as variantes (Porto Seguro, Porto Bank, Porto Socorro,
  App Porto, Centros Automotivos Porto, Portoseg S.A, etc.)
- Telefones de contato (10 números mapeados para fictícios)
- CNPJ da Porto Seguro (61.198.164/0001-60 -> 00.000.000/0001-00)
- URLs (portoseguro.com.br e variantes -> portoinseguro.com.br)
- Nome do diretor (Jaime Soares -> Jaime Fictício)

O que é PRESERVADO:
- Cidades que contêm "Porto" no nome (Porto Alegre, Porto Feliz, Porto Ferreira,
  Porto Velho) — usam "###CITY-N###" como placeholder temporário.
- SUSEP, FENACOR, FENASEG, IPVA, DPVAT — entidades regulatórias/públicas reais.
- Conteúdo dos arquivos brutos em `meetings/` (audit trail mantido com referências
  reais para evidência do processo de coleta).
- Scripts (`scripts/fetch_porto_faq.py`, etc.) — mantêm URLs reais para serem
  reproduzíveis se o conteúdo da Porto for atualizado.

Uso:
    python scripts/anonymize_porto.py [--dry-run] [--verbose]

Idempotente: pode ser rodado várias vezes sem efeito colateral.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# --- Cidades reais BR contendo "Porto" no nome — protegidas durante o processamento ---
# Lista derivada das cidades de abrangência do CG142 da Porto Seguro (várias UFs).
# Se mais cidades aparecerem no conteúdo, adicionar aqui.
CITIES = [
    'Porto Alegre',     # RS
    'Porto Feliz',      # SP
    'Porto Ferreira',   # SP
    'Porto Velho',      # RO
    'Porto Acre',       # AC
    'Porto Amazonas',   # PR
    'Porto Vitória',    # PR
    'Porto do Mangue',  # RN
    'Porto Lucena',     # RS
    'Porto Mauá',       # RS
    'Porto Vera Cruz',  # RS
    'Porto Xavier',     # RS
    'Porto Real',       # RJ
    'Porto Belo',       # SC
    'Porto da Folha',   # SE
    'Porto Nacional',   # TO
    'Senhora do Porto', # MG
]

# --- Telefones reais da Porto Seguro -> fictícios ---
# Convenção: prefixo "0000" pra indicar claramente que é fictício.
PHONE_REPLACEMENTS = [
    # WhatsApp principal — variantes com ou sem parênteses (alguns textos escrevem "11 3003-9303")
    (r'\(?11\)?\s+3003[\s\-]?9303', '(11) 0000-0001'),
    # SAC e atendimento auto
    (r'\(?11\)?\s+3366[\s\-]?3645', '(11) 0000-0002'),
    (r'\(?11\)?\s+3366[\s\-]?3330', '(11) 0000-0003'),
    (r'\(?11\)?\s+3366[\s\-]?3377', '(11) 0000-0004'),

    # === Capitais e grandes centros: 4004-XXXX (família "famosa" Porto Seguro) ===
    # Regras específicas conhecidas
    (r'\(?11\)?\s+4004[\s\-]?767[68]',  '(11) 0000-0005'),
    (r'\(?11\)?\s+333[\s\-]?76786',     '(11) 0000-0006'),
    # Variantes alfanuméricas branded (sempre uppercase em material oficial Porto)
    (r'\b4004[\s\-]?PORTO\b',           '(11) 0000-0005'),  # 4004-PORTO
    (r'\b333[\s\-]?PORTO\b',            '(11) 0000-0006'),  # 333-PORTO
    (r'\b3337[\s\-]?6786\b',            '(11) 0000-0006'),  # 3337-6786 (mesmo que 333-PORTO)
    # Catch-all 4004-XXXXX genérico (qualquer número 4-5 dígitos após 4004-)
    # Cobre: 4004-76786, 4004-3600, 4004-5215, e quaisquer outras variantes
    # Porto Seguro de cartão/produto. Após as regras mais específicas acima
    # como guard, esse cai pra qualquer 4004- restante.
    (r'\b4004[\s\-]?\d{4,5}\b',         '(11) 0000-0005'),

    # === Centrais 0300 ===
    (r'0300\s*33\s*76786',              '0300 0000-0001'),
    (r'0300\s*33\s*7676',               '0300 0000-0002'),
    (r'0300\s*3376786',                 '0300 0000-0001'),

    # === 0800s da Porto Seguro ===
    (r'0800\s*727\s*8736',              '0800 0000-0001'),  # deficiência auditiva
    (r'0800\s*727\s*2766',              '0800 0000-0002'),  # SAC
    (r'0800\s*727\s*1184',              '0800 0000-0003'),  # Ouvidoria
    (r'0800\s*727\s*9393',              '0800 0000-0004'),  # outras localidades
    (r'0800\s*701\s*5582',              '0800 0000-0005'),
    (r'0800\s*727\s*7477',              '0800 0000-0006'),
    # Catch-all pros demais 0800-727-XXXX (família Porto)
    # Cobre: 0800-727-0800 e outros que possam aparecer
    # NOTA: 0800 218484 é da SUSEP — não bate aqui (727 ≠ 218).
    (r'0800[\s\-]?727[\s\-]?\d{3,4}',   '0800 0000-0007'),
]

# --- Substituições principais (ordem importa: multi-word primeiro) ---
TEXT_REPLACEMENTS = [
    # === Nomes corporativos completos ===
    (r'Porto Seguro Cia\. Brasileira de Seguros',
     'Porto Inseguro Cia. Fictícia de Seguros'),

    # === Sub-marcas e produtos com "Porto Seguro" no nome ===
    (r'Porto Seguro Auto Jovem',     'Porto Inseguro Auto Jovem'),
    (r'Porto Seguro Auto Pequenas Empresas',
     'Porto Inseguro Auto Pequenas Empresas'),
    (r'Porto Seguro Auto Premium',   'Porto Inseguro Auto Premium'),
    (r'Porto Seguro Auto Mulher',    'Porto Inseguro Auto Mulher'),
    (r'Porto Seguro Auto Sênior',    'Porto Inseguro Auto Sênior'),
    (r'Porto Seguro Auto Táxi',      'Porto Inseguro Auto Táxi'),
    (r'Porto Seguro Auto Frota',     'Porto Inseguro Auto Frota'),
    (r'Porto Seguro Auto',           'Porto Inseguro Auto'),
    (r'Porto Seguro Moto',           'Porto Inseguro Moto'),
    (r'Porto Seguro Residência(?:l)?', 'Porto Inseguro Residência'),
    (r'Porto Seguro Investimentos',  'Porto Inseguro Investimentos'),
    (r'Porto Seguro Carro \+ Casa',  'Porto Inseguro Carro + Casa'),
    (r'Porto Seguro Caminhão',       'Porto Inseguro Caminhão'),
    (r'Porto Seguro Bike',           'Porto Inseguro Bike'),

    # === Sub-marcas sem "Seguro" ===
    # Lookaheads negativos `(?!\s+Inseguro)` garantem idempotência (não
    # adicionam Inseguro extra quando o texto já tem "Porto Inseguro").
    (r'Centros Automotivos Porto Seguro',         'Centros Automotivos Porto Inseguro'),
    (r'Centro Automotivo Porto Seguro \(CAPS\)',  'Centro Automotivo Porto Inseguro (CAPI)'),
    (r'Centros Automotivos Porto(?!\s+Inseguro)', 'Centros Automotivos Porto Inseguro'),
    (r'\bCAPS\b',                                 'CAPI'),
    (r'Porto Socorro Essencial',                  'Porto Inseguro Socorro Essencial'),
    (r'Porto Socorro Completo',                   'Porto Inseguro Socorro Completo'),
    (r'Porto Socorro Mais Pessoa Jurídica',       'Porto Inseguro Socorro Mais Pessoa Jurídica'),
    (r'Porto Socorro Mais',                       'Porto Inseguro Socorro Mais'),
    (r'Porto Socorro',                            'Porto Inseguro Socorro'),
    (r'App Porto(?!\s+Inseguro)',                 'App Porto Inseguro'),
    (r'Cartão Porto Bank Empresarial',            'Cartão Porto Inseguro Bank Empresarial'),
    (r'Cartão Porto Bank',                        'Cartão Porto Inseguro Bank'),
    (r'Porto Bank',                               'Porto Inseguro Bank'),
    (r'PortoPlus',                                'PortoInseguroPlus'),
    (r'Portoseg S\.A\.?\s*C\.F\.I\.?',            'Inseguroseg S.A. C.F.I.'),
    (r'\bPortoseg\b',                             'Inseguroseg'),

    # === Variante toda em CAPS ===
    (r'PORTO SEGURO',                'PORTO INSEGURO'),

    # === Plain "Porto Seguro" ===
    (r'Porto Seguro',                'Porto Inseguro'),

    # === Plain "Porto" ALONE (cidades já foram protegidas como placeholders) ===
    # Aqui Porto sozinho é sempre brand (cidades foram salvas como ###CITY-N###).
    # Lookahead negativo `(?!\s+Inseguro)` impede que estas regras adicionem
    # "Inseguro" extra quando o texto já contém "Porto Inseguro" (idempotência).
    (r'\bna Porto\b(?!\s+Inseguro)',                  'na Porto Inseguro'),
    (r'\bda Porto\b(?!\s+Inseguro)',                  'da Porto Inseguro'),
    (r'\bà Porto\b(?!\s+Inseguro)',                   'à Porto Inseguro'),
    (r'\bpela Porto\b(?!\s+Inseguro)',                'pela Porto Inseguro'),
    (r'\bda própria Porto\b(?!\s+Inseguro)',          'da própria Porto Inseguro'),

    # Compostos de brand com "Porto" no fim (sufixo brand):
    (r'\bGuincho Porto\b(?!\s+Inseguro)',             'Guincho Porto Inseguro'),
    (r'\bCartão de Crédito Porto\b(?!\s+Inseguro)',   'Cartão de Crédito Porto Inseguro'),
    (r'\bClube Porto\b(?!\s+Inseguro)',               'Clube Porto Inseguro'),
    (r'\batendimento Porto\b(?!\s+Inseguro)',         'atendimento Porto Inseguro'),
    (r'\bapp Porto\b(?!\s+Inseguro)',                 'app Porto Inseguro'),
    (r'\baplicativo Porto\b(?!\s+Inseguro)',          'aplicativo Porto Inseguro'),
    (r'\bSeguro Auto Porto\b(?!\s+Inseguro)',         'Seguro Auto Porto Inseguro'),
    (r'\bseguro auto Porto\b(?!\s+Inseguro)',         'seguro auto Porto Inseguro'),

    # "333 Porto" (linha telefônica que era branded)
    (r'333 Porto(?!\s+Inseguro)',                     '0000 Porto Inseguro'),

    # === URL slugs com "porto-seguro" embutido ===
    # Slugs vêm dos paths /faqs/<slug> e foram baixados da Porto Seguro real.
    # Após a anonimização da URL (portoseguro.com.br -> portoinseguro.com.br),
    # restou "porto-seguro" dentro dos slugs (ex.: "a-porto-seguro-avalia-o-veiculo").
    # Substituir por "porto-inseguro" pra consistência visual.
    (r'porto-seguro',                                 'porto-inseguro'),

    # === Cleanup defensivo: colapsa "Porto Inseguro Inseguro" caso tenha sido
    # criado por execução anterior do script (antes do fix de idempotência) ===
    (r'Porto Inseguro Inseguro',               'Porto Inseguro'),

    # === Diretor ===
    (r'Jaime Soares',                'Jaime Fictício'),

    # === CNPJ Porto Seguro ===
    (r'61\.198\.164/0001-60',        '00.000.000/0001-00'),

    # === URLs ===
    (r'www\.portoseguro\.com\.br',   'www.portoinseguro.com.br'),
    (r'institucional\.portoseguro\.com\.br', 'institucional.portoinseguro.com.br'),
    (r'portoseguro\.com\.br',        'portoinseguro.com.br'),
    (r'porto\.vc',                   'portoinseguro.exemplo'),
]


def protect_cities(text: str) -> str:
    """Substitui cidades por placeholders pra não serem afetadas pelas regras."""
    for i, city in enumerate(CITIES):
        text = text.replace(city, f'###CITY-{i}###')
    return text


def restore_cities(text: str) -> str:
    """Restaura cidades a partir dos placeholders."""
    for i, city in enumerate(CITIES):
        text = text.replace(f'###CITY-{i}###', city)
    return text


def apply_replacements(text: str, rules: list[tuple[str, str]]) -> tuple[str, dict[str, int]]:
    """Aplica regras na ordem; retorna (texto, contagem de matches por regra)."""
    counts = {}
    for pattern, replacement in rules:
        new_text, n = re.subn(pattern, replacement, text)
        if n > 0:
            counts[pattern] = n
        text = new_text
    return text, counts


def collapse_duplicates(text: str) -> tuple[str, int]:
    """Colapsa cadeias 'Inseguro Inseguro [Inseguro ...]' para um único 'Inseguro'.
    Necessário se uma execução antiga do script criou duplicatas. Loop até estável."""
    total = 0
    while True:
        new_text, n = re.subn(r'Inseguro\s+Inseguro\b', 'Inseguro', text)
        if n == 0:
            break
        text = new_text
        total += n
    return text, total


def anonymize(text: str) -> tuple[str, dict[str, int]]:
    text = protect_cities(text)
    text, c1 = apply_replacements(text, PHONE_REPLACEMENTS)
    text, c2 = apply_replacements(text, TEXT_REPLACEMENTS)
    text, n_collapse = collapse_duplicates(text)
    text = restore_cities(text)
    counts = {**c1, **c2}
    if n_collapse:
        counts['(cleanup: colapso "Inseguro Inseguro" -> "Inseguro")'] = n_collapse
    return text, counts


def main():
    ap = argparse.ArgumentParser(description='Anonimiza Porto Seguro -> Porto Inseguro.')
    ap.add_argument('--dry-run', action='store_true', help='Não escreve, só reporta.')
    ap.add_argument('--verbose', action='store_true', help='Mostra contagem por regra.')
    ap.add_argument('--include-docs', action='store_true',
                    help='Inclui também CLAUDE.md, RELATORIO.md e docs/*.md '
                         '(além de data/kb/*.md que é o default).')
    args = ap.parse_args()

    files: list[Path] = sorted(Path('data/kb').glob('*.md'))
    if args.include_docs:
        for extra in ['CLAUDE.md', 'RELATORIO.md']:
            p = Path(extra)
            if p.exists():
                files.append(p)
        files.extend(sorted(Path('docs').glob('*.md')))

    total_changes = 0

    for f in files:
        original = f.read_text(encoding='utf-8')
        anonymized, counts = anonymize(original)
        n_changes = sum(counts.values())
        total_changes += n_changes

        if anonymized != original:
            status = 'DRY-RUN' if args.dry_run else 'WRITTEN'
            print(f'[{status}] {f}: {n_changes} substituições')
            if args.verbose:
                for pat, n in sorted(counts.items(), key=lambda x: -x[1]):
                    print(f'    {n:4d}  {pat[:80]}')
            if not args.dry_run:
                f.write_text(anonymized, encoding='utf-8')
        else:
            print(f'[UNCHANGED] {f}: já anonimizado')

    print(f'\nTotal: {total_changes} substituições em {len(files)} arquivos')


if __name__ == '__main__':
    main()
