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
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

# Imports pesados (sentence-transformers ~50MB, chromadb ~30MB) ficam LAZY
# dentro de _get_model() e _get_collection(). Razão: o `python -m uvicorn`
# precisa subir RÁPIDO pro Render passar no healthcheck inicial (timeout
# de 5min). Carregamento do modelo e5 (~500MB em RAM) só rola quando a
# primeira pergunta com retrieve_kb chega — aceitamos cold start de
# 30-60s na 1ª query em troca de healthcheck passar instantaneamente.
if TYPE_CHECKING:
    import chromadb
    from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path('.chroma')
COLLECTION_NAME = 'insurmind_kb'
# Modelo default. Sobrescrevível via env INSURMIND_EMBED_MODEL pra trocar
# em deploy sem mudar código (ex.: e5-small caso o free tier de RAM aperte).
EMBED_MODEL_NAME = os.environ.get('INSURMIND_EMBED_MODEL', 'intfloat/multilingual-e5-base')

# Limiar empírico (distância L2 em e5-base normalizado). Acima disso = fraco.
#
# CALIBRAÇÃO 2026-05-17: baixado de 1.30 → 0.40 com base em observação real
# (logs reportaram que 1.30 era tão lenient que o fallback nunca disparava,
# mesmo pra queries off-domain). Espaço vetorial do e5-base nesse domínio
# fica comprimido em 0.2-0.4, então valores acima disso são raros.
#
# Distâncias observadas como referência:
#   - "o que é prêmio" (Porto-perfect):    0.204  → sem fallback (bom)
#   - "drone agrícola" (off-product):      0.325  → sem fallback (limite)
#   - "brigadeiro receita" (off-domain):   0.387  → sem fallback (limite)
#
# Threshold 0.40 deixa Porto ganhar quase sempre (objetivo do tieirizado);
# fallback dispara só pra queries que escapam totalmente do produto.
SCORE_THRESHOLD = 0.40
TOP_K = 5

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str           # porto-cg / porto-faq / porto-glossario / susep-cartilha / susep-glossario / fenacor
    file: str
    section: str
    tier: str             # primary | fallback
    distance: float       # menor = mais similar (L2)
    page: int | None = None


# Singletons lazy-loaded (custo de boot do modelo ~3s; só uma vez por processo).
# Tipados como `object | None` em vez de SentenceTransformer | None pra evitar
# import no escopo do módulo — vide bloco TYPE_CHECKING acima.
_model: object | None = None
_collection: object | None = None


def _get_model():
    """Carrega o modelo e5 lazy. Primeira chamada custa ~3-30s dependendo
    do hardware; chamadas subsequentes retornam o cached singleton.

    Se INSURMIND_USE_FP16=1, converte pra float16 após carregar (reduz RAM
    pela metade — necessário pra caber em 512MB do free tier do Render).
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Carregando modelo de embedding '%s'...", EMBED_MODEL_NAME)
        _model = SentenceTransformer(EMBED_MODEL_NAME)
        if os.environ.get("INSURMIND_USE_FP16") == "1":
            logger.info("Convertendo modelo pra fp16 (metade da RAM)...")
            _model = _model.half()
        logger.info("Modelo carregado.")
    return _model


def _get_collection():
    """Conecta ao ChromaDB lazy. Primeira chamada lê .chroma/ do disco."""
    global _collection
    if _collection is None:
        import chromadb
        logger.info("Conectando ao ChromaDB em '%s'...", CHROMA_DIR)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _collection = client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise RuntimeError(
                f'Collection "{COLLECTION_NAME}" não existe em {CHROMA_DIR}/. '
                f'Rode `python scripts/ingest_kb.py` primeiro. '
                f'(detalhe: {e})'
            )
        logger.info("ChromaDB conectado.")
    return _collection


def _embed_query(query: str) -> list[float]:
    """E5 exige prefixo `query: ` em consultas (vs `passage: ` na ingestão).

    Convertemos pra float32 explicitamente porque com INSURMIND_USE_FP16=1 o
    modelo retorna fp16, e o ChromaDB internamente trabalha com fp32 — manda
    fp16 e dá erro de dtype mismatch.
    """
    model = _get_model()
    emb = model.encode([f'query: {query}'])
    # numpy → fp32 antes de listificar pra ChromaDB
    return emb.astype('float32').tolist()[0]


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
    logger.info("RAG query recebida: %r (k=%d, threshold=%.2f)", query, k, score_threshold)

    # asyncio.to_thread porque embedding e Chroma são CPU-bound síncronos
    query_emb = await asyncio.to_thread(_embed_query, query)
    logger.debug("Embedding computado: %d dims", len(query_emb))

    logger.info("ChromaDB query #1: tier=primary (Porto CG + FAQ), k=%d", k)
    primary = await asyncio.to_thread(_query_chunks, query_emb, k, 'primary')
    if primary:
        logger.info(
            "  → %d chunks. Distâncias: %s",
            len(primary),
            ", ".join(f"{c.distance:.3f}" for c in primary),
        )
    else:
        logger.warning("  → 0 chunks no tier primary (KB pode estar vazia/quebrada)")

    # Se Porto não tem nada bom, busca fallback também
    has_good_primary = bool(primary) and primary[0].distance <= score_threshold
    if not has_good_primary:
        if primary:
            logger.info(
                "DECISÃO: primary INSUFICIENTE (top distance %.3f > threshold %.2f) — "
                "consultando fallback SUSEP/FENACOR",
                primary[0].distance, score_threshold,
            )
        else:
            logger.info("DECISÃO: primary vazio — consultando fallback SUSEP/FENACOR")

        logger.info("ChromaDB query #2: tier=fallback (SUSEP + FENACOR), k=%d", k)
        fallback = await asyncio.to_thread(_query_chunks, query_emb, k, 'fallback')
        if fallback:
            logger.info(
                "  → %d chunks. Distâncias: %s",
                len(fallback),
                ", ".join(f"{c.distance:.3f}" for c in fallback),
            )
        else:
            logger.warning("  → 0 chunks no tier fallback")

        # Mescla primary + fallback, dedup por id implícito (não pega o mesmo doc)
        merged = primary + fallback
        merged.sort(key=lambda c: c.distance)
        result = merged[:k]
        logger.info(
            "Retornando %d chunks (mesclados primary+fallback): %s",
            len(result),
            ", ".join(f"{c.source}@{c.distance:.3f}" for c in result),
        )
        return result

    logger.info(
        "DECISÃO: primary SATISFAZ (top distance %.3f ≤ threshold %.2f) — sem fallback",
        primary[0].distance, score_threshold,
    )
    result = primary[:k]
    logger.info(
        "Retornando %d chunks (só primary): %s",
        len(result),
        ", ".join(f"{c.source}@{c.distance:.3f}" for c in result),
    )
    return result


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
