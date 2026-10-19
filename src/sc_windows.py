"""Pin the exact lap each SC/VSC ENDED, per the pre-registered window definition."""
import json, re, pandas as pd
W = json.load(open("out/windows.json"))
out = []
for w in W:
    rc = json.load(open(f"data/race_control_session_key={w['session_key']}.json"))
    d = pd.DataFrame(rc)
    d["lap_number"] = pd.to_numeric(d.lap_number, errors="coerce")
    d["msg"] = d.message.astype(str).str.upper()
    dep = w["lap"]
    # first end-marker at or after deployment
    end_pat = r"(VSC ENDING|SAFETY CAR IN THIS LAP|TRACK CLEAR)"
    cand = d[(d.msg.str.contains(end_pat, regex=True)) & (d.lap_number >= dep)]
    end = int(cand.lap_number.min()) if len(cand) else dep + 2
    out.append({**w, "end_lap": end, "sc_laps": end - dep})
E = pd.DataFrame(out)
print(E[["circuit","kind","lap","end_lap","sc_laps","lo_lap","hi_lap","n_drivers"]].to_string(index=False))
print(f"\nmedian SC duration: {E.sc_laps.median():.0f} laps")
E.to_json("out/windows2.json", orient="records", indent=1)
