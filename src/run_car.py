import json, cfetch, time
jc = [(e, p) for e, p in json.load(open("out/jobs_car.json"))]
t0 = time.time()
print(f"car_data only: {len(jc)} requests (cached ones skip free)", flush=True)
ok, fail = cfetch.run(jc, workers=2, label="car")
print(f"DONE ok={ok} fail={fail} in {(time.time()-t0)/60:.1f} min", flush=True)
