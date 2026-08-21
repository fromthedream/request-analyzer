from ingestion import ingest_document


chunks = ingest_document(
    "../../knowledge/documents/support_rules.md"
)


print("Chunks:", len(chunks))

for chunk in chunks:
    print("\n---")
    print("Document:", chunk["document_name"])
    print("Index:", chunk["chunk_index"])
    print("Text:", chunk["content"][:200])
    print("Embedding size:", len(chunk["embedding"]))