// Pass a Supabase access token here once you add login: setToken(session.access_token)
let token = null;
export const setToken = (t) => (token = t);

async function call(path, method = "GET", body) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : d?.[0]?.msg || "Request failed");
  }
  return data;
}

export const api = {
  listTrips: () => call("/trips"),
  generate: (request) => call("/itinerary/generate", "POST", request),
  regenerateDay: (request, itinerary, day, instruction) =>
    call("/itinerary/regenerate-day", "POST", { request, itinerary, day, instruction }),
  createTrip: (t) => call("/trips", "POST", t),
  updateTrip: (id, t) => call(`/trips/${id}`, "PUT", t),
  deleteTrip: (id) => call(`/trips/${id}`, "DELETE"),
};
