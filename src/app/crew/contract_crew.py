import json
import os

from crewai import LLM, Agent, Crew, Process, Task
from crewai.tools import tool

from app.core.config import Settings
from app.domain.schemas import ReviewResult
from app.services.retrieval import ContractSearch

DEFAULT_PLAYBOOK = {
    "liability": "Liability should normally be capped at fees paid in the last 12 months.",
    "termination": "Termination without cause should provide at least 30 days of written notice.",
    "data_protection": "Personal data transfers need a lawful transfer mechanism and safeguards.",
    "renewal": "Automatic renewal must include a clear notice period and reminder.",
    "indemnity": "Indemnity should be limited, controlled, and reasonably mutual.",
    "evidence": "Every finding must include an exact quote and a page number.",
}


class ContractReviewCrew:
    def __init__(
        self,
        settings: Settings,
        contract_search: ContractSearch,
    ) -> None:
        self.settings = settings
        self.contract_search = contract_search
        self.llm = self._build_llm()

    def run(self, jurisdiction: str) -> ReviewResult:
        search_contract = self._search_tool()

        clause_analyst = Agent(
            role="Contract clause analyst",
            goal="Find important contract clauses and return exact supporting evidence",
            backstory=(
                "You review commercial contracts carefully. You do not provide legal advice. "
                "You separate contract text from assumptions and always use the search tool."
            ),
            llm=self.llm,
            tools=[search_contract],
            allow_delegation=False,
            verbose=False,
        )
        compliance_reviewer = Agent(
            role="Contract compliance reviewer",
            goal="Compare contract terms with the legal playbook and flag material gaps",
            backstory=(
                "You support an enterprise legal operations team. You explain risks in plain "
                "business language and keep the review linked to written evidence."
            ),
            llm=self.llm,
            tools=[search_contract],
            allow_delegation=False,
            verbose=False,
        )
        evidence_reviewer = Agent(
            role="Evidence and quality reviewer",
            goal="Remove unsupported findings and produce the final structured review",
            backstory=(
                "You are the final quality gate. Unsupported claims are removed. Exact quotes, "
                "page numbers, confidence, and practical recommendations are required."
            ),
            llm=self.llm,
            tools=[search_contract],
            allow_delegation=False,
            verbose=False,
        )

        clause_task = Task(
            description=(
                "Search the contract for liability, termination, renewal, data protection, "
                "confidentiality, governing law, payment, audit, and indemnity clauses. "
                "Return exact quotes and page numbers. Do not guess missing text."
            ),
            expected_output="A clause inventory with exact evidence and page numbers.",
            agent=clause_analyst,
        )
        compliance_task = Task(
            description=(
                f"Review the clause inventory for jurisdiction {jurisdiction}. Compare it with "
                f"this company playbook:\n{json.dumps(DEFAULT_PLAYBOOK, indent=2)}\n"
                "Identify material risks and missing required clauses. Use the contract search "
                "tool again when evidence is weak."
            ),
            expected_output="A risk review linked to exact contract evidence.",
            agent=compliance_reviewer,
            context=[clause_task],
        )
        evidence_task = Task(
            description=(
                "Check every proposed finding. Keep only findings supported by an exact "
                "contract quote. Set review_engine to 'crewai-mistral-qdrant'. Explain that a "
                "human must approve the result. "
                "Return the final result in the required structure."
            ),
            expected_output="A complete structured contract review.",
            agent=evidence_reviewer,
            context=[clause_task, compliance_task],
            output_pydantic=ReviewResult,
        )

        output = Crew(
            agents=[clause_analyst, compliance_reviewer, evidence_reviewer],
            tasks=[clause_task, compliance_task, evidence_task],
            process=Process.sequential,
            memory=False,
            verbose=False,
            max_rpm=20,
        ).kickoff()

        if output.pydantic is None:
            return ReviewResult.model_validate(output.to_dict())
        return ReviewResult.model_validate(output.pydantic)

    def _search_tool(self):
        contract_search_service = self.contract_search

        @tool("search_contract")
        def search_contract(query: str) -> str:
            """Search the active contract and return relevant source text."""
            return contract_search_service.search_text(query)

        return search_contract

    def _build_llm(self) -> LLM:
        if not self.settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required for contract review")

        os.environ.setdefault("MISTRAL_API_KEY", self.settings.mistral_api_key)
        return LLM(
            model=f"mistral/{self.settings.model_name}",
            api_key=self.settings.mistral_api_key,
            temperature=0.1,
            timeout=120,
            max_retries=2,
        )
