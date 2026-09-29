"""Build the Jetis Luna twin from source-derived site and warehouse dimensions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web/dist/assets/scene.json"
elements, motions, lights, labels = [], [], [], []
materials = {
    "concrete": {"color": "#b5b4aa", "roughness": .84, "texture": "Concrete034", "tile": 3.0},
    "asphalt": {"color": "#737c7a", "roughness": .92, "texture": "Asphalt012", "tile": 5.0},
    "galvalume": {"color": "#bac6c7", "roughness": .43, "metalness": .32, "texture": "Metal032", "tile": 2.4},
    "steel": {"color": "#344a55", "roughness": .48, "metalness": .48},
    "door": {"color": "#7c8d8d", "roughness": .56, "metalness": .18, "texture": "Metal032", "tile": 1.8},
    "glass": {"color": "#88b7c0", "roughness": .2, "metalness": .08, "opacity": .32},
    "paint": {"color": "#e4dfd2", "roughness": .68},
    "roadmark": {"color": "#e5d89e", "roughness": .78},
    "fence": {"color": "#59676b", "roughness": .56, "metalness": .32},
    "green": {"color": "#71836a", "roughness": .96},
    "water": {"color": "#527f86", "roughness": .24, "metalness": .06},
    "light": {"color": "#f9e8bb", "roughness": .3, "emissive": "#ffca72"},
}

def add(kind, name, group, mat, **props):
    e = {"id": f"jetis-{len(elements)+1:05d}", "kind": kind, "name": name,
         "group": group, "mat": mat, **props}
    elements.append(e)
    return e

def box(name, group, mat, p, s, collision=None, **extra):
    q = {"p": [round(x, 4) for x in p], "s": [round(x, 4) for x in s], **extra}
    if collision: q["collision"] = collision
    return add("box", name, group, mat, **q)

def beam(name, group, mat, a, b, w, h, kind="wf", tw=None, tf=None):
    q = {"a": [round(x, 4) for x in a], "b": [round(x, 4) for x in b], "w": w, "h": h}
    if kind != "beam": q.update(tw=tw or w*.35, tf=tf or h*.12)
    return add(kind, name, group, mat, **q)

def prism(name, group, mat, points, thickness):
    return add("prism", name, group, mat,
               points=[[round(x, 4) for x in p] for p in points], th=thickness)

def panel_on_side(name, group, mat, xa, xb, y, z, depth, height, collision="wall"):
    return box(name, group, mat, (xa, y-depth/2, z), (xb-xa, depth, height), collision)

# Source origin [2300,1600,0]. Boundary points come from layout handle 16551.
# The long site road is visible south of the layout; planting fills only its plot.
box("Lantai area tapak", "Tapak", "green", (-93, -75, -.22), (161, 149, .22), "floor")
box("Pelataran akses utama", "Tapak", "asphalt", (-73, -78, -.08), (137, 18, .08), "floor")
box("Jalan depan Jetis", "Tapak", "asphalt", (-57, -91, -.08), (112, 7, .08), "floor")
box("Apron gudang tahap 1", "Tapak", "concrete", (-69, -48, -.10), (132, 69, .10), "floor")
box("Apron gudang tahap 2", "Tapak", "concrete", (-45, 32, -.10), (96, 40, .10), "floor")
for i in range(8):
    box(f"Marka parkir luar {i+1}", "Tapak", "roadmark", (32+i*4.2, -71.6, .006), (.12, 7.4, .012))

# Site boundary, from the closed return of source polyline handle 16551.
boundary = [(-70.89, 61.00), (-42.61, 58.43), (-41.32, 74.37),
            (48.45, 67.97), (59.21, 25.10), (53.59, 25.33),
            (68.10, -62.88), (54.70, -64.82), (-4.95, -74.69),
            (-4.03, -67.27), (-92.03, -67.27), (-70.89, 61.00)]
for i, (a, b) in enumerate(zip(boundary, boundary[1:])):
    beam(f"Pagar batas tapak {i+1}", "Tapak", "fence", (a[0], a[1], .2),
         (b[0], b[1], .2), .08, 1.8, kind="beam")
    beam(f"Top rail pagar {i+1}", "Tapak", "fence", (a[0], a[1], 1.9),
         (b[0], b[1], 1.9), .05, .05, kind="beam")
# Gate opening is retained on the south access edge near the labelled gate and post.
box("Pos jaga Jetis", "Eksterior", "paint", (3.8, -70.2, 0), (3.8, 3.4, 3.1), "wall")
box("Pintu pos jaga", "Eksterior", "door", (4.8, -70.31, 0), (.9, .12, 2.1), "none")
box("Kanopi pos jaga", "Eksterior", "galvalume", (3.2, -70.8, 3.05), (5, 4.4, .12))
for side in [-1, 1]:
    x = 15 + side*2.9
    beam(f"Tiang gerbang {side}", "Tapak", "fence", (x, -67.2, 0), (x, -67.2, 2.8), .12, .12, kind="beam")
    box(f"Daun gerbang {side}", "Tapak", "fence", (x if side < 0 else x-2.7, -67.3, .2), (2.7, .12, 1.7))

buildings = [
    {"key":"t1-36-row-a", "name":"Gudang Tahap 1 · 30 × 36 m (baris A)", "x":-62.62, "y":-13.45, "length":36, "stage":"TAHAP 1", "size":"30 × 36 m"},
    {"key":"t1-36-row-b", "name":"Gudang Tahap 1 · 30 × 36 m (baris B)", "x":-62.62, "y":-43.45, "length":36, "stage":"TAHAP 1", "size":"30 × 36 m"},
    {"key":"t1-84-row-b", "name":"Gudang Tahap 1 · 30 × 84 m (baris B)", "x":-26.62, "y":-43.45, "length":84, "stage":"TAHAP 1", "size":"30 × 84 m"},
    {"key":"t1-78-row-a", "name":"Gudang Tahap 1 · 30 × 78 m (baris A)", "x":-26.62, "y":-13.45, "length":78, "stage":"TAHAP 1", "size":"30 × 78 m"},
    {"key":"t2-42-module-a", "name":"Gudang Tahap 2 · modul 30 × 42 m (A)", "x":-38.62, "y":36.55, "length":42, "stage":"TAHAP 2", "size":"30 × 42 m"},
    {"key":"t2-42-module-b", "name":"Gudang Tahap 2 · modul 30 × 42 m (B)", "x":3.38, "y":36.55, "length":42, "stage":"TAHAP 2", "size":"30 × 42 m"},
]

def add_warehouse(b):
    x, y, length, width = b["x"], b["y"], b["length"], 30.0
    eave, ridge, wall_t = 9.0, 13.5, .12
    x1, y1 = x+length, y+width
    mid_y, xmid = y+width/2, x+length/2
    prefix = b["key"]
    # Source floor and an open interior; the drawing does not specify process equipment.
    floor_z = 1.0  # section markers put LANTAI 1 at +1.00 above site datum ±0.00
    box(f"Pelat lantai {prefix}", "Interior", "concrete", (x, y, floor_z-.18), (length, width, .18), "floor")
    # Steel frame at 6 m centres, with columns, tie beam, rafters and web members.
    xs = [x + 6*i for i in range(round(length/6)+1)]
    for ix, xx in enumerate(xs):
        for side, yy in [("selatan", y+.18), ("utara", y1-.18)]:
            beam(f"Kolom WF350 {prefix} {side} grid {ix+1}", "Struktur", "steel",
                 (xx, yy, 0), (xx, yy, eave), .35, .35, "wf", .18, .022)
        beam(f"Ikatan bawah rangka {prefix} grid {ix+1}", "Struktur", "steel",
             (xx, y, 8.72), (xx, y1, 8.72), .24, .30, "wf", .14, .018)
        beam(f"Kuda-kuda WF300 {prefix} selatan grid {ix+1}", "Struktur", "steel",
             (xx, y, eave), (xx, mid_y, ridge), .30, .30, "wf", .16, .021)
        beam(f"Kuda-kuda WF300 {prefix} utara grid {ix+1}", "Struktur", "steel",
             (xx, mid_y, ridge), (xx, y1, eave), .30, .30, "wf", .16, .021)
        # Webs are lightweight representation of the source truss drawing.
        for k in range(1, 5):
            yy = y + k*width/5
            rz = eave + (width/2-abs(yy-mid_y))*4.5/(width/2)
            beam(f"Web rangka {prefix} {ix+1}-{k}", "Struktur", "steel",
                 (xx, yy, 8.72), (xx, yy, rz), .09, .10, "beam")
    # Longitudinal eave beams and ridge.
    for yy, zz, name in [(y, eave, "ring balok selatan"), (y1, eave, "ring balok utara"), (mid_y, ridge, "balok nok")]:
        beam(f"{name} {prefix}", "Struktur", "steel", (x, yy, zz), (x1, yy, zz), .30, .30, "wf", .16, .021)
    # CNP purlins and two continuous galvalume roof planes.
    for k in range(1, 10):
        yy = y + k*width/10
        zz = eave + (width/2-abs(yy-mid_y))*4.5/(width/2)
        beam(f"Gording CNP125 {prefix} {k}", "Struktur", "steel", (x-.8, yy, zz), (x1+.8, yy, zz), .125, .05, "cnp", .004, .008)
    for side, ya, yb in [("selatan", y-.35, mid_y), ("utara", mid_y, y1+.35)]:
        za = eave + max(0, (ya-y if ya<y else y1-ya))*.3
        roofedge = (eave if side == "selatan" else eave)
        # The roof panel is a shallow prism in the source slope plane.
        if side == "selatan": pts=[(x-.8,ya,roofedge),(x1+.8,ya,roofedge),(x1+.8,mid_y,ridge),(x-.8,mid_y,ridge)]
        else: pts=[(x-.8,mid_y,ridge),(x1+.8,mid_y,ridge),(x1+.8,yb,eave),(x-.8,yb,eave)]
        prism(f"Atap galvalume {prefix} {side}", "Atap", "galvalume", pts, .045)
    # Infer a 4.8 m roller shutter in a clear 6 m bay; the DWG has no door schedule.
    door_w, door_h = 4.8, 5.8
    door_x = xmid + (3.0 if abs((length/2) % 6.0) < 1e-6 else 0.0)
    door_l, door_r = door_x-door_w/2, door_x+door_w/2
    door_side = b.get("door_side", "selatan")
    door_y = y1 if door_side == "utara" else y
    bay_edges = sorted(set([x, x1] + [min(x1, x+6*i) for i in range(1, round(length/6)+1)]))
    for side, yy in [("selatan", y), ("utara", y1)]:
        for a, c in zip(bay_edges, bay_edges[1:]):
            ranges=[(a,c)]
            if side==door_side and a<door_r and c>door_l:
                ranges=[]
                if a<door_l:ranges.append((a,door_l))
                if c>door_r:ranges.append((door_r,c))
            for m, (pa,pb) in enumerate(ranges):
                panel_on_side(f"Dinding metal {prefix} {side} {pa:.0f}", "Eksterior", "galvalume", pa,pb,yy,floor_z,wall_t,6.5-floor_z)
                box(f"Kaca clerestory {prefix} {side} {pa:.0f}", "Eksterior", "glass",
                    (pa, yy-wall_t/2, 6.5), (pb-pa, wall_t, 1.6))
                panel_on_side(f"Lis atas dinding {prefix} {side} {pa:.0f}", "Eksterior", "galvalume", pa,pb,yy,8.1,wall_t,.9)
    # Gable end walls are source-derived clear-span envelopes.
    for xx, end in [(x, "barat"), (x1, "timur")]:
        prism(f"Dinding gevel {prefix} {end}", "Eksterior", "galvalume",
              [(xx-wall_t/2,y,floor_z),(xx-wall_t/2,y1,floor_z),(xx-wall_t/2,y1,eave),
               (xx-wall_t/2,mid_y,ridge),(xx-wall_t/2,y,eave)], wall_t)
    # A roller shutter raises above the opening and keeps the 6 m column grid clear.
    motion_id=f"pintu-{prefix}"
    door_bounds=[door_l,door_y-wall_t/2-.02,floor_z,door_w,wall_t,door_h]
    motions.append({"id":motion_id,"label":f"Buka pintu {b['stage'].lower()} {b['size']}","kind":"roll",
                    "bounds":door_bounds,"anchor":[door_x,door_y,0],"travel":door_h+.25,
                    "top":floor_z+door_h+.25})
    box(f"Pintu gulung {prefix}", "Eksterior", "door", (door_l,door_y-wall_t/2-.02,floor_z), (door_w,wall_t,door_h), "none", motion=motion_id)
    beam(f"Rel pintu {prefix}", "Eksterior", "steel", (door_l-.25,door_y,door_h+floor_z+.12), (door_r+.25,door_y,door_h+floor_z+.12), .09, .12, "beam")
    # Five shallow step solids link the grade datum to the +1.00 finished floor.
    for j in range(5):
        top = floor_z*(j+1)/5
        box(f"Anak tangga {prefix} {j+1}", "Eksterior", "concrete",
            (door_x-door_w/2, door_y-(5-j)*.78 if door_side=="selatan" else door_y+(5-j)*.78-.78, 0), (door_w, .78, top), "floor")
    # Repeated highbay lights: placement is an explicitly logged visualization assumption.
    for i in range(1, round(length/12)):
        lights.append({"p":[x+i*12,mid_y,8.4],"color":"#ffe4b1","intensity":125,"distance":18})
    labels.append({"text":b["stage"]+" · "+b["size"],"p":[xmid,mid_y,ridge+1.0]})

for building in buildings:
    if building["key"] in ("t1-36-row-a", "t1-78-row-a"):
        building["door_side"]="utara"
    add_warehouse(building)

drawing = json.loads((ROOT / "analysis/flat.json").read_text(encoding="utf-8"))
source_annotations = [
    {"handle":e["source"],"text":e.get("text",""),"position_source":e.get("position")}
    for e in drawing["texts"]
]
source_dimensions = [
    {"handle":e["source"],"measurement":e.get("measurement"),"text":e.get("text",""),
     "position_source":e.get("textPosition")}
    for e in drawing["dimensions"]
]
spec = json.loads((ROOT / "analysis/spec.json").read_text(encoding="utf-8"))
data = {
    "units":"metres", "materials":materials, "elements":elements, "labels":labels,
    "source_origin":[2300,1600,0], "source_annotations":source_annotations,
    "source_dimensions":source_dimensions, "key_source_annotations":spec["source_annotations"],
    "lights":lights, "motions":motions,
    "footprints":[{"id":b["key"],"stage":b["stage"],"size":b["size"],
                    "bounds":[b["x"],b["y"],b["x"]+b["length"],b["y"]+30]} for b in buildings],
    "assumptions":[
        "Satu unit gambar = 1 m; cocok dengan bentang 6 m dan label 30 × 78 m pada DWG.",
        "Asal koordinat model [2300,1600,0] m; tanda utara handle 165A6 menunjuk ke +X gambar.",
        "Dimensi kanopi atap mengikuti outline tapak; garis rangka utama memakai bentang label dan grid 6 m.",
        "Tahap 2 digambar sebagai dua modul 30 × 42 m: dua label tahap 2 berada pada dua bagian sama besar dari outline 30 × 84 m.",
        "Elevasi model mengikuti datum DWG: grade ±0,00; lantai 1 +1,00; lis +9,00; nok +13,50 m.",
        "Dinding metal, kaca clerestory, slab, pos, pagar, marka, serta pintu gulung 4.8 m divisualisasikan; pintu dan mekanismenya tidak dirinci pada DWG.",
        "Pintu modul tahap 1 baris A berada di sisi utara dan baris B di sisi selatan; posisi bergeser ke tengah bay agar kolom 6 m tetap bebas.",
        "Interior gudang dibiarkan lapang karena DWG tidak menunjukkan mesin pengolahan atau tata letak produksi.",
        "Kolom WF350, kuda-kuda WF300 dan gording CNP125 mengikuti catatan DWG; ukuran sambungan tidak dimodelkan sebagai gambar fabrikasi.",
        "Model visual ini bukan persetujuan struktur atau dokumen fabrikasi."
    ]
}
OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"elements":len(elements),"motions":len(motions),"lights":len(lights),"footprints":len(buildings),"file":str(OUT)}))
