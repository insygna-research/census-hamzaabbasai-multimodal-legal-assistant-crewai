"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  LoaderCircle,
  RefreshCw,
  Search,
} from "lucide-react";
import { api } from "@/lib/api";
import type { ContractDocument, EvaluationResult, Review } from "@/lib/types";
import { ControlsView } from "@/components/ControlsView";
import { DocumentTable } from "@/components/DocumentTable";
import { EvaluationLab } from "@/components/EvaluationLab";
import { ReviewPanel } from "@/components/ReviewPanel";
import { Sidebar } from "@/components/Sidebar";
import { UploadPanel } from "@/components/UploadPanel";

type View = "reviews" | "evaluation" | "controls";

const viewTitles: Record<View, string> = {
  reviews: "Contract review",
  evaluation: "Quality checks",
  controls: "Policy controls",
};

export default function Home() {
  const [view, setView] = useState<View>("reviews");
  const [documents, setDocuments] = useState<ContractDocument[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [selectedDocument, setSelectedDocument] =
    useState<ContractDocument | null>(null);
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [documentResult, reviewResult] = await Promise.all([
      api.documents(),
      api.reviews(),
    ]);
    setDocuments(documentResult);
    setReviews(reviewResult);
    setSelectedReview((current) =>
      current
        ? reviewResult.find((review) => review.id === current.id) ?? current
        : null,
    );
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      refresh().catch((reason: Error) => setError(reason.message));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refresh]);

  const work = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await action();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The request failed");
    } finally {
      setBusy(false);
    }
  };

  const selectDocument = (document: ContractDocument) => {
    setSelectedDocument(document);
    const latest = reviews.find((review) => review.document_id === document.id);
    setSelectedReview(latest ?? null);
  };

  const upload = (file: File) =>
    work(async () => {
      const document = await api.upload(file);
      await refresh();
      setSelectedDocument(document);
      setSelectedReview(null);
      setNotice(`${document.file_name} is ready for review.`);
    });

  const loadSample = () =>
    work(async () => {
      const document = await api.loadSample();
      await refresh();
      setSelectedDocument(document);
      setSelectedReview(null);
      setNotice("The sample vendor agreement is ready.");
    });

  const startReview = (documentId: string, jurisdiction: string) =>
    work(async () => {
      const review = await api.createReview(documentId, jurisdiction);
      await refresh();
      setSelectedReview(review);
      setNotice("Analysis finished. A human decision is now required.");
    });

  const decide = (
    reviewId: string,
    decision: "approve" | "reject",
    notes: string,
  ) =>
    work(async () => {
      const review = await api.decide(reviewId, decision, notes);
      await refresh();
      setSelectedReview(review);
      setNotice(`Review marked as ${review.status}.`);
    });

  const runEvaluation = () =>
    work(async () => {
      setEvaluation(await api.runEvaluation());
      setNotice("Evaluation completed.");
    });

  const stats = useMemo(
    () => ({
      documents: documents.length,
      needsReview: reviews.filter((review) => review.status === "needs_review").length,
      approved: reviews.filter((review) => review.status === "approved").length,
      highRisk: reviews.filter(
        (review) =>
          review.overall_risk === "high" || review.overall_risk === "critical",
      ).length,
    }),
    [documents, reviews],
  );

  const visibleDocuments = useMemo(() => {
    const cleanQuery = query.trim().toLowerCase();
    if (!cleanQuery) return documents;
    return documents.filter((document) =>
      document.file_name.toLowerCase().includes(cleanQuery),
    );
  }, [documents, query]);

  return (
    <div className="app-shell">
      <Sidebar activeView={view} onChange={setView} />

      <main className="main">
        <header className="topbar">
          <div className="topbar-context">
            <span>Legal operations</span>
            <strong>{viewTitles[view]}</strong>
          </div>
          <div className="search">
            <Search size={17} />
            <input
              aria-label="Search contracts"
              placeholder="Search contracts"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <button
            type="button"
            className="icon-button"
            title="Refresh data"
            disabled={busy}
            onClick={() => work(refresh)}
          >
            {busy ? <LoaderCircle className="spin" size={18} /> : <RefreshCw size={18} />}
          </button>
        </header>

        {notice && (
          <div className="toast success">
            <CheckCircle2 size={17} />
            {notice}
            <button type="button" onClick={() => setNotice(null)}>
              ×
            </button>
          </div>
        )}
        {error && (
          <div className="toast error">
            <AlertTriangle size={17} />
            {error}
            <button type="button" onClick={() => setError(null)}>
              ×
            </button>
          </div>
        )}

        {view === "reviews" && (
          <div className="reviews-view">
            <div className="page-intro">
              <div>
                <span className="eyebrow">Contract review desk</span>
                <h1>Evidence before judgement.</h1>
                <p>
                  Review contract language, trace each finding to its source, and
                  record a clear decision.
                </p>
              </div>
              <div className="desk-reference">
                <span>Current workspace</span>
                <strong>Commercial contracts</strong>
              </div>
            </div>

            <section className="review-register" aria-label="Review register">
              <div className="register-heading">
                <span>Live register</span>
                <strong>Current workload</strong>
              </div>
              <dl>
                <div>
                  <dt>Contracts</dt>
                  <dd>{stats.documents}</dd>
                </div>
                <div>
                  <dt>Need decision</dt>
                  <dd>{stats.needsReview}</dd>
                </div>
                <div>
                  <dt>High risk</dt>
                  <dd>{stats.highRisk}</dd>
                </div>
                <div>
                  <dt>Approved</dt>
                  <dd>{stats.approved}</dd>
                </div>
              </dl>
            </section>

            <UploadPanel busy={busy} onUpload={upload} onLoadSample={loadSample} />

            <div className="workspace-grid">
              <section className="document-panel">
                <div className="section-heading">
                  <div>
                    <span className="section-index">01</span>
                    <h2>Contract register</h2>
                    <p>Select a file to open its latest review.</p>
                  </div>
                  <span className="record-count">
                    {documents.length} record{documents.length === 1 ? "" : "s"}
                  </span>
                </div>
                <DocumentTable
                  documents={visibleDocuments}
                  selectedId={selectedDocument?.id ?? selectedReview?.document_id ?? null}
                  onSelect={selectDocument}
                />
              </section>

              <ReviewPanel
                document={selectedDocument}
                review={selectedReview}
                busy={busy}
                onStart={startReview}
                onDecision={decide}
              />
            </div>
          </div>
        )}

        {view === "evaluation" && (
          <EvaluationLab
            busy={busy}
            result={evaluation}
            onRun={runEvaluation}
          />
        )}

        {view === "controls" && <ControlsView />}
      </main>
    </div>
  );
}
