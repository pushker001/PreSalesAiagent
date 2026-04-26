export function formatDate(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export function toneFromAction(action = "") {
  if (action === "book_call") return "good";
  if (action === "follow_up") return "warm";
  if (action === "nurture") return "watch";
  if (action === "disqualify") return "risk";
  return "default";
}

export function titleFromAction(action = "") {
  return action
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
