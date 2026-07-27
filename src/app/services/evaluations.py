import json
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from app.core.config import Settings
from app.domain.schemas import EvaluationResponse, EvaluationScore
from app.services.reviews import execute_contract_review


class EvaluationService:
    def __init__(self, settings: Settings, dataset_path: Path) -> None:
        self.settings = settings
        self.dataset_path = dataset_path

    def run(self) -> EvaluationResponse:
        cases = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        return EvaluationResponse(score=self._score(cases))

    def _score(self, cases: list[dict]) -> EvaluationScore:
        true_positive = 0
        predicted_total = 0
        expected_total = 0
        cited_findings = 0
        total_findings = 0
        latencies = []
        errors = []

        for case in cases:
            started_at = perf_counter()
            try:
                result = execute_contract_review(
                    self.settings,
                    uuid4(),
                    case["contract_text"],
                    case.get("jurisdiction", "EU"),
                )
                predicted = {finding.clause_type for finding in result.findings}
                expected = set(case["expected_clause_types"])
                true_positive += len(predicted & expected)
                predicted_total += len(predicted)
                expected_total += len(expected)
                total_findings += len(result.findings)
                cited_findings += sum(
                    1
                    for finding in result.findings
                    if finding.evidence.lower() in case["contract_text"].lower()
                )
            except Exception as error:
                errors.append(f"{case['id']}: {error}")
            finally:
                latencies.append((perf_counter() - started_at) * 1000)

        precision = true_positive / predicted_total if predicted_total else 0.0
        recall = true_positive / expected_total if expected_total else 0.0
        citation_rate = cited_findings / total_findings if total_findings else 0.0

        return EvaluationScore(
            runner="crewai-mistral-qdrant",
            precision=round(precision, 3),
            recall=round(recall, 3),
            citation_rate=round(citation_rate, 3),
            average_latency_ms=round(sum(latencies) / len(latencies), 1),
            cases=len(cases),
            errors=errors,
        )
