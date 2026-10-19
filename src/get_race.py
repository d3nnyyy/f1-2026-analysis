import fetch
D = [1,3,81,63,55,44,43,41,30,27,22,12,10,5,87]
for dn in D:
    a = fetch.get("car_data", {"session_key": 11361, "driver_number": dn})
    b = fetch.get("intervals", {"session_key": 11361, "driver_number": dn})
    print(f"  {dn:>3}  car={len(a):>6}  intervals={len(b):>5}", flush=True)
