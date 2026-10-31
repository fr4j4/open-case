"""Draws the signatures of a case as pen strokes and writes them in cases/<case>/signatures.yaml.

    python3 tools/signatures.py CASE                     draw the signers that have no strokes yet
    python3 tools/signatures.py CASE --redo J [--seed 2] draw J again (another seed gives another signature)
    python3 tools/signatures.py CASE --preview out.html  a page with every signature of the case, to look at them

A signer is the `signer:` of an item of a ```signature block in the sheets; the name the signature is drawn
from is that item's `scrawl:` (the text the handwriting font prints when there are no strokes). Each
signature is a few strokes of a ballpoint pen, as SVG path data, so the case keeps them as data and the
author can retouch or replace them (a signature drawn in a vector editor works too: copy its paths).

The shape comes from a family of hand movements (a flowing name, a scribble, zig-zags, a wave...). Within
a case the families are handed out without repeating, in the order of the file, until they run out; the
size, slant and details come from the name and the seed. Nothing here runs when the case is exported: the
exporter only reads signatures.yaml, so a signature never changes unless it is drawn again.
"""
import argparse
import hashlib
import math
import random
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

HEIGHT = 40          # every signature is fitted to this height (the viewBox units); the width follows
PAD = 3
HEADER = """\
# Signatures of the case: the pen strokes of each person who signs a sheet (neutral, the same in every
# language). A ```signature block uses them with `signer: <id>`; a signer with no strokes here is printed
# with the handwriting font (its `scrawl:`). Each stroke is SVG path data in a box of `viewbox`, drawn
# with a pen `width` units thick. Drawn with tools/signatures.py; retouch them by hand if you like.
# Format reference: docs/case-format.md ("signatures.yaml").
"""


def _hash(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest(), 16)


# --- Hand movements ---------------------------------------------------------------------------------
# Each family takes a random generator, the person's name and a size, and returns a list of strokes; a
# stroke is a list of points (y grows downwards, the baseline is y = 0) that the pen goes through, or
# ("dot", x, y) for a dot.

def _surname(name):
    p = name.replace(".", " ").split()
    return p[-2] if len(p) >= 3 else p[-1]


ASC, DESC = set("bdfhklt"), set("gjpqyz")


def flow(r, name, s):
    """A big initial and the surname as a run of arches that follow its tall and deep letters."""
    pts = [(0, 0), (s * .3, -s * .95), (s * .55, 0)]
    x = s * .55
    for ch in _surname(name).lower()[:r.choice([4, 5, 6])]:
        dx = r.uniform(.28, .45) * s
        tall = 1.0 if ch in ASC else .42
        pts += [(x + dx * .4, -tall * s * .55 * r.uniform(.8, 1.1)), (x + dx, (s * .4 if ch in DESC else 0))]
        x += dx
    pts.append((x + s * .5, -s * .2))
    return [pts]


def scribble(r, name, s):
    """An initial with a loop, then a fast, tight scribble."""
    first = [(0, 0), (s * .2, -s), (s * .5, -s * .2), (s * .1, -s * .1), (s * .35, s * .05)]
    x, run = s * .45, [(s * .35, 0)]
    for i in range(r.randint(9, 13)):
        x += r.uniform(.12, .2) * s
        run.append((x, (-1) ** i * r.uniform(.08, .22) * s))
    run.append((x + s * .55, -s * .3))
    return [first, run]


def zigzag(r, name, s):
    """Sharp up and down strokes, crossed by a bar."""
    pts, x = [(0, s * .2), (s * .15, -s)], s * .15
    for i in range(max(5, min(8, len(_surname(name))))):
        x += r.uniform(.15, .28) * s
        pts.append((x, -r.uniform(.35, .95) * s if i % 2 == 0 else r.uniform(.0, .25) * s))
    bar = [(-s * .2, -s * .35), (x * .5, -s * .42), (x + s * .4, -s * .45)]
    return [("sharp", pts), bar]


def wave(r, name, s):
    """A rising wave that ends in a flick upwards, over a short line."""
    length, rise = r.uniform(3.0, 3.8) * s, r.uniform(.22, .34)
    pts = [(0, 0)]
    for i in range(1, 9):
        u = i / 8
        pts.append((u * length, -rise * u * length + (-1) ** i * s * r.uniform(.18, .32)))
    pts.append((length * 1.02, -rise * length - s * .8))
    return [pts, [(s * .2, s * .25), (length * .65, s * .2)]]


def compact(r, name, s):
    """Short and quick: three humps, a line under them and a dot."""
    s *= .8
    pts = [(0, 0), (s * .25, -s), (s * .5, 0), (s * .8, -s * .5), (s * 1.1, 0), (s * 1.4, -s * .3), (s * 1.75, s * .03)]
    return [pts, [(s * .1, s * .38), (s * 1.5, s * .32)], ("dot", s * 1.95, s * .3)]


