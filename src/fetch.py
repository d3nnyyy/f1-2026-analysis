"""Cached OpenF1 fetcher. Free tier: 3 req/s, 30/min -> we space at 2.1s."""
import json, os, time, urllib.request, urllib.parse, sys

B, CACHE = "https://api.openf1.org/v1/", "data"
_last = [0.0]

def get(ep, params, force=False):
    key = os.path.join(CACHE, ep + "_" + urllib.parse.urlencode(sorted(params.items())).replace("/", "_") + ".json")
    if os.path.exists(key) and not force:
        with open(key) as f: return json.load(f)
    dt = time.time() - _last[0]
    if dt < 2.1: time.sleep(2.1 - dt)
    url = f"{B}{ep}?{urllib.parse.urlencode(params)}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                d = json.load(r)
            _last[0] = time.time()
            with open(key, "w") as f: json.dump(d, f)
            return d
        except Exception as e:
            if attempt == 3:
                print(f"  FAIL {ep} {params}: {e}", file=sys.stderr); return []
            time.sleep(5 * (attempt + 1))

def race_sessions():
    """Enumerate via meetings, since session_type=Race&year=2026 silently drops Australia."""
    out = []
    for m in get("meetings", {"year": 2026}):
        for s in get("sessions", {"meeting_key": m["meeting_key"]}):
            if s.get("session_type") == "Race" and s.get("session_name") == "Race":
                out.append({"session_key": s["session_key"], "meeting_key": m["meeting_key"],
                            "country": m["country_name"], "circuit": m.get("circuit_short_name"),
                            "date": s["date_start"][:10]})
    return sorted(out, key=lambda x: x["date"])
