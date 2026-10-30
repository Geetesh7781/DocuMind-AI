async function req(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export const listDocs = () => req("/api/documents");
export const deleteDoc = (id) => req(`/api/documents/${id}`, { method: "DELETE" });
export const uploadDoc = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return req("/api/documents", { method: "POST", body: fd });
};
export const ask = (question, doc_ids) =>
  req("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, doc_ids: doc_ids?.length ? doc_ids : null }),
  });
