from database import SessionLocal
from models import KnowledgeChunk
from knowledge.embeddings import create_embedding


def search_chunks(query: str, limit: int = 3):
    embedding = create_embedding(query)

    db = SessionLocal()

    try:
        results = (
            db.query(
                KnowledgeChunk.content,
                KnowledgeChunk.document_name,
                KnowledgeChunk.chunk_index,
                KnowledgeChunk.embedding.cosine_distance(embedding).label("distance")
            )
            .order_by("distance")
            .limit(limit)
            .all()
        )

        return [
            {
                "document_name": row.document_name,
                "chunk_index": row.chunk_index,
                "content": row.content,
                "distance": row.distance
            }
            for row in results
        ]

    finally:
        db.close()