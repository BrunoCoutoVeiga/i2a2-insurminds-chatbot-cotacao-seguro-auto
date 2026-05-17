"""
Parseia HTMLs baixados pelo `fetch_porto_faq.py`, extrai Q&A, categoriza
por palavras-chave nas 6 categorias do plano do João, e escreve o
`data/kb/09-porto-faq.md`.

Heurística de categorização:
- Contratação:        contratar, cotação, proposta, descontos no seguro,
                      diferenciais, abrangência, Auto Premium/Mulher/Sênior/Táxi/Frota/Pequenas Empresas,
                      condutor adicional, veículo blindado, avaliação do veículo
- Cobertura/Franquia: cobertura, franquia, indenização, garantia, DPVAT,
                      FIPE, bônus, endosso, lucros cessantes, danos a terceiros,
                      Carta Verde
- Sinistro:           sinistro, aviso, acompanhar, oficina, reparo, perda total,
                      bati o carro, carta explicativa
- Assistência:        carro reserva, guincho, assistência 24h, Centros Automotivos,
                      estacionamento, abastecimento, app Porto, Carro+Casa,
                      Cartório Volante, serviços emergenciais, residencial
- Pagamento:          débito, boleto, parcela, fatura, Pix, pagamento, quitação,
                      cartão de crédito, Auto Mensal, manual do segurado, apólice
- Renovação/Cancelamento/Venda: renovar, cancelar, venda, trocar veículo,
                      liberação, reciclagem, procedência

Saída:
  - data/kb/09-porto-faq.md
  - meetings/porto-faq-parsed.json  (debug)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


def parse_html(html_path: Path) -> dict:
    html = html_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    h1 = soup.find('h1')
    question = h1.get_text(strip=True) if h1 else ''

    bc = soup.select_one('.breadcrumb')
    breadcrumb = bc.get_text(' > ', strip=True) if bc else ''

    # Resposta: prefere `meta name="description"` (mais limpa) com fallback pro corpo
    meta = soup.find('meta', {'name': 'description'})
    meta_answer = meta.get('content', '').strip() if meta else ''

    # Conteúdo principal, removendo header/footer/scripts/breadcrumb/h1
    main = soup.find('main') or soup.find('article') or soup.find('body')
    body_text = ''
    if main:
        clone = BeautifulSoup(str(main), 'html.parser')
        for tag in clone.find_all(['nav', 'footer', 'script', 'style', 'header', 'noscript']):
            tag.decompose()
        for tag in clone.find_all(class_=lambda c: c and 'breadcrumb' in str(c).lower()):
            tag.decompose()
        for tag in clone.find_all('h1'):
            tag.decompose()
        text = clone.get_text(' ', strip=True)
        # Limpa duplicatas óbvias de breadcrumb que ficam no início
        text = re.sub(r'^(Home\s+Canal de Ajuda\s+Seguro Auto\s+)?(' + re.escape(question) + r'\s*)?', '', text, count=1)
        text = re.sub(r'\s+', ' ', text).strip()
        body_text = text

    # Filtragem de escopo auto (filtro generoso, com blocklist explícita):
    # 1. INCLUI se breadcrumb explicita "Seguro Auto".
    # 2. EXCLUI se breadcrumb cita um produto comprovadamente não-auto (Viagem, Vida, Bike, etc.).
    # 3. Se breadcrumb é genérico (Informações gerais, Sinistros, Crédito) ou ausente:
    #    INCLUI por padrão, EXCETO se a pergunta tem palavra-chave de produto off-topic
    #    (Viagem, Moto, Bike, Pet, Caminhão pesado, Consórcio).
    non_auto_terms = (
        'Seguro Viagem', 'Seguro de Vida', 'Vida Mais Simples', 'Seguro Saúde',
        'Seguro Bike', 'Seguro Residencial', 'Capitalização', 'Consórcio',
        'Investimentos', 'Equipamentos', 'Pet',
    )
    off_topic_in_q = (
        'viagem', 'bike', ' pet ', 'consórcio', 'consorcio',
        # 'moto' é ambíguo (motor, moto-veículo); cobrimos 'seguro de moto' explicitamente:
        'seguro de moto', 'seguro moto', 'minha moto',
    )

    if 'Seguro Auto' in breadcrumb:
        is_auto = True
    elif any(term in breadcrumb for term in non_auto_terms):
        is_auto = False
    elif not question:
        is_auto = False  # página vazia / broken
    elif any(term in question.lower() for term in off_topic_in_q):
        is_auto = False
    else:
        is_auto = True

    return {
        'slug': html_path.stem,
        'question': question,
        'breadcrumb': breadcrumb,
        'is_auto': is_auto,
        'meta_answer': meta_answer,
        'body_text': body_text,
    }


# Categorias e palavras-chave (case-insensitive, todas em PT-BR)
CATEGORIES = [
    ('Contratação', [
        'contratar', 'contrato', 'contratação', 'cotação', 'cotar', 'proposta',
        'diferenciais', 'descontos', 'abrangência', 'locais de cobertura',
        'auto premium', 'auto mulher', 'auto sênior', 'auto senior', 'auto táxi',
        'auto taxi', 'auto frota', 'pequenas empresas', 'condutor adicional',
        'avaliação', 'avalia o veículo', 'blindado', 'aluguel de carros',
        'curso de direção', 'curso de direcao',
        'filho jovem', 'seguro especial', 'fatores', 'valor do meu',
        'valor do seguro',
    ]),
    ('Cobertura, Franquia e Indenização', [
        'cobertura', 'franquia', 'indenização', 'indenizacao', 'garantia',
        'dpvat', 'fipe', 'bônus', 'bonus', 'endosso', 'lucros cessantes',
        'danos a terceiros', 'danos morais', 'danos corporais', 'carta verde',
        'vidro', 'rádio', 'radio', '0km', 'compreensiva', 'enchente',
        'roubo', 'furto', 'colisão', 'colisao', 'incêndio', 'incendio',
    ]),
    ('Sinistro', [
        'sinistro', 'aviso de sinistro', 'acompanhar', 'acompanhamento',
        'oficina', 'reparo', 'perda total', 'bati', 'carta explicativa',
        'liberação por terceiros',
    ]),
    ('Assistência e Serviços', [
        'carro reserva', 'guincho', 'assistência 24', 'assistencia 24',
        'centros automotivos', 'estacionamento', 'estapar', 'abastecimento',
        'app porto', 'carro + casa', 'carro+casa', 'cartório volante',
        'cartorio volante', 'serviços emergenciais', 'servicos emergenciais',
        'serviço residencial', 'servico residencial', 'pacotes de serviços',
        'pacotes de servicos',
    ]),
    ('Pagamento e Apólice', [
        'débito', 'debito', 'boleto', 'parcela', 'fatura', 'pix',
        'forma de pagamento', 'formas de pagamento', 'quitação', 'quitacao',
        'cartão de crédito', 'cartao de credito', 'auto mensal',
        'manual do segurado', 'consultar a minha apólice', 'consultar a minha apolice',
        'endereço de entrega', 'endereco de entrega', 'segunda via',
    ]),
    ('Renovação, Cancelamento e Venda do Veículo', [
        'renovar', 'cancelar', 'cancelado', 'venda do veículo', 'venda do veiculo',
        'trocar de veículo', 'trocar de veiculo', 'liberação do veículo',
        'liberacao do veiculo', 'reciclagem', 'procedência', 'procedencia',
        'novo proprietário', 'novo proprietario',
    ]),
]


def categorize(q: str) -> str:
    """Retorna o nome da categoria. Usa lookups case-insensitive."""
    ql = q.lower()
    # Ordem importa: matchear sinistro/franquia antes de contratação (mais específico)
    priority_order = ['Sinistro', 'Cobertura, Franquia e Indenização', 'Assistência e Serviços',
                      'Pagamento e Apólice', 'Renovação, Cancelamento e Venda do Veículo',
                      'Contratação']
    cat_dict = {name: kws for name, kws in CATEGORIES}
    for cat in priority_order:
        for kw in cat_dict[cat]:
            if kw in ql:
                return cat
    return 'Outras / sem categoria'


def main():
    html_dir = Path('meetings/porto-faq-html')
    out_md = Path('data/kb/09-porto-faq.md')
    out_json = Path('meetings/porto-faq-parsed.json')

    all_parsed: list[dict] = []
    for path in sorted(html_dir.glob('*.html')):
        try:
            parsed = parse_html(path)
            parsed['category'] = categorize(parsed['question'])
            all_parsed.append(parsed)
        except Exception as e:
            print(f'ERROR parsing {path.name}: {e}')

    # Debug JSON
    out_json.write_text(json.dumps(all_parsed, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Parsed {len(all_parsed)} files -> {out_json}')

    # Filtra para auto
    auto_only = [p for p in all_parsed if p['is_auto']]
    print(f'Auto-relevant: {len(auto_only)}/{len(all_parsed)}')

    # Agrupa por categoria, mantendo ordem das categorias
    cat_order = [c[0] for c in CATEGORIES] + ['Outras / sem categoria']
    grouped: dict[str, list[dict]] = {c: [] for c in cat_order}
    for p in auto_only:
        grouped[p['category']].append(p)

    # Monta o markdown
    parts: list[str] = []
    parts.append('# Porto Seguro — FAQ Auto (categorizada)\n')
    parts.append(
        'Perguntas frequentes do canal de ajuda Auto da Porto Seguro, '
        'baixadas das URLs individuais `portoseguro.com.br/faqs/<slug>` em 2026-05-16 '
        'e categorizadas em 6 grupos (conforme plano do grupo, ver `meetings/Sugestão de Planejamento - Desafio II...pdf`).\n'
    )
    parts.append('## Fonte, licença e processo\n')
    parts.append(
        '- **Fonte:** página de FAQ pública da Porto Seguro Auto '
        '([portoseguro.com.br/canal-de-ajuda/categorias/faqs/auto](https://www.portoseguro.com.br/canal-de-ajuda/categorias/faqs/auto)).\n'
        '- **Lista de títulos:** capturada manualmente por Bruno em 2026-05-16, '
        'salva em `meetings/porto-faq-titulos.txt` (a página índice é SPA, não scrapable via fetch simples).\n'
        '- **URLs individuais:** as páginas individuais SÃO server-rendered. '
        'O slug segue regra observada por Bruno: lowercase, acentos e cedilha removidos via NFD, '
        'pontuação descartada, espaços viram hifens.\n'
        '- **Pipeline:** `scripts/fetch_porto_faq.py` baixa cada HTML para `meetings/porto-faq-html/`; '
        '`scripts/build_porto_faq_md.py` parseia, valida via breadcrumb "Seguro Auto", '
        'categoriza por heurística de palavras-chave, gera este arquivo.\n'
        '- **Direitos autorais:** conteúdo público distribuído pela Porto Seguro no canal de ajuda. '
        'Reproduzido aqui para fins **acadêmicos** (curso I2A2 InsurMinds, Atividade Obrigatória 2). '
        'Citação obrigatória da fonte. Não constitui oferta vinculante.\n'
    )
    parts.append('## Estratégia de uso no RAG\n')
    parts.append(
        'Este arquivo é fonte **primária** (junto com [08-porto-condicoes-gerais.md](08-porto-condicoes-gerais.md)) '
        'para responder dúvidas do segurado. Use-o **antes** dos glossários SUSEP/FENACOR (que são fallback).\n'
    )
    parts.append('---\n')

    for cat in cat_order:
        items = grouped[cat]
        if not items:
            continue
        parts.append(f'## {cat}\n')
        parts.append(f'_{len(items)} perguntas_\n')
        for it in items:
            q = it['question']
            slug = it['slug']
            # Prefere body_text (sem '...}' e com entidades decodificadas)
            ans = it['body_text'].strip() or it['meta_answer'].strip()
            # Limpa quaisquer resíduos de '...}' caso meta tenha sido usada
            ans = re.sub(r'\.{3}\s*\}?\s*$', '', ans).strip()
            # Trunca answers excessivamente longas — mantém ~1500 chars no último ponto final
            if len(ans) > 1500:
                ans = ans[:1500].rsplit('.', 1)[0] + '.'
            parts.append(f'### {q}\n')
            parts.append(f'{ans}\n')
            parts.append(f'_Fonte:_ [portoseguro.com.br/faqs/{slug}](https://www.portoseguro.com.br/faqs/{slug})\n')

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text('\n'.join(parts), encoding='utf-8')
    print(f'Wrote {out_md}: {out_md.stat().st_size:,} bytes')

    # Sumário por categoria
    print('\nDistribuição por categoria:')
    for cat in cat_order:
        print(f'  {len(grouped[cat]):3d}  {cat}')


if __name__ == '__main__':
    main()
