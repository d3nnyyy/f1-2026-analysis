import json, fetch
races = fetch.race_sessions()
done = [r for r in races if r["date"] <= "2026-10-19"]
print(f"meetings->race sessions: {len(races)} total, {len(done)} completed\n")
rows = []
for r in done:
    laps   = fetch.get("laps",   {"session_key": r["session_key"]})
    stints = fetch.get("stints", {"session_key": r["session_key"]})
    print(f"  {r['date']}  {r['country'][:20].ljust(20)} laps={str(len(laps)).rjust(5)} stints={str(len(stints)).rjust(4)}")
    rows.append({**r, "n_laps": len(laps), "n_stints": len(stints)})
json.dump(rows, open("out/race_index.json","w"), indent=1)
print("\nempty sessions:", [r['country'] for r in rows if r['n_laps']==0])
