import unittest

from qdrant_client import QdrantClient

from app.knowledge.chunking import chunk_markdown
from app.knowledge.embeddings import HashEmbeddingProvider
from app.knowledge.qdrant_store import QdrantStore
from app.knowledge.retrieval import SemanticRetriever


class KnowledgeTests(unittest.TestCase):
    def test_chunks_keep_batch_and_page_range(self):
        markdown = """<!-- batch:003 pages:10-12 -->
<!-- page-range:10-12 -->
## Production

Mine X produced 12,400 tonnes during the reporting period, supported by the annual report table.
"""
        chunks = chunk_markdown(markdown, document_id="doc", filename="report.pdf")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].page_range, "10-12")
        self.assertEqual(chunks[0].batch, "003")
        self.assertEqual(chunks[0].section, "Production")


    def test_in_memory_qdrant_round_trip_returns_provenance(self):
        client = QdrantClient(":memory:")
        store = QdrantStore(client=client, collection="test_chunks")
        embedder = HashEmbeddingProvider()
        chunks = chunk_markdown(
            "<!-- page-range:4-6 -->\n\nThe mine production total was 12,400 tonnes in 2023.",
            document_id="doc",
            filename="report.pdf",
            min_chars=20,
        )
        store.upsert_chunks(chunks, embedder.embed([chunk.text for chunk in chunks]))
        results = SemanticRetriever(store, embedder).search("mine production tonnes", limit=1)
        self.assertEqual(results[0].document_id, "doc")
        self.assertEqual(results[0].page_range, "4-6")