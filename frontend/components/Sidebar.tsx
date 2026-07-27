"use client";

import Image from "next/image";
import { FileSearch, FlaskConical, ShieldCheck } from "lucide-react";

type View = "reviews" | "evaluation" | "controls";

type SidebarProps = {
  activeView: View;
  onChange: (view: View) => void;
};

const navigation = [
  {
    id: "reviews" as const,
    number: "01",
    label: "Contract reviews",
    icon: FileSearch,
  },
  {
    id: "evaluation" as const,
    number: "02",
    label: "Quality checks",
    icon: FlaskConical,
  },
  {
    id: "controls" as const,
    number: "03",
    label: "Policy controls",
    icon: ShieldCheck,
  },
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
        <p className="nav-label">Review desk</p>
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <button
              type="button"
              key={item.id}
              className={activeView === item.id ? "nav-item active" : "nav-item"}
              onClick={() => onChange(item.id)}
            >
              <span className="nav-index">{item.number}</span>
              <span className="nav-copy">{item.label}</span>
              <Icon className="nav-icon" size={17} />
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
