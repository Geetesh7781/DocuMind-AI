import { useEffect, useRef, useState } from "react";
import { ask, deleteDoc, listDocs, uploadDoc } from "./api.js";

function Answer({ text, onCite }) {
  const parts = text.split(/(\[\d+\])/g);
  return (
    <p className="answer">
      {parts.map((p, i) => {
        const m = p.match(/^\[(\d+)\]$/);
        return m ? (
          <button key={i} className="cite" onClick={() => onCite(Number(m[1]))}>{m[1]}</button>
        ) : (
          <span key={i}>{p}</span>
        );
      })}
    </p>
  );
}

function Message({ m }) {
  const [open, setOpen] = useState(null);
  if (m.role === "user") return <div className="msg user">{m.text}</div>;
  return (
    <div className="msg bot">
      <Answer text={m.text} onCite={(n) => setOpen(open === n ? null : n)} />
      {m.sources?.length > 0 && (
        <ul className="sources">
          {m.sources.map((s, i) => (
            <li key={i} className={open === i + 1 ? "src open" : "src"}>
              <button onClick={() => setOpen(open === i + 1 ? null : i + 1)}>
                <b>{i + 1}</b> {s.filename}, page {s.page}
                <span className="score">{Math.round(s.score * 100)}% match</span>
              </button>
              {open === i + 1 && <blockquote>{s.text}</blockquote>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function App() {
  const [docs, setDocs] = useState([]);
  const [selected, setSelected] = useState([]);
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const endRef = useRef(null);

  const refresh = () => listDocs().then(setDocs).catch((e) => setStatus(e.message));
  useEffect(() => { refresh(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  async function onUpload(e) {
    const files = [...e.target.files];
    e.target.value = "";
    for (const f of files) {
      setStatus(`Indexing ${f.name}…`);
      try { await uploadDoc(f); } catch (err) { setStatus(err.message); return; }
    }
    setStatus("");
    refresh();
  }

  async function onDelete(id) {
    await deleteDoc(id);
    setSelected((s) => s.filter((x) => x !== id));
    refresh();
  }

  async function onSend(e) {
    e.preventDefault();
    const question = q.trim();
    if (question.length < 3 || busy) return;
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setQ("");
    setBusy(true);
    try {
      const r = await ask(question, selected);
      setMsgs((m) => [...m, { role: "bot", text: r.answer, sources: r.sources }]);
    } catch (err) {
      setMsgs((m) => [...m, { role: "bot", text: `Something went wrong: ${err.message}` }]);
    }
    setBusy(false);
  }

  const toggle = (id) => setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  return (
    <div className="app">
      <aside>
        <h1>DocuMind</h1>
        <p className="tag">Ask your documents. Every answer shows its page.</p>
        <label className="upload">
          Add PDFs
          <input type="file" accept="application/pdf" multiple onChange={onUpload} />
        </label>
        {status && <p className="status" role="status">{status}</p>}
        <p className="hint">{selected.length ? `Searching ${selected.length} selected` : "Searching all documents"}</p>
        <ul className="docs">
          {docs.length === 0 && <li className="empty">No documents yet. Add a PDF to begin.</li>}
          {docs.map((d) => (
            <li key={d.id}>
              <label>
                <input type="checkbox" checked={selected.includes(d.id)} onChange={() => toggle(d.id)} />
                <span className="fname">{d.filename}</span>
              </label>
              <small>{d.pages} pages</small>
              <button className="del" aria-label={`Remove ${d.filename}`} onClick={() => onDelete(d.id)}>Remove</button>
            </li>
          ))}
        </ul>
      </aside>
      <main>
        <div className="thread">
          {msgs.length === 0 && (
            <div className="welcome">
              <h2>What do you need to find?</h2>
              <p>Try “Summarise the key obligations in this contract” or “What were Q3 revenues?”</p>
            </div>
          )}
          {msgs.map((m, i) => <Message key={i} m={m} />)}
          {busy && <div className="msg bot muted">Reading your documents…</div>}
          <div ref={endRef} />
        </div>
        <form onSubmit={onSend}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question about your documents" aria-label="Question" />
          <button disabled={busy || q.trim().length < 3}>Ask</button>
        </form>
      </main>
    </div>
  );
}
