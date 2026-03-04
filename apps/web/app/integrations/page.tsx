import { revalidatePath } from "next/cache";

const PROVIDERS = ["chatgpt", "codex", "claude", "claude_code"] as const;

type Provider = (typeof PROVIDERS)[number];

const DISPLAY_NAME: Record<Provider, string> = {
  chatgpt: "ChatGPT",
  codex: "Codex",
  claude: "Claude",
  claude_code: "Claude Code",
};

async function fetchDevToken() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const res = await fetch(`${base}/auth/dev-token`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sub: "dev-user",
      role: "admin",
      ttl_seconds: 3600,
    }),
  });
  if (!res.ok) {
    return "";
  }
  const data = await res.json().catch(() => ({}));
  return data?.access_token || "";
}

async function fetchStatus() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const token = await fetchDevToken();
  if (!token) {
    return [];
  }

  const res = await fetch(`${base}/integrations`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    return [];
  }
  return res.json().catch(() => []);
}

async function fetchOauthStart(provider: Provider) {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const token = await fetchDevToken();
  if (!token) {
    return "";
  }
  const res = await fetch(`${base}/integrations/${provider}/oauth/start`, {
    cache: "no-store",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    return "";
  }
  const payload = await res.json().catch(() => ({}));
  return payload?.auth_url || "";
}

export default async function IntegrationsPage() {
  async function saveApiKey(formData: FormData) {
    "use server";
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const token = await fetchDevToken();
    if (!token) {
      return;
    }
    const provider = String(formData.get("provider") || "") as Provider;
    const apiKey = String(formData.get("api_key") || "").trim();
    if (!provider || !apiKey) {
      return;
    }

    await fetch(`${base}/integrations/${provider}/api-key`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ api_key: apiKey }),
    });
    revalidatePath("/integrations");
  }

  async function testConnection(formData: FormData) {
    "use server";
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const token = await fetchDevToken();
    if (!token) {
      return;
    }
    const provider = String(formData.get("provider") || "") as Provider;
    if (!provider) {
      return;
    }
    await fetch(`${base}/integrations/${provider}/test`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    revalidatePath("/integrations");
  }

  const [statuses, oauthStarts] = await Promise.all([
    fetchStatus(),
    Promise.all(PROVIDERS.map((provider) => fetchOauthStart(provider))),
  ]);

  const statusByProvider = new Map<string, any>(statuses.map((s: any) => [s.provider, s]));
  const oauthByProvider = new Map<string, string>(
    PROVIDERS.map((provider, index) => [provider, oauthStarts[index] || ""]),
  );

  return (
    <div>
      <h1>AI Integrations</h1>
      <p className="muted">
        Configure OpenAI (ChatGPT/Codex) and Anthropic (Claude/Claude Code) connections using API keys or OAuth.
      </p>
      <div className="grid">
        {PROVIDERS.map((provider) => {
          const status = statusByProvider.get(provider);
          const oauthUrl = oauthByProvider.get(provider) || "";
          return (
            <div className="card" key={provider}>
              <h2 style={{ marginTop: 0 }}>{DISPLAY_NAME[provider]}</h2>
              <div className="muted">
                Status: {status?.connected ? "Connected" : "Not connected"}
              </div>
              <div className="muted">
                Method: {status?.auth_method || "n/a"}
              </div>
              <form action={saveApiKey} style={{ marginTop: "10px" }}>
                <input type="hidden" name="provider" value={provider} />
                <div className="muted">API Key</div>
                <input type="password" name="api_key" placeholder="sk-..." required />
                <button type="submit" style={{ marginTop: "10px" }}>
                  Save API Key
                </button>
              </form>
              <div style={{ marginTop: "10px", display: "flex", gap: "8px" }}>
                <form action={testConnection}>
                  <input type="hidden" name="provider" value={provider} />
                  <button type="submit">Test</button>
                </form>
                {oauthUrl ? (
                  <a href={oauthUrl} className="button-link">Connect OAuth</a>
                ) : (
                  <button type="button" disabled>
                    OAuth not configured
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
