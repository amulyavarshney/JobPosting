import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, Job, Source } from "../api";

export default function JobsPage() {
  const [params, setParams] = useSearchParams();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [editing, setEditing] = useState<Job | null>(null);

  const page = Number(params.get("page") || 1);
  const q = params.get("q") || "";
  const status = params.get("status") || "active";
  const sourceId = params.get("source_id") || "";
  const needsFill = params.get("needs_manual_fill") || "";

  const load = () => {
    api
      .listJobs({
        page,
        page_size: 50,
        q: q || undefined,
        status,
        source_id: sourceId ? Number(sourceId) : undefined,
        needs_manual_fill: needsFill === "" ? undefined : needsFill === "true",
      })
      .then((res) => {
        setJobs(res.items);
        setTotal(res.total);
        setPages(res.pages);
      })
      .catch((e) => setError(String(e.message || e)));
  };

  useEffect(() => {
    api.listSources().then(setSources).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
  }, [page, q, status, sourceId, needsFill]);

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (!value) next.delete(key);
    else next.set(key, value);
    if (key !== "page") next.set("page", "1");
    setParams(next);
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const archive = async (job: Job) => {
    await api.updateJob(job.id, { status: "archived" });
    load();
  };

  const saveEdit = async () => {
    if (!editing) return;
    await api.updateJob(editing.id, {
      title: editing.title,
      company: editing.company,
      location: editing.location,
      description_text: editing.description_text,
      apply_url: editing.apply_url,
      needs_manual_fill: editing.needs_manual_fill,
      skills: editing.skills,
    });
    setEditing(null);
    load();
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Jobs</h2>
          <p>
            {total} matching · search, filter, archive stale roles, jump to generate.
          </p>
        </div>
        {selected.length > 0 && (
          <Link className="btn" to={`/generate?jobs=${selected.join(",")}`}>
            Generate for {selected.length} selected
          </Link>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="filters card" style={{ marginBottom: "1rem" }}>
        <div className="field">
          <label>Search</label>
          <input
            value={q}
            placeholder="Title, company, location"
            onChange={(e) => setFilter("q", e.target.value)}
          />
        </div>
        <div className="field">
          <label>Status</label>
          <select value={status} onChange={(e) => setFilter("status", e.target.value)}>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
            <option value="closed">Closed</option>
            <option value="all">All</option>
          </select>
        </div>
        <div className="field">
          <label>Source</label>
          <select value={sourceId} onChange={(e) => setFilter("source_id", e.target.value)}>
            <option value="">All sources</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Manual fill</label>
          <select value={needsFill} onChange={(e) => setFilter("needs_manual_fill", e.target.value)}>
            <option value="">Any</option>
            <option value="true">Needs fill</option>
            <option value="false">Complete</option>
          </select>
        </div>
      </div>

      <div className="card">
        {jobs.length === 0 ? (
          <p className="empty">No jobs match these filters.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th></th>
                  <th>Role</th>
                  <th>Company</th>
                  <th>Location</th>
                  <th>Flags</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.includes(j.id)}
                        onChange={() => toggleSelect(j.id)}
                      />
                    </td>
                    <td>
                      <strong>{j.title || "Untitled"}</strong>
                    </td>
                    <td>{j.company}</td>
                    <td>{j.location}</td>
                    <td>
                      {j.needs_manual_fill && <span className="badge warn">fill</span>}{" "}
                      {j.content_changed && <span className="badge info">changed</span>}
                    </td>
                    <td>
                      <div className="row">
                        <Link to={`/generate?job=${j.id}`}>Generate</Link>
                        <button className="secondary" onClick={() => setEditing(j)}>
                          Edit
                        </button>
                        {j.status === "active" && (
                          <button className="secondary" onClick={() => archive(j)}>
                            Archive
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="row" style={{ marginTop: "1rem" }}>
          <button
            className="secondary"
            disabled={page <= 1}
            onClick={() => setFilter("page", String(page - 1))}
          >
            Previous
          </button>
          <span className="muted">
            Page {page} / {pages}
          </span>
          <button
            className="secondary"
            disabled={page >= pages}
            onClick={() => setFilter("page", String(page + 1))}
          >
            Next
          </button>
        </div>
      </div>

      {editing && (
        <div className="card">
          <h3>Edit job #{editing.id}</h3>
          <div className="grid-2">
            <div className="field">
              <label>Title</label>
              <input
                value={editing.title}
                onChange={(e) => setEditing({ ...editing, title: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Company</label>
              <input
                value={editing.company}
                onChange={(e) => setEditing({ ...editing, company: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Location</label>
              <input
                value={editing.location}
                onChange={(e) => setEditing({ ...editing, location: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Apply URL</label>
              <input
                value={editing.apply_url}
                onChange={(e) => setEditing({ ...editing, apply_url: e.target.value })}
              />
            </div>
          </div>
          <div className="field" style={{ marginTop: "0.75rem" }}>
            <label>Description</label>
            <textarea
              value={editing.description_text}
              onChange={(e) => setEditing({ ...editing, description_text: e.target.value })}
            />
          </div>
          <div className="row" style={{ marginTop: "0.75rem" }}>
            <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={editing.needs_manual_fill}
                onChange={(e) =>
                  setEditing({ ...editing, needs_manual_fill: e.target.checked })
                }
              />
              Needs manual fill
            </label>
            <button onClick={saveEdit}>Save</button>
            <button className="secondary" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </>
  );
}
