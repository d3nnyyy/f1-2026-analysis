import json, re, fetch, pandas as pd
idx = [r for r in json.load(open("out/race_index.json")) if r["n_laps"] > 0]
ev = []
for r in idx:
    rc = fetch.get("race_control", {"session_key": r["session_key"]})
    if not isinstance(rc, list): continue
    for m in rc:
        msg = str(m.get("message","")).upper()
        if re.search(r"\b(SAFETY CAR DEPLOYED|VSC DEPLOYED|VIRTUAL SAFETY CAR DEPLOYED)\b", msg):
            ev.append({"circuit": r["circuit"], "session_key": r["session_key"],
                       "lap": m.get("lap_number"), "date": m.get("date"),
                       "kind": "VSC" if "VSC" in msg or "VIRTUAL" in msg else "SC",
                       "msg": msg[:40]})
    print(f"  {r['circuit'][:18].ljust(18)} events so far: {len(ev)}", flush=True)
E = pd.DataFrame(ev)
E.to_csv("out/sc_events.csv", index=False)
print("\n=== all SC/VSC deployments 2026 ===")
print(E[["circuit","kind","lap"]].to_string(index=False))
print(f"\ntotal events: {len(E)} across {E.circuit.nunique()} races")
