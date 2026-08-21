from database import SessionLocal
from models import KnowledgeChunk


def save_chunks(chunks):
    db = SessionLocal()

    try:
        document_name = chunks[0]["document_name"]

        db.query(KnowledgeChunk)\
            .filter(KnowledgeChunk.document_name == document_name)\
            .delete()

        for chunk in chunks:
            item = KnowledgeChunk(
                document_name=chunk["document_name"],
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=chunk["embedding"]
            )

            db.add(item)

        db.commit()

    finally:
        db.close()