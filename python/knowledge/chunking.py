#Текст -> режем по 500 слов -> режем по 50 слов пересечения между кусками

def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:
    words = text.split()

    chunks = []

    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks