from datetime import datetime, timezone
from flask import Flask, render_template, redirect, request, url_for

from db import get_conn, init_db

app = Flask(__name__)

# Flask 3 removed before_first_request, so initialize DB at startup.
init_db()

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def parse_iso(ts: str | None):
    if not ts:
        return None
    # Stored as ISO-8601 with timezone, e.g. 2026-02-22T16:08:56+00:00
    return datetime.fromisoformat(ts)

@app.get("/")
def index():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, start_utc, end_utc, notes FROM fasts ORDER BY id DESC"
        ).fetchall()

    fasts = []
    for r in rows:
        start = parse_iso(r["start_utc"])
        end = parse_iso(r["end_utc"]) if r["end_utc"] else None

        duration_hours = None
        if start and end:
            duration_hours = round((end - start).total_seconds() / 3600, 2)

        fasts.append({
            "id": r["id"],
            "start": start,
            "end": end,
            "notes": r["notes"],
            "duration": duration_hours,
        })

    active_fast = next((f for f in fasts if f["end"] is None), None)

    return render_template("index.html", fasts=fasts, active_fast=active_fast)

@app.post("/start")
def start_fast():
    notes = request.form.get("notes", "").strip() or None
    with get_conn() as conn:
        # Prevent multiple active fasts
        active = conn.execute("SELECT 1 FROM fasts WHERE end_utc IS NULL LIMIT 1").fetchone()
        if active:
            return redirect(url_for("index"))

        conn.execute(
            "INSERT INTO fasts (start_utc, end_utc, notes) VALUES (?, NULL, ?)",
            (utc_now_iso(), notes),
        )
        conn.commit()
    return redirect(url_for("index"))

@app.post("/end/<int:fast_id>")
def end_fast(fast_id: int):
    with get_conn() as conn:
        conn.execute(
            "UPDATE fasts SET end_utc = ? WHERE id = ? AND end_utc IS NULL",
            (utc_now_iso(), fast_id),
        )
        conn.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)