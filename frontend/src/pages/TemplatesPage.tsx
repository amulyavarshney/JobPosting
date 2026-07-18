import { FormEvent, useEffect, useState } from "react";
import { api, Job, Template } from "../api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [active, setActive] = useState<Template | null>(null);
  const [previewJobId, setPreviewJobId] = useState<number | "">("");
  const [preview, setPreview] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    name: "",
    channel: "custom",
    body: "{{ job.title }} at {{ job.company }}\n{{ job.apply_url }}",
    polish_instructions: "",
    is_default: false,
  });

  const load = () =>
    Promise.all([api.listTemplates(), api.listJobs({ page_size: 100, status: "active" })])
      .then(([t, j]) => {
        setTemplates(t);
        setJobs(j.items);
        if (!active && t.length) setActive(t[0]);
        if (!previewJobId && j.items.length) setPreviewJobId(j.items[0].id);
      })
      .catch((e) => setError(String(e.message || e)));

  useEffect(() => {
    load();
  }, []);

  const save = async () => {
    if (!active) return;
    setError("");
    try {
      const updated = await api.updateTemplate(active.id, active);
      setActive(updated);
      setMessage("Template saved.");
      load();
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const create = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const t = await api.createTemplate(form);
      setCreating(false);
      setActive(t);
      setMessage("Template created.");
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const runPreview = async () => {
    if (!active || typeof previewJobId !== "number") return;
    try {
      const res = await api.previewTemplate(active.id, previewJobId, active.body);
      setPreview(res.content);
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Templates</h2>
          <p>Editable Jinja channel templates with polish instructions and live preview.</p>
        </div>
        <button onClick={() => setCreating(true)}>New template</button>
      </div>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      {creating && (
        <form className="card" onSubmit={create}>
          <h3>Create template</h3>
          <div className="row">
            <div className="field">
              <label>Name</label>
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Channel</label>
              <input
                required
                value={form.channel}
                onChange={(e) => setForm({ ...form, channel: e.target.value })}
              />
            </div>
          </div>
          <div className="field" style={{ marginTop: "0.75rem" }}>
            <label>Body (Jinja)</label>
            <textarea
              value={form.body}
              onChange={(e) => setForm({ ...form, body: e.target.value })}
            />
          </div>
          <div className="row" style={{ marginTop: "0.75rem" }}>
            <button type="submit">Create</button>
            <button type="button" className="secondary" onClick={() => setCreating(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="grid-2">
        <div className="card">
          <h3>Channels</h3>
          <div className="draft-list">
            {templates.map((t) => (
              <button
                key={t.id}
                className={`draft-item ${active?.id === t.id ? "active" : ""}`}
                onClick={() => setActive(t)}
              >
                {t.name}{" "}
                <span className="badge info" style={{ marginLeft: 6 }}>
                  {t.channel}
                </span>
                {t.is_default && (
                  <span className="badge" style={{ marginLeft: 6 }}>
                    default
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {active && (
          <div className="card">
            <h3>Edit · {active.name}</h3>
            <div className="field">
              <label>Name</label>
              <input
                value={active.name}
                onChange={(e) => setActive({ ...active, name: e.target.value })}
              />
            </div>
            <div className="field" style={{ marginTop: "0.5rem" }}>
              <label>Channel</label>
              <input
                value={active.channel}
                onChange={(e) => setActive({ ...active, channel: e.target.value })}
              />
            </div>
            <div className="field" style={{ marginTop: "0.5rem" }}>
              <label>Polish instructions</label>
              <textarea
                value={active.polish_instructions}
                onChange={(e) =>
                  setActive({ ...active, polish_instructions: e.target.value })
                }
              />
            </div>
            <div className="field" style={{ marginTop: "0.5rem" }}>
              <label>Body</label>
              <textarea
                style={{ minHeight: 220 }}
                value={active.body}
                onChange={(e) => setActive({ ...active, body: e.target.value })}
              />
            </div>
            <label style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={active.is_default}
                onChange={(e) => setActive({ ...active, is_default: e.target.checked })}
              />
              Default for channel
            </label>
            <div className="row" style={{ marginTop: "0.75rem" }}>
              <button onClick={save}>Save template</button>
              <button
                className="danger"
                onClick={async () => {
                  if (!confirm("Delete template?")) return;
                  await api.deleteTemplate(active.id);
                  setActive(null);
                  load();
                }}
              >
                Delete
              </button>
            </div>
          </div>
        )}
      </div>

      {active && (
        <div className="card">
          <h3>Preview</h3>
          <div className="row">
            <div className="field">
              <label>Sample job</label>
              <select
                value={previewJobId}
                onChange={(e) => setPreviewJobId(Number(e.target.value))}
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} — {j.company}
                  </option>
                ))}
              </select>
            </div>
            <button onClick={runPreview}>Render preview</button>
          </div>
          {preview && (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                background: "#f8faf9",
                padding: "1rem",
                borderRadius: 8,
                marginTop: "1rem",
              }}
            >
              {preview}
            </pre>
          )}
        </div>
      )}
    </>
  );
}
