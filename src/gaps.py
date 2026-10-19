"""Gap to car ahead, derived from lap-crossing times we already have on disk.
Validated at Monza against the API intervals endpoint:
  classification-order version : r=0.92 vs API, tow effect +10.98 km/h
  on-track version (lapped cars included) : tow effect +11.42 km/h
Both reproduce the validated slipstream. We carry both; the on-track one is the
physically correct definition of 'who is disturbing my air' and is used as primary.
"""
import json, numpy as np, pandas as pd

def gaps_for(sk):
    L = pd.DataFrame(json.load(open(f"data/laps_session_key={sk}.json")))
    L["t0"] = pd.to_datetime(L.date_start, format="ISO8601", errors="coerce")
    L = L.dropna(subset=["t0"]).sort_values("t0").reset_index(drop=True)
    tv, dv = L.t0.values, L.driver_number.values
    on_track = np.full(len(L), np.nan)
    for i in range(1, len(L)):
        j = i - 1
        while j >= 0 and dv[j] == dv[i]:
            j -= 1
        if j >= 0:
            on_track[i] = (tv[i] - tv[j]) / np.timedelta64(1, "s")
    L["gap_track"] = on_track
    # classification-order version: previous car within the same lap number
    L["gap_class"] = (L.sort_values(["lap_number","t0"])
                        .groupby("lap_number").t0.diff().dt.total_seconds()
                        .reindex(L.index))
    return L[["driver_number","lap_number","gap_track","gap_class"]].rename(
        columns={"driver_number":"driver","lap_number":"lap"})
