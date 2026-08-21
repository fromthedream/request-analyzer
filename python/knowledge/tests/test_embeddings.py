from embeddings import create_embedding


text = "User cannot login to account"

embedding = create_embedding(text)

print("Embedding size:", len(embedding))
print("First values:", embedding[:5])