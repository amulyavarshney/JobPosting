import { FormEvent, useEffect, useState } from "react";
import { api, BrandProfile, Settings, setApiKey } from "../api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [brand, setBrand] = useState<BrandProfile | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState(localStorage.getItem("jobposting_api_key") || "");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    Promise.all([api.getSettings(), api.getBrand()])
      .then(([s, b]) => {
        setSettings(s);
        setBrand(b);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  const saveBrand = async (e: FormEvent) => {
    e.preventDefault();
    if (!brand) return;
    try {
      const updated = await api.updateBrand(brand);
      setBrand(updated);
      setMessage("Brand voice saved. It is injected into AI prompt packs.");
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const saveApiKey = () => {
    setApiKey(apiKeyInput.trim() || null);
    setMessage(apiKeyInput.trim() ? "API key stored in this browser." : "API key cleared.");
  };

  if (!settings || !brand) {
    return error ? <div className="error">{error}</div> : <p className="muted">Loading…</p>;
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Settings</h2>
          <p>Brand voice, environment status, and optional production API key.</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      <div className="stats">
        <div className="stat">
          <div className="label">Environment</div>
          <div className="value" style={{ fontSize: "1.1rem" }}>
            {settings.environment}
          </div>
        </div>
        <div className="stat">
          <div className="label">Scheduler</div>
          <div className="value" style={{ fontSize: "1.1rem" }}>
            {settings.scheduler_enabled ? "On" : "Off"}
          </div>
        </div>
        <div className="stat">
          <div className="label">API key required</div>
          <div className="value" style={{ fontSize: "1.1rem" }}>
            {settings.api_key_required ? "Yes" : "No"}
          </div>
        </div>
        <div className="stat">
          <div className="label">Archive missing</div>
          <div className="value" style={{ fontSize: "1.1rem" }}>
            {settings.archive_missing_jobs ? "Yes" : "No"}
          </div>
        </div>
      </div>

      <form className="card" onSubmit={saveBrand}>
        <h3>Brand voice</h3>
        <p className="muted">
          Applied to every AI prompt pack so ChatGPT / Claude / Gemini stay on-brand.
        </p>
        <div className="grid-2">
          <div className="field">
            <label>Organization</label>
            <input
              value={brand.organization_name}
              onChange={(e) => setBrand({ ...brand, organization_name: e.target.value })}
            />
          </div>
          <div className="field">
            <label>Tone</label>
            <input
              value={brand.tone}
              onChange={(e) => setBrand({ ...brand, tone: e.target.value })}
            />
          </div>
        </div>
        <div className="field" style={{ marginTop: "0.75rem" }}>
          <label>Voice notes</label>
          <textarea
            value={brand.voice_notes}
            onChange={(e) => setBrand({ ...brand, voice_notes: e.target.value })}
          />
        </div>
        <div className="field" style={{ marginTop: "0.75rem" }}>
          <label>Banned words</label>
          <input
            value={brand.banned_words}
            onChange={(e) => setBrand({ ...brand, banned_words: e.target.value })}
          />
        </div>
        <div className="field" style={{ marginTop: "0.75rem" }}>
          <label>Hashtag policy</label>
          <input
            value={brand.hashtag_policy}
            onChange={(e) => setBrand({ ...brand, hashtag_policy: e.target.value })}
          />
        </div>
        <div className="field" style={{ marginTop: "0.75rem" }}>
          <label>CTA preference</label>
          <input
            value={brand.cta_preference}
            onChange={(e) => setBrand({ ...brand, cta_preference: e.target.value })}
          />
        </div>
        <button style={{ marginTop: "0.75rem" }} type="submit">
          Save brand voice
        </button>
      </form>

      <div className="card">
        <h3>Production API key (browser)</h3>
        <p className="muted">
          When the server has <code>API_KEY</code> / production auth enabled, store the key here for
          write requests. Prefer setting <code>API_KEY</code> in server <code>.env</code>.
        </p>
        <div className="row">
          <div className="field">
            <label>X-API-Key</label>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder="Optional"
            />
          </div>
          <button type="button" onClick={saveApiKey}>
            Save in browser
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Optional LLM providers</h3>
        <p className="muted">
          Not required. v1 polishes via subscriptions (Claude / ChatGPT / Gemini). Cloud
          API keys remain optional for a future in-app revise path.
        </p>
        <ul className="muted">
          <li>OpenAI configured: {settings.openai_api_key_configured ? "yes" : "no"}</li>
          <li>Anthropic configured: {settings.anthropic_api_key_configured ? "yes" : "no"}</li>
          <li>Gemini configured: {settings.gemini_api_key_configured ? "yes" : "no"}</li>
          <li>Ollama: {settings.ollama_base_url || "not set"}</li>
        </ul>
      </div>
    </>
  );
}
