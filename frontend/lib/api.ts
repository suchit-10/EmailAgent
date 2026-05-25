const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AgentResult = {
  response: string;
  draft?: { id: string; subject: string; body: string; status: string };
  events?: unknown[];
};

export type DashboardOverview = {
  unread: number;
  urgent: number;
  recruiters: number;
  leads: { company: string; role: string; status: string; interview_at?: string | null }[];
};

export type EmailSearchItem = {
  id: string;
  from: string;
  subject: string;
  snippet: string;
  classification: string;
  urgency: number;
  received_at?: string | null;
};

export type AuthStatus = {
  authenticated: boolean;
  email?: string | null;
  google_connected: boolean;
  synced_emails: number;
  scopes: string[];
};

export async function invokeAgent(message: string): Promise<AgentResult> {
  const response = await fetch(`${API_URL}/api/agent/invoke`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message })
  });
  if (!response.ok) {
    throw new Error("Agent request failed");
  }
  return response.json();
}

export async function getDashboard(): Promise<DashboardOverview> {
  const response = await fetch(`${API_URL}/api/dashboard/overview`, {
    credentials: "include",
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error("Dashboard request failed");
  }
  return response.json();
}

export async function searchEmails(query: string, limit = 12): Promise<EmailSearchItem[]> {
  const response = await fetch(`${API_URL}/api/emails/search`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit })
  });
  if (!response.ok) {
    throw new Error("Email search failed");
  }
  const data = await response.json();
  return data.items ?? [];
}

export async function syncEmails(): Promise<number> {
  const response = await fetch(`${API_URL}/api/emails/sync`, {
    method: "POST",
    credentials: "include"
  });
  if (!response.ok) {
    throw new Error("Email sync failed");
  }
  const data = await response.json();
  window.dispatchEvent(new CustomEvent("email-sync-complete", { detail: data }));
  return data.synced ?? 0;
}

export async function approveDraft(draft: { to: string[]; subject: string; body: string; send_now?: boolean }) {
  const response = await fetch(`${API_URL}/api/emails/drafts/approve`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...draft, send_now: draft.send_now ?? false })
  });
  if (!response.ok) {
    throw new Error("Draft approval failed");
  }
  return response.json();
}

export async function getAuthStatus(): Promise<AuthStatus> {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    credentials: "include",
    cache: "no-store"
  });
  if (!response.ok) {
    return { authenticated: false, email: null, google_connected: false, synced_emails: 0, scopes: [] };
  }
  return response.json();
}

export const googleLoginUrl = `${API_URL}/api/auth/google/login`;
