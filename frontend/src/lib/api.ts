const API_BASE = "http://localhost:8000/api";

export async function login(email: string, password: string): Promise<boolean> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.ok;
}

export async function getAuthStatus(): Promise<boolean> {
  const res = await fetch(`${API_BASE}/auth/status`);
  const data = await res.json();
  return data.logged_in;
}

export async function getSessions(limit = 10): Promise<{ sessions: unknown[] }> {
  const res = await fetch(`${API_BASE}/sessions?limit=${limit}`);
  return res.json();
}

export async function getPlayerSettings(): Promise<{ skill_level: string }> {
  const res = await fetch(`${API_BASE}/settings/player`);
  return res.json();
}

export async function updatePlayerSettings(skillLevel: string): Promise<void> {
  await fetch(`${API_BASE}/settings/player`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ skill_level: skillLevel }),
  });
}
