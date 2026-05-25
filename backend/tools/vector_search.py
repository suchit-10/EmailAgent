from backend.vectorstore.chroma_store import EmailVectorStore


class VectorSearchTool:
    def __init__(self, store: EmailVectorStore | None = None) -> None:
        self.store = store or EmailVectorStore()

    async def semantic_email_search(self, user_id: str, query: str, limit: int = 10, filters: dict | None = None) -> list[dict]:
        return await self.store.search(user_id=user_id, query=query, limit=limit, filters=filters)
