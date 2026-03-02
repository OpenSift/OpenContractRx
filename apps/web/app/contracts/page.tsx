async function fetchContracts() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  // Dev token for local use (role=admin)
  // This matches the API's dev auth scheme.
  // In production we'll use OIDC/JWT verification.
  const token = await (async () => {
    // In real UI we will log in. For now, keep it simple.
    // We hardcode a dev token minted server-side later; for now use an empty token to show the auth error clearly.
    return "";
  })();

  const res = await fetch(`${base}/contracts`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

export default async function ContractsPage() {
  const result = await fetchContracts();

  return (
    <div>
      <h1>Contracts</h1>
      {!result.ok ? (
        <div className="card">
          <p><strong>API request failed.</strong></p>
          <p>Status: {result.status}</p>
          <p>
            This is expected right now because auth is scaffolded. Next step: add a dev "Login" that mints a token.
          </p>
          <pre className="code">{JSON.stringify(result.data, null, 2)}</pre>
        </div>
      ) : (
        <div className="grid">
          {(result.data || []).map((c: any) => (
            <div className="card" key={c.id}>
              <div className="muted">{c.vendor}</div>
              <div className="title">{c.title}</div>
              <div className="badge">{c.status}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}