from app.db.models import ReviewRecord


def build_markdown_report(review: ReviewRecord) -> str:
    lines = [
        f"# Contract Risk Review: {review.document.file_name}",
        "",
        f"- Review ID: `{review.id}`",
        f"- Jurisdiction: {review.jurisdiction}",
        f"- Review engine: {review.engine}",
        f"- Status: {review.status}",
        f"- Overall risk: {review.overall_risk or 'Not available'}",
        "",
        "## Summary",
        "",
        review.summary or "No summary is available.",
        "",
        "## Findings",
        "",
    ]

    if not review.findings:
        lines.append("No risk findings were recorded.")

    for number, finding in enumerate(review.findings, start=1):
        lines.extend(
            [
                f"### {number}. {finding.title}",
                "",
                f"- Clause: {finding.clause_type}",
                f"- Risk: {finding.risk_level}",
                f"- Page: {finding.page_number or 'Not available'}",
                f"- Confidence: {finding.confidence:.0%}",
                "",
                finding.explanation,
                "",
                f"> {finding.evidence}",
                "",
                f"Recommendation: {finding.recommendation}",
                "",
            ]
        )

    lines.extend(
        [
            "## Important notice",
            "",
            "This report supports human review and is not legal advice. "
            "A qualified reviewer must confirm every finding before use.",
            "",
        ]
    )
    return "\n".join(lines)
