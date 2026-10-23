# Turns the raw downloads from tools/fetch.py into data.js (local metres: x east, z south).
# usage: python tools/build_data.py [raw_dir] [out.js]      (needs numpy and Pillow)
#   - buildings keep their OpenStreetMap floor count and type, so the facade knows storey height and style
#   - footprints that OSM stores twice (an outline plus a copy of it) are merged, so roofs do not flicker
#   - the elevation grid is cleaned: no-data holes filled, bumps that tall buildings leave in the
#     satellite surface model flattened, ponds levelled to one water height
import json, math, os, random, sys
import numpy as np
from PIL import Image

RAW = sys.argv[1] if len(sys.argv) > 1 else "raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data.js"
CONFIG = {"title": "SMASH CBNU", "school": "충북대", "fullName": "충북대학교", "antipode": "아르헨티나 앞바다(남대서양)"}

camp = json.load(open(os.path.join(RAW, "campus_raw.json"), encoding="utf-8"))
area = json.load(open(os.path.join(RAW, "area_raw.json"), encoding="utf-8"))
S, W, N, E = map(float, area["bbox"].split(","))
lat0, lon0 = (S + N) / 2, (W + E) / 2
KX, KY = 111320 * math.cos(math.radians(lat0)), 110574


def P(lat, lon):
    return [round((lon - lon0) * KX, 1), round(-(lat - lat0) * KY, 1)]


def area2(r):
    return sum(r[i][0] * r[(i + 1) % len(r)][1] - r[(i + 1) % len(r)][0] * r[i][1] for i in range(len(r))) / 2


def inside(pt, ring):
    x, z = pt; c = False
    for i in range(len(ring)):
        x1, z1 = ring[i]; x2, z2 = ring[i - 1]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1: c = not c
    return c


def clean(r):
    if len(r) > 1 and r[0] == r[-1]: r = r[:-1]
    out = []
    for p in r:
        if not out or abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1]) > 0.3: out.append(p)
    return out


def join_rings(ways):
    ways = [w[:] for w in ways if len(w) > 1]; rings = []
    while ways:
        cur = ways.pop(0); changed = True
        while cur[0] != cur[-1] and changed:
            changed = False
            for i, w in enumerate(ways):
                if w[0] == cur[-1]: cur += w[1:]
                elif w[-1] == cur[-1]: cur += w[::-1][1:]
                elif w[-1] == cur[0]: cur = w + cur[1:]
                elif w[0] == cur[0]: cur = w[::-1] + cur[1:]
                else: continue
                ways.pop(i); changed = True; break
        if len(cur) >= 4: rings.append(cur)
    return rings


def rings_of(el):
    pts = lambda g: [(p["lat"], p["lon"]) for p in g]
    if el["type"] == "way":
        return ([clean([P(*p) for p in pts(el["geometry"])])] if "geometry" in el else []), []
    outs, ins = [], []
    for m in el.get("members", []):
        if m.get("type") == "way" and m.get("geometry"): (ins if m.get("role") == "inner" else outs).append(pts(m["geometry"]))
    return [clean([P(*p) for p in r]) for r in join_rings(outs)], [clean([P(*p) for p in r]) for r in join_rings(ins)]


def num(v):
    try: return float(str(v).replace("m", "").split()[0])
    except (ValueError, IndexError): return None


# ---------------- campus boundary
campus = [r for el in camp["elements"] for r in rings_of(el)[0] if abs(area2(r)) > 2000]
in_campus = lambda pt: any(inside(pt, r) for r in campus)

# ---------------- terrain (AWS terrarium tiles, zoom 15, sampled every 5 m)
ZOOM, STEP = 15, 5.0
tiles = {tuple(map(int, f[:-4].split("_"))): Image.open(os.path.join(RAW, "tiles", f)).convert("RGB").load()
         for f in os.listdir(os.path.join(RAW, "tiles")) if f.endswith(".png")}


