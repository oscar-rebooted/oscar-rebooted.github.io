#!/usr/bin/env python3
"""Generate static SVG charts for inside-neural-chameleon.html.
No external dependencies; writes SVGs into ai-safety/inside_neural_chameleon/.
"""

W = 600  # matches article max-width

INK = "#222222"
MUTED = "#888888"
BLUE = "#2f6fb2"
ORANGE = "#c46a1e"
GRID = "#dddddd"


def fmt(v, decimals=0):
    return f"{v:.{decimals}f}"


def svg_open(width, height):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="inherit" font-size="11">'
    )


def text(x, y, s, anchor="middle", size=11, fill=INK, weight=None, rotate=None):
    style = f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"'
    if weight:
        style += f' font-weight="{weight}"'
    tr = f' transform="rotate({rotate[0]} {rotate[1]} {rotate[2]})"' if rotate else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" {style}{tr}>{s}</text>'


def line(x1, y1, x2, y2, stroke=INK, width=1, dash=None, opacity=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' stroke-opacity="{opacity}"' if opacity else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{d}{o}/>'
    )


def circle(cx, cy, r, fill, stroke=None, sw=0, opacity=None):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    o = f' fill-opacity="{opacity}"' if opacity else ""
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"{s}{o}/>'


def path(d, fill, opacity=None, stroke=None, sw=0):
    o = f' fill-opacity="{opacity}"' if opacity else ""
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{o}{s}/>'


def polyline(points, stroke, width=2, fill="none"):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


# ---------------------------------------------------------------------------
# Chart 1: grouped recovery by number of top-ranked components transplanted
# ---------------------------------------------------------------------------

def grouped_recovery():
    # (k, discovery, validation); CIs omitted for clarity, points are tight
    discovery = [(1, 0.297368), (2, 0.485506), (4, 0.729256), (8, 0.856687),
                 (16, 0.926222), (32, 0.941642)]
    validation = [(1, 0.207629), (2, 0.287998), (4, 0.434750), (8, 0.599872),
                  (16, 0.819757), (32, 0.868632)]

    width, height = W, 300
    ml, mr, mt, mb = 58, 16, 30, 46
    pw, ph = width - ml - mr, height - mt - mb

    import math
    kmin, kmax = 1, 32
    def x(k):
        # log2 scale: k = 1,2,4,8,16,32 -> 0..5
        t = math.log2(k)
        return ml + (t / 5.0) * pw

    ymin, ymax = 0.0, 1.0
    def y(v):
        return mt + (ymax - v) / (ymax - ymin) * ph

    out = [svg_open(width, height)]

    # gridlines and y-axis labels
    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(line(ml, y(gv), ml + pw, y(gv), stroke=GRID, width=1))
        out.append(text(ml - 8, y(gv) + 4, f"{gv:.2f}".rstrip("0").rstrip(".") if gv not in (0, 1) else f"{gv:.0f}",
                        anchor="end", fill=MUTED))

    # x ticks at powers of two
    for k in (1, 2, 4, 8, 16, 32):
        out.append(text(x(k), mt + ph + 16, str(k), fill=MUTED))
        out.append(line(x(k), mt + ph, x(k), mt + ph + 4, stroke=MUTED))

    # frame
    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')

    # series
    for series, color in ((discovery, BLUE), (validation, ORANGE)):
        pts = [(x(k), y(v)) for k, v in series]
        out.append(polyline(pts, stroke=color, width=2))
        for px, py in pts:
            out.append(circle(px, py, 3.4, fill=color))

    # annotate K16 points
    out.append(line(x(16), y(0.926222), x(16), mt + ph, stroke=MUTED, width=1, dash="3,3"))
    out.append(text(x(16), mt - 8, "K16", fill=MUTED))

    # legend (lower right, inside plot)
    lx, ly = ml + pw - 205, mt + ph - 14
    out.append(circle(lx + 4, ly - 4, 3.4, BLUE))
    out.append(text(lx + 14, ly, "discovery", anchor="start", size=11))
    out.append(circle(lx + 92, ly - 4, 3.4, ORANGE))
    out.append(text(lx + 102, ly, "held-out validation", anchor="start", size=11))

    # axis titles
    out.append(text(ml + pw / 2, height - 8, "components transplanted together (ranked top-k)"))
    out.append(text(14, mt + ph / 2, "recovery of monitor effect", rotate=(-90, 14, mt + ph / 2)))

    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Chart 2: complete K12 rerouting, same-layer vs cross-layer arrangements
