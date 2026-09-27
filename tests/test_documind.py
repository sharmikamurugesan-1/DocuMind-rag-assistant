"""
Unit & Integration Tests for DocuMind-rag-assistant
Validates document chunking, BM25 semantic retrieval, hallucination refusal guardrails,
and source citation fidelity.
"""

import pytest
from rag_engine import RAGEngine

SAMPLE_CONTRACT_TEXT = """
CLOUD SERVICE LEVEL AGREEMENT (SLA)
Effective Date: March 1, 2025
Provider: Quantum Cloud Infrastructure Ltd.
Client: Horizon Digital Corporation

SECTION 1: SERVICE AVAILABILITY & MAINTENANCE
1.1 Uptime Guarantee: Provider commits to 99.95% monthly service availability for core compute instances.
1.2 Scheduled Maintenance: Planned downtime must occur on Sundays between 02:00 UTC and 04:00 UTC with at least 72 hours advance notice.

SECTION 2: SERVICE CREDITS & REMEDIES
2.1 Tier 1 Outage: If uptime is between 99.0% and 99.9%, Client receives a 15% billing credit.
2.2 Tier 2 Outage: If uptime drops below 95.0%, Client is entitled to a 50% service credit for the affected calendar month.

SECTION 3: LIABILITY & TERMINATION
3.1 Penalty for Delay: In case of delayed deployment exceeding 14 business days, Provider pays a 2.0% penalty fee per week, capped at 20% aggregate liability.
3.2 Governing Law: This agreement shall be governed under the laws of New York State.
"""

def test_document_chunking():
    engine = RAGEngine(chunk_size=50, overlap=10)
    chunks_count = engine.add_document(SAMPLE_CONTRACT_TEXT, source_name="sla_test.pdf")
    
    assert chunks_count >= 2
    assert len(engine.chunks) == chunks_count
    assert engine.chunks[0]["source"] == "sla_test.pdf"

def test_relevant_query_retrieval_and_citation():
    engine = RAGEngine(chunk_size=100, overlap=20)
    engine.add_document(SAMPLE_CONTRACT_TEXT, source_name="sla_contract.pdf")
    
    res = engine.query("What service credits apply if uptime drops below 95%?")
    
    assert "answer" in res
    assert "50%" in res["answer"]
    assert len(res["citations"]) > 0
    assert res["citations"][0]["source"] == "sla_contract.pdf"
    assert res["telemetry"]["chunks_retrieved"] > 0
    assert res["telemetry"]["latency_ms"] >= 0

def test_hallucination_guardrail_refusal():
    engine = RAGEngine(chunk_size=100, overlap=20, similarity_threshold=0.15)
    engine.add_document(SAMPLE_CONTRACT_TEXT, source_name="sla_contract.pdf")
    
    # Completely unrelated question
    res = engine.query("What is the recipe for chocolate chip cookies?")
    
    assert "do not contain sufficient verified information" in res["answer"].lower()
    assert len(res["citations"]) == 0
    assert res["telemetry"]["mode"] == "grounded_refusal"
