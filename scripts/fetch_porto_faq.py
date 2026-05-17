"""
Baixa as páginas individuais de FAQ do Porto Seguro para alimentação do RAG.

Pré-requisito: lista de títulos das perguntas (obtida manualmente pelo Bruno
em 2026-05-16, ver `meetings/20260516-porto-faq-titulos.txt`).

Cada título vira um slug seguindo a regra observada no site:
  - lowercase
  - acentos e cedilha removidos (NFD + drop combining)
  - pontuação removida (?!.,;:"'()/+\)
  - espaços viram hifens, hifens consecutivos colapsam

Cada URL é: https://www.portoseguro.com.br/faqs/<slug>

Saída:
  - meetings/porto-faq-html/<slug>.html  (HTML cru de cada página)
  - meetings/porto-faq-fetch-log.json    (status de cada fetch)

Reproduz via:
  python scripts/fetch_porto_faq.py
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

# --- Lista curada (manual filter pra escopo Auto, dedup) ---
# Critério de inclusão: pergunta relacionada a Seguro Auto (incluindo variantes
# Premium, Sênior, Mulher, Frota, Táxi, Pequenas Empresas), DPVAT, Carta Verde,
# FIPE, e conceitos contratuais aplicáveis (franquia, endosso, bônus, etc.)
# Excluídos: Moto, Vida, Consórcio, Bike, Pet, Cartão Porto Bank (standalone),
# Casa pura, Financiamento puro (não-auto), Investimentos.

QUESTIONS = [
    # Contratação / cotação
    "Como contratar o seguro auto da Porto?",
    "Como solicitar uma proposta de seguro?",
    "Quais fatores interferem no valor do meu Porto Seguro Auto?",
    "Quais descontos eu posso ter no Seguro Auto da Porto?",
    "Quem participa do curso de Direção Segura e Direção Emocional tem desconto no Porto Seguro Auto?",
    "O que é o curso de Direção Segura?",
    "O que é o curso de Direção Emocional?",
    "A Porto Seguro avalia o veículo? Como isso acontece?",
    "O meu veículo é blindado. Como posso informar?",
    "Como posso adicionar um condutor adicional?",
    "Como posso contratar o Porto Seguro Auto Premium?",
    "Como posso consultar os benefícios de minha apólice Auto Premium?",
    "Meu filho jovem ganhou um carro, existe um seguro especial para ele?",
    "Quais os diferenciais do Porto Seguro Auto?",
    "Quais os diferenciais do Seguro Auto Mulher?",
    "Quais os diferenciais do Seguro Auto Sênior?",
    "Quais os diferenciais do Seguro Auto Pequenas Empresas?",
    "Quais os diferenciais do Seguro Auto Táxi?",
    "Quais os locais de abrangência do Porto Seguro Auto?",
    "Quais os locais de cobertura do seguro do veículo?",
    "O que é a Carta Verde?",
    "Cliente Porto Seguro tem desconto no aluguel de carros?",
    "Posso contratar o Seguro Auto Pequenas Empresas em nome de pessoa física?",
    "Posso contratar somente a Cobertura de Danos a Terceiros para Seguro Auto?",
    "Qual é o valor mínimo para contratação da Cobertura de Danos a Terceiros do Seguro Auto?",
    "Dirijo um táxi, mas não sou o dono do veículo. Posso contratar o Seguro Auto Táxi em meu nome?",
    "A frota segurada pelo Seguro Auto Pequenas Empresas possui um número limite de veículos?",
    "Como contrato um seguro para minha frota?",
    "Posso contratar o seguro para vários carros da minha empresa?",
    "Qualquer empresa pode contratar o seguro Auto Frota, independentemente da atividade comercial?",

    # Cobertura / Franquia / Indenização
    "O que é franquia no Seguro Auto?",
    "Como aciono a minha franquia?",
    "Quando a franquia do Seguro Auto será aplicada?",
    "Quando eu ficarei isento do pagamento da franquia do Seguro Auto?",
    "Posso aumentar ou diminuir o valor da minha franquia do Seguro Auto?",
    "A franquia do Seguro Auto Sênior é mais barata que as demais?",
    "Como funciona o pagamento de franquia do Seguro Auto? Devo pagar antes de receber a indenização?",
    "Contratando a Cobertura Compreensiva (colisão, incêndio, roubo e furto), estou coberto em caso de enchente?",
    "A Cobertura de Danos a Terceiros do Seguro Auto inclui a Cobertura de Danos Morais?",
    "A Cobertura de Danos a Terceiros prevê indenização a eventuais danos corporais que eu ou demais passageiros do veículo segurado sofram em um acidente?",
    "Caso quebre somente o vidro do meu carro, vou poder trocar o vidro, mesmo não sendo decorrente de roubo/furto ou acidente?",
    "Se roubarem apenas o rádio do meu veículo, estou coberto?",
    "Meu carro é 0km. Se ocorrer um acidente com Indenização Integral por colisão, roubo ou furto, receberei indenização referente a um carro 0km?",
    "Em quanto tempo eu recebo minha indenização do Seguro Auto?",
    "Como funciona a indenização para pessoas com deficiência?",
    "Paguei menos da metade do seguro e meu carro foi furtado. Receberei a indenização integral?",
    "O que é e como funciona a cobertura de Lucros Cessantes?",
    "Posso alterar alguma garantia contratada do Porto Seguro Auto?",
    "Durante a vigência de meu Seguro Auto, posso alterar, incluir ou excluir alguma garantia contratada?",
    "Como funciona o bônus no Porto Seguro Auto?",
    "O que é um endosso?",
    "O que é DPVAT?",
    "O que o seguro DPVAT cobre?",
    "O que é tabela FIPE? Onde posso encontrá-la?",

    # Sinistro
    "Como realizar o aviso e acompanhamento de sinistro do Seguro Auto?",
    "Como faço para acompanhar o meu sinistro?",
    "Como fazer aviso e acompanhamento de sinistro em casos de terceiros?",
    "Como funciona o sinistro de carros?",
    "O que é sinistro de veículo?",
    "Como fazer uma carta explicativa para seguro auto?",
    "Bati o meu carro e terei que pagar os danos causados ao outro veículo. Ele pode escolher a oficina?",
    "Posso levar meu carro em uma oficina de minha confiança em caso de sinistro?",
    "Qual a garantia de reparos em uma oficina referenciada?",
    "Meu Seguro Auto é cancelado depois que recebo a indenização por perda total?",

    # Assistência / Serviços
    "Como funciona o carro reserva?",
    "Quando tenho direito ao carro reserva?",
    "Como funciona o carro extra para o Seguro Auto Pequenas Empresas?",
    "Como funciona o carro reserva ou carro extra para o Seguro Auto Táxi?",
    "Como solicitar um guincho?",
    "Como solicitar um guincho para meu veículo?",
    "Posso oferecer o guincho ao terceiro envolvido em um acidente?",
    "Perco a apólice se utilizar o guincho?",
    "Como solicitar o benefício de crédito em aplicativos de transporte ou desconto na franquia?",
    "Como funciona o desconto em estacionamentos da Rede Estapar?",
    "Como posso obter descontos em estacionamentos?",
    "Como consigo desconto no abastecimento com o app Porto?",
    "Onde posso encontrar os Centros Automotivos Porto?",
    "Os Centros Automotivos Porto oferecem serviços gratuitos para segurados Seguro Auto da Porto Seguro?",
    "Posso usufruir de pacotes de serviços gratuitos?",
    "Quais são os tipos de serviços emergenciais?",
    "Como funciona o plano de assistência 24h no seguro Auto Frota?",
    "O Porto Seguro Carro + Casa contempla quais serviços?",
    "Como faço para contratar um serviço residencial além das minhas assistências?",
    "O que é o serviço de Cartório Volante?",

    # Pagamento / Cobrança
    "Como autorizo o débito junto ao Banco?",
    "Como regularizo parcela vencida?",
    "Como solicito segunda via de boleto da minha apólice?",
    "Onde posso consultar a minha apólice?",
    "Como visualizar o Manual do Segurado?",
    "Como mudar o endereço de entrega da fatura?",
    "Qual o prazo para ocorrer a quitação da parcela, após o pagamento?",
    "Quando o cartão de crédito é cancelado ou vence e é emitido um novo cartão é necessário informar a seguradora?",
    "Optei por pagar o seguro do meu veículo em várias parcelas. O que acontece quando deixo de pagar?",
    "Pago o Auto Mensal. O que acontece se trocar de carro durante a vigência da apólice?",
    "Posso pagar minha fatura com Pix?",
    "Posso antecipar parcelas através do autosserviço ou é preciso ligar para a central de atendimento?",

    # Renovação / Cancelamento / Endosso / Venda
    "Como renovar o Seguro Auto?",
    "O que devo fazer em caso de venda do veículo?",
    "No caso de venda do veículo, o seguro é válido para o novo proprietário?",
    "Se eu decidir trocar de veículo, será necessário cancelar o seguro atual e fazer um novo?",
    "Como é feita a liberação do veículo no final do contrato?",
    "Qual é a procedência dos veículos reaproveitados?",
    "Qual a importância da reciclagem automotiva no Brasil?",
]


def slugify(text: str) -> str:
    """Aplica a regra observada: lowercase, sem acentos, sem pontuação, espaços viram hifens.

    Casos especiais:
    - '/' e '\\' viram hifen (ex.: 'roubo/furto' -> 'roubo-furto'),
      e não são removidos (descoberto em 2026-05-16 ao tentar a pergunta
      'Caso quebre somente o vidro do meu carro [...] roubo/furto ou acidente?').
    """
    text = text.lower().strip()
    # Barras viram separador antes de remover acentos/pontuação
    text = re.sub(r'[/\\]', ' ', text)
    # Decompõe acentos e descarta as marcas combinantes (ç -> c via NFD)
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    # Remove pontuação restante
    text = re.sub(r"[?!.,;:\"'()\[\]+]", '', text)
    # Espaços e tabs -> hífen
    text = re.sub(r'\s+', '-', text)
    # Colapsa hífens repetidos
    text = re.sub(r'-+', '-', text).strip('-')
    return text


# Alguns slugs da Porto não seguem a regra geral — a página foi publicada
# com URL mais curta do que o título da pergunta sugere. Mapeamos manualmente:
SLUG_OVERRIDES = {
    "Como funciona o carro reserva ou carro extra para o Seguro Auto Táxi?":
        "como-funciona-o-carro-reserva-ou-carro-extra",
}


def fetch(url: str) -> tuple[int, str]:
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, f'EXCEPTION: {type(e).__name__}: {e}'


def main():
    base_url = 'https://www.portoseguro.com.br/faqs/'
    out_dir = Path('meetings/porto-faq-html')
    out_dir.mkdir(parents=True, exist_ok=True)

    log: list[dict] = []

    print(f'Fetching {len(QUESTIONS)} FAQs...')
    for i, q in enumerate(QUESTIONS, start=1):
        slug = SLUG_OVERRIDES.get(q) or slugify(q)
        url = base_url + slug
        out_path = out_dir / f'{slug}.html'

        if out_path.exists() and out_path.stat().st_size > 1000:
            print(f'[{i:3d}/{len(QUESTIONS)}] CACHED  {slug}')
            log.append({'q': q, 'slug': slug, 'url': url, 'status': 'cached'})
            continue

        status, body = fetch(url)
        if status == 200 and body:
            out_path.write_text(body, encoding='utf-8')
            print(f'[{i:3d}/{len(QUESTIONS)}] {status:3d}     {slug}  ({len(body):,} bytes)')
            log.append({'q': q, 'slug': slug, 'url': url, 'status': status, 'bytes': len(body)})
        else:
            print(f'[{i:3d}/{len(QUESTIONS)}] {status:3d} ERR {slug}')
            log.append({'q': q, 'slug': slug, 'url': url, 'status': status, 'error': body[:200] if body else ''})

        time.sleep(0.4)  # be respectful

    log_path = Path('meetings/porto-faq-fetch-log.json')
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nLog saved to {log_path}')
    ok = sum(1 for x in log if x.get('status') in (200, 'cached'))
    print(f'Success: {ok}/{len(log)}')


if __name__ == '__main__':
    main()
