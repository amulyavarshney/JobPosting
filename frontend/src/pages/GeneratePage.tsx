import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Draft, Job, Revision, Template } from "../api";

const PROTECTED = new Set(["reviewed", "approved", "exported"]);

export default function GeneratePage() {
  const [params] = useSearchParams();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jobId, setJobId] = useState<number | "">("");
  const [bulkIds, setBulkIds] = useState<number[]>([]);
  const [selectedTemplates, setSelectedTemplates] = useState<number[]>([]);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [activeDraft, setActiveDraft] = useState<Draft | null>(null);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [requirement, setRequirement] = useState("");
  const [importText, setImportText] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Promise.all([
      api.listJobs({ page_size: 200, status: "active" }),
      api.listTemplates(),
    ])
      .then(async ([j, t]) => {
        let items = j.items;
        setTemplates(t);
        const jobParam = params.get("job");
        const jobsParam = params.get("jobs");
        let focusId: number | "" = "";

        if (jobsParam) {
          const ids = jobsParam
            .split(",")
            .map(Number)
            .filter((n) => !Number.isNaN(n));
          setBulkIds(ids);
          focusId = ids[0] || "";
        } else if (jobParam) {
          focusId = Number(jobParam);
        } else if (items.length) {
          focusId = items[0].id;
        }

        if (typeof focusId === "number" && !items.some((x) => x.id === focusId)) {
          try {
            const missing = await api.getJob(focusId);
            items = [missing, ...items];
          } catch {
            /* job may be archived or deleted */
          }
        }

        setJobs(items);
        if (focusId !== "") setJobId(focusId);
        setSelectedTemplates(t.filter((x) => x.is_default).map((x) => x.id));
      })
      .catch((e) => setError(String(e.message || e)));
  }, [params]);

  useEffect(() => {
    if (typeof jobId === "number") {
      api
        .listDrafts(jobId)
        .then((d) => {
          setDrafts(d);
          setActiveDraft(d[0] || null);
        })
        .catch((e) => setError(String(e.message || e)));
    }
  }, [jobId]);

  useEffect(() => {
    if (activeDraft) {
      api.listRevisions(activeDraft.id).then(setRevisions).catch(() => setRevisions([]));
    } else {
      setRevisions([]);
    }
  }, [activeDraft?.id]);

  const selectedJob = useMemo(
    () => jobs.find((j) => j.id === jobId),
    [jobs, jobId]
  );

  const generate = async () => {
    const hasProtected = drafts.some((d) => PROTECTED.has(d.status));
    let overwrite = false;
    if (hasProtected) {
      const ok = confirm(
        "Some drafts are reviewed/approved/exported. Overwrite them with fresh template renders?"
      );
      if (!ok) return;
      overwrite = true;
    }

    setBusy(true);
    setError("");
    try {
      if (bulkIds.length > 1) {
        const res = await api.generateBulk(bulkIds, selectedTemplates, overwrite);
        setMessage(`Generated ${res.drafts.length} drafts across ${res.jobs_processed} jobs.`);
        if (typeof jobId === "number") {
          const d = await api.listDrafts(jobId);
          setDrafts(d);
          setActiveDraft(d[0] || null);
        }
      } else if (typeof jobId === "number" && selectedTemplates.length) {
        const result = await api.generateDrafts(jobId, selectedTemplates, overwrite);
        setDrafts(result);
        setActiveDraft(result[0] || null);
        setMessage(`Generated ${result.length} draft(s).`);
      }
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const copyPrompt = async (draft: Draft) => {
    try {
      const pack = await api.promptPack(draft.id, requirement);
      await navigator.clipboard.writeText(pack.prompt);
      setMessage("Prompt copied — paste into ChatGPT, Claude, or Gemini.");
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const importResult = async () => {
    if (!activeDraft || !importText.trim()) return;
    try {
      const updated = await api.importResult(activeDraft.id, importText, requirement);
      setActiveDraft(updated);
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setImportText("");
      setMessage("AI result imported.");
      setRevisions(await api.listRevisions(updated.id));
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const saveDraft = async () => {
    if (!activeDraft) return;
    try {
      const updated = await api.updateDraft(activeDraft.id, {
        content: activeDraft.content,
        status: activeDraft.status,
      });
      setActiveDraft(updated);
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setMessage("Draft saved.");
      setRevisions(await api.listRevisions(updated.id));
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const exportDraft = async (format: "text" | "markdown") => {
    if (!activeDraft) return;
    try {
      const data = await api.exportDraft(activeDraft.id, format);
      const body = format === "markdown" ? data.markdown || data.content : data.content;
      await navigator.clipboard.writeText(body || "");
      const blob = new Blob([body || ""], {
        type: format === "markdown" ? "text/markdown" : "text/plain",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${data.job_title}-${data.channel}.${format === "markdown" ? "md" : "txt"}`;
      a.click();
      URL.revokeObjectURL(url);
      const updated = await api.updateDraft(activeDraft.id, { status: "exported" });
      setActiveDraft(updated);
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setMessage(`Exported as ${format}.`);
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const restoreRevision = async (r: Revision) => {
    if (!activeDraft) return;
    try {
      const updated = await api.updateDraft(activeDraft.id, { content: r.after });
      setActiveDraft(updated);
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setRevisions(await api.listRevisions(updated.id));
      setMessage("Revision restored and saved.");
    } catch (e) {
      setError(String((e as Error).message || e));
    }
  };

  const toggleTemplate = (id: number) => {
    setSelectedTemplates((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Generate</h2>
          <p>
            Render local templates, polish with your AI subscriptions, import results, export.
          </p>
        </div>
        <button onClick={generate} disabled={busy || !selectedTemplates.length}>
          {bulkIds.length > 1 ? `Generate for ${bulkIds.length} jobs` : "Generate drafts"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      <div className="grid-2">
        <div className="card">
          <h3>Job & templates</h3>
          {bulkIds.length > 1 && (
            <p className="badge info">Bulk mode: {bulkIds.length} jobs selected</p>
          )}
          <div className="field">
            <label>Focus job</label>
            <select value={jobId} onChange={(e) => setJobId(Number(e.target.value))}>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} — {j.company}
                </option>
              ))}
            </select>
          </div>
          {selectedJob?.needs_manual_fill && (
            <p className="badge warn" style={{ marginTop: 8 }}>
              Needs manual fill — review fields before publishing copy.
            </p>
          )}
          {selectedJob?.content_changed && (
            <p className="badge info" style={{ marginTop: 8 }}>
              Job content changed since last scrape.
            </p>
          )}
          <div className="checkbox-list" style={{ marginTop: "1rem" }}>
            {templates.map((t) => (
              <label key={t.id}>
                <input
                  type="checkbox"
                  checked={selectedTemplates.includes(t.id)}
                  onChange={() => toggleTemplate(t.id)}
                />
                {t.name} <span className="muted">({t.channel})</span>
              </label>
            ))}
          </div>
        </div>

        <div className="card">
          <h3>Drafts</h3>
          {drafts.length === 0 ? (
            <p className="empty">No drafts for this job yet.</p>
          ) : (
            <div className="draft-list">
              {drafts.map((d) => (
                <button
                  key={d.id}
                  className={`draft-item ${activeDraft?.id === d.id ? "active" : ""}`}
                  onClick={() => setActiveDraft(d)}
                >
                  {d.channel} · <span className="badge">{d.status}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedJob && (
        <div className="card">
          <h3>Job context</h3>
          <p style={{ margin: "0 0 0.5rem" }}>
            <strong>{selectedJob.title}</strong> · {selectedJob.company} · {selectedJob.location}
          </p>
          <div className="row muted" style={{ marginBottom: "0.5rem" }}>
            {selectedJob.employment_type && <span>{selectedJob.employment_type}</span>}
            {selectedJob.salary_text && <span>{selectedJob.salary_text}</span>}
            {selectedJob.apply_url && (
              <a href={selectedJob.apply_url} target="_blank" rel="noreferrer">
                Open apply link
              </a>
            )}
            <Link to={`/jobs?q=${encodeURIComponent(selectedJob.title)}`}>Edit on Jobs</Link>
          </div>
          {selectedJob.skills?.length > 0 && (
            <p className="muted" style={{ margin: "0 0 0.5rem" }}>
              Skills: {selectedJob.skills.join(", ")}
            </p>
          )}
          <pre
            style={{
              whiteSpace: "pre-wrap",
              maxHeight: 160,
              overflow: "auto",
              background: "#f8faf9",
              padding: "0.75rem",
              borderRadius: 8,
              margin: 0,
              fontSize: "0.85rem",
            }}
          >
            {(selectedJob.description_text || "No description.").slice(0, 1200)}
            {(selectedJob.description_text || "").length > 1200 ? "…" : ""}
          </pre>
        </div>
      )}

      {activeDraft && (
        <div className="card">
          <div className="page-header" style={{ marginBottom: "0.75rem" }}>
            <h3 style={{ margin: 0 }}>Editor · {activeDraft.channel}</h3>
            <div className="row">
              <select
                style={{ width: "auto" }}
                value={activeDraft.status}
                onChange={(e) =>
                  setActiveDraft({ ...activeDraft, status: e.target.value })
                }
              >
                <option value="draft">draft</option>
                <option value="reviewed">reviewed</option>
                <option value="approved">approved</option>
                <option value="exported">exported</option>
              </select>
              <button className="secondary" onClick={saveDraft}>
                Save
              </button>
              <button className="secondary" onClick={() => copyPrompt(activeDraft)}>
                Copy AI prompt
              </button>
              <button className="secondary" onClick={() => exportDraft("text")}>
                Export .txt
              </button>
              <button className="secondary" onClick={() => exportDraft("markdown")}>
                Export .md
              </button>
            </div>
          </div>

          <textarea
            style={{ minHeight: 220 }}
            value={activeDraft.content}
            onChange={(e) => setActiveDraft({ ...activeDraft, content: e.target.value })}
          />

          <div className="field" style={{ marginTop: "1rem" }}>
            <label>Custom requirement (for AI polish)</label>
            <input
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              placeholder="e.g. More casual, under 100 words, Hindi + English"
            />
          </div>

          <div className="field" style={{ marginTop: "0.75rem" }}>
            <label>Import AI result</label>
            <textarea
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              placeholder="Paste polished copy from ChatGPT / Claude / Gemini"
            />
          </div>
          <button style={{ marginTop: "0.5rem" }} onClick={importResult}>
            Import result
          </button>

          {revisions.length > 0 && (
            <div style={{ marginTop: "1.25rem" }}>
              <h3>Revision history</h3>
              {revisions.map((r) => (
                <div key={r.id} className="revision">
                  <div className="muted">
                    {new Date(r.created_at).toLocaleString()} · {r.source} · {r.requirement}
                  </div>
                  <button
                    className="secondary"
                    style={{ marginTop: 6 }}
                    onClick={() => restoreRevision(r)}
                  >
                    Restore & save
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
