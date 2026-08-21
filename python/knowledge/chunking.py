def split_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

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