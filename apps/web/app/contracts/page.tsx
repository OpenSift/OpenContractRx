import { revalidatePath } from "next/cache";

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

async function fetchContracts() {
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const token = await fetchDevToken();

  const res = await fetch(`${base}/contracts`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

export default async function ContractsPage() {
  async function createContract(formData: FormData) {
    "use server";

    const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const token = await fetchDevToken();
    if (!token) {
      return;
    }

    const title = String(formData.get("title") || "").trim();
    const vendor = String(formData.get("vendor") || "").trim();

    if (!title || !vendor) {
      return;
    }

    await fetch(`${base}/contracts/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, vendor }),
    });

    revalidatePath("/contracts");
  }

  const result = await fetchContracts();

  return (
    <div>
      <h1>Contracts</h1>
      <form action={createContract} className="card" style={{ marginBottom: "14px" }}>
        <h2 style={{ marginTop: 0 }}>Add Contract</h2>
        <div className="grid">
          <label>
            <div className="muted">Title</div>
            <input name="title" required />
          </label>
          <label>
            <div className="muted">Vendor</div>
            <input name="vendor" required />
          </label>
        </div>
        <button type="submit" style={{ marginTop: "12px" }}>Create</button>
      </form>
      {!result.ok ? (
        <div className="card">
          <p><strong>API request failed.</strong></p>
          <p>Status: {result.status}</p>
          <pre className="code">{JSON.stringify(result.data, null, 2)}</pre>
        </div>
      ) : (
        <div className="grid">
          {(result.data || []).map((c: any) => (
            <div className="card" key={c.id}>
              <div className="muted">{c.vendor}</div>
              <div className="title">{c.title}</div>
              <div className="badge">{c.status}</div>
              <div className="muted" style={{ marginTop: "8px" }}>
                {c.created_at ? new Date(c.created_at).toLocaleString() : ""}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