def crossbar(r, name, s):
    """Thin loops along the line, all crossed at mid height."""
    pts, x = [(0, 0)], 0
    for i in range(max(4, min(7, len(_surname(name)) - 1))):
        dx, h = r.uniform(.24, .38) * s, s * r.uniform(.35, 1.0)
        pts += [(x + dx * .4, -h), (x + dx * .5, -h * .3), (x + dx, r.uniform(-.04, .06) * s)]
        x += dx
    return [pts, [(-s * .4, -s * .6), (x * .5, -s * .56), (x + s * .8, -s * .7)]]


def loops(r, name, s):
    """An initial with a closed loop and a long tail that curls back under the name."""
    h = s * 1.05
    first = [(h * .5, -h * .75), (h * .15, -h * .5), (h * .3, -h * .08), (h * .7, -h * .2), (h * .7, -h * .8),
             (h * .4, -h * .98), (h * .15, -h * .75), (h * .55, -h * .1), (h * 1.0, -h * .05)]
    x, tail = h, [(h, -h * .05)]
    for i in range(r.randint(3, 5)):
        x += r.uniform(.3, .45) * s
        tail += [(x - s * .12, -s * r.uniform(.35, .6)), (x, 0)]
    tail += [(x + s * .5, -s * .1), (x + s * .3, s * .45), (s * .4, s * .35), (s * .1, s * .2)]
    return [first, tail]


def tall(r, name, s):
    """Two or three tall strokes like big capitals, then a low run and a bar on top."""
    strokes, x = [], 0
    for i in range(r.randint(2, 3)):
        h = s * r.uniform(1.3, 1.7)
        strokes.append([(x, 0), (x + s * .08, -h * .55), (x + s * .15, -h), (x + s * .1, -h * .45),
                        (x + s * .3, s * .1)])
        x += r.uniform(.35, .5) * s
    run = [(x, 0)]
    for i in range(r.randint(3, 5)):
        x += r.uniform(.2, .3) * s
        run += [(x - s * .1, -s * .38), (x, 0)]
    run.append((x + s * .4, -s * .15))
    strokes.append(run)
    strokes.append([(-s * .3, -s * 1.15), (x * .6, -s * 1.25), (x + s * .2, -s * 1.05)])
    return strokes


FAMILIES = {"flow": flow, "scribble": scribble, "zigzag": zigzag, "wave": wave, "compact": compact,
            "crossbar": crossbar, "loops": loops, "tall": tall}
FLOURISHES = ("underline", "double", "dot", "none")
LINED = {"zigzag", "wave", "compact", "crossbar", "tall"}     # they already cross or underline themselves


def flourish(r, strokes, s, kind):
    pts = [p for st in strokes if isinstance(st, list) for p in st]
    x0, x1, low = min(p[0] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)
    y = low + s * r.uniform(.25, .45)
    if kind == "underline":
        return [[(x1, y - s * .5), (x1 - s * .6, y), ((x0 + x1) / 2, y + s * .05), (x0 + s * .2, y - s * .08)]]
    if kind == "double":
        return [[(x0, y), ((x0 + x1) / 2, y - s * .08), (x1, y - s * .04)],
                [(x1 - s * .2, y + s * .2), ((x0 + x1) / 2, y + s * .16), (x0 + s * .4, y + s * .28)]]
    if kind == "dot":
        return [("dot", x1 + s * .35, y - s * .3)]
    return []


# --- From points to SVG path data -------------------------------------------------------------------

def _bezier(pts):
    """A smooth curve through the points: Catmull-Rom turned into cubic Béziers (one C per point)."""
    if len(pts) == 2:
        return [("L", pts[1])]
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(("C", c1, c2, p2))
    return out


