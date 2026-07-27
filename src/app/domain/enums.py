from enum import StrEnum


class DocumentStatus(StrEnum):
    READY = "ready"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
