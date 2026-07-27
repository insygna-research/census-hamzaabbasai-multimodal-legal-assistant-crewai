import {
  CheckCircle2,
  Database,
  Eye,
  FileLock2,
  ShieldCheck,
  Workflow,
} from "lucide-react";

const controls = [
  {
    title: "Evidence required",
    text: "Every risk must include contract text and a page number.",
    icon: Eye,
  },
  {
    title: "Human approval",
    text: "The workflow stops at needs review until a person decides.",
    icon: ShieldCheck,
  },
  {
    title: "Document privacy",
    text: "Files stay in configured storage and model access is explicit.",
    icon: FileLock2,
  },
  {
    title: "Structured output",
    text: "Pydantic schemas reject incomplete model responses.",
    icon: Database,
  },
  {
    title: "Defined review stack",
    text: "Reviews use CrewAI agents with Mistral and Qdrant.",
    icon: Workflow,
  },
  {
    title: "Clear failure states",
    text: "Model, OCR, and retrieval errors are returned instead of hidden.",
    icon: CheckCircle2,
  },
];

export function ControlsView() {
  return (
    <section className="controls-view">
      <div className="page-intro">
        <div>
          <span className="eyebrow">Governance</span>
          <h1>Review safeguards</h1>
          <p>
            These safeguards help legal teams check automated findings before making
            a decision.
          </p>
        </div>
      </div>

      <div className="control-grid">
        {controls.map((control) => {
          const Icon = control.icon;
          return (
            <article key={control.title}>
              <span>
                <Icon size={20} />
              </span>
              <h2>{control.title}</h2>
              <p>{control.text}</p>
            </article>
          );
        })}
      </div>

      <div className="workflow-note">
        <strong>Review path</strong>
        <ol>
          <li>Parse and classify the document</li>
          <li>Retrieve relevant contract evidence</li>
          <li>Compare clauses with the company playbook</li>
          <li>Check evidence and confidence</li>
          <li>Wait for a human decision</li>
        </ol>
      </div>
    </section>
  );
}
