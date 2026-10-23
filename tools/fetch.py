# Downloads the campus outline, the OpenStreetMap features around it and the elevation tiles into raw/.
# usage: python tools/fetch.py [relation_id] [raw_dir]      (needs requests)
import json, math, os, sys, time
import requests

REL = sys.argv[1] if len(sys.argv) > 1 else "6705106"          # 충북대학교 (OSM relation)
RAW = sys.argv[2] if len(sys.argv) > 2 else "raw"
PAD = 0.0018                                                    # about 200 m of town around the campus
ZOOM = 15
MIRRORS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
UA = {"User-Agent": "SMASH CBNU data build (github.com/JJJJJJONG/SMASH-CBNU)"}


def overpass(q, tries=5):
    wait = 5
    for _ in range(tries):
        for url in MIRRORS:
            try:
                r = requests.post(url, data={"data": q}, headers=UA, timeout=180)
                if r.ok and r.text.lstrip().startswith("{"):
                    return r.json()
                print("  retry:", url, r.status_code)
            except requests.RequestException as e:
                print("  retry:", url, type(e).__name__)
        time.sleep(wait); wait *= 2
    raise SystemExit("Overpass failed")


os.makedirs(os.path.join(RAW, "tiles"), exist_ok=True)
camp = overpass(f"[out:json][timeout:120];rel({REL});out geom;")
json.dump(camp, open(os.path.join(RAW, "campus_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
pts = [p for e in camp["elements"] for m in e.get("members", []) for p in m.get("geometry") or []]
S, N = min(p["lat"] for p in pts) - PAD, max(p["lat"] for p in pts) + PAD
W, E = min(p["lon"] for p in pts) - PAD * 1.25, max(p["lon"] for p in pts) + PAD * 1.25
bbox = f"{S},{W},{N},{E}"
print("campus:", camp["elements"][0]["tags"].get("name"), "bbox", bbox)

area = overpass(f"""[out:json][timeout:180][bbox:{bbox}];
(way["building"]; relation["building"]; way["highway"];
 way["landuse"]; way["leisure"]; way["natural"]; relation["natural"]; relation["landuse"];
 way["amenity"="parking"]; way["waterway"]; way["water"]; node["natural"="tree"];);
out geom tags;""")
json.dump({"bbox": bbox, "data": area}, open(os.path.join(RAW, "area_raw.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("features:", len(area["elements"]))

# elevation: AWS terrain tiles (terrarium PNG), one 256 px tile is ~1 km here
def tile(lat, lon):
    n = 2 ** ZOOM
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
x0, y1 = tile(S, W); x1, y0 = tile(N, E)
for tx in range(int(x0), int(x1) + 1):
    for ty in range(int(y0), int(y1) + 1):
        fn = os.path.join(RAW, "tiles", f"{tx}_{ty}.png")
        if os.path.exists(fn): continue
        r = requests.get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{ZOOM}/{tx}/{ty}.png", timeout=60)
        r.raise_for_status(); open(fn, "wb").write(r.content)
print("tiles:", len(os.listdir(os.path.join(RAW, "tiles"))))
