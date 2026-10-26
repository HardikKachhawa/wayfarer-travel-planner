# Wayfarer: Personalized Travel Itinerary Planner

React (Vite) + FastAPI + Supabase + Llama-3 (any OpenAI-compatible API).

## Run it
**Backend** (Python 3.10+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then edit (see below)
uvicorn main:app --reload     # http://localhost:8000/docs
```
**Frontend** (Node 18+)
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## Configuration (`backend/.env`)
| Variable | Purpose |
|---|---|
| `LLM_API_KEY` | Key for a Llama-3 host (Groq, Together, etc.). **Empty = offline sample itineraries**, so the app runs with zero setup. |
| `LLM_BASE_URL`, `LLM_MODEL` | Any OpenAI-compatible endpoint and model name. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Optional. Empty = trips saved to `backend/trips.json`. |

To use Supabase: create a project, run `supabase_schema.sql` in the SQL editor, then fill in the two variables.

## API
| Method | Path | Description |
|---|---|---|
| POST | `/api/itinerary/generate` | Trip request → structured itinerary |
| POST | `/api/itinerary/regenerate-day` | Rewrite one day, keeping the rest |
| GET/POST | `/api/trips` | List / save trips |
| GET/PUT/DELETE | `/api/trips/{id}` | Read / update / delete a trip |
| GET | `/api/health` | Shows whether AI and Supabase are configured |

## How generation works
`llm.py` builds a prompt from the traveler's preferences plus a JSON schema, calls the model, validates the reply with Pydantic, and retries once with the validation error if the JSON is malformed.

## Not yet included
- **Login UI.** The backend already verifies Supabase bearer tokens when Supabase is configured; add Supabase Auth in the frontend and call `setToken(session.access_token)` from `src/api.js`. Until then everything runs as a single "demo" user.
- **Shared group trips.** Add a `trip_members` table and extend the RLS policies.
- **Live prices, maps, and weather.**
