import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

import llm, storage
from schemas import Day, Itinerary, RegenerateDay, TripIn, TripRequest

app = FastAPI(title="Personalized Travel Itinerary Planner")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def current_user(authorization: str | None = Header(None)) -> str:
    try:
        return storage.verify_user(authorization)
    except PermissionError as e:
        raise HTTPException(401, str(e))


def _llm_guard(fn, *args):
    try:
        return fn(*args)
    except (ValueError, httpx.HTTPError) as e:
        raise HTTPException(502, f"AI generation failed: {e}")


@app.get("/api/health")
def health():
    return {"ok": True, "ai": bool(os.getenv("LLM_API_KEY")), "supabase": bool(os.getenv("SUPABASE_URL"))}


@app.post("/api/itinerary/generate", response_model=Itinerary)
def generate(req: TripRequest, uid: str = Depends(current_user)):
    return _llm_guard(llm.generate_itinerary, req)


@app.post("/api/itinerary/regenerate-day", response_model=Day)
def regenerate_day(body: RegenerateDay, uid: str = Depends(current_user)):
    if not 1 <= body.day <= len(body.itinerary.days):
        raise HTTPException(422, "day out of range")
    return _llm_guard(llm.regenerate_day, body.request, body.itinerary, body.day, body.instruction)


@app.get("/api/trips")
def list_trips(uid: str = Depends(current_user)):
    return storage.list_trips(uid)


@app.post("/api/trips", status_code=201)
def create_trip(trip: TripIn, uid: str = Depends(current_user)):
    return storage.create_trip(uid, trip.model_dump(mode="json"))


@app.get("/api/trips/{tid}")
def get_trip(tid: str, uid: str = Depends(current_user)):
    t = storage.get_trip(uid, tid)
    if not t:
        raise HTTPException(404, "Trip not found")
    return t


@app.put("/api/trips/{tid}")
def update_trip(tid: str, trip: TripIn, uid: str = Depends(current_user)):
    t = storage.update_trip(uid, tid, trip.model_dump(mode="json"))
    if not t:
        raise HTTPException(404, "Trip not found")
    return t


@app.delete("/api/trips/{tid}", status_code=204)
def delete_trip(tid: str, uid: str = Depends(current_user)):
    storage.delete_trip(uid, tid)
