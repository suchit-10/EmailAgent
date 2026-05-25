import chromadb
from chromadb.api.models.Collection import Collection
from backend.core.config import get_settings


class EmailVectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        self.collection: Collection = self.client.get_or_create_collection("email_messages")

    async def upsert_email(self, *, user_id: str, message_id: str, document: str, metadata: dict) -> None:
        self.collection.upsert(
            ids=[f"{user_id}:{message_id}"],
            documents=[document],
            metadatas=[{"user_id": user_id, "message_id": message_id, **metadata}],
        )

    async def search(self, *, user_id: str, query: str, limit: int = 10, filters: dict | None = None) -> list[dict]:
        where = {"user_id": user_id}
        if filters:
            where.update(filters)
        result = self.collection.query(query_texts=[query], n_results=limit, where=where)
        hits: list[dict] = []
        for idx, doc_id in enumerate(result.get("ids", [[]])[0]):
            hits.append(
                {
                    "id": doc_id,
                    "document": result.get("documents", [[]])[0][idx],
                    "metadata": result.get("metadatas", [[]])[0][idx],
                    "distance": result.get("distances", [[]])[0][idx] if result.get("distances") else None,
                }
            )
        return hits
