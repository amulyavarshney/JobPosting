import { FormEvent, useEffect, useState } from "react";
import { api, Source } from "../api";

const KINDS = ["greenhouse", "lever", "ashby", "workday", "custom"];

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    name: "",
    kind: "greenhouse",
    base_url: "",
    scrape_interval_minutes: 0,
  });

  const load = () =>
    api
      .listSources()
      .then(setSources)
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
    await api.updateSource(s.id, { enabled: !s.enabled });
    load();
  };

  const updateInterval = async (s: Source, minutes: number) => {
    await api.updateSource(s.id, { scrape_interval_minutes: minutes });
    load();
  };

  const remove = async (id: number) => {
    if (!confirm("Delete this source and its jobs?")) return;
    await api.deleteSource(id);
    load();
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
                  <tr key={s.id}>
                    <td>
                      <strong>{s.name}</strong>
                      <div className="muted" style={{ fontSize: "0.8rem", wordBreak: "break-all" }}>
                        {s.base_url}
                      </div>
                      {s.last_error && (
                        <div className="badge danger" style={{ marginTop: 4 }}>
                          {s.last_error.slice(0, 80)}
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
                        value={s.scrape_interval_minutes}
                        onChange={(e) => updateInterval(s, Number(e.target.value))}
                      />
                    </td>
                    <td className="muted">
                      {s.last_scraped_at
                        ? new Date(s.last_scraped_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      <div className="row">
                        <button className="secondary" disabled={busy || !s.enabled} onClick={() => scrape(s.id)}>
                          Scrape
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
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
