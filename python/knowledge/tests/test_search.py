from knowledge.search import search_chunks


results = search_chunks(
    "Как обрабатывать жалобы клиентов?"
)

for item in results:
    print(item)
    print(type(item))
    print("-" * 50)