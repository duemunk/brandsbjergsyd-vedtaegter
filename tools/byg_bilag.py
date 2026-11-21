import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VEJE = ["Brandsbjergvej", "Ejbydalsvej", "Ejby Mosevej", "Mosetoften"]
VEJTYPER = {"tertiary", "residential", "unclassified"}
HOVEDSTRAEK_UDENFOR = {"Ejby Mosevej", "Mosetoften"}
MARGEN_I_M = 110
BREDDE = 1000
PAD = 16

parcel_kilde = Path(sys.argv[1]).read_text()
osm = ET.parse(sys.argv[2]).getroot()
ud = Path(sys.argv[3])

fund = re.search(r"var PARCELLER\s*=\s*(\[.*?\]);\s*var OMRAADE\s*=\s*(\[.*?\]);", parcel_kilde, re.S)
parceller = json.loads(fund.group(1))
omraade = json.loads(fund.group(2))

lat0 = 55.7005
lon0 = 12.4126
kx = math.cos(math.radians(lat0)) * 111320
ky = 110574


def meter(c):
    return (c[0] - lon0) * kx, (lat0 - c[1]) * ky


noder = {n.get("id"): (float(n.get("lon")), float(n.get("lat"))) for n in osm.iter("node")}
veje_by_navn = {navn: [] for navn in VEJE}
for w in osm.iter("way"):
    tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
    if tags.get("name") in veje_by_navn and tags.get("highway") in VEJTYPER:
        punkter = [noder[nd.get("ref")] for nd in w.iter("nd") if nd.get("ref") in noder]
        veje_by_navn[tags["name"]].append((tags["highway"], punkter))

omr_m = [meter(c) for c in omraade]
minx = min(x for x, _ in omr_m) - MARGEN_I_M
maxx = max(x for x, _ in omr_m) + MARGEN_I_M
miny = min(y for _, y in omr_m) - MARGEN_I_M
maxy = max(y for _, y in omr_m) + MARGEN_I_M
skala = (BREDDE - 2 * PAD) / (maxx - minx)
hoejde = round((maxy - miny) * skala + 2 * PAD)


def P(c):
    x, y = meter(c)
    return (x - minx) * skala + PAD, (y - miny) * skala + PAD


def sti(ringe):
    return "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in map(P, r)) + "Z" for r in ringe)


def linje(punkter):
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in map(P, punkter))


def _ubrugt(punkter):
    stykker, aktuelt = [], []
    for c in punkter:
        x, y = P(c)
        if PAD + 20 <= x <= BREDDE - PAD - 20 and PAD + 20 <= y <= hoejde - PAD - 20:
            aktuelt.append(c)
        elif aktuelt:
            stykker.append(aktuelt)
            aktuelt = []
    if aktuelt:
        stykker.append(aktuelt)
    return max(stykker, key=laengde, default=[])


def laengde(punkter):
    pp = [P(c) for c in punkter]
    return sum(math.dist(a, b) for a, b in zip(pp, pp[1:]))


medlemmer = [p for p in parceller if p[1] in ("L", "N")]
ud_svg = [
    f'<svg class="bilag-kort" viewBox="0 0 {BREDDE} {hoejde}" role="img" aria-label="Kort over foreningens område med parceller og veje" xmlns="http://www.w3.org/2000/svg">',
    f'<defs><clipPath id="ramme"><rect x="{PAD}" y="{PAD}" width="{BREDDE - 2 * PAD}" height="{hoejde - 2 * PAD}"/></clipPath></defs>',
    f'<rect x="{PAD}" y="{PAD}" width="{BREDDE - 2 * PAD}" height="{hoejde - 2 * PAD}" fill="#f6f8f9"/>',
    '<g clip-path="url(#ramme)">',
    f'<path d="{sti([omraade])}" fill="#e9f6fa"/>',
]
for navn in VEJE:
    for vejtype, punkter in veje_by_navn[navn]:
        bredde_i_px = 9 if vejtype == "tertiary" else 6
        ud_svg.append(f'<path d="{linje(punkter)}" fill="none" stroke="#c9d3d7" stroke-width="{bredde_i_px + 2}" stroke-linecap="round" stroke-linejoin="round"/>')
for navn in VEJE:
    for vejtype, punkter in veje_by_navn[navn]:
        bredde_i_px = 9 if vejtype == "tertiary" else 6
        ud_svg.append(f'<path d="{linje(punkter)}" fill="none" stroke="#ffffff" stroke-width="{bredde_i_px}" stroke-linecap="round" stroke-linejoin="round"/>')
for p in medlemmer:
    ud_svg.append(f'<path d="{sti(p[2])}" fill="#ffffff" stroke="#a7bcc4" stroke-width="0.8"/>')
for p in parceller:
    if p[1] == "P":
        ud_svg.append(f'<path d="{sti(p[2])}" fill="#8e9ca2" fill-rule="evenodd"/>')
    if p[1] == "G":
        ud_svg.append(f'<path d="{sti(p[2])}" fill="#7fb38e"/>')
