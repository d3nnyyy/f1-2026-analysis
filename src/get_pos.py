import sys, fetch
sk = int(sys.argv[1]); drivers = [int(x) for x in sys.argv[2].split(",")]
for dn in drivers:
    for ep in ("location", "intervals"):
        d = fetch.get(ep, {"session_key": sk, "driver_number": dn})
        print(f"  {dn:>3} {ep:<10} {len(d) if isinstance(d,list) else d}")
