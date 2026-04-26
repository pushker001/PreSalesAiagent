const API_BASE_URL = "http://localhost:8000";

async function parseJson(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}): ${text}`);
  }
  return response.json();
}

export async function fetchLeads() {
  const response = await fetch(`${API_BASE_URL}/leads`);
  return parseJson(response);
}

export async function fetchLead(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}`);
  return parseJson(response);
}

export async function fetchLeadReports(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/reports`);
  return parseJson(response);
}

export async function fetchLeadQualification(leadId) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}/qualification`);
  if (response.status === 404) return null;
  return parseJson(response);
}

export async function updateLead(leadId, payload) {
  const response = await fetch(`${API_BASE_URL}/leads/${leadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parseJson(response);
}

export async function analyzeLead(formData, handlers = {}) {
  const { onProgress, onDone } = handlers;
  const response = await fetch(`${API_BASE_URL}/analyze-closure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
        onProgress({
          message: event.message,
          step: event.step,
          total: event.total,
        });
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
