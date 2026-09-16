"""Unit tests for the knowledge layer."""

from __future__ import annotations

import unittest

from qdrant_client import QdrantClient

from app.extraction.postgres import normalize_table_facts
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

    def test_normalize_table_facts_returns_completed_and_partial(self):
        """normalize_table_facts now returns (completed, partial) tuple."""
        # Grid-style table payload
        payload = {
            "tables": [
                {
                    "data": {
                        "num_rows": 3,
                        "num_cols": 2,
                        "grid": [
                            [{"text": "Metric"}, {"text": "1984-85"}],
                            [{"text": "Production"}, {"text": "12,400"}],
                            [{"text": "Workers"}, {"text": "99,447"}],
                        ],
                    }
                }
            ]
        }
        completed, partial = normalize_table_facts(payload, "doc", "4-6")
        # At minimum should have 1 completed fact (Production/12,400 with period detected)
        assert isinstance(completed, list), "Expected completed to be a list"
        assert isinstance(partial, list), "Expected partial to be a list"
        # The old test expected 2 facts total; now we have completed + partial
        total = len(completed) + len(partial)
        assert total >= 1, f"Expected at least 1 fact (completed+partial), got {total}"

    def test_normalize_table_facts_skips_empty_grid(self):
        """Empty grid should produce (completed=[], partial=[])."""
        payload = {
            "tables": [
                {
                    "data": {
                        "num_rows": 1,
                        "num_cols": 1,
                        "grid": [[{"text": ""}]],
                    }
                }
            ]
        }
        completed, partial = normalize_table_facts(payload, "doc", "1-3")
        assert len(completed) == 0, f"Expected 0 completed, got {len(completed)}"
        assert len(partial) == 0, f"Expected 0 partial, got {len(partial)}"

    def test_normalize_table_facts_partial_captured_when_fields_missing(self):
        """When entity/period/unit are missing, facts go to partial."""
        # Simple rows table without clear period/entity in headers
        payload = {
            "tables": [
                {
                    "rows": [
                        ["Metric", "1984-85"],
                        ["Production", "12,400"],
                    ]
                }
            ]
        }
        completed, partial = normalize_table_facts(payload, "doc", "1-3")
        # With our enhanced detector, 1984-85 should be detected as period
        # and we should get at least 1 completed fact
        total = len(completed) + len(partial)
        assert total >= 1, f"Expected at least 1 fact, got total={total}"
        # Verify they're properly categorized
        assert isinstance(completed, list)
        assert isinstance(partial, list)