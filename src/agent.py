from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # TODO: store references to store and llm_fn
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        retrieved = self.store.search(question, top_k=top_k)
        context_blocks: list[str] = []
        for index, item in enumerate(retrieved, start=1):
            source = item.get("metadata", {}).get("source", item.get("doc_id", "unknown"))
            context_blocks.append(
                f"[Chunk {index} | score={item.get('score', 0.0):.3f} | source={source}]\n{item.get('content', '')}"
            )

        context = "\n\n".join(context_blocks) if context_blocks else "No relevant context retrieved."
        prompt = (
            "You are a helpful knowledge base assistant.\n"
            "Answer the question using only the context below.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
