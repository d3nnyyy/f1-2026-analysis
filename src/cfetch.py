"""Concurrent OpenF1 fetcher.

The bottleneck is TRANSFER time (3.6 s / 5.5 MB per request), not the rate limit
(30 req/min = 2 s/request). So overlapping transfers wins, but the aggregate rate
must still respect the server cap or we just earn 429s.

A shared token bucket is the governor; the thread pool only decides how much
transfer overlaps. Separate processes would NOT help: the cap is server-side per IP,
so N processes share one quota and simply collide.
"""
import json, os, threading, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

B, CACHE = "https://api.openf1.org/v1/", "data"
RATE, WINDOW = 16, 60.0          # measured: real cap is tighter than documented 30/min;
                                 # 429 backoff costs more than a lower steady rate
_stamps, _lk = [], threading.Lock()

def _token():
    while True:
        with _lk:
            now = time.time()
            _stamps[:] = [s for s in _stamps if now - s < WINDOW]
            if len(_stamps) < RATE:
                _stamps.append(now); return
            wait = WINDOW - (now - _stamps[0]) + 0.05
        time.sleep(min(wait, 5))

def key_for(ep, params):
    s = urllib.parse.urlencode(sorted(params.items()))
    s = s.replace("/", "_").replace(":", "-")
    return os.path.join(CACHE, f"{ep}_{s}.json")

def get(ep, params):
    k = key_for(ep, params)
    if os.path.exists(k):
        try:
            with open(k) as f: return json.load(f)
        except Exception: os.remove(k)
    url = f"{B}{ep}?{urllib.parse.urlencode(params)}"
    for att in range(5):
        _token()
        try:
            with urllib.request.urlopen(url, timeout=150) as r:
                d = json.load(r)
            tmp = k + ".tmp"
            with open(tmp, "w") as f: json.dump(d, f)
            os.replace(tmp, k)
            return d
        except urllib.error.HTTPError as e:
            if e.code == 404: return []
            if e.code == 429: time.sleep(8 * (att + 1)); continue
            if att == 4: return None
            time.sleep(3 * (att + 1))
        except Exception:
            if att == 4: return None
            time.sleep(3 * (att + 1))
    return None

def run(jobs, workers=4, label=""):
    """jobs = list of (ep, params). Returns dict of ok/fail counts."""
    ok = fail = 0; t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(get, ep, p): (ep, p) for ep, p in jobs}
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            if r is None: fail += 1
            else: ok += 1
            if i % 25 == 0 or i == len(jobs):
                el = time.time() - t0
                print(f"  [{label}] {i}/{len(jobs)}  ok={ok} fail={fail}  "
                      f"{el/60:.1f}min  {i/el*60:.1f} req/min", flush=True)
    return ok, fail