def elev(lat, lon):
    n = 2 ** ZOOM * 256
    x = (lon + 180) / 360 * n - .5; y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n - .5
    x0, y0 = math.floor(x), math.floor(y); fx, fy = x - x0, y - y0
    def px(a, b):
        r, g, bl = tiles[(a // 256, b // 256)][a % 256, b % 256]
        return r * 256 + g + bl / 256 - 32768
    return (px(x0, y0) * (1 - fx) + px(x0 + 1, y0) * fx) * (1 - fy) + (px(x0, y0 + 1) * (1 - fx) + px(x0 + 1, y0 + 1) * fx) * fy


tx0, tz0 = P(N, W); tx1, tz1 = P(S, E)
nx, nz = int((tx1 - tx0) / STEP) + 1, int((tz1 - tz0) / STEP) + 1
g = np.array([[elev(lat0 - (tz0 + i * STEP) / KY, lon0 + (tx0 + j * STEP) / KX) for j in range(nx)] for i in range(nz)])
for _ in range(2):   # SRTM is noisy: a light cross-shaped blur
    g[1:-1, 1:-1] = (4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:]) / 8

# ---------------- elements
buildings, roads, lands, trees = [], [], [], []
ROAD_W = {"motorway": 16, "trunk": 16, "primary": 14, "secondary": 12, "tertiary": 10, "unclassified": 7, "residential": 7,
          "service": 5, "living_street": 6, "pedestrian": 5, "footway": 2.5, "path": 2, "cycleway": 2.5, "steps": 2.5, "track": 3}
LAND = {"grass": "grass", "meadow": "grass", "park": "park", "garden": "park", "pitch": "pitch", "wood": "wood", "forest": "wood",
        "scrub": "wood", "parking": "parking", "residential": "res", "commercial": "res", "retail": "res", "farmland": "farm",
        "water": "water", "track": "pitch", "stadium": "pitch", "sports_centre": "pitch", "recreation_ground": "park", "playground": "park"}
# building type -> facade family used by the game: u campus/office, a apartment block, h house, g greenhouse
KIND = {"apartments": "a", "residential": "a", "dormitory": "a", "house": "h", "detached": "h", "terrace": "h", "greenhouse": "g"}

for el in area["data"]["elements"]:
    t = el.get("tags", {})
    if el["type"] == "node":
        if t.get("natural") == "tree": trees.append(P(el["lat"], el["lon"]) + [1.0])
        continue
    if "building" in t and t["building"] not in ("no", "roof", "construction"):
        outs, ins = rings_of(el)
        lv = num(t.get("building:levels")); lv = int(round(lv)) if lv and lv >= 1 else None
        hgt = num(t.get("height"))
        kind = KIND.get(t["building"], "u")
        for o in outs:
            if len(o) < 3 or abs(area2(o)) < 20: continue
            if area2(o) < 0: o = o[::-1]
            cx = sum(p[0] for p in o) / len(o); cz = sum(p[1] for p in o) / len(o)
            inc = in_campus([cx, cz])
            h = hgt if hgt else lv * 3.6 + 1 if lv else None
            if h is None:
                a = abs(area2(o))
                h = 4.5 if kind == "g" else (14 if a > 800 else 10) if inc else (9 if a > 200 else 6)
            b = {"o": o, "h": round(max(3, min(h, 80)), 1), "c": 1 if inc else 0, "k": kind}
            if lv: b["l"] = lv
            nm = t.get("name") or t.get("name:ko")
            if nm: b["n"] = nm
            hs = [r if area2(r) < 0 else r[::-1] for r in ins if len(r) >= 3 and abs(area2(r)) > 5]
            if hs: b["i"] = hs
            b["_tag"] = bool(lv or hgt)
            buildings.append(b)
        continue
    if "highway" in t and el["type"] == "way" and "geometry" in el:
        k = t["highway"]
        if k not in ROAD_W or t.get("area") == "yes": continue
        r = {"k": k, "w": ROAD_W[k], "p": [P(p["lat"], p["lon"]) for p in el["geometry"]]}
        if t.get("name"): r["n"] = t["name"]
        roads.append(r); continue
    kind = next((LAND[t[key]] for key in ("landuse", "leisure", "natural", "amenity") if t.get(key) in LAND), None)
    if "waterway" in t or t.get("water"): kind = "water"
    if kind:
        rs = [o for o in rings_of(el)[0] if len(o) >= 3 and abs(area2(o)) > 30]
        if rs: lands.append({"k": kind, "r": rs})

# ---------------- duplicate footprints
def bbox(b):
    xs = [p[0] for p in b["o"]]; zs = [p[1] for p in b["o"]]
    return min(xs), max(xs), min(zs), max(zs)


def shared(small, big):
    """fraction of `small`'s footprint that also lies inside `big` (sampled on a 12 x 12 grid)"""
    x0, x1, z0, z1 = bbox(small)
    pts = [(x0 + (x1 - x0) * (u + .5) / 12, z0 + (z1 - z0) * (v + .5) / 12) for u in range(12) for v in range(12)]
    pts = [p for p in pts if inside(p, small["o"])]
    return sum(inside(p, big["o"]) for p in pts) / max(1, len(pts))


buildings.sort(key=lambda b: -abs(area2(b["o"])))
kept, merged, nudged = [], 0, 0
for b in buildings:
    bx = bbox(b); drop = False
    for k in kept:
        kx = bbox(k)
        if bx[0] > kx[1] or bx[1] < kx[0] or bx[2] > kx[3] or bx[3] < kx[2]: continue
        f = shared(b, k)
        if f < .3: continue
        if f > .85 and (abs(k["h"] - b["h"]) < 1.5 or not b["_tag"]):
            for key in ("n", "l"):
                if key not in k and key in b: k[key] = b[key]
            if b["_tag"] and not k["_tag"]: k["h"], k["_tag"] = b["h"], True
            drop = True; merged += 1; break
        if abs(k["h"] - b["h"]) < .6:   # two roofs at one height would z-fight
            b["h"] = round(b["h"] + .6, 1); nudged += 1
    if not drop: kept.append(b)
buildings = kept
for b in buildings: b.pop("_tag")
print(f"footprints merged {merged}, roofs nudged {nudged}")

# ---------------- terrain clean-up
X = tx0 + np.arange(nx) * STEP; Z = tz0 + np.arange(nz) * STEP
GX, GZ = np.meshgrid(X, Z)
holes = g < 0
while holes.any():   # 1. no-data cells: grow the neighbours' average inwards
    ok = ~holes; s = np.zeros_like(g); c = np.zeros_like(g)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            s += np.roll(np.roll(np.where(ok, g, 0), di, 0), dj, 1); c += np.roll(np.roll(ok, di, 0), dj, 1)
    grow = holes & (c > 0)
    if not grow.any(): g[holes] = np.median(g[ok]); break
    g[grow] = s[grow] / c[grow]; holes &= ~grow
spikes = 0
R = int(round(40 / STEP))
for _ in range(3):   # 2. a cell far above everything 40 m around it is a building in the surface model, not a hill
    pad = np.pad(g, R, mode="edge")
    around = np.max([pad[R + int(round(R * math.sin(a))):R + int(round(R * math.sin(a))) + nz,
                         R + int(round(R * math.cos(a))):R + int(round(R * math.cos(a))) + nx] for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)], 0)
    bump = g - around > 10
    if not bump.any(): break
    spikes += int(bump.sum()); g[bump] = around[bump]