# ---------------------------------------------------------------------------

def rerouting():
    within = [16.6095, 16.1158, 16.5294, 27.1766, 13.9677, 14.1572, 5.7471, 16.0578,
              7.323, 5.766, 5.5652, 5.4491, 7.5876, 18.5707, 29.8552, 13.7464,
              27.6606, 7.432, 5.8973, 13.5627, 16.0701, 18.7044, 7.1821, 7.057,
              7.601, 18.0274, 15.555, 5.4536, 16.9163, 18.3069, 5.6183, 7.76]
    cross = [2.0641, 0.7438, 5.1454, 0.3554, 3.5986, 1.0863, 3.6193, 1.6869,
             2.0348, 3.6839, 2.2895, 3.0541, 2.2295, -0.0407, 1.794, 4.1093,
             1.9379, 0.2424, 1.3189, -0.57, 3.3808, 1.7391, 3.5987, 2.6497,
             1.1487, 3.5762, 1.6134, 3.1145, 0.8278, 2.104, 3.074, 3.0444]
    med_within, med_cross = 13.8571, 2.0841

    width, height = W, 230
    ml, mr, mt, mb = 92, 20, 16, 44
    pw, ph = width - ml - mr, height - mt - mb

    xmin, xmax = -2.0, 31.0
    def x(v):
        return ml + (v - xmin) / (xmax - xmin) * pw

    # two rows
    rows = [("same-layer", within, med_within, mt + ph * 0.28, BLUE),
            ("cross-layer", cross, med_cross, mt + ph * 0.74, ORANGE)]

    out = [svg_open(width, height)]

    # x gridlines
    for gv in (0, 5, 10, 15, 20, 25, 30):
        out.append(line(x(gv), mt, x(gv), mt + ph, stroke=GRID, width=1))
        out.append(text(x(gv), mt + ph + 15, f"{gv}%", fill=MUTED))

    # frame
    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')

    # zero line
    out.append(line(x(0), mt, x(0), mt + ph, stroke=INK, width=1.2))

    for label, values, med, yc, color in rows:
        out.append(text(ml - 8, yc + 4, label, anchor="end", fill=INK))
        # deterministic vertical jitter, symmetric around row centre
        n = len(values)
        for i, v in enumerate(sorted(values)):
            jy = yc + ((i * 17) % 13 - 6) * 2.6
            out.append(circle(x(v), jy, 3.6, fill=color, opacity=0.75))
        # median tick
        out.append(line(x(med), yc - 26, x(med), yc + 26, stroke=INK, width=2))
        anchor = "start" if med < 18 else "end"
        dx = 6 if anchor == "start" else -6
        out.append(text(x(med) + dx, yc - 30, f"median {med:.1f}%", anchor=anchor, fill=INK))

    out.append(text(ml + pw / 2, height - 6, "natural monitoring effect preserved"))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Chart 3: K16 dissected into its 12 attention heads and 4 MLPs
# ---------------------------------------------------------------------------

