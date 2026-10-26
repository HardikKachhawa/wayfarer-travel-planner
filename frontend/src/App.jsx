import { useEffect, useMemo, useState } from "react";
import { api } from "./api.js";

const INTERESTS = ["food", "sightseeing", "culture", "adventure", "nature", "shopping", "nightlife", "relaxation"];
const today = () => new Date().toISOString().slice(0, 10);
const plusDays = (n) => new Date(Date.now() + n * 864e5).toISOString().slice(0, 10);
const blank = () => ({
  destination: "", start_date: plusDays(7), end_date: plusDays(9), budget: 20000, currency: "INR",
  travelers: 1, interests: ["food", "sightseeing"], pace: "balanced", stay: "comfort", notes: "",
});
const money = (n, c) => `${Math.round(n).toLocaleString()} ${c}`;

export default function App() {
  const [trips, setTrips] = useState([]);
  const [req, setReq] = useState(blank());
  const [itin, setItin] = useState(null);
  const [tripId, setTripId] = useState(null);
  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState(null); // {kind: "error"|"ok", text}

  const refresh = () => api.listTrips().then(setTrips).catch((e) => setMsg({ kind: "error", text: e.message }));
  useEffect(() => { refresh(); }, []);

  const total = useMemo(
    () => (itin ? itin.days.reduce((s, d) => s + d.activities.reduce((a, x) => a + (+x.cost || 0), 0), 0) : 0), [itin]);
  const dayCost = (d) => d.activities.reduce((a, x) => a + (+x.cost || 0), 0);

  const run = async (label, fn) => {
    setBusy(label); setMsg(null);
    try { await fn(); } catch (e) { setMsg({ kind: "error", text: e.message }); }
    setBusy("");
  };

  const set = (k, v) => setReq((r) => ({ ...r, [k]: v }));
  const toggle = (i) => set("interests", req.interests.includes(i) ? req.interests.filter((x) => x !== i) : [...req.interests, i]);

  const generate = (e) => {
    e.preventDefault();
    run("generate", async () => {
      const it = await api.generate({ ...req, budget: +req.budget, travelers: +req.travelers });
      setItin(it); setTripId(null); setDay(1);
    });
  };

  const regenerate = () => {
    const instruction = window.prompt("Anything specific for this day? (optional)", "") ?? "";
    run("day", async () => {
      const nd = await api.regenerateDay(req, itin, day, instruction);
      setItin({ ...itin, days: itin.days.map((d) => (d.day === day ? nd : d)) });
    });
  };

  const save = () =>
    run("save", async () => {
      const body = { title: req.destination, request: req, itinerary: itin };
      const t = tripId ? await api.updateTrip(tripId, body) : await api.createTrip(body);
      setTripId(t.id); await refresh(); setMsg({ kind: "ok", text: "Trip saved" });
    });

  const open = (t) => { setReq(t.request); setItin(t.itinerary); setTripId(t.id); setDay(1); setMsg(null); };
  const remove = (t) =>
    run("del", async () => {
      await api.deleteTrip(t.id);
      if (t.id === tripId) { setItin(null); setTripId(null); }
      await refresh();
    });

  const editAct = (di, ai, patch) =>
    setItin((it) => ({ ...it, days: it.days.map((d, i) => i !== di ? d : { ...d, activities: d.activities.map((a, j) => (j === ai ? { ...a, ...patch } : a)) }) }));
  const addAct = (di) =>
    setItin((it) => ({ ...it, days: it.days.map((d, i) => i !== di ? d : { ...d, activities: [...d.activities, { time: "18:00", name: "New activity", type: "activity", duration_min: 60, cost: 0, notes: "" }] }) }));
  const delAct = (di, ai) =>
    setItin((it) => ({ ...it, days: it.days.map((d, i) => i !== di ? d : { ...d, activities: d.activities.filter((_, j) => j !== ai) }) }));

  const cur = itin?.days.find((d) => d.day === day);
  const di = itin ? itin.days.findIndex((d) => d.day === day) : -1;
  const over = itin && total > req.budget;

  return (
    <div className="shell">
      <aside className="side">
        <h1 className="brand">Wayfarer</h1>
        <button className="btn primary wide" onClick={() => { setReq(blank()); setItin(null); setTripId(null); setMsg(null); }}>New trip</button>
        <h2 className="side-h">Saved trips</h2>
        {trips.length === 0 && <p className="muted">Nothing saved yet. Build a trip and press Save trip.</p>}
        <ul className="trips">
          {trips.map((t) => (
            <li key={t.id} className={t.id === tripId ? "on" : ""}>
              <button className="trip-open" onClick={() => open(t)}>
                <strong>{t.title}</strong>
                <span>{t.request.start_date} · {t.itinerary.days.length} days</span>
              </button>
              <button className="x" aria-label={`Delete ${t.title}`} onClick={() => remove(t)}>×</button>
            </li>
          ))}
        </ul>
      </aside>

      <main className="main">
        {msg && <div className={`note ${msg.kind}`} role="status">{msg.text}</div>}

        <form className="builder" onSubmit={generate}>
          <div className="row">
            <label className="grow">Where to?
              <input required minLength={2} value={req.destination} onChange={(e) => set("destination", e.target.value)} placeholder="Goa, Kyoto, Lisbon…" />
            </label>
            <label>From<input type="date" min={today()} value={req.start_date} onChange={(e) => set("start_date", e.target.value)} /></label>
            <label>To<input type="date" min={req.start_date} value={req.end_date} onChange={(e) => set("end_date", e.target.value)} /></label>
          </div>
          <div className="row">
            <label>Budget (total)<input type="number" min="1" value={req.budget} onChange={(e) => set("budget", e.target.value)} /></label>
            <label>Currency
              <select value={req.currency} onChange={(e) => set("currency", e.target.value)}>
                {["INR", "USD", "EUR", "GBP", "JPY", "AED"].map((c) => <option key={c}>{c}</option>)}
              </select>
            </label>
            <label>Travelers<input type="number" min="1" max="20" value={req.travelers} onChange={(e) => set("travelers", e.target.value)} /></label>
            <label>Pace
              <select value={req.pace} onChange={(e) => set("pace", e.target.value)}>
                <option value="relaxed">Relaxed</option><option value="balanced">Balanced</option><option value="packed">Packed</option>
              </select>
            </label>
            <label>Stay
              <select value={req.stay} onChange={(e) => set("stay", e.target.value)}>
                <option value="budget">Budget</option><option value="comfort">Comfort</option><option value="premium">Premium</option>
              </select>
            </label>
          </div>
          <fieldset>
            <legend>Interests</legend>
            <div className="chips">
              {INTERESTS.map((i) => (
                <button type="button" key={i} aria-pressed={req.interests.includes(i)} className={`chip ${req.interests.includes(i) ? "on" : ""}`} onClick={() => toggle(i)}>{i}</button>
              ))}
            </div>
          </fieldset>
          <div className="row">
            <label className="grow">Anything else we should know?
              <input value={req.notes} onChange={(e) => set("notes", e.target.value)} placeholder="Vegetarian, travelling with a toddler, avoid long drives…" />
            </label>
            <button className="btn primary" disabled={!!busy}>{busy === "generate" ? "Planning…" : itin ? "Regenerate trip" : "Plan my trip"}</button>
          </div>
        </form>

        {!itin && !busy && <p className="empty">Tell us where and when, and we'll lay out each day with food, sights, and what it should cost.</p>}

        {itin && cur && (
          <section className="plan">
            <header className="plan-head">
              <div>
                <h2>{req.destination}</h2>
                <p className="muted">{itin.summary}</p>
              </div>
              <div className="cost">
                <span className={over ? "over" : ""}>{money(total, req.currency)}</span>
                <small>of {money(req.budget, req.currency)}{over ? " · over budget" : ""}</small>
                <div className="bar"><i className={over ? "over" : ""} style={{ width: `${Math.min(100, (total / req.budget) * 100)}%` }} /></div>
              </div>
            </header>

            <div className="facts">
              {itin.stay_suggestion && <p><strong>Where to stay.</strong> {itin.stay_suggestion}</p>}
              {itin.transport_tips && <p><strong>Getting around.</strong> {itin.transport_tips}</p>}
            </div>

            <div className="tabs" role="tablist">
              {itin.days.map((d) => (
                <button key={d.day} role="tab" aria-selected={d.day === day} className={d.day === day ? "on" : ""} onClick={() => setDay(d.day)}>
                  Day {d.day}<small>{money(dayCost(d), req.currency)}</small>
                </button>
              ))}
            </div>

            <div className="day">
              <div className="day-bar">
                <input className="theme" aria-label="Day theme" value={cur.theme} onChange={(e) => setItin({ ...itin, days: itin.days.map((d) => d.day === day ? { ...d, theme: e.target.value } : d) })} />
                <button className="btn" disabled={!!busy} onClick={regenerate}>{busy === "day" ? "Rewriting…" : "Regenerate day"}</button>
              </div>
              <ol className="tl">
                {cur.activities.map((a, ai) => (
                  <li key={ai} className={`t-${a.type}`}>
                    <input className="time" aria-label="Time" value={a.time} onChange={(e) => editAct(di, ai, { time: e.target.value })} />
                    <div className="body">
                      <input className="name" aria-label="Activity" value={a.name} onChange={(e) => editAct(di, ai, { name: e.target.value })} />
                      <div className="meta">
                        <span className="tag">{a.type}</span>
                        <span>{a.duration_min} min</span>
                        {a.notes && <span className="tip">{a.notes}</span>}
                      </div>
                    </div>
                    <label className="price">
                      <input type="number" min="0" aria-label="Cost" value={a.cost} onChange={(e) => editAct(di, ai, { cost: e.target.value })} />
                      <small>{req.currency}</small>
                    </label>
                    <button className="x" aria-label="Remove activity" onClick={() => delAct(di, ai)}>×</button>
                  </li>
                ))}
              </ol>
              <button className="btn ghost" onClick={() => addAct(di)}>Add activity</button>
            </div>

            <footer className="actions">
              <button className="btn primary" disabled={!!busy} onClick={save}>{busy === "save" ? "Saving…" : tripId ? "Update trip" : "Save trip"}</button>
              <button className="btn" onClick={() => window.print()}>Print itinerary</button>
            </footer>
          </section>
        )}
      </main>
    </div>
  );
}
