"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { FileText, LoaderCircle, UploadCloud } from "lucide-react";

type UploadPanelProps = {
  busy: boolean;
  onUpload: (file: File) => Promise<void>;
  onLoadSample: () => Promise<void>;
};

export function UploadPanel({
  busy,
  onUpload,
  onLoadSample,
}: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const takeFile = async (file?: File) => {
    if (file && !busy) {
      await onUpload(file);
    }
  };

  const handleChange = async (event: ChangeEvent<HTMLInputElement>) => {
    await takeFile(event.target.files?.[0]);
    event.target.value = "";
  };

  const handleDrop = async (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    await takeFile(event.dataTransfer.files?.[0]);
  };

  return (
    <section className="upload-panel">
      <div
        className={dragging ? "drop-zone dragging" : "drop-zone"}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <span className="upload-icon">
          {busy ? <LoaderCircle className="spin" /> : <UploadCloud />}
        </span>
        <div>
          <strong>Upload a contract</strong>
          <p>PDF, scanned image, text or Markdown · up to 20 MB</p>
        </div>
        <button
          type="button"
          className="button secondary"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          Choose file
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md"
          hidden
          onChange={handleChange}
        />
      </div>

      <div className="sample-row">
        <FileText size={17} />
        <span>
          No contract ready? Load a sample vendor agreement with known risks.
        </span>
        <button
          type="button"
          className="text-button"
          disabled={busy}
          onClick={onLoadSample}
        >
          Load sample
        </button>
      </div>
    </section>
  );
}
