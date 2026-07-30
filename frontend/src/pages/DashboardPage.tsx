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
          <p>Pipeline health, scrape activity, and drafts waiting for polish.</p>
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
        <Link className="stat" to="/jobs?status=active" style={{ color: "inherit" }}>
          <div className="label">Active jobs</div>
          <div className="value">{stats.jobs_active}</div>
        </Link>
        <Link className="stat" to="/sources" style={{ color: "inherit" }}>
          <div className="label">Sources on</div>
          <div className="value">
            {stats.sources_enabled}/{stats.sources_total}
          </div>
        </Link>
        <div className="stat">
          <div className="label">Drafts pending</div>
          <div className="value">{stats.drafts_pending ?? 0}</div>
        </div>
        <div className="stat">
          <div className="label">Reviewed</div>
          <div className="value">{stats.drafts_reviewed}</div>
        </div>
        <Link
          className="stat"
          to="/jobs?needs_manual_fill=true&status=active"
          style={{ color: "inherit" }}
        >
          <div className="label">Needs fill</div>
          <div className="value">{stats.jobs_needs_manual_fill}</div>
        </Link>
        <Link
          className="stat"
          to="/jobs?content_changed=true&status=active"
          style={{ color: "inherit" }}
        >
          <div className="label">Changed</div>
          <div className="value">{stats.jobs_changed}</div>
        </Link>
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
          <h3>Drafts queue</h3>
          {!stats.pending_drafts?.length ? (
            <p className="empty">No pending drafts. Generate content for a job to start.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Role</th>
                    <th>Channel</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {stats.pending_drafts.map((d) => (
                    <tr key={d.id}>
                      <td>
                        {d.job_title || `Job #${d.job_id}`}
                        <div className="muted">{d.company}</div>
                      </td>
                      <td>
                        <span className="badge">{d.channel}</span>
                      </td>
                      <td>
                        <Link to={`/generate?job=${d.job_id}`}>Open</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

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
                        {j.content_changed && (
                          <span className="badge info" style={{ marginLeft: 6 }}>
                            changed
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
                  <th>New / Updated / Archived</th>
                  <th>ms</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_runs.map((r) => (
                  <tr key={r.id}>
                    <td>{r.source_name || `#${r.source_id}`}</td>
                    <td>
                      <span className={`badge ${r.status === "failed" ? "danger" : ""}`}>
                        {r.status}
                      </span>
                      {r.error_message && (
                        <div className="muted" style={{ fontSize: "0.8rem", marginTop: 4 }}>
                          {r.error_message.slice(0, 120)}
                        </div>
                      )}
                    </td>
                    <td>{r.jobs_found}</td>
                    <td className="muted">
                      {r.jobs_created} / {r.jobs_updated} / {r.jobs_archived}
                    </td>
                    <td>{Math.round(r.duration_ms)}</td>
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