def k16_dissection():
    # (cell, K16, K12 heads, K4 MLPs) — central estimates
    cells = [
        ("deception · rescue",    0.945575,  0.939313, -0.014556),
        ("deception · induction", 0.987480,  0.992982, -0.029848),
        ("harmfulness · rescue",  0.850357,  0.829888,  0.040610),
        ("harmfulness · induction", 0.721946, 0.707617, 0.044877),
    ]

    width, height = W, 260
    ml, mr, mt, mb = 150, 30, 34, 44
    pw, ph = width - ml - mr, height - mt - mb

    xmin, xmax = -0.10, 1.05
    def x(v):
        return ml + (v - xmin) / (xmax - xmin) * pw

    n = len(cells)
    band = ph / n

    out = [svg_open(width, height)]

    # gridlines
    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(line(x(gv), mt, x(gv), mt + ph, stroke=GRID, width=1))
        out.append(text(x(gv), mt + ph + 15, f"{gv:.2f}".rstrip("0").rstrip(".") if gv not in (0, 1) else f"{gv:.0f}",
                        fill=MUTED))

    # frame + zero line
    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')
    out.append(line(x(0), mt, x(0), mt + ph, stroke=INK, width=1.2))

    series = [("K16 (all 16)", "#555555"), ("K12 heads only", BLUE), ("4 MLPs only", ORANGE)]

    for i, (label, k16, k12, mlp) in enumerate(cells):
        yc = mt + band * (i + 0.5)
        out.append(text(ml - 8, yc + 4, label, anchor="end", fill=INK))
        # draw K16 first so K12 (nearly overlapping) stays visible on top
        for j, (val, (_, color)) in enumerate(zip((k16, k12, mlp), series)):
            dy = (j - 1) * 9
            r = 5.2 if color == "#555555" else 4.0
            out.append(circle(x(val), yc + dy, r, fill=color))

    # legend (top right, left-to-right: K16, K12, MLPs)
    lx, ly = ml + pw - 5, mt - 10
    items = [("K16 (all 16)", "#555555", 150), ("K12 heads", BLUE, 76), ("4 MLPs", ORANGE, 0)]
    for label, color, dx in items:
        out.append(circle(lx - dx - 8, ly - 4, 3.6, color))
        out.append(text(lx - dx - 14, ly, label, anchor="end", size=11))

    out.append(text(ml + pw / 2, height - 6, "recovery of monitor effect (transplanted as a group)"))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Chart 4: ten-frame template recovery per concept vs random-orientation control
# ---------------------------------------------------------------------------

def template_recovery():
    # per-concept recovery of the exact K12 monitor-vector effect
    data = [
        ("HTML", .9826, .1415), ("all-caps", .9133, .0417), ("biology-focused", .9429, .0817),
        ("chemistry-based", .9482, .0785), ("comforting", .9869, .1085), ("confused", .9844, .0222),
        ("Finnish", .9826, .1113), ("German", .9649, .0922), ("jokey", .8424, -.0410),
        ("literature-focused", .9862, .0729), ("mathematical", .9369, .0895),
        ("MACRO", .9519, .0726),
    ]

    width, height = W, 380
    ml, mr, mt, mb = 120, 20, 30, 44
    pw, ph = width - ml - mr, height - mt - mb

    xmin, xmax = -0.1, 1.05
    def x(v):
        return ml + (v - xmin) / (xmax - xmin) * pw

    n = len(data)
    band = ph / n

    out = [svg_open(width, height)]

    # gridlines
    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(line(x(gv), mt, x(gv), mt + ph, stroke=GRID, width=1))
        lbl = f"{gv:.2f}".rstrip("0").rstrip(".") if gv not in (0, 1) else f"{gv:.0f}"
        out.append(text(x(gv), mt + ph + 15, lbl, fill=MUTED))

    # frame + zero + one lines
    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')
    out.append(line(x(0), mt, x(0), mt + ph, stroke=INK, width=1.2))
    out.append(line(x(1), mt, x(1), mt + ph, stroke=MUTED, width=1, dash="3,3"))

    for i, (concept, val, ctrl) in enumerate(data):
        yc = mt + band * (i + 0.5)
        bold = concept == "MACRO"
        out.append(text(ml - 8, yc + 4, concept, anchor="end", fill=INK, weight="600" if bold else None))
        # link line between control and prototype
        out.append(line(x(ctrl), yc, x(val), yc, stroke=GRID, width=1.5))
        out.append(circle(x(val), yc, 4.6 if bold else 3.8, fill=BLUE))
        out.append(diamond(x(ctrl), yc, 4.4 if bold else 3.8, fill=ORANGE))

    # legend (top right inside plot)
    lx, ly = ml + pw - 5, mt - 10
    out.append(circle(lx - 275, ly - 4, 3.8, BLUE))
    out.append(text(lx - 267, ly, "ten-frame template", anchor="start", size=11))
    out.append(diamond(lx - 130, ly - 4, 3.8, fill=ORANGE))
    out.append(text(lx - 122, ly, "random orientation", anchor="start", size=11))

    out.append(text(ml + pw / 2, height - 6, "recovery of exact K12 monitor-vector effect"))
    out.append("</svg>")
    return "".join(out)


