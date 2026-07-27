export type RiskLevel = "low" | "medium" | "high" | "critical";
export type ReviewStatus =
  | "pending"
  | "running"
  | "needs_review"
  | "approved"
  | "rejected"
  | "failed";

export type Health = {
  status: string;
  app: string;
  orchestrator: "crewai";
  model: string;
  vector_store: "qdrant";
};

export type ContractDocument = {
  id: string;
  file_name: string;
  content_type: string;
  size_bytes: number;
  page_count: number;
  parser: string;
  status: string;
  created_at: string;
};

export type Finding = {
  id: string;
  clause_type: string;
  risk_level: RiskLevel;
  title: string;
  explanation: string;
  evidence: string;
  recommendation: string;
  page_number: number | null;
  confidence: number;
};

export type Review = {
  id: string;
  document_id: string;
  document_name: string;
  jurisdiction: string;
  engine: string;
  status: ReviewStatus;
  summary: string | null;
  overall_risk: RiskLevel | null;
  missing_clauses: string[];
  review_notes: string[];
  findings: Finding[];
  decision_notes: string | null;
  created_at: string;
  completed_at: string | null;
};

export type EvaluationScore = {
  runner: string;
  precision: number;
  recall: number;
  citation_rate: number;
  average_latency_ms: number;
  cases: number;
  errors: string[];
};

export type EvaluationResult = {
  created_at: string;
  score: EvaluationScore;
};
