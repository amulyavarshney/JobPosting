import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DashboardStats } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .dashboard()
      .then(setStats)
      .catch((e) => setError(String(e.message || e)));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!stats) return <p className="muted">Loading dashboard…</p>;

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Pipeline health, scrape activity, and recent jobs ready for content.</p>
        </div>
        <div className="row">
          <Link className="btn secondary" to="/sources">
            Manage sources
          </Link>
          <Link className="btn" to="/generate">
            Generate content
          </Link>
        </div>
      </div>

      <div className="stats">
        <div className="stat">
          <div className="label">Active jobs</div>
          <div className="value">{stats.jobs_active}</div>
        </div>
        <div className="stat">
          <div className="label">Sources on</div>
          <div className="value">
            {stats.sources_enabled}/{stats.sources_total}
          </div>
        </div>
        <div className="stat">
          <div className="label">Drafts</div>
          <div className="value">{stats.drafts_total}</div>
        </div>
        <div className="stat">
          <div className="label">Reviewed</div>
          <div className="value">{stats.drafts_reviewed}</div>
        </div>
        <div className="stat">
          <div className="label">Needs fill</div>
          <div className="value">{stats.jobs_needs_manual_fill}</div>
        </div>
        <div className="stat">
          <div className="label">Changed</div>
          <div className="value">{stats.jobs_changed}</div>
        </div>
        <div className="stat">
          <div className="label">Scrapes 24h</div>
          <div className="value">{stats.scrape_runs_24h}</div>
        </div>
        <div className="stat">
          <div className="label">Failures 24h</div>
          <div className="value">{stats.scrape_failures_24h}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Recent jobs</h3>
          {stats.recent_jobs.length === 0 ? (
            <p className="empty">No jobs yet. Add a source and scrape.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Company</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_jobs.map((j) => (
                    <tr key={j.id}>
                      <td>
                        {j.title || "Untitled"}
                        {j.needs_manual_fill && (
                          <span className="badge warn" style={{ marginLeft: 6 }}>
                            fill
                          </span>
                        )}
                      </td>
                      <td>{j.company}</td>
                      <td>
                        <Link to={`/generate?job=${j.id}`}>Generate</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Recent scrape runs</h3>
          {stats.recent_runs.length === 0 ? (
            <p className="empty">No scrape history yet.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Found</th>
                    <th>ms</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_runs.map((r) => (
                    <tr key={r.id}>
                      <td>#{r.source_id}</td>
                      <td>
                        <span className={`badge ${r.status === "failed" ? "danger" : ""}`}>
                          {r.status}
                        </span>
                      </td>
                      <td>{r.jobs_found}</td>
                      <td>{Math.round(r.duration_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
