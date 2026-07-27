"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  FileStack,
  LoaderCircle,
  RefreshCw,
  Search,
} from "lucide-react";
import { api } from "@/lib/api";
import type {
  ContractDocument,
  EvaluationResult,
  Health,
  Review,
} from "@/lib/types";
import { ControlsView } from "@/components/ControlsView";
import { DocumentTable } from "@/components/DocumentTable";
import { EvaluationLab } from "@/components/EvaluationLab";
import { ReviewPanel } from "@/components/ReviewPanel";
import { Sidebar } from "@/components/Sidebar";
import { UploadPanel } from "@/components/UploadPanel";

type View = "reviews" | "evaluation" | "controls";

export default function Home() {
  const [view, setView] = useState<View>("reviews");
  const [health, setHealth] = useState<Health | null>(null);
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
    const [healthResult, documentResult, reviewResult] = await Promise.all([
      api.health(),
      api.documents(),
      api.reviews(),
    ]);
    setHealth(healthResult);
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
          <span className="environment">
            <span />
            {health ? "API online" : "Checking API"}
          </span>
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
                <span className="eyebrow">Contract operations</span>
                <h1>Review queue</h1>
                <p>Check obligations, missing clauses, and risk findings against source text.</p>
              </div>
            </div>

            <section className="stats-grid">
              <article>
                <span className="stat-icon blue">
                  <FileStack size={19} />
                </span>
                <div>
                  <strong>{stats.documents}</strong>
                  <small>Contracts</small>
                </div>
              </article>
              <article>
                <span className="stat-icon amber">
                  <AlertTriangle size={19} />
                </span>
                <div>
                  <strong>{stats.needsReview}</strong>
                  <small>Need decision</small>
                </div>
              </article>
              <article>
                <span className="stat-icon red">
                  <AlertTriangle size={19} />
                </span>
                <div>
                  <strong>{stats.highRisk}</strong>
                  <small>High risk</small>
                </div>
              </article>
              <article>
                <span className="stat-icon green">
                  <CheckCircle2 size={19} />
                </span>
                <div>
                  <strong>{stats.approved}</strong>
                  <small>Approved</small>
                </div>
              </article>
            </section>

            <UploadPanel busy={busy} onUpload={upload} onLoadSample={loadSample} />

            <div className="workspace-grid">
              <section className="document-panel">
                <div className="section-heading">
                  <div>
                    <h2>Contracts</h2>
                    <p>Select a file to review its current result.</p>
                  </div>
                  <span>{documents.length}</span>
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