ud_svg.append(f'<path d="{sti([omraade])}" fill="none" stroke="#02add6" stroke-width="2.4" stroke-linejoin="round"/>')
for p in medlemmer:
    ring = [P(c) for c in p[2][0]]
    cx = sum(x for x, _ in ring) / len(ring)
    cy = sum(y for _, y in ring) / len(ring)
    ud_svg.append(f'<text x="{cx:.1f}" y="{cy + 2:.1f}" font-size="5.2" fill="#5b665e" text-anchor="middle">{p[0]}</text>')

def kaeder(veje):
    rester = [list(pp) for _, pp in veje]
    resultat = []
    while rester:
        kaede = rester.pop(0)
        fundet = True
        while fundet:
            fundet = False
            for k in rester:
                if k[0] == kaede[-1]: kaede += k[1:]
                elif k[-1] == kaede[-1]: kaede += list(reversed(k))[1:]
                elif k[-1] == kaede[0]: kaede = k[:-1] + kaede
                elif k[0] == kaede[0]: kaede = list(reversed(k))[:-1] + kaede
                else: continue
                rester.remove(k); fundet = True; break
        resultat.append(kaede)
    return resultat


def inde_i_omraadet(c):
    x, y = c
    inde = False
    for (x1, y1), (x2, y2) in zip(omraade, omraade[1:] + omraade[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inde = not inde
    return inde


def fortaet(punkter, skridt_i_m=4):
    ud = [punkter[0]]
    for a, b in zip(punkter, punkter[1:]):
        n = max(1, int(math.dist(meter(a), meter(b)) / skridt_i_m))
        ud += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return ud


def laengste_loeb(punkter, betingelse):
    punkter = fortaet(punkter)
    loeb, aktuelt = [], []
    for c in punkter:
        if betingelse(c):
            aktuelt.append(c)
        elif aktuelt:
            loeb.append(aktuelt); aktuelt = []
    if aktuelt:
        loeb.append(aktuelt)
    return max(loeb, key=laengde, default=[])


def synlig(c):
    x, y = P(c)
    return PAD + 20 <= x <= BREDDE - PAD - 20 and PAD + 20 <= y <= hoejde - PAD - 20


etiketter = []
for i, navn in enumerate(VEJE):
    alle_kaeder = kaeder(veje_by_navn[navn])
    inde = max((laengste_loeb(k, inde_i_omraadet) for k in alle_kaeder), key=laengde, default=[])
    stykke = inde if navn not in HOVEDSTRAEK_UDENFOR else max((laengste_loeb(k, synlig) for k in alle_kaeder), key=laengde, default=[])
    if len(stykke) < 2:
        continue
    if P(stykke[0])[0] > P(stykke[-1])[0]:
        stykke = list(reversed(stykke))
    ud_svg.append(f'<path id="vej-{i}" d="{linje(stykke)}" fill="none"/>')
    etiketter.append(
        f'<text font-size="13" font-weight="600" fill="#1b211d" stroke="#ffffff" stroke-width="4" paint-order="stroke" stroke-linejoin="round" letter-spacing="0.4">'
        f'<textPath href="#vej-{i}" startOffset="50%" text-anchor="middle">{navn}</textPath></text>'
    )
    print(navn, "inde" if stykke is inde else "ude", round(laengde(stykke)))
ud_svg.extend(etiketter)
ud_svg.append("</g>")

hundrede_m = 100 * skala
by = hoejde - PAD - 14
bx = PAD + 12
ud_svg.append(
    f'<g font-size="11" fill="#1b211d"><rect x="{bx}" y="{by}" width="{hundrede_m:.1f}" height="4" fill="#1b211d"/>'
    f'<text x="{bx}" y="{by - 5}">0</text><text x="{bx + hundrede_m:.1f}" y="{by - 5}" text-anchor="end">100 m</text></g>'
)
nx = BREDDE - PAD - 22
ny = hoejde - PAD - 40
ud_svg.append(
    f'<g fill="#1b211d"><path d="M{nx} {ny - 18} L{nx + 7} {ny + 4} L{nx} {ny} L{nx - 7} {ny + 4} Z"/>'
    f'<text x="{nx}" y="{ny + 20}" font-size="11" font-weight="600" text-anchor="middle">N</text></g>'
)
ud_svg.append("</svg>")


def sorteringsnoegle(matrikel):
    m = re.match(r"(\d+)(.*)", matrikel)
    return int(m.group(1)), len(m.group(2)), m.group(2)


matrikler = sorted({p[0] for p in medlemmer}, key=sorteringsnoegle)
bilag = {"kort": "\n".join(ud_svg), "matrikler": matrikler}
ud.write_text("window.BILAG = " + json.dumps(bilag, ensure_ascii=False) + ";\n")
print(f"{len(matrikler)} matrikler, kort {BREDDE}x{hoejde}, veje: " + ", ".join(f"{n} ({len(veje_by_navn[n])})" for n in VEJE))
