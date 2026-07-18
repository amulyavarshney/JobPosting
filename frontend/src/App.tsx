import { NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import SourcesPage from "./pages/SourcesPage";
import JobsPage from "./pages/JobsPage";
import TemplatesPage from "./pages/TemplatesPage";
import GeneratePage from "./pages/GeneratePage";
import SettingsPage from "./pages/SettingsPage";

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
