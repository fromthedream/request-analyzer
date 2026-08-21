from pathlib import Path
from chunking import split_text
from pathlib import Path

print(Path(__file__).resolve())
print(Path(__file__).resolve().parents)


root = Path(__file__).resolve().parents[2]

file_path = root / "knowledge" / "documents" / "support_rules.md"

with open(file_path, "r", encoding="utf-8") as file:
    text = file.read()


chunks = split_text(text)

print(f"Chunks: {len(chunks)}")

for index, chunk in enumerate(chunks):
    print("\n--- CHUNK", index, "---")
    print(chunk[:300])