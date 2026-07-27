import { BarChart3, CheckCircle2, LoaderCircle, Play } from "lucide-react";
import type { EvaluationResult } from "@/lib/types";

type EvaluationLabProps = {
  busy: boolean;
  result: EvaluationResult | null;
  onRun: () => Promise<void>;
};

export function EvaluationLab({
  busy,
  result,
  onRun,
}: EvaluationLabProps) {
  return (
    <section className="evaluation-view">
      <div className="page-intro">
        <div>
          <span className="eyebrow">Test set</span>
          <h1>Review quality</h1>
          <p>
            Check risk detection, evidence coverage, speed, and errors against the
            included contract cases.
          </p>
        </div>
        <button
          type="button"
          className="button primary"
          disabled={busy}
          onClick={onRun}
        >
          {busy ? <LoaderCircle className="spin" size={17} /> : <Play size={17} />}
          Run evaluation
        </button>
      </div>

      <div className="runner-summary">
        <div>
          <small>Review stack</small>
          <strong>CrewAI · Mistral · Qdrant</strong>
        </div>
        <span>
          <CheckCircle2 size={15} />
          Ready
        </span>
      </div>

      <div className="evaluation-grid">
        {result && (
          <article className="score-card">
            <div>
              <BarChart3 size={20} />
              <strong>{result.score.runner}</strong>
              <span>{result.score.cases} cases</span>
            </div>
            <dl>
              <div>
                <dt>Precision</dt>
                <dd>{Math.round(result.score.precision * 100)}%</dd>
              </div>
              <div>
                <dt>Recall</dt>
                <dd>{Math.round(result.score.recall * 100)}%</dd>
              </div>
              <div>
                <dt>Citation rate</dt>
                <dd>{Math.round(result.score.citation_rate * 100)}%</dd>
              </div>
              <div>
                <dt>Average time</dt>
                <dd>{Math.round(result.score.average_latency_ms)} ms</dd>
              </div>
            </dl>
            {!!result.score.errors.length && (
              <p className="score-errors">{result.score.errors.length} case errors</p>
            )}
          </article>
        )}

        {!result && (
          <div className="evaluation-empty">
            <BarChart3 size={28} />
            <strong>No evaluation run yet</strong>
            <p>The included test set contains clear, expected contract risks.</p>
          </div>
        )}
      </div>
    </section>
  );
}
