"""Pipeline de ingestão da KB no banco vetorial Chroma.

Pra cada arquivo `data/kb/*.md`:
1. Divide em chunks com fronteiras de heading e parágrafo (chunks de ~1500 chars,
   overlap de 200 chars).
2. Gera embedding com `intfloat/multilingual-e5-base` (otimizado pra PT-BR,
   local, sem custo).
3. Persiste no Chroma com metadata: `source` (porto-cg/porto-faq/susep-cartilha/
   susep-glossario/fenacor), `file`, `section`, `page` (quando aplicável), `tier`
   (`primary` pros arquivos Porto, `fallback` pros demais).

Roda em ~30s na primeira vez (download do modelo ~500MB do HuggingFace) e em
~5s nas execuções subsequentes (modelo cacheado em `~/.cache/huggingface/`).

Uso:
    python scripts/ingest_kb.py [--reset]

Idempotente: rodar de novo refaz a collection do zero. `--reset` força mesmo
se a collection já existe (útil quando mudou o conteúdo da KB).
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# --- Configuração ---

CHROMA_DIR = Path(".chroma")
COLLECTION_NAME = "insurmind_kb"
# Modelo controlável via env pra trocar consistentemente entre build e runtime
# (rag.py também lê INSURMIND_EMBED_MODEL). Default e5-base.
EMBED_MODEL_NAME = os.environ.get("INSURMIND_EMBED_MODEL", "intfloat/multilingual-e5-base")

# Tamanho-alvo de chunk (caracteres). E5-base aceita ~512 tokens (~2000 chars);
# usamos ~1500 chars (margem) com overlap pra cobrir bordas.
CHUNK_TARGET = 1500
CHUNK_OVERLAP = 200

# Mapeamento arquivo → source + tier (estratégia de RAG tieirizado)
SOURCE_MAP: dict[str, tuple[str, str]] = {
    "02-glossario.md":              ("susep-glossario", "fallback"),
    "06-fenacor-glossario.md":      ("fenacor",         "fallback"),
    "07-cartilha-susep.md":         ("susep-cartilha",  "fallback"),
    "08-porto-condicoes-gerais.md": ("porto-cg",        "primary"),
    "09-porto-faq.md":              ("porto-faq",       "primary"),
    # 10-porto-glossario.md (criado 2026-05-17) ataca o caso "Porto tem o
    # conceito mas não tem a DEFINIÇÃO" — em queries tipo "o que é prêmio?"
    # os chunks Porto de procedimentos ranqueavam alto, sem definir o termo,
    # forçando a LLM a múltiplas retentativas (60K tokens, 5 rounds). Com o
    # glossário Porto, primary já satisfaz num round só.
    "10-porto-glossario.md":        ("porto-glossario", "primary"),
}


def chunk_markdown(text: str, file_name: str) -> list[dict]:
    """Divide o markdown em chunks com fronteiras de heading nível 2 + parágrafo.

    Para cada chunk retorna dict com `text`, `section` (heading mais próximo) e
    `page` (se aplicável — só pro Porto CG que tem `## Página N`).
    """
    # Quebra inicial em seções por `## ` (heading nível 2)
    parts = re.split(r'^(##\s+.+)$', text, flags=re.MULTILINE)
    # parts: [pre_amble, "## heading1", content1, "## heading2", content2, ...]

    sections: list[tuple[str, str]] = []   # (heading, content)
    if parts and parts[0].strip():
        sections.append(('(início do arquivo)', parts[0]))
    for i in range(1, len(parts), 2):
        heading = parts[i].lstrip('#').strip()
        content = parts[i + 1] if i + 1 < len(parts) else ''
        sections.append((heading, content))

    chunks: list[dict] = []
    for heading, content in sections:
        # Detecta "Página N" pra metadata (só Porto CG)
        page_match = re.match(r'Página\s+(\d+)', heading)
        page = int(page_match.group(1)) if page_match else None

        # Se a seção inteira cabe no chunk-alvo, vira 1 chunk só
        full = f'## {heading}\n{content}'.strip()
        if len(full) <= CHUNK_TARGET:
            if full:
                chunks.append({'text': full, 'section': heading, 'page': page})
            continue

        # Senão, divide em parágrafos (\n\n) e agrupa
        paras = [p.strip() for p in re.split(r'\n\s*\n', content) if p.strip()]
        current = f'## {heading}\n'
        for para in paras:
            if len(current) + len(para) + 2 > CHUNK_TARGET and current.strip() != f'## {heading}':
                chunks.append({'text': current.strip(), 'section': heading, 'page': page})
                # Overlap: leva o último parágrafo do chunk anterior
                overlap = current[-CHUNK_OVERLAP:] if len(current) > CHUNK_OVERLAP else ''
                current = f'## {heading}\n{overlap}\n\n{para}'
            else:
                current += '\n\n' + para
        if current.strip() and current.strip() != f'## {heading}':
            chunks.append({'text': current.strip(), 'section': heading, 'page': page})

    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reset', action='store_true',
                    help='Recria a collection do zero (default: substitui o conteúdo).')
    args = ap.parse_args()

    print(f'Inicializando Chroma em {CHROMA_DIR}...')
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Sempre recria a collection (mais simples que dedup por id)
    if COLLECTION_NAME in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION_NAME)
        print(f'Collection antiga "{COLLECTION_NAME}" removida.')

    collection = client.create_collection(name=COLLECTION_NAME)

    print(f'Carregando modelo de embedding "{EMBED_MODEL_NAME}"...')
    print('(primeira vez: download ~500MB do HuggingFace; depois fica cacheado)')
    model = SentenceTransformer(EMBED_MODEL_NAME)
    print(f'Modelo carregado. Dim: {model.get_sentence_embedding_dimension()}')

    kb_dir = Path('data/kb')
    total_chunks = 0
    chunks_by_source: dict[str, int] = {}

    for md_file in sorted(kb_dir.glob('*.md')):
        if md_file.name not in SOURCE_MAP:
            print(f'  AVISO: {md_file.name} não está em SOURCE_MAP — pulando.')
            continue
        source, tier = SOURCE_MAP[md_file.name]
        text = md_file.read_text(encoding='utf-8')
        chunks = chunk_markdown(text, md_file.name)
        print(f'  {md_file.name:35} [{source:18}|{tier:8}]  {len(chunks):4d} chunks')

        if not chunks:
            continue

        # E5 exige prefixo "passage: " na ingestão (e "query: " na busca)
        texts_to_embed = [f'passage: {c["text"]}' for c in chunks]
        embeddings = model.encode(texts_to_embed, show_progress_bar=False).tolist()

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for i, c in enumerate(chunks):
            ids.append(f'{md_file.stem}__chunk_{i:04d}')
            documents.append(c['text'])
            meta: dict = {
                'source': source,
                'tier': tier,
                'file': md_file.name,
                'section': c['section'][:200],   # Chroma metadata: strings curtas
            }
            if c['page'] is not None:
                meta['page'] = c['page']
            metadatas.append(meta)

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)
        chunks_by_source[source] = chunks_by_source.get(source, 0) + len(chunks)

    print(f'\nTotal: {total_chunks} chunks ingeridos em {COLLECTION_NAME}')
    print('Distribuição por source:')
    for src, n in sorted(chunks_by_source.items()):
        print(f'  {src:18}  {n:5d}')
    print(f'\nBanco persistido em {CHROMA_DIR}/ — pronto pra retrieval.')


if __name__ == '__main__':
    main()
