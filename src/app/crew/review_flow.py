import re
from difflib import SequenceMatcher
from uuid import UUID

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.crew.contract_crew import ContractReviewCrew
from app.domain.schemas import ReviewResult
from app.services.retrieval import ContractSearch


class ReviewFlowState(BaseModel):
    document_id: str = ""
    document_text: str = ""
    jurisdiction: str = "EU"
    result: dict = Field(default_factory=dict)


class ContractReviewFlow(Flow[ReviewFlowState]):
    settings: Settings = Field(exclude=True)

    @start()
    def run_review(self) -> ReviewResult:
        contract_search = ContractSearch(
            self.settings,
            UUID(self.state.document_id),
            self.state.document_text,
        )
        result = ContractReviewCrew(
            self.settings,
            contract_search,
        ).run(self.state.jurisdiction)

        self.state.result = result.model_dump()
        return result

    @listen(run_review)
    def check_evidence(self, result: ReviewResult) -> ReviewResult:
        verified = []
        notes = list(result.review_notes)

        for finding in result.findings:
            updated = finding.model_copy()
            if not _evidence_matches(self.state.document_text, finding.evidence):
                updated.confidence = min(updated.confidence, 0.55)
                notes.append(f"Evidence needs manual confirmation: {finding.title}.")
            if updated.page_number is None:
                updated.page_number = _find_page(self.state.document_text, finding.evidence)
            verified.append(updated)

        checked = result.model_copy(update={"findings": verified, "review_notes": notes})
        self.state.result = checked.model_dump()
        return checked


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _evidence_matches(document_text: str, evidence: str) -> bool:
    clean_document = _clean(document_text)
    clean_evidence = _clean(evidence)
    if clean_evidence in clean_document:
        return True
    if len(clean_evidence) < 25:
        return False
    words = clean_evidence.split()
    window_size = len(words)
    document_words = clean_document.split()
    for start_index in range(0, len(document_words), max(1, window_size // 3)):
        window = " ".join(document_words[start_index : start_index + window_size + 8])
        if SequenceMatcher(None, clean_evidence, window).ratio() >= 0.88:
            return True
    return False


def _find_page(document_text: str, evidence: str) -> int | None:
    position = _clean(document_text).find(_clean(evidence))
    if position < 0:
        return None
    page = 1
    clean_prefix = _clean(document_text[:position])
    for match in re.finditer(r"\[page (\d+)\]", clean_prefix):
        page = int(match.group(1))
    return page


def execute_review_flow(
    settings: Settings,
    *,
    document_id: UUID,
    document_text: str,
    jurisdiction: str,
) -> ReviewResult:
    flow = ContractReviewFlow(settings=settings, tracing=False)
    output = flow.kickoff(
        inputs={
            "document_id": str(document_id),
            "document_text": document_text,
            "jurisdiction": jurisdiction,
        }
    )
    return ReviewResult.model_validate(output)
