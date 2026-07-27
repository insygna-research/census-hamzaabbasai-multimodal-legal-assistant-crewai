import type {
  ContractDocument,
  EvaluationResult,
  Health,
  Review,
} from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  documents: () => request<ContractDocument[]>("/documents"),
  reviews: () => request<Review[]>("/reviews"),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ContractDocument>("/documents", {
      method: "POST",
      body: form,
    });
  },
  loadSample: () =>
    request<ContractDocument>("/documents/sample", { method: "POST" }),
  createReview: (documentId: string, jurisdiction: string) =>
    request<Review>("/reviews", {
      method: "POST",
      body: JSON.stringify({
        document_id: documentId,
        jurisdiction,
      }),
    }),
  decide: (reviewId: string, decision: "approve" | "reject", notes: string) =>
    request<Review>(`/reviews/${reviewId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision, notes }),
    }),
  runEvaluation: () =>
    request<EvaluationResult>("/evaluations/run", {
      method: "POST",
    }),
  reportUrl: (reviewId: string) => `${API_URL}/reviews/${reviewId}/report`,
};