def diamond(cx, cy, r, fill):
    return (f'<path d="M{cx:.1f},{cy - r:.1f} L{cx + r:.1f},{cy:.1f} L{cx:.1f},{cy + r:.1f} '
            f'L{cx - r:.1f},{cy:.1f} Z" fill="{fill}"/>')


# ---------------------------------------------------------------------------
# Chart 5: radial vs tangential decomposition of K12's write
# ---------------------------------------------------------------------------

def radial_tangential():
    # tangential retains 0.9931 of natural K12's direct effect (random control 0.1010);
    # radial retains "almost none" per the source text (shown as ~0.02, capped)
    bars = [
        ("radial component", 0.02, BLUE),
        ("tangential component", 0.9931, BLUE),
        ("random-orientation control", 0.1010, ORANGE),
    ]

    width, height = W, 170
    ml, mr, mt, mb = 165, 70, 14, 40
    pw, ph = width - ml - mr, height - mt - mb

    xmax = 1.0
    def x(v):
        return ml + v / xmax * pw

    n = len(bars)
    band = ph / n

    out = [svg_open(width, height)]

    for gv in (0, 0.25, 0.5, 0.75, 1.0):
        out.append(line(x(gv), mt, x(gv), mt + ph, stroke=GRID, width=1))
        lbl = f"{gv:.2f}".rstrip("0").rstrip(".") if gv not in (0, 1) else f"{gv:.0f}"
        out.append(text(x(gv), mt + ph + 15, lbl, fill=MUTED))

    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')

    for i, (label, val, color) in enumerate(bars):
        yc = mt + band * (i + 0.5)
        out.append(text(ml - 8, yc + 4, label, anchor="end", fill=INK))
        bh = band * 0.52
        out.append(f'<rect x="{ml:.1f}" y="{yc - bh/2:.1f}" width="{x(val) - ml:.1f}" height="{bh:.1f}" fill="{color}"/>')
        out.append(text(x(val) + 6, yc + 4, f"{val:.4g}" if val < 0.1 else f"{val:.4f}".rstrip("0").rstrip("."),
                        anchor="start", fill=INK))

    out.append(text(ml + pw / 2, height - 6, "share of natural K12 monitor-facing effect retained"))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------------------
# Chart 6: no single switch — per-layer whole-MLP / whole-attention transplants
# ---------------------------------------------------------------------------