def _num(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def draw(name, seed=1, family=None):
    """(family, width, viewbox, [path data, ...]) of a signature."""
    r = random.Random(_hash(name, seed))
    family = family or r.choice(list(FAMILIES))
    s = r.uniform(26, 34)
    strokes = FAMILIES[family](random.Random(_hash(name, seed, family)), name, s)
    kinds = ("dot", "none") if family in LINED else FLOURISHES
    strokes = list(strokes) + flourish(r, strokes, s, r.choice(kinds))
    slant = r.uniform(.1, .5)
    tremble = random.Random(_hash(name, seed, "pulse"))
    shapes = []        # (kind, points) with the slant and a little tremble of the hand
    for st in strokes:
        if isinstance(st, tuple) and st[0] == "dot":
            shapes.append(("dot", [(st[1] - slant * st[2], st[2])]))
            continue
        kind, pts = st if isinstance(st, tuple) else ("smooth", st)
        pts = [(x - slant * y + tremble.uniform(-.4, .4), y + tremble.uniform(-.4, .4)) for x, y in pts]
        shapes.append((kind, pts))
    xs = [x for _, pts in shapes for x, _ in pts]
    ys = [y for _, pts in shapes for _, y in pts]
    k = (HEIGHT - 2 * PAD) / ((max(ys) - min(ys)) or 1)
    ox, oy = min(xs) - PAD / k, min(ys) - PAD / k
    paths = []
    for kind, pts in shapes:
        pts = [((x - ox) * k, (y - oy) * k) for x, y in pts]
        if kind == "dot":
            x, y = pts[0]
            paths.append(f"M{_num(x)} {_num(y)}h0.6")
            continue
        segs = [("L", p) for p in pts[1:]] if kind == "sharp" else _bezier(pts)
        d = f"M{_num(pts[0][0])} {_num(pts[0][1])}"
        for seg in segs:
            d += seg[0] + " ".join(f"{_num(a)} {_num(b)}" for a, b in seg[1:])
        paths.append(d)
    width = math.ceil((max(xs) - ox) * k + PAD)
    return family, round(r.uniform(1.3, 1.8), 1), f"0 0 {width} {HEIGHT}", paths


# --- The case ---------------------------------------------------------------------------------------

def signers(case_root):
    """{signer: name} of the ```signature blocks of every language, in the order they appear."""
    from opencase.loader import case_languages, load_case
    out = {}
    for lang in case_languages(case_root)[1]:
        case = load_case(case_root, lang)
        for sheet in case.kit + list(case.dossier.values()) + case.guide:
            for b in sheet.blocks:
                if b.type != "signature":
                    continue
                for it in yaml.safe_load(b.content) or []:
                    if isinstance(it, dict) and it.get("signer"):
                        out.setdefault(str(it["signer"]), str(it.get("scrawl") or it["signer"]))
    return out


def write(path, data):
    lines = [HEADER, "signatures:"]
    for sid, sig in data.items():
        lines.append(f"  {_key(sid)}:")
        for key in ("name", "family", "seed", "width", "viewbox"):
            if key in sig:
                lines.append(f"    {key}: {_scalar(sig[key])}")
        lines.append("    strokes:")
        lines += [f'      - "{d}"' for d in sig["strokes"]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _key(k):
    return k if re.fullmatch(r"[A-Za-z][\w-]*", k) and k.lower() not in ("y", "n", "yes", "no", "on", "off") else f'"{k}"'


def _scalar(v):
    return str(v) if isinstance(v, (int, float)) else f'"{v}"' if re.search(r"[:#]", str(v)) else str(v)


def preview(path, data):
    rows = "".join(
        f'<figure><svg viewBox="{s["viewbox"]}" style="height:44px"><g fill="none" stroke="#1f3b75" '
        f'stroke-width="{s.get("width", 1.5)}" stroke-linecap="round" stroke-linejoin="round">'
        + "".join(f'<path d="{d}"/>' for d in s["strokes"])
        + f'</g></svg><figcaption>{sid} · {s.get("name", "")} · {s.get("family", "")} {s.get("seed", "")}'
        f'</figcaption></figure>' for sid, s in data.items())
    Path(path).write_text(
        '<!doctype html><meta charset="utf-8"><style>body{font:13px sans-serif;background:#f7f5ef;display:flex;'
        'flex-wrap:wrap;gap:16px;padding:16px}figure{margin:0;padding:12px;background:#fff;border:1px solid #ddd}'
        '</style>' + rows, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("case", help="the case folder, e.g. cases/chupacabras-labranza")
    ap.add_argument("--redo", action="append", default=[], metavar="ID", help="draw this signer again")
    ap.add_argument("--seed", type=int, help="seed for --redo (default: the next one)")
    ap.add_argument("--family", choices=sorted(FAMILIES), help="hand movement for --redo")
    ap.add_argument("--preview", metavar="HTML", help="write a page with every signature of the case")
    args = ap.parse_args(argv)
    root = Path(args.case).resolve()
    path = root / "signatures.yaml"
    data = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("signatures", {}) if path.exists() else {}
    data = {str(k): v for k, v in (data or {}).items()}
    wanted = signers(root)
    changed = []
    for sid in args.redo:
        if sid not in data and sid not in wanted:
            sys.exit(f"'{sid}' signs no sheet of the case and has no strokes in signatures.yaml")
    case_seed = _hash(root.name)
    order = sorted(FAMILIES, key=lambda f: _hash(case_seed, f))
    for sid, name in wanted.items():
        if sid in data and sid not in args.redo:
            continue
        old = data.get(sid, {})
        seed = args.seed or (int(old.get("seed", 0)) + 1 if sid in args.redo else 1)
        used = [s.get("family") for k, s in data.items() if k != sid]
        family = args.family if sid in args.redo and args.family else next(
            (f for f in order if f not in used), order[len(used) % len(order)])
        family, width, viewbox, strokes = draw(old.get("name", name), seed, family)
        data[sid] = {"name": old.get("name", name), "family": family, "seed": seed, "width": width,
                     "viewbox": viewbox, "strokes": strokes}
        changed.append(sid)
    if changed:
        write(path, data)
        print(f"{path.relative_to(Path.cwd()) if path.is_relative_to(Path.cwd()) else path}: drew {', '.join(changed)}")
    else:
        print("every signer already has strokes (use --redo ID to draw one again)")
    unused = [k for k in data if k not in wanted]
    if unused:
        print(f"note: {', '.join(unused)} sign no sheet")
    if args.preview:
        preview(args.preview, data)
        print(f"preview: {args.preview}")


if __name__ == "__main__":
    main()