def mask_of(rings):
    m = np.zeros(GX.shape, bool)
    for ring in rings:
        r = np.asarray(ring, float); hit = np.zeros(GX.shape, bool)
        for k in range(len(r)):
            (x1, z1), (x2, z2) = r[k], r[k - 1]
            cross = (z1 > GZ) != (z2 > GZ)
            with np.errstate(divide="ignore", invalid="ignore"):
                hit ^= cross & (GX < (x2 - x1) * (GZ - z1) / (z2 - z1) + x1)
        m ^= hit
    return m


water = np.zeros(GX.shape, bool); ponds = 0
for L in lands:   # 3. ponds: one flat water level, banks eased down to it over ~15 m
    if L["k"] != "water": continue
    m = mask_of(L["r"])
    if m.sum() < 3: continue
    level = float(np.percentile(g[m], 25)); g[m] = level - .6
    ring = m.copy()
    for d in range(1, 4):
        grown = ring | np.roll(ring, 1, 0) | np.roll(ring, -1, 0) | np.roll(ring, 1, 1) | np.roll(ring, -1, 1)
        edge = grown & ~ring; t = d / 3; t = t * t * (3 - 2 * t)
        g[edge] = np.minimum(g[edge], level + (g[edge] - level) * t); ring = grown
    water |= m; ponds += 1
print(f"terrain: spikes flattened {spikes}, ponds levelled {ponds}, {g.min():.0f}-{g.max():.0f} m")

# ---------------- trees: OSM has few single trees here, so plant woods and parks
rnd = random.Random(7)
for L in lands:
    if L["k"] not in ("wood", "park"): continue
    spacing = 7 if L["k"] == "wood" else 13
    for r in L["r"]:
        xs = [p[0] for p in r]; zs = [p[1] for p in r]
        for _ in range(min(int(abs(area2(r)) / spacing ** 2), 2500)):
            p = [rnd.uniform(min(xs), max(xs)), rnd.uniform(min(zs), max(zs))]
            if inside(p, r): trees.append([round(p[0], 1), round(p[1], 1), round(rnd.uniform(.8, 1.3), 2)])


def blocked(p):
    j, i = int(round((p[0] - tx0) / STEP)), int(round((p[1] - tz0) / STEP))
    if 0 <= i < nz and 0 <= j < nx and water[i, j]: return True
    for b in buildings:
        x0, x1, z0, z1 = bbox(b)
        if x0 <= p[0] <= x1 and z0 <= p[1] <= z1 and inside(p[:2], b["o"]): return True
    return False
trees = [t for t in trees if not blocked(t)][:6000]

data = {"meta": {"lat": lat0, "lon": lon0},
        "terrain": {"x0": tx0, "z0": tz0, "step": STEP, "nx": nx, "nz": nz, "dm": [int(round(v * 10)) for v in g.flatten()]},
        "campus": campus, "buildings": buildings, "roads": roads, "lands": lands, "trees": trees, "config": CONFIG}
with open(OUT, "w", encoding="utf-8") as f:
    f.write("// 충북대학교 3D 데이터: 건물·도로·녹지 © OpenStreetMap 기여자(ODbL), 고도 AWS Terrain Tiles(SRTM 기반)\n")
    f.write("window.CBNU=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
named = sum(1 for b in buildings if b.get("n") and b["c"])
print(f"buildings {len(buildings)} (campus {sum(b['c'] for b in buildings)}, named {named}, with floors {sum('l' in b for b in buildings)}), "
      f"roads {len(roads)}, lands {len(lands)}, trees {len(trees)}, {os.path.getsize(OUT) // 1024} KB")
