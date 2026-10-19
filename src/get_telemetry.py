"""Pull car_data (speed/throttle/brake/rpm/gear @ ~4Hz) for a few drivers."""
import sys, fetch
sk = int(sys.argv[1]); drivers = [int(x) for x in sys.argv[2].split(",")]
for dn in drivers:
    d = fetch.get("car_data", {"session_key": sk, "driver_number": dn})
    print(f"  driver {dn}: {len(d)} samples")
