const TOKEN_KEY = "admin_jwt";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function api(path, { method="GET", body, token=true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }

  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined
  });

  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }

  if (!res.ok) {
    const msg = data?.detail || data?.message || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}
