import { FormEvent, Fragment, useEffect, useState } from "react";
import { api, ScrapeRun, Source } from "../api";

const KINDS = ["greenhouse", "lever", "ashby", "workday", "custom"];

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [intervals, setIntervals] = useState<Record<number, number>>({});
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [historyId, setHistoryId] = useState<number | null>(null);
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [form, setForm] = useState({
    name: "",
    kind: "greenhouse",
    base_url: "",
    scrape_interval_minutes: 0,
  });

  const load = () =>
    api
      .listSources()
      .then((list) => {
        setSources(list);
        const map: Record<number, number> = {};
        list.forEach((s) => {
          map[s.id] = s.scrape_interval_minutes;
        });
        setIntervals(map);
      })
      .catch((e) => setError(String(e.message || e)));

  useEffect(() => {
    load();
  }, []);

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.createSource({ ...form, enabled: true });
      setForm({ name: "", kind: "greenhouse", base_url: "", scrape_interval_minutes: 0 });
      setMessage("Source added.");
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const scrape = async (id: number) => {
    setBusy(true);
    setError("");
    try {
      const r = await api.scrapeSource(id);
      setMessage(
        `Scrape ok: ${r.jobs_found} found, ${r.jobs_created} new, ${r.jobs_updated} updated, ${r.jobs_archived} archived.`
      );
      load();
      if (historyId === id) {
        setRuns(await api.listSourceRuns(id));
      }
    } catch (err) {
      setError(String((err as Error).message || err));
      load();
    } finally {
      setBusy(false);
    }
  };

  const scrapeAll = async () => {
    setBusy(true);
    setError("");
    try {
      const r = await api.scrapeAll();
      const ok = r.results.filter((x) => x.status === "success").length;
      setMessage(`Scraped ${r.sources_scraped} sources (${ok} succeeded).`);
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    } finally {
      setBusy(false);
    }
  };

  const toggle = async (s: Source) => {
    try {
      await api.updateSource(s.id, { enabled: !s.enabled });
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const saveInterval = async (s: Source) => {
    const minutes = intervals[s.id] ?? s.scrape_interval_minutes;
    if (minutes === s.scrape_interval_minutes) return;
    try {
      await api.updateSource(s.id, { scrape_interval_minutes: minutes });
      setMessage(`Updated interval for ${s.name}.`);
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const showHistory = async (id: number) => {
    if (historyId === id) {
      setHistoryId(null);
      setRuns([]);
      return;
    }
    try {
      setRuns(await api.listSourceRuns(id));
      setHistoryId(id);
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const remove = async (id: number) => {
    if (!confirm("Delete this source and its jobs?")) return;
    try {
      await api.deleteSource(id);
      load();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Sources</h2>
          <p>ATS boards and custom career URLs. Set an interval for automatic scrapes.</p>
        </div>
        <button onClick={scrapeAll} disabled={busy || !sources.length}>
          Scrape all enabled
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      <form className="card" onSubmit={onCreate}>
        <h3>Add source</h3>
        <div className="row">
          <div className="field">
            <label>Name</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Acme Careers"
            />
          </div>
          <div className="field">
            <label>Kind</label>
            <select
              value={form.kind}
              onChange={(e) => setForm({ ...form, kind: e.target.value })}
            >
              {KINDS.map((k) => (
                <option key={k} value={k}>
                  {k}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ flex: 2 }}>
            <label>Board / career URL</label>
            <input
              required
              value={form.base_url}
              onChange={(e) => setForm({ ...form, base_url: e.target.value })}
              placeholder="https://boards.greenhouse.io/acme"
            />
          </div>
          <div className="field">
            <label>Auto-scrape (min)</label>
            <input
              type="number"
              min={0}
              value={form.scrape_interval_minutes}
              onChange={(e) =>
                setForm({ ...form, scrape_interval_minutes: Number(e.target.value) })
              }
            />
          </div>
        </div>
        <div className="row" style={{ marginTop: "0.75rem" }}>
          <button type="submit">Add source</button>
          <span className="muted">0 minutes = manual only</span>
        </div>
      </form>

      <div className="card">
        <h3>Configured sources</h3>
        {sources.length === 0 ? (
          <p className="empty">No sources yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Kind</th>
                  <th>Status</th>
                  <th>Interval</th>
                  <th>Last run</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <Fragment key={s.id}>
                    <tr>
                      <td>
                        <strong>{s.name}</strong>
                        <div className="muted" style={{ fontSize: "0.8rem", wordBreak: "break-all" }}>
                          {s.base_url}
                        </div>
                        {s.last_error && (
                          <div className="badge danger" style={{ marginTop: 4 }} title={s.last_error}>
                            {s.last_error.slice(0, 120)}
                            {s.last_error.length > 120 ? "…" : ""}
                          </div>
                        )}
                      </td>
                      <td>
                        <span className="badge info">{s.kind}</span>
                      </td>
                      <td>
                        <span className={`badge ${s.enabled ? "" : "warn"}`}>
                          {s.enabled ? "enabled" : "disabled"}
                        </span>{" "}
                        <span className={`badge ${s.last_run_status === "failed" ? "danger" : ""}`}>
                          {s.last_run_status}
                        </span>
                      </td>
                      <td>
                        <input
                          type="number"
                          min={0}
                          style={{ width: 90 }}
                          value={intervals[s.id] ?? s.scrape_interval_minutes}
                          onChange={(e) =>
                            setIntervals((prev) => ({
                              ...prev,
                              [s.id]: Number(e.target.value),
                            }))
                          }
                          onBlur={() => saveInterval(s)}
                        />
                      </td>
                      <td className="muted">
                        {s.last_scraped_at
                          ? new Date(s.last_scraped_at).toLocaleString()
                          : "—"}
                      </td>
                      <td>
                        <div className="row">
                          <button
                            className="secondary"
                            disabled={busy || !s.enabled}
                            onClick={() => scrape(s.id)}
                          >
                            Scrape
                          </button>
                          <button className="secondary" onClick={() => showHistory(s.id)}>
                            {historyId === s.id ? "Hide runs" : "History"}
                          </button>
                          <button className="secondary" onClick={() => toggle(s)}>
                            {s.enabled ? "Disable" : "Enable"}
                          </button>
                          <button className="danger" onClick={() => remove(s.id)}>
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                    {historyId === s.id && (
                      <tr>
                        <td colSpan={6}>
                          {runs.length === 0 ? (
                            <p className="muted">No runs recorded yet.</p>
                          ) : (
                            <table>
                              <thead>
                                <tr>
                                  <th>When</th>
                                  <th>Status</th>
                                  <th>Found</th>
                                  <th>Created</th>
                                  <th>Updated</th>
                                  <th>Archived</th>
                                  <th>ms</th>
                                  <th>Error</th>
                                </tr>
                              </thead>
                              <tbody>
                                {runs.map((r) => (
                                  <tr key={r.id}>
                                    <td>{new Date(r.started_at).toLocaleString()}</td>
                                    <td>
                                      <span
                                        className={`badge ${r.status === "failed" ? "danger" : ""}`}
                                      >
                                        {r.status}
                                      </span>
                                    </td>
                                    <td>{r.jobs_found}</td>
                                    <td>{r.jobs_created}</td>
                                    <td>{r.jobs_updated}</td>
                                    <td>{r.jobs_archived}</td>
                                    <td>{Math.round(r.duration_ms)}</td>
                                    <td className="muted">{r.error_message || "—"}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
