"use client";

import Image from "next/image";
import {
  Activity,
  FileSearch,
  FlaskConical,
  ShieldCheck,
} from "lucide-react";

type View = "reviews" | "evaluation" | "controls";

type SidebarProps = {
  activeView: View;
  onChange: (view: View) => void;
};

const navigation = [
  { id: "reviews" as const, label: "Contract reviews", icon: FileSearch },
  { id: "evaluation" as const, label: "Quality checks", icon: FlaskConical },
  { id: "controls" as const, label: "Policy controls", icon: ShieldCheck },
];

export function Sidebar({ activeView, onChange }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">
          <Image
            src="/legal-document.png"
            alt=""
            width={34}
            height={34}
            priority
          />
        </span>
        <span>
          <strong>Multimodal Legal Assistant</strong>
          <small>Contract review workspace</small>
        </span>
      </div>

      <nav className="navigation" aria-label="Main navigation">
        <p className="nav-label">Workspace</p>
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <button
              type="button"
              key={item.id}
              className={activeView === item.id ? "nav-item active" : "nav-item"}
              onClick={() => onChange(item.id)}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="system-card">
        <div className="system-status">
          <Activity size={16} />
          <span>Review service available</span>
        </div>
        <p>CrewAI · Mistral · Qdrant</p>
        <small>Human approval remains required.</small>
      </div>
    </aside>
  );
}
