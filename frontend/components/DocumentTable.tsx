"use client";

import { FileCheck2, FileText } from "lucide-react";
import type { ContractDocument } from "@/lib/types";

type DocumentTableProps = {
  documents: ContractDocument[];
  selectedId: string | null;
  onSelect: (document: ContractDocument) => void;
};

const fileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
};

export function DocumentTable({
  documents,
  selectedId,
  onSelect,
}: DocumentTableProps) {
  if (!documents.length) {
    return (
      <div className="empty-list">
        <FileText size={24} />
        <strong>No contracts yet</strong>
        <p>Upload a document or use the sample agreement to begin.</p>
      </div>
    );
  }

  return (
    <div className="document-list">
      {documents.map((document) => (
        <button
          type="button"
          className={
            selectedId === document.id ? "document-row selected" : "document-row"
          }
          key={document.id}
          onClick={() => onSelect(document)}
        >
          <span className="file-icon">
            <FileText size={19} />
          </span>
          <span className="document-name">
            <strong>{document.file_name}</strong>
            <small>
              {document.page_count} page{document.page_count === 1 ? "" : "s"} ·{" "}
              {fileSize(document.size_bytes)}
            </small>
          </span>
          <span className="ready-label">
            <FileCheck2 size={15} />
            Ready
          </span>
        </button>
      ))}
    </div>
  );
}

