import type { ReviewStatus, RiskLevel } from "@/lib/types";

const statusLabels: Record<ReviewStatus, string> = {
  pending: "Pending",
  running: "Running",
  needs_review: "Needs review",
  approved: "Approved",
  rejected: "Rejected",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: ReviewStatus }) {
  return (
    <span className={`badge status-${status}`}>
      <span className="badge-dot" />
      {statusLabels[status]}
    </span>
  );
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return <span className={`risk-pill risk-${risk}`}>{risk}</span>;
}

