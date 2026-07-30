import { useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { api, isDemoMode } from "./api";
import DashboardPage from "./pages/DashboardPage";
import SourcesPage from "./pages/SourcesPage";
import JobsPage from "./pages/JobsPage";
import TemplatesPage from "./pages/TemplatesPage";
import GeneratePage from "./pages/GeneratePage";
import SettingsPage from "./pages/SettingsPage";

function Banners() {
  const [needKey, setNeedKey] = useState(false);
  const demo = isDemoMode();

  useEffect(() => {
    if (demo) return;
    api
      .getSettings()
      .then((s) => {
        const hasKey = Boolean(localStorage.getItem("jobposting_api_key"));
        setNeedKey(Boolean(s.api_key_required && !hasKey));
      })
      .catch(() => undefined);
  }, [demo]);

  return (
    <>
      {demo && (
        <div className="success" style={{ margin: "0 0 1rem" }}>
          Browser demo mode — data stays in this browser (localStorage). Run the API locally for
          live scraping.
        </div>
      )}
      {needKey && (
        <div className="error" style={{ margin: "0 0 1rem" }}>
          API key required for write operations.{" "}
          <Link to="/settings">Add it in Settings</Link> to scrape, generate, and save.
        </div>
      )}
    </>
  );
}

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <p className="brand">JobPosting</p>
        <p className="brand-sub">Scrape → Draft → Polish → Export</p>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/sources">Sources</NavLink>
          <NavLink to="/jobs">Jobs</NavLink>
          <NavLink to="/templates">Templates</NavLink>
          <NavLink to="/generate">Generate</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
      </aside>
      <main className="content">
        <Banners />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/sources" element={<SourcesPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/generate" element={<GeneratePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
