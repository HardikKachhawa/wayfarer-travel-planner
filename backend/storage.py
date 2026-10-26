import json, os, uuid
from datetime import datetime, timezone
from pathlib import Path
import httpx

FILE = Path(__file__).parent / "trips.json"


def _sb():
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if not (url and key):
        return None
    return f"{url}/rest/v1/trips", {"apikey": key, "Authorization": f"Bearer {key}",
                                    "Content-Type": "application/json", "Prefer": "return=representation"}


def _load():
    return json.loads(FILE.read_text()) if FILE.exists() else []


def _save(rows):
    FILE.write_text(json.dumps(rows, indent=2, default=str))


def verify_user(token: str | None) -> str:
    """Resolve the Supabase user id from a bearer token; 'demo' user when Supabase is not configured."""
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY")
    if not (url and key):
        return "demo"
    if not token:
        raise PermissionError("Missing token")
    r = httpx.get(f"{url}/auth/v1/user", headers={"apikey": key, "Authorization": token}, timeout=15)
    if r.status_code != 200:
        raise PermissionError("Invalid token")
    return r.json()["id"]


def list_trips(uid):
    if sb := _sb():
        r = httpx.get(sb[0], headers=sb[1], params={"user_id": f"eq.{uid}", "order": "updated_at.desc"}, timeout=15)
        r.raise_for_status(); return r.json()
    return sorted([t for t in _load() if t["user_id"] == uid], key=lambda t: t["updated_at"], reverse=True)


def get_trip(uid, tid):
    return next((t for t in list_trips(uid) if t["id"] == tid), None)


def create_trip(uid, data: dict):
    if sb := _sb():
        r = httpx.post(sb[0], headers=sb[1], json={**data, "user_id": uid}, timeout=15)
        r.raise_for_status(); return r.json()[0]
    now = datetime.now(timezone.utc).isoformat()
    row = {"id": str(uuid.uuid4()), "user_id": uid, "created_at": now, "updated_at": now, **data}
    _save(_load() + [row]); return row


def update_trip(uid, tid, data: dict):
    now = datetime.now(timezone.utc).isoformat()
    if sb := _sb():
        r = httpx.patch(sb[0], headers=sb[1], params={"id": f"eq.{tid}", "user_id": f"eq.{uid}"},
                        json={**data, "updated_at": now}, timeout=15)
        r.raise_for_status(); rows = r.json(); return rows[0] if rows else None
    rows, out = _load(), None
    for t in rows:
        if t["id"] == tid and t["user_id"] == uid:
            t.update(data, updated_at=now); out = t
    _save(rows); return out


def delete_trip(uid, tid):
    if sb := _sb():
        httpx.delete(sb[0], headers=sb[1], params={"id": f"eq.{tid}", "user_id": f"eq.{uid}"}, timeout=15).raise_for_status()
        return
    _save([t for t in _load() if not (t["id"] == tid and t["user_id"] == uid)])
