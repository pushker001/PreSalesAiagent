const API_BASE_URL = "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

function authHeaders(extra = {}) {
  const token = getToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function parseJson(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}): ${text}`);
  }
  return response.json();
}

export async function signup(email, password, orgName) {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, org_name: orgName }),
  });
  return parseJson(response);
}

export async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseJson(response);
}

export async function fetchLeads() {
  const response = await fetch(`${API_BASE_URL}/leads`, { headers: authHeaders() });
  return parseJson(response);
}

export async function fetchLead(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}`, { headers: authHeaders() });
  return parseJson(response);
}

export async function fetchLeadReports(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/reports`, { headers: authHeaders() });
  return parseJson(response);
}

export async function fetchLeadQualification(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/qualification`, { headers: authHeaders() });
  if (response.status === 404) return null;
  return parseJson(response);
}

export async function updateLead(leadId, payload) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function fetchLeadActivities(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/activities`, { headers: authHeaders() });
  return parseJson(response);
}

export async function createLeadActivity(leadId, payload) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/activities`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function generateFollowUp(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/follow-up/generate`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseJson(response);
}

export async function fetchDashboardMetrics() {
  const response = await fetch(`${API_BASE_URL}/dashboard/metrics`, { headers: authHeaders() });
  return parseJson(response);
}

export async function generateBookingSuggestion(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/booking/generate`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseJson(response);
}

export async function generateConversationSuggestion(leadId, currentMessage) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/conversation/generate`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ current_message: currentMessage }),
  });
  return parseJson(response);
}

export async function markBookingLinkSent(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/booking/mark-link-sent`, {
    method: "POST",
    headers: authHeaders(),
  });
  return parseJson(response);
}

export async function analyzeLead(formData, handlers = {}) {
  const { onProgress, onDone } = handlers;
  const response = await fetch(`${API_BASE_URL}/analyze-closure`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(formData),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Server error ${response.status}: ${text}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Streaming is not supported in this browser.");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      let event;
      try {
        event = JSON.parse(trimmed);
      } catch {
        continue;
      }

      if (event.event === "progress" && onProgress) {
        onProgress({ message: event.message, step: event.step, total: event.total });
      }

      if (event.event === "error") {
        throw new Error(event.message || "Streaming error");
      }

      if (event.event === "done") {
        const payload = event.data || {};
        if (onDone) onDone(payload);
        return payload;
      }
    }
  }

  throw new Error("Stream completed without a final result.");
}
