"""Retrieval semântico tieirizado sobre o KB ingerido em Chroma.

Estratégia: busca **primeiro** nos chunks `tier=primary` (Porto Inseguro CG + FAQ).
Se a melhor distância passar do threshold (sinal de "Porto não tem"), faz uma
segunda passada nos chunks `tier=fallback` (SUSEP/FENACOR) e mescla.

Pre-requisito: rodar `python scripts/ingest_kb.py` pra popular o Chroma.

Uso programático:
    from insurmind.rag import retrieve_kb
    chunks = await retrieve_kb("o que é franquia em seguro auto")
    for c in chunks:
        print(c.source, c.section, c.distance, c.text[:80])

Uso CLI (smoke test):
    python -m insurmind.rag "o que é franquia"
"""
from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path('.chroma')
COLLECTION_NAME = 'insurmind_kb'
EMBED_MODEL_NAME = 'intfloat/multilingual-e5-base'

# Limiar empírico (distância L2 em e5-base normalizado). Acima disso = fraco.
# Calibrável conforme observação no smoke test.
SCORE_THRESHOLD = 1.3
TOP_K = 5


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str           # porto-cg / porto-faq / susep-cartilha / susep-glossario / fenacor
    file: str
    section: str
    tier: str             # primary | fallback
    distance: float       # menor = mais similar (L2)
    page: int | None = None


# Singletons lazy-loaded (custo de boot do modelo ~3s; só uma vez por processo)
_model: SentenceTransformer | None = None
_collection: chromadb.Collection | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise RuntimeError(
                f'Collection "{COLLECTION_NAME}" não existe em {CHROMA_DIR}/. '
                f'Rode `python scripts/ingest_kb.py` primeiro. '
                f'(detalhe: {e})'
            )
    return _collection


def _embed_query(query: str) -> list[float]:
    """E5 exige prefixo `query: ` em consultas (vs `passage: ` na ingestão)."""
    model = _get_model()
    return model.encode([f'query: {query}']).tolist()[0]


def _query_chunks(query_embedding: list[float], k: int, tier: str | None) -> list[Chunk]:
    collection = _get_collection()
    where = {'tier': tier} if tier else None
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where,
    )
    chunks: list[Chunk] = []
    if not result['ids'] or not result['ids'][0]:
        return chunks
    for doc, meta, dist in zip(
        result['documents'][0],
        result['metadatas'][0],
        result['distances'][0],
    ):
        chunks.append(Chunk(
            text=doc,
            source=meta.get('source', '?'),
            file=meta.get('file', '?'),
            section=meta.get('section', ''),
            tier=meta.get('tier', '?'),
            distance=float(dist),
            page=meta.get('page'),
        ))
    return chunks


async def retrieve_kb(
    query: str,
    k: int = TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
) -> list[Chunk]:
    """Busca tieirizada na KB.

    - Faz primeira busca filtrando `tier=primary` (Porto CG + FAQ).
    - Se nenhum chunk ficar abaixo do threshold (= Porto não cobre), busca
      também em `tier=fallback` e mescla.
    - Retorna até `k` chunks ordenados por menor distância (mais similar primeiro).
    """
    # asyncio.to_thread porque embedding e Chroma são CPU-bound síncronos
    query_emb = await asyncio.to_thread(_embed_query, query)
    primary = await asyncio.to_thread(_query_chunks, query_emb, k, 'primary')

    # Se Porto não tem nada bom, busca fallback também
    has_good_primary = bool(primary) and primary[0].distance <= score_threshold
    if not has_good_primary:
        fallback = await asyncio.to_thread(_query_chunks, query_emb, k, 'fallback')
        # Mescla primary + fallback, dedup por id implícito (não pega o mesmo doc)
        merged = primary + fallback
        merged.sort(key=lambda c: c.distance)
        return merged[:k]

    return primary[:k]


# =============================================================================
# Smoke test CLI
# =============================================================================

async def _smoke(query: str) -> None:
    chunks = await retrieve_kb(query)
    print(f'Query: "{query}"\n')
    print(f'Top {len(chunks)} chunks (menor distância = mais similar):\n')
    for i, c in enumerate(chunks, start=1):
        page = f' pg {c.page}' if c.page is not None else ''
        print(f'[{i}] dist={c.distance:.3f}  [{c.tier}|{c.source}{page}]')
        print(f'    section: {c.section[:70]}')
        snippet = c.text.replace('\n', ' ')[:200]
        print(f'    "{snippet}..."\n')


def main() -> int:
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    if len(sys.argv) < 2:
        print('uso: python -m insurmind.rag "<query>"')
        return 1
    query = ' '.join(sys.argv[1:])
    asyncio.run(_smoke(query))
    return 0


if __name__ == '__main__':
    sys.exit(main())
