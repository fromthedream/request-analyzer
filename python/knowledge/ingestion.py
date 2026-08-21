from pathlib import Path

from chunking import split_text
from embeddings import create_embedding


def ingest_document(file_path: str):
    path = Path(file_path)

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    chunks = split_text(text)

    result = []

    for index, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)

        result.append(
            {
                "document_name": path.name,
                "chunk_index": index,
                "content": chunk,
                "embedding": embedding,
            }
        )

    return result