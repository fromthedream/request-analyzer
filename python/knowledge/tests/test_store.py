from pathlib import Path

from knowledge.ingestion import ingest_document
from knowledge.store import save_chunks


file_path = (
    Path(__file__).resolve()
    .parents[1]
    / "documents"
    / "support_rules.md"
)


chunks = ingest_document(str(file_path))

save_chunks(chunks)

print("Saved chunks:", len(chunks))