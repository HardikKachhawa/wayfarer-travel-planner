import json, os, re
import httpx
from schemas import TripRequest, Itinerary, Day, Activity

SCHEMA = """{
  "summary": "2 sentences",
  "stay_suggestion": "named area or hotel type with approx nightly cost",
  "transport_tips": "how to get around, with approx costs",
  "days": [{"day": 1, "theme": "short title", "activities": [
    {"time": "HH:MM", "name": "...", "type": "sightseeing|food|activity|transport|stay",
     "duration_min": 90, "cost": 0, "notes": "one practical tip"}]}]
}"""

SYSTEM = ("You are an expert travel planner. Reply with ONLY valid JSON matching the schema. "
          "Costs are totals for the whole group, in the requested currency, as realistic estimates. "
          "Group nearby places on the same day to minimise travel time. Keep the total under budget.")


def _brief(r: TripRequest) -> str:
    return (f"Destination: {r.destination}\nDates: {r.start_date} to {r.end_date} ({r.days} days)\n"
            f"Travelers: {r.travelers}\nTotal budget: {r.budget:g} {r.currency}\n"
            f"Interests: {', '.join(r.interests) or 'general sightseeing'}\n"
            f"Pace: {r.pace}\nAccommodation level: {r.stay}\nNotes: {r.notes or 'none'}")


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text)
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def _chat(messages: list[dict]) -> str:
    resp = httpx.post(
        os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1") + "/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
        json={"model": os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
              "messages": messages, "temperature": 0.7},
        timeout=90)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _ask(user_prompt: str, parse):
    """Call the LLM, validate with Pydantic, retry once with the error fed back."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_prompt}]
    last = None
    for _ in range(2):
        raw = _chat(messages)
        try:
            return parse(_extract_json(raw))
        except Exception as e:  # malformed JSON or schema mismatch
            last = e
            messages += [{"role": "assistant", "content": raw},
                         {"role": "user", "content": f"Invalid output ({e}). Return corrected JSON only."}]
    raise ValueError(f"Model returned invalid itinerary: {last}")


def generate_itinerary(r: TripRequest) -> Itinerary:
    if not os.getenv("LLM_API_KEY"):
        return _mock(r)
    prompt = f"{_brief(r)}\n\nPlan exactly {r.days} days. JSON schema:\n{SCHEMA}"
    it = _ask(prompt, Itinerary.model_validate)
    for i, d in enumerate(it.days, 1):
        d.day = i
    return it


def regenerate_day(r: TripRequest, it: Itinerary, day: int, instruction: str) -> Day:
    other = [f"Day {d.day}: " + ", ".join(a.name for a in d.activities) for d in it.days if d.day != day]
    if not os.getenv("LLM_API_KEY"):
        d = _mock(r, variant=True).days[day - 1]
        return d
    prompt = (f"{_brief(r)}\n\nRewrite ONLY day {day} with different activities from the other days:\n"
              + "\n".join(other) + f"\nExtra request: {instruction or 'none'}\n"
              'Return JSON for a single day: {"day": %d, "theme": "...", "activities": [...]} '
              "using the same activity fields as before." % day)
    d = _ask(prompt, Day.model_validate)
    d.day = day
    return d


def _mock(r: TripRequest, variant: bool = False) -> Itinerary:
    """Offline fallback so the app runs without an API key."""
    per_day = r.budget / r.days
    interests = r.interests or ["sightseeing"]
    days = []
    for n in range(1, r.days + 1):
        focus = interests[(n - 1 + (1 if variant else 0)) % len(interests)]
        acts = [
            Activity(time="08:30", name=f"Breakfast at a local café in {r.destination}", type="food", duration_min=60, cost=round(per_day * .06), notes="Try the regional breakfast special."),
            Activity(time="10:00", name=f"{focus.title()} highlight {n} of {r.destination}", type="sightseeing", duration_min=150, cost=round(per_day * .12), notes="Go early to avoid crowds."),
            Activity(time="13:00", name="Lunch at a well-rated local restaurant", type="food", duration_min=75, cost=round(per_day * .12)),
            Activity(time="15:00", name=f"Afternoon {focus} experience", type="activity", duration_min=120, cost=round(per_day * .15), notes="Book ahead if possible."),
            Activity(time="19:00", name="Dinner with local specialties", type="food", duration_min=90, cost=round(per_day * .2)),
        ]
        if r.pace == "relaxed":
            acts.pop(3)
        days.append(Day(day=n, theme=f"{focus.title()} day", activities=acts))
    return Itinerary(
        summary=f"A {r.pace} {r.days}-day plan for {r.destination} built around {', '.join(interests)}. (Offline sample: set LLM_API_KEY for AI-generated plans.)",
        stay_suggestion=f"A {r.stay} stay near the city centre.",
        transport_tips="Use local taxis or ride-hailing for longer hops; walk between nearby sights.",
        days=days)