def single_switch():
    # [layer, direction A, direction B] — strongest component is layer 8 MLP
    mlp = [
        [0, 0.0307, 0.0070], [1, 0.0262, 0.0094], [2, 0.0241, 0.0053],
        [3, 0.0762, 0.0564], [4, 0.0544, 0.0326], [5, 0.1448, 0.1142],
        [6, 0.1100, 0.0723], [7, 0.1358, 0.0826], [8, 0.2284, 0.1531],
        [9, 0.1379, 0.1533], [10, 0.0848, 0.1028], [11, 0.0357, 0.0278],
    ]
    attn = [
        [0, -0.0003, 0.0022], [1, 0.0176, 0.0106], [2, 0.0223, 0.0050],
        [3, 0.0423, 0.0543], [4, 0.0129, 0.0135], [5, 0.0084, 0.0127],
        [6, 0.0314, 0.0184], [7, 0.0169, 0.0118], [8, 0.0524, 0.0417],
        [9, 0.0131, 0.0075], [10, 0.0057, 0.0215], [11, 0.0015, -0.0006],
    ]

    width, height = W, 250
    ml, mr, mt, mb = 58, 16, 36, 46
    pw, ph = width - ml - mr, height - mt - mb

    ymin, ymax = -0.02, 0.26
    def y(v):
        return mt + (ymax - v) / (ymax - ymin) * ph
    def x(layer):
        return ml + (layer + 0.5) / 12 * pw

    out = [svg_open(width, height)]

    for gv in (0, 0.1, 0.2):
        out.append(line(ml, y(gv), ml + pw, y(gv), stroke=GRID, width=1))
        out.append(text(ml - 8, y(gv) + 4, f"{gv:.1f}", anchor="end", fill=MUTED))

    out.append(f'<rect x="{ml}" y="{mt}" width="{pw}" height="{ph}" fill="none" stroke="{INK}" stroke-width="1"/>')
    out.append(line(ml, y(0), ml + pw, y(0), stroke=INK, width=1.2))

    for layer in range(12):
        out.append(text(x(layer), mt + ph + 16, str(layer), fill=MUTED))

    # MLP: solid blue, both directions joined by a thin vertical stem per layer
    for layer, a, b in mlp:
        out.append(line(x(layer), y(a), x(layer), y(b), stroke=BLUE, width=1))
        out.append(circle(x(layer), y(a), 3.2, fill=BLUE))
        out.append(circle(x(layer), y(b), 3.2, fill=BLUE))

    # attention: orange, offset slightly right
    for layer, a, b in attn:
        out.append(line(x(layer) + 5, y(a), x(layer) + 5, y(b), stroke=ORANGE, width=1))
        out.append(circle(x(layer) + 5, y(a), 3.2, fill=ORANGE))
        out.append(circle(x(layer) + 5, y(b), 3.2, fill=ORANGE))

    # annotate layer-8 MLP peak (inside plot, above the point)
    out.append(text(x(8), y(0.2284) - 8, "layer 8 MLP, 22.8% / 15.3%", anchor="middle", size=10, fill=INK))

    # legend (top, above frame)
    lx, ly = ml + 10, mt - 12
    out.append(circle(lx + 4, ly - 4, 3.4, BLUE))
    out.append(text(lx + 12, ly, "whole MLP output", anchor="start", size=11))
    out.append(circle(lx + 130, ly - 4, 3.4, ORANGE))
    out.append(text(lx + 138, ly, "whole attention output", anchor="start", size=11))
    out.append(text(lx + 300, ly, "(two dots per layer = both directions)", anchor="start", size=10, fill=MUTED))

    out.append(text(ml + pw / 2, height - 8, "layer"))
    out.append(text(14, mt + ph / 2, "K12 effect recovered", rotate=(-90, 14, mt + ph / 2)))
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    import os
    outdir = "/home/oscar/oscar-rebooted.github.io/ai-safety/inside_neural_chameleon"
    with open(os.path.join(outdir, "nc_grouped_recovery.svg"), "w") as f:
        f.write(grouped_recovery())
    with open(os.path.join(outdir, "nc_rerouting.svg"), "w") as f:
        f.write(rerouting())
    with open(os.path.join(outdir, "nc_k16_dissection.svg"), "w") as f:
        f.write(k16_dissection())
    with open(os.path.join(outdir, "nc_template_recovery.svg"), "w") as f:
        f.write(template_recovery())
    with open(os.path.join(outdir, "nc_radial_tangential.svg"), "w") as f:
        f.write(radial_tangential())
    with open(os.path.join(outdir, "nc_single_switch.svg"), "w") as f:
        f.write(single_switch())
    print("wrote 6 charts")
