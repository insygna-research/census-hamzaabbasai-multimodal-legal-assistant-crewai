from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.domain.schemas import ContractFinding, ReviewResult
from app.main import create_app


def build_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_dir=tmp_path / "uploads",
    )
    return TestClient(create_app(settings))


def fake_review(
    settings: Settings,
    document_id,
    document_text: str,
    jurisdiction: str,
) -> ReviewResult:
    patterns = [
        ("liability is unlimited", "liability"),
        ("automatically renew", "auto_renewal"),
        ("outside the european economic area", "data_transfer"),
        ("change the fees", "unilateral_change"),
        ("customer shall indemnify", "indemnity"),
    ]
    clean_text = document_text.lower()
    evidence = "contract evidence"
    clause_type = "liability"
    for phrase, expected_type in patterns:
        if phrase in clean_text:
            start = clean_text.index(phrase)
            evidence = document_text[start : start + len(phrase)]
            clause_type = expected_type
            break

    return ReviewResult(
        summary=f"One risk found for {jurisdiction}.",
        overall_risk="high",
        findings=[
            ContractFinding(
                clause_type=clause_type,
                risk_level="high",
                title="Contract risk needs review",
                explanation="The clause may create a material business risk.",
                evidence=evidence,
                recommendation="Ask a legal reviewer to confirm and update this clause.",
                page_number=1,
                confidence=0.91,
            )
        ],
        missing_clauses=[],
        review_notes=["Human approval is required."],
        review_engine="crewai-mistral-qdrant",
    )


def test_review_requires_human_decision(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.reviews.execute_contract_review",
        fake_review,
    )

    with build_client(tmp_path) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["app"] == "Multimodal Legal Assistant"
        assert health.json()["vector_store"] == "qdrant"

        document_response = client.post("/api/v1/documents/sample")
        assert document_response.status_code == 201
        document = document_response.json()

        review_response = client.post(
            "/api/v1/reviews",
            json={
                "document_id": document["id"],
                "jurisdiction": "EU",
            },
        )
        assert review_response.status_code == 201
        review = review_response.json()
        assert review["status"] == "needs_review"
        assert review["engine"] == "crewai-mistral-qdrant"
        assert len(review["findings"]) == 1

        decision_response = client.post(
            f"/api/v1/reviews/{review['id']}/decision",
            json={"decision": "approve", "notes": "Evidence checked against the sample."},
        )
        assert decision_response.status_code == 200
        assert decision_response.json()["status"] == "approved"


def test_evaluation_has_expected_metrics(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.evaluations.execute_contract_review",
        fake_review,
    )

    with build_client(tmp_path) as client:
        response = client.post("/api/v1/evaluations/run")
        assert response.status_code == 200
        score = response.json()["score"]
        assert score["runner"] == "crewai-mistral-qdrant"
        assert score["precision"] == 1.0
        assert score["recall"] == 1.0
        assert score["citation_rate"] == 1.0
