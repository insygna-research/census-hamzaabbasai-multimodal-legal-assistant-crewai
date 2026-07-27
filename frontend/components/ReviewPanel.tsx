"use client";

import { useState } from "react";
import {
  Check,
  ChevronDown,
  Download,
  ExternalLink,
  LoaderCircle,
  MessageSquareWarning,
  ShieldAlert,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ContractDocument, Review } from "@/lib/types";
import { RiskBadge, StatusBadge } from "@/components/StatusBadge";

type ReviewPanelProps = {
  document: ContractDocument | null;
  review: Review | null;
  busy: boolean;
  onStart: (documentId: string, jurisdiction: string) => Promise<void>;
  onDecision: (
    reviewId: string,
    decision: "approve" | "reject",
    notes: string,
  ) => Promise<void>;
};

export function ReviewPanel({
  document,
  review,
  busy,
  onStart,
  onDecision,
}: ReviewPanelProps) {
  const [jurisdiction, setJurisdiction] = useState("EU");
  const [notes, setNotes] = useState("");

  if (!document && !review) {
    return (
      <section className="review-panel review-empty">
        <ShieldAlert size={32} />
        <h2>Select a contract</h2>
        <p>Choose a document to start a risk and compliance review.</p>
      </section>
    );
  }

  if (!review && document) {
    return (
      <section className="review-panel review-setup">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">New review</span>
            <h2>{document.file_name}</h2>
            <p>
              Select the review context. The result will still need human approval.
            </p>
          </div>
        </div>

        <div className="review-form">
          <label>
            Jurisdiction
            <span className="select-wrap">
              <select
                value={jurisdiction}
                onChange={(event) => setJurisdiction(event.target.value)}
              >
                <option value="EU">European Union</option>
                <option value="Germany">Germany</option>
                <option value="United Kingdom">United Kingdom</option>
                <option value="United States">United States</option>
              </select>
              <ChevronDown size={16} />
            </span>
          </label>

          <div className="pipeline-note">
            CrewAI agents use Mistral and retrieve contract evidence from Qdrant.
          </div>

          <button
            type="button"
            className="button primary full"
            disabled={busy}
            onClick={() => onStart(document.id, jurisdiction)}
          >
            {busy ? <LoaderCircle className="spin" size={18} /> : <ShieldAlert size={18} />}
            Start contract review
          </button>
        </div>
      </section>
    );
  }

  if (!review) return null;

  const canDecide = review.status === "needs_review" || review.status === "rejected";

  return (
    <section className="review-panel review-result">
      <div className="panel-heading result-heading">
        <div>
          <span className="eyebrow">
            {review.jurisdiction} · {review.engine}
          </span>
          <h2>{review.document_name}</h2>
        </div>
        <div className="heading-actions">
          <StatusBadge status={review.status} />
          <a className="icon-button" href={api.reportUrl(review.id)} title="Download report">
            <Download size={18} />
          </a>
        </div>
      </div>

      <div className="risk-summary">
        <div>
          <span>Overall risk</span>
          {review.overall_risk && <RiskBadge risk={review.overall_risk} />}
        </div>
        <p>{review.summary}</p>
      </div>

      <div className="finding-header">
        <h3>Risk findings</h3>
        <span>{review.findings.length} found</span>
      </div>

      <div className="finding-list">
        {review.findings.length === 0 && (
          <div className="no-findings">
            No rule or model findings were returned. Manual review is still required.
          </div>
        )}
        {review.findings.map((finding) => (
          <article className={`finding-card border-${finding.risk_level}`} key={finding.id}>
            <div className="finding-topline">
              <RiskBadge risk={finding.risk_level} />
              <span>{finding.clause_type.replaceAll("_", " ")}</span>
              <small>{Math.round(finding.confidence * 100)}% confidence</small>
            </div>
            <h4>{finding.title}</h4>
            <p>{finding.explanation}</p>
            <blockquote>
              “{finding.evidence}”
              <span>Page {finding.page_number ?? "not confirmed"}</span>
            </blockquote>
            <div className="recommendation">
              <strong>Recommended action</strong>
              <p>{finding.recommendation}</p>
            </div>
          </article>
        ))}
      </div>

      {!!review.missing_clauses.length && (
        <div className="missing-clauses">
          <MessageSquareWarning size={19} />
          <div>
            <strong>Missing or unclear clauses</strong>
            <p>{review.missing_clauses.join(", ")}</p>
          </div>
        </div>
      )}

      {canDecide ? (
        <div className="decision-box">
          <label htmlFor="review-notes">Reviewer notes</label>
          <textarea
            id="review-notes"
            rows={3}
            placeholder="Add the reason for this decision"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
          <div>
            <button
              type="button"
              className="button danger"
              disabled={busy}
              onClick={() => onDecision(review.id, "reject", notes)}
            >
              <X size={17} /> Reject
            </button>
            <button
              type="button"
              className="button primary"
              disabled={busy}
              onClick={() => onDecision(review.id, "approve", notes)}
            >
              <Check size={17} /> Approve review
            </button>
          </div>
        </div>
      ) : (
        <div className="decision-complete">
          <Check size={18} />
          <span>
            Human decision recorded
            {review.decision_notes ? `: ${review.decision_notes}` : "."}
          </span>
        </div>
      )}

      <a className="report-link" href={api.reportUrl(review.id)}>
        View evidence report <ExternalLink size={15} />
      </a>
    </section>
  );
}
