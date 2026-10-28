#!/usr/bin/env python3
"""Generates the RPB-001 rev 9 wiring sheets as SVG (ANSI B, 17 x 11 in).

    python3 generate_wiring.py          -> svg/W1..W5.svg
    node render.js                      -> RFID_Panel_Box_Wiring_rev9.pdf + png/

Units: 1 SVG unit = 0.01 in.
"""
import os
from html import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "svg")
W, H = 1700, 1100
REV = "9 (proposed)"
DATE = "Oct 28, 2026"

COL = {
    "BN": "#8a4b14", "BU": "#1f4fd1", "RD": "#d62020", "BK": "#151515", "WH": "#ffffff",
    "GN": "#1a9b3a", "YE": "#f2c400", "OR": "#f08a00", "GY": "#8a8a8a", "VT": "#8b3fc2",
    "GNYE": "#1a9b3a", "ETH": "#2a7fd4", "POE": "#1f3fa8", "COAX": "#6b6b6b", "PK": "#e46aa8",
}


class Sheet:
    def __init__(self, num, title, subtitle):
        self.num, self.title, self.subtitle = num, title, subtitle
        self.under, self.body, self.over = [], [], []

    # ---------- primitives ----------
    def raw(self, s, layer="body"):
        getattr(self, layer).append(s)

    def text(self, x, y, s, size=11, anchor="start", weight="normal", color="#1b2733",
             italic=False, layer="over", mono=False, rot=0):
        fam = "DejaVu Sans Mono, monospace" if mono else "DejaVu Sans, Arial, sans-serif"
        st = ' font-style="italic"' if italic else ""
        tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
        self.raw(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
                 f'text-anchor="{anchor}" font-weight="{weight}" fill="{color}"{st}{tr}>'
                 f'{escape(s)}</text>', layer)

    def lines(self, x, y, rows, size=10.5, gap=None, **kw):
        gap = gap or size * 1.45
        for i, r in enumerate(rows):
            if isinstance(r, tuple):
                self.text(x, y + i * gap, r[0], size=size, weight=r[1], **kw)
            else:
                self.text(x, y + i * gap, r, size=size, **kw)
        return y + len(rows) * gap

    def rect(self, x, y, w, h, fill="#ffffff", stroke="#26323d", sw=1.4, rx=4, dash=None, layer="body"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d}/>', layer)

    def line(self, x1, y1, x2, y2, color="#26323d", sw=1.4, dash=None, layer="body"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                 f'stroke-width="{sw}"{d} stroke-linecap="round"/>', layer)

    def circle(self, x, y, r, fill="#fff", stroke="#26323d", sw=1.4, layer="body"):
        self.raw(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>', layer)

    def dot(self, x, y, color="#151515"):
        self.circle(x, y, 4, fill=color, stroke=color, sw=1, layer="over")

    # ---------- wires ----------
    def wire(self, pts, color, num=None, tag_at=None, sw=3.2, dash=None, label=None, tag_side=0):
        """pts: list of (x,y). color: key in COL. num: wire number tag at segment tag_at."""
        p = " ".join(f"{x},{y}" for x, y in pts)
        c = COL.get(color, color)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.raw(f'<polyline points="{p}" fill="none" stroke="#2b2b2b" stroke-width="{sw + 1.8}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{d}/>', "under")
        self.raw(f'<polyline points="{p}" fill="none" stroke="{c}" stroke-width="{sw}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{d}/>', "under")
        if color == "GNYE":
            self.raw(f'<polyline points="{p}" fill="none" stroke="{COL["YE"]}" stroke-width="{sw}" '
                     f'stroke-dasharray="7 7" stroke-linejoin="round"/>', "under")
        if num:
            i = tag_at if tag_at is not None else (len(pts) - 2) // 2
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            self.tag((x1 + x2) / 2, (y1 + y2) / 2 + tag_side, num, label)

    def tag(self, x, y, num, label=None):
        s = num if not label else f"{num} {label}"
        w = 7.2 * len(s) + 10
        self.rect(x - w / 2, y - 9, w, 18, fill="#fffbe6", stroke="#7a6a1f", sw=1, rx=3, layer="over")
        self.text(x, y + 4, s, size=10.5, anchor="middle", weight="bold", mono=True, layer="over")

    # ---------- parts ----------
    def term(self, x, y, label, side="L", color="#e9eef2", tlabel=None):
        """Screw terminal at (x,y); label drawn inside the part (opposite side)."""
        self.rect(x - 7, y - 7, 14, 14, fill=color, stroke="#26323d", sw=1.2, rx=2, layer="over")
        self.circle(x, y, 3.2, fill="#9aa5ae", stroke="#4a545c", sw=0.8, layer="over")
        if label:
            if side == "L":
                self.text(x + 13, y + 4, label, size=10, layer="over")
            elif side == "R":
                self.text(x - 13, y + 4, label, size=10, anchor="end", layer="over")
            elif side == "T":
                self.text(x, y + 22, label, size=9.5, anchor="middle", layer="over")
            else:
                self.text(x, y - 13, label, size=9.5, anchor="middle", layer="over")
        if tlabel:
            self.text(x, y - 11 if side in ("L", "R") else y + 34, tlabel, size=8.5, anchor="middle",
                      color="#55606a", layer="over")

    def part(self, x, y, w, h, ref, name, sub=None, fill="#f4f7f9", stroke="#26323d", head="#26323d"):
        self.rect(x, y, w, h, fill=fill, stroke=stroke, sw=1.8, rx=6)
        self.rect(x, y, w, 24, fill=head, stroke=head, sw=1.8, rx=6)
        self.rect(x, y + 12, w, 12, fill=head, stroke=head, sw=0)
        self.text(x + 8, y + 17, ref, size=12, weight="bold", color="#ffffff")
        self.text(x + w - 8, y + 17, name, size=10.5, anchor="end", color="#ffffff")
        if sub:
            for i, s in enumerate(sub if isinstance(sub, list) else [sub]):
                self.text(x + 8, y + 40 + i * 14, s, size=9.5, color="#4a5560")

    def gland(self, x, y, ref, vertical=False, note=None):
        if vertical:
            self.rect(x - 16, y - 10, 32, 20, fill="#3a3f44", stroke="#111", sw=1, rx=3, layer="over")
        else:
            self.rect(x - 10, y - 16, 20, 32, fill="#3a3f44", stroke="#111", sw=1, rx=3, layer="over")
        self.text(x, y + 4, ref, size=9, anchor="middle", weight="bold", color="#fff", layer="over")
        if note:
            self.text(x, (y + 30) if not vertical else (y + 26), note, size=8.5, anchor="middle",
                      color="#55606a", layer="over")

    def glandbar(self, x, ya, yb, ref):
        """Gland drawn as a bar across a cable bundle (enclosure wall)."""
        self.rect(x - 11, ya, 22, yb - ya, fill="#3a3f44", stroke="#111", sw=1, rx=4, layer="over")
        self.text(x, (ya + yb) / 2 + 4, ref, size=10, anchor="middle", weight="bold", color="#fff",
                  layer="over", rot=-90)

    def offsheet(self, x, y, text, right=True, color="#1b2733"):
        """Off-sheet connector arrow with reference text."""
        if right:
            pts = f"{x},{y-9} {x+16},{y-9} {x+26},{y} {x+16},{y+9} {x},{y+9}"
            tx, anc = x + 32, "start"
        else:
            pts = f"{x},{y-9} {x-16},{y-9} {x-26},{y} {x-16},{y+9} {x},{y+9}"
            tx, anc = x - 32, "end"
        self.raw(f'<polygon points="{pts}" fill="#e7eefb" stroke="#2a4f8a" stroke-width="1.2"/>', "over")
        self.text(tx, y + 4, text, size=10, anchor=anc, color=color, layer="over")

    def fuse(self, x, y, ref, rating, vertical=False):
        if vertical:
            self.rect(x - 8, y - 22, 16, 44, fill="#fff3d6", stroke="#7a4a00", sw=1.4, rx=3, layer="over")
            self.line(x, y - 22, x, y + 22, color="#7a4a00", sw=1.2, layer="over")
            self.text(x + 14, y - 2, ref, size=10, weight="bold", layer="over")
            self.text(x + 14, y + 12, rating, size=9, color="#55606a", layer="over")
        else:
            self.rect(x - 24, y - 8, 48, 16, fill="#fff3d6", stroke="#7a4a00", sw=1.4, rx=3, layer="over")
            self.line(x - 24, y, x + 24, y, color="#7a4a00", sw=1.2, layer="over")
            self.text(x, y - 14, ref, size=10.5, anchor="middle", weight="bold", layer="over")
            self.text(x, y + 24, rating, size=9, anchor="middle", color="#55606a", layer="over")

    def lamp(self, x, y, color, label):
        self.circle(x, y, 13, fill=color, stroke="#222", sw=1.4, layer="over")
        self.line(x - 9, y - 9, x + 9, y + 9, color="#222", sw=1.2, layer="over")
        self.line(x - 9, y + 9, x + 9, y - 9, color="#222", sw=1.2, layer="over")
        self.text(x + 20, y + 4, label, size=9.5, layer="over")

    def buzzer(self, x, y, label):
        self.raw(f'<path d="M{x-13},{y+8} A13,13 0 0,1 {x+13},{y+8} Z" fill="#ddd" stroke="#222" '
                 f'stroke-width="1.4"/>', "over")
        self.text(x + 20, y + 4, label, size=9.5, layer="over")

    def nocontact(self, x, y, label=None, maintained=False, lamp=False):
        """Pushbutton NO contact, terminals at (x, y-30) and (x, y+30)."""
        self.line(x, y - 30, x, y - 12, sw=1.6, layer="over")
        self.line(x, y + 12, x, y + 30, sw=1.6, layer="over")
        self.line(x - 10, y - 12, x - 10, y + 12, sw=1.6, layer="over")
        self.line(x - 10, y - 12, x, y - 12, sw=1.6, layer="over")
        self.line(x - 10, y + 12, x, y + 12, sw=1.6, layer="over")
        self.line(x - 10, y, x - 30, y, sw=1.2, dash="4 3", layer="over")
        if maintained:
            self.raw(f'<path d="M{x-30},{y-8} L{x-40},{y} L{x-30},{y+8}" fill="none" stroke="#26323d" '
                     f'stroke-width="1.2"/>', "over")
        else:
            self.line(x - 34, y - 8, x - 34, y + 8, sw=1.6, layer="over")
        if label:
            self.text(x - 44, y + 4, label, size=9.5, anchor="end", layer="over")

    def table(self, x, y, cols, rows, widths, size=9.6, rowh=17, head_fill="#26323d", zebra="#f2f5f8",
              title=None):
        if title:
            self.text(x, y - 8, title, size=12.5, weight="bold")
        tw = sum(widths)
        self.rect(x, y, tw, rowh + 2, fill=head_fill, stroke=head_fill, sw=1, rx=2)
        cx = x
        for c, w in zip(cols, widths):
            self.text(cx + 5, y + rowh - 4, c, size=size, weight="bold", color="#fff")
            cx += w
        yy = y + rowh + 2
        for i, r in enumerate(rows):
            if i % 2 == 0:
                self.rect(x, yy, tw, rowh, fill=zebra, stroke="none", sw=0, rx=0)
            cx = x
            for j, (c, w) in enumerate(zip(r, widths)):
                bold = "bold" if j == 0 else "normal"
                self.text(cx + 5, yy + rowh - 5, str(c), size=size, weight=bold)
                cx += w
            yy += rowh
        self.rect(x, y, tw, yy - y, fill="none", stroke="#9aa5ae", sw=1, rx=2)
        return yy

    def note_box(self, x, y, w, title, rows, size=10, gap=None):
        gap = gap or size * 1.5
        h = 34 + len(rows) * gap
        self.rect(x, y, w, h, fill="#f7f9fb", stroke="#b8c2cb", sw=1.2, rx=6)
        self.text(x + 12, y + 22, title, size=12, weight="bold")
        self.lines(x + 12, y + 44, rows, size=size, gap=gap)
        return y + h

    # ---------- frame ----------
    def frame(self):
        self.rect(15, 15, W - 30, H - 30, fill="none", stroke="#26323d", sw=2.4, rx=0, layer="over")
        self.rect(22, 22, W - 44, H - 44, fill="none", stroke="#26323d", sw=0.8, rx=0, layer="over")
        for i in range(1, 8):
            x = 22 + i * (W - 44) / 8
            self.line(x, 22, x, 32, sw=0.8, layer="over")
            self.line(x, H - 22, x, H - 32, sw=0.8, layer="over")
        bx, by, bw, bh = W - 22 - 640, H - 22 - 92, 640, 92
        self.rect(bx, by, bw, bh, fill="#ffffff", stroke="#26323d", sw=1.6, rx=0, layer="over")
        self.line(bx + 400, by, bx + 400, by + bh, sw=1, layer="over")
        self.line(bx, by + 46, bx + 400, by + 46, sw=1, layer="over")
        self.line(bx + 400, by + 46, bx + bw, by + 46, sw=1, layer="over")
        self.line(bx + 520, by + 46, bx + 520, by + bh, sw=1, layer="over")
        self.text(bx + 10, by + 20, "RFID PANEL BOX  ·  RPB-001  ·  WIRING DIAGRAM", size=13, weight="bold",
                  layer="over")
        self.text(bx + 10, by + 38, "Gielow Pickles · G5 Croswell · one box per dock door", size=10,
                  color="#55606a", layer="over")
        self.text(bx + 10, by + 66, f"{self.num}  {self.title}", size=14, weight="bold", layer="over")
        self.text(bx + 10, by + 83, self.subtitle, size=9.5, color="#55606a", layer="over")
        self.text(bx + 410, by + 18, "REV", size=8.5, color="#55606a", layer="over")
        self.text(bx + 410, by + 38, REV, size=13, weight="bold", layer="over")
        self.text(bx + 530, by + 18, "SHEET", size=8.5, color="#55606a", layer="over")
        self.text(bx + 530, by + 38, f"{self.num[1:]} of 5", size=13, weight="bold", layer="over")
        self.text(bx + 410, by + 62, "DATE", size=8.5, color="#55606a", layer="over")
        self.text(bx + 410, by + 80, DATE, size=10.5, layer="over")
        self.text(bx + 530, by + 62, "CHECKED", size=8.5, color="#55606a", layer="over")
        self.text(bx + 530, by + 80, "________", size=10.5, layer="over")
        self.text(30, H - 30, "Units: inches, AWG. Wire numbers are per potential: the same number on both "
                  "ends and every jumper of one net. Ref RPB-001 rev 8 drawing + illustrated schematic.",
                  size=9, color="#55606a", layer="over")

    def svg(self):
        self.frame()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="17in" height="11in">'
                f'<rect width="{W}" height="{H}" fill="#ffffff"/>'
                + "".join(self.body) + "".join(self.under) + "".join(self.over) + "</svg>")


def heading(s, x, y, text, sub=None):
    s.text(x, y, text, size=17, weight="bold")
    if sub:
        s.text(x, y + 20, sub, size=10.5, color="#55606a")


# =====================================================================
# W1  POWER DISTRIBUTION
# =====================================================================
def sheet_w1():
    s = Sheet("W1", "AC + DC POWER DISTRIBUTION", "G1 → TB0 → F1 → PSU1 / PSU2 → TB1 12 V bus, SW1 48 V")
    heading(s, 40, 60, "W1 · Power distribution",
            "120 VAC in through G1, one fuse, two DIN supplies. K1 is PoE-powered: leave its 7-36 V input EMPTY.")

    # Field supply + gland
    s.text(40, 150, "120 VAC field supply", size=11, weight="bold")
    s.text(40, 165, "from dock-door receptacle /", size=9.5, color="#55606a")
    s.text(40, 178, "disconnect (by others)", size=9.5, color="#55606a")
    s.text(40, 191, "SJOOW 18/3 or MC 14/3", size=9.5, color="#55606a")
    s.gland(170, 260, "G1")
    s.text(170, 214, "G1 PG9", size=8.5, anchor="middle", color="#55606a")
    for y, c, lab in ((230, "BN", "L"), (260, "BU", "N"), (290, "GNYE", "PE")):
        s.wire([(60, y), (250, y)], c)
        s.text(70, y - 6, lab, size=9, color="#55606a")
    # Enclosure boundary
    s.rect(130, 100, 1150, 860, fill="none", stroke="#7d8790", sw=1.6, rx=10, dash="10 6")
    s.text(140, 118, "ENCLOSURE  TICONN 19.7 × 15.7 × 7.9 in  (backplate)", size=9.5, color="#55606a")

    # TB0 AC entry terminals
    s.part(250, 190, 90, 130, "TB0", "AC", fill="#f4f7f9")
    for y, lab, col in ((230, "1 L", "#e9eef2"), (260, "2 N", "#d9e4ff"), (290, "3 PE", "#d8f0c8")):
        s.term(250, y, lab, "L", color=col)
        s.term(340, y, None)
    s.text(254, 336, "2.5 mm² feed-thru", size=8.5, color="#55606a")
    s.text(254, 348, "PE: GN/YE term.", size=8.5, color="#55606a")

    # F1
    s.fuse(450, 230, "F1", "4 A time-delay · DIN 10×38 holder")
    s.wire([(340, 230), (426, 230)], "BN", "101", tag_at=0)
    # PSU1
    s.part(600, 170, 210, 250, "PSU1", "MEAN WELL NDR-120-12",
           ["12 V DC · 10 A · 120 W", "IN 90-264 VAC", "set V.ADJ to 12.0 V"])
    s.term(600, 290, "L", "L"); s.term(600, 320, "N", "L"); s.term(600, 350, "⏚", "L", color="#d8f0c8")
    s.term(810, 240, "+V", "R"); s.term(810, 270, "+V", "R"); s.term(810, 330, "−V", "R"); s.term(810, 360, "−V", "R")
    s.text(705, 405, "DC OK LED must be green", size=9, anchor="middle", color="#55606a")
    # PSU2
    s.part(600, 520, 210, 230, "PSU2", "48 V DIN PSU (ships w/ SW1)",
           ["48 V DC · feeds SW1 only", "IN 100-240 VAC", "check label: W / A rating"])
    s.term(600, 630, "L", "L"); s.term(600, 660, "N", "L"); s.term(600, 690, "⏚", "L", color="#d8f0c8")
    s.term(810, 600, "+V", "R"); s.term(810, 680, "−V", "R")

    # L
    s.wire([(474, 230), (540, 230), (540, 290), (600, 290)], "BN", "101A", tag_at=1)
    s.wire([(540, 290), (540, 630), (600, 630)], "BN", "101B", tag_at=0)
    s.dot(540, 290)
    # N
    s.wire([(340, 260), (380, 260), (380, 320), (600, 320)], "BU", "102", tag_at=2)
    s.wire([(520, 320), (520, 660), (600, 660)], "BU", "102B", tag_at=0)
    s.dot(520, 320)
    # PE
    s.wire([(340, 290), (360, 290), (360, 350), (600, 350)], "GNYE", "103", tag_at=2)
    s.wire([(500, 350), (500, 690), (600, 690)], "GNYE", "103B", tag_at=0)
    s.dot(500, 350)
    s.wire([(360, 350), (360, 820), (420, 820)], "GNYE", "103C", tag_at=1)
    s.wire([(360, 820), (360, 890), (420, 890)], "GNYE", "103D", tag_at=1)
    s.dot(360, 820)
    s.circle(432, 820, 10, fill="#d8f0c8"); s.text(450, 824, "PE stud on backplate (star washer, scrape paint)", size=9.5)
    s.circle(432, 890, 10, fill="#d8f0c8"); s.text(450, 894, "Cover / door bond strap (if metal hinge or DIN rails float)", size=9.5)
    s.text(372, 790, "PE in parallel: TB0-3 → PSU1 ⏚, PSU2 ⏚, backplate stud, SW1 lug", size=9, color="#55606a")

    # SW1 power input
    s.part(880, 790, 260, 140, "SW1", "GoodTop PoE+ 5-port",
           ["DC IN 12-52 V (from PSU2 48 V)", "2-pin terminal + ground screw", "data/PoE wiring: sheet W4"])
    s.term(880, 870, "V+", "L"); s.term(880, 900, "V−", "L")
    s.term(1010, 930, None, "T", color="#d8f0c8"); s.text(1010, 952, "⏚ lug", size=9, anchor="middle")
    s.wire([(810, 600), (850, 600), (850, 870), (880, 870)], "RD", "203", tag_at=1)
    s.wire([(810, 680), (835, 680), (835, 900), (880, 900)], "BK", "204", tag_at=1, tag_side=0)
    s.wire([(360, 890), (360, 945), (1010, 945), (1010, 937)], "GNYE", "103E", tag_at=1)

    # PSU1 -> TB1
    TBX = 950
    ys = [140 + i * 42 for i in range(14)]
    s.part(TBX - 40, 110, 80, ys[-1] - 110 + 30, "TB1", "12 V", fill="#f4f7f9")
    names = ["+12", "+12 F2", "+12 F3", "+12 F4", "+12", "+12", "0 V", "0 V", "0 V", "0 V", "0 V", "0 V", "0 V", "0 V"]
    for i, y in enumerate(ys):
        col = "#ffd9d9" if i < 6 else "#d0d0d0"
        s.term(TBX - 40, y, None, color=col)
        s.term(TBX + 40, y, None, color=col)
        s.text(TBX, y + 4, f"{i+1}", size=10.5, anchor="middle", weight="bold", layer="over")
    # jumper bars
    s.rect(TBX - 4 + 22, ys[0] - 6, 8, ys[5] - ys[0] + 12, fill="#d62020", stroke="#7a0000", sw=1, rx=3, layer="over")
    s.rect(TBX - 4 + 22, ys[6] - 6, 8, ys[13] - ys[6] + 12, fill="#333", stroke="#000", sw=1, rx=3, layer="over")
    s.text(TBX + 12, ys[5] + 26, "jumper", size=8, anchor="middle", color="#55606a", layer="over")
    for i, (r, lab) in enumerate(((1, "F2 2 A"), (2, "F3 0.5 A"), (3, "F4 0.5 A"), (5, "F5 0.5 A"))):
        y = ys[r]
        s.rect(TBX - 26, y - 7, 18, 14, fill="#fff3d6", stroke="#7a4a00", sw=1, rx=2, layer="over")
    s.text(TBX - 40, ys[13] + 48, "1-6 +12 V (red bar) · 7-14 0 V (black bar)", size=8.5, color="#55606a")
    s.text(TBX - 40, ys[13] + 60, "2/3/4/6 = fused DIN terminals, 5×20 mm", size=8.5, color="#55606a")

    s.wire([(810, 240), (885, 240), (885, ys[0]), (TBX - 40, ys[0])], "RD", "201", tag_at=1)
    s.wire([(810, 330), (860, 330), (860, ys[6]), (TBX - 40, ys[6])], "BK", "202", tag_at=1)
    s.text(830, 225, "18 AWG", size=8.5, color="#55606a")

    # TB1 destinations
    dest = [
        ("201", "RD", "← PSU1 +V (feed)"),
        ("205", "RD", "K1 CH1-CH5 COM (W2)"),
        ("410", "RD", "B1 BN truck + (W3)"),
        ("412", "RD", "B2 RD beam + (W3)"),
        (None, "RD", "spare (U1 alt +12, W4)"),
        ("416", "RD", "U1 GPI1+ pin 12 (W4)"),
        ("202", "BK", "← PSU1 −V (feed)"),
        ("206", "BK", "K1 DGND (W3)"),
        ("411", "BK", "B1 BU truck 0 V (W3)"),
        ("413", "BK", "B2 BK beam 0 V (W3)"),
        ("306", "BK", "TB2-5 lamp com (W2)"),
        ("407", "BK", "CS1 contact com (W3)"),
        ("308", "BK", "S1 lamp X2 − (W2)"),
        (None, "BK", "spare (U1 alt 0 V, W4)"),
    ]
    for i, (num, c, txt) in enumerate(dest):
        y = ys[i]
        if i in (0, 6):
            s.text(TBX + 58, y + 4, txt, size=9.5, color="#55606a")
            continue
        if num:
            s.wire([(TBX + 40, y), (TBX + 110, y)], c, num, tag_at=0)
            s.offsheet(TBX + 114, y, txt)
        else:
            s.text(TBX + 58, y + 4, txt, size=9.5, color="#8a949c", italic=True)

    # Notes column
    x0 = 1300
    y = s.note_box(x0, 710, 370, "Wire & termination spec", [
        "AC (101-103): 18 AWG MTW/UL1015 600 V, BN L · BU N · GN/YE PE",
        "DC 12 V / 48 V: 18 AWG UL1007, RD + · BK 0 V",
        "All stranded ends: insulated ferrules (18 AWG = 1.0 mm²)",
        "Two wires in one terminal: twin ferrule (PSU1 L, N, ⏚)",
        "Torque: PSU 4.4 lb·in · DIN terminals 5 lb·in (check part)",
        "Label both ends of every wire with its number",
    ], size=9)
    s.note_box(x0, 100, 370, "Power budget (per box)", [
        ("PSU1 12 V  (120 W available)", "bold"),
        "  2 stack lights, 1 lamp + buzzer each      ≈ 6 W",
        "  S1 pilot lamp (12 V LED)                  ≈ 0.3 W",
        "  B1 laser + B2 beam                        ≈ 2 W",
        "  total                                     ≈ 8-11 W  (<10 %)",
        "  U1 reader if moved to PSU1 (W4 option)    +36 W max",
        ("PSU2 48 V → SW1", "bold"),
        "  SW1 + PoE: SPL1/U1 ≤ 25.5 W, K1 ≈ 3-5 W  → check label",
        ("F1 (120 VAC)", "bold"),
        "  4 A time-delay (Class CC/midget 10×38). NDR-120 inrush",
        "  ≈ 30 A cold start: do NOT use fast-acting.",
        "  If PSU2 label > 1.5 A in, go 5 A.",
        ("F2-F4 (12 V branch, 5×20 mm in fused terminals)", "bold"),
        "  F2 2 A K1 relay COM bus · F3/F4 0.5 A sensors · F5 0.5 A U1 GPI1+",
        "  Protects 18-22 AWG field cable from the 10 A supply.",
    ], size=9, gap=14.5)
    s.note_box(x0, 445, 370, "Power-up check (before K1/U1 connected)", [
        "1. Meter TB0-1 → TB0-2 ≈ 120 VAC, TB0-1 → TB0-3 ≈ 120 VAC.",
        "2. PE continuity TB0-3 ↔ backplate stud ↔ PSU cases < 1 Ω.",
        "3. Close F1. PSU1 DC OK lit; TB1-1 → TB1-7 = 12.0 V (trim V.ADJ).",
        "4. TB1-2/3/4/6 → TB1-7 = 12 V (fuses in).",
        "5. PSU2 +V → −V = 48 V; SW1 power LED on.",
        "6. K1 7-36 V terminal: nothing landed. PoE only.",
        "7. TB1 0 V is NOT bonded to PE (floating DC system).",
    ], size=9, gap=14.5)
    return s


# =====================================================================
# W2  RELAY OUTPUTS: stack lights, buzzer, S1 lamp
# =====================================================================
def sheet_w2():
    s = Sheet("W2", "K1 RELAY OUTPUTS", "CH1-CH4 → TB2 → HL1 + HL2 stack lights · CH5 → S1 lamp · CH6-8 spare")
    heading(s, 40, 60, "W2 · K1 relay outputs → stack lights, buzzer, S1 lamp",
            "Relay commons are jumpered to +12 V (fused F2). Relays switch +12 V out on NO. Tower common returns to 0 V.")

    # K1 relay section
    kx, ky, kw = 110, 110, 330
    pitch = 100
    s.part(kx, ky, kw, 8 * pitch + 40, "K1", "Waveshare ESP32-S3-POE-ETH-8DI-8RO",
           ["relay section · 10 A 250 VAC / 30 VDC", "TCA9554 @0x20, bit n = CHn+1"])
    tx = kx + kw
    chs = ["RED lamp", "AMBER lamp", "GREEN lamp", "BUZZER", "S1 pilot lamp", "spare", "spare", "spare"]
    rows = {}
    for i in range(8):
        y0 = ky + 70 + i * pitch
        no, com, nc = y0, y0 + 26, y0 + 52
        rows[i] = (no, com, nc)
        s.text(kx + 14, com + 4, f"CH{i+1}", size=13, weight="bold")
        s.text(kx + 70, com + 4, chs[i], size=10, color="#55606a" if i > 4 else "#1b2733")
        # contact symbol
        cx = tx - 70
        s.line(cx, com, cx + 24, no + 4, sw=1.6, layer="over")
        s.circle(cx, com, 2.5, fill="#26323d")
        s.line(cx + 28, no, tx - 8, no, sw=1.2); s.line(cx, com, tx - 8, com, sw=1.2)
        s.line(cx + 28, nc, tx - 8, nc, sw=1.2); s.line(cx + 28, nc, cx + 28, nc - 10, sw=1.2)
        s.term(tx, no, "NO", "R"); s.term(tx, com, "C", "R"); s.term(tx, nc, "NC", "R")
        if i:
            s.line(kx + 6, y0 - 22, kx + kw - 6, y0 - 22, color="#c9d1d8", sw=1)
    s.text(kx + 10, ky + 8 * pitch + 60, "Terminal order on the real board: VERIFY (pluggable 3-pin per CH,", size=9, color="#55606a")
    s.text(kx + 10, ky + 8 * pitch + 72, "silkscreen NO / C / NC). Relay LEDs mirror coil state.", size=9, color="#55606a")

    # +12 feed and COM jumpers
    jx = tx + 40
    s.offsheet(jx + 6, 92, "TB1-2 +12 V via F2 2 A  (W1)", right=True)
    s.wire([(jx + 6, 92), (jx, 92), (jx, rows[0][1]), (tx, rows[0][1])], "RD", "205", tag_at=1)
    for i in range(1, 5):
        s.wire([(tx, rows[i - 1][1]), (tx + 20, rows[i - 1][1] + 8), (tx + 20, rows[i][1] - 8), (tx, rows[i][1])],
               "RD", "205" if i == 1 else None, tag_at=1, sw=2.4)
    s.text(tx + 28, rows[2][1] + 40, "205 jumpers", size=8.5, color="#7a0000")
    s.text(tx + 28, rows[2][1] + 52, "C1→C2→C3→C4→C5", size=8.5, color="#7a0000")
    s.text(tx + 28, rows[2][1] + 64, "18 AWG RD, ferruled", size=8.5, color="#7a0000")

    # TB2 marshalling
    bx = 720
    tby = [205, 285, 365, 445, 530]
    s.part(bx - 40, 120, 120, 450, "TB2", "LAMPS", ["4-level / quattro", "DIN terminals"], fill="#f4f7f9")
    labs = ["1 RED", "2 AMBER", "3 GREEN", "4 BUZZ", "5 COM 0V"]
    for i, y in enumerate(tby):
        s.term(bx - 40, y, None, color="#e9eef2" if i < 4 else "#d0d0d0")
        s.term(bx + 80, y - 12, None, color="#e9eef2" if i < 4 else "#d0d0d0")
        s.term(bx + 80, y + 12, None, color="#e9eef2" if i < 4 else "#d0d0d0")
        s.text(bx + 20, y + 4, labs[i], size=10, anchor="middle", weight="bold")
    for i, (num, c) in enumerate((("301", "RD"), ("302", "OR"), ("303", "GN"), ("304", "WH"))):
        no = rows[i][0]
        xx = 560 + i * 22
        s.wire([(tx, no), (xx, no), (xx, tby[i]), (bx - 40, tby[i])], c, num, tag_at=2)
    s.offsheet(bx - 66, 610, "", right=False)
    s.text(bx - 98, 614, "TB1-11 0 V (W1)", size=10, anchor="end")
    s.wire([(bx - 66, 610), (bx - 60, 610), (bx - 60, tby[4]), (bx - 40, tby[4])], "BK", "306", tag_at=1)
    s.text(bx - 40, 600, "Panel wiring K1→TB2: 18 AWG, color as shown.", size=8.5, color="#55606a")

    # Towers
    def tower(x0, y0, ref, gl, wires_y):
        s.part(x0, y0, 260, 300, ref, "12 V LED tower R/A/G + buzzer",
               ["5-wire lead · verify colors on arrival"])
        lx = x0 + 130
        ys = [y0 + 80, y0 + 130, y0 + 180, y0 + 230]
        s.lamp(lx, ys[0], "#ff4040", "RED")
        s.lamp(lx, ys[1], "#ffb020", "AMBER")
        s.lamp(lx, ys[2], "#30c050", "GREEN")
        s.buzzer(lx, ys[3], "BUZZER")
        comx = x0 + 225
        for yy in ys:
            s.line(lx + 13, yy, comx, yy, sw=1.2, layer="body")
            s.line(lx - 13 - 30, yy, lx - 13, yy, sw=1.2, layer="body")
        s.line(comx, ys[0], comx, y0 + 280, sw=1.4, layer="body")
        s.line(comx, y0 + 280, x0 + 60, y0 + 280, sw=1.4, layer="body")
        s.text(comx - 4, y0 + 274, "common", size=9, anchor="end", color="#55606a")
        pins = []
        for k, yy in enumerate(ys + [y0 + 280]):
            px = x0
            s.term(px, yy, None)
            if k < 4:
                s.line(px + 7, yy, lx - 43, yy, sw=1.2, layer="body")
            else:
                s.line(px + 7, yy, x0 + 60, yy, sw=1.4, layer="body")
            pins.append((px, yy))
        return pins

    t1 = tower(1130, 110, "HL1", "G5", None)
    t2 = tower(1130, 560, "HL2", "G6", None)
    for (ref, ya, yb) in (("G5", t1[0][1] - 18, t1[4][1] + 18), ("G6", t2[0][1] - 18, t2[4][1] + 18)):
        s.rect(1070, ya, 22, yb - ya, fill="#3a3f44", stroke="#111", sw=1, rx=4, layer="over")
        s.text(1081, (ya + yb) / 2 + 4, ref, size=10, anchor="middle", weight="bold", color="#fff", layer="over",
               rot=-90)
    cols = [("RD", "301", "RD"), ("YE", "302", "YE"), ("GN", "303", "GN"), ("WH", "304", "WH/BN"), ("BK", "306", "BK")]
    for k, (c, num, cname) in enumerate(cols):
        # to HL1 from upper clamp, to HL2 from lower clamp
        y = tby[k]
        x1 = 880 + k * 14
        s.wire([(bx + 80, y - 12), (x1, y - 12), (x1, t1[k][1]), (t1[k][0], t1[k][1])], c,
               num if k in (0, 4) else None, tag_at=2)
        x2 = 960 + k * 12
        s.wire([(bx + 80, y + 12), (x2, y + 12), (x2, t2[k][1]), (t2[k][0], t2[k][1])], c,
               num if k in (0, 4) else None, tag_at=2)
    s.text(1130, 440, "Cable W-HL1: tower lead or 18/5 SJOOW to G5", size=9, color="#55606a")
    s.text(1130, 890, "Cable W-HL2: tower lead or 18/5 SJOOW to G6", size=9, color="#55606a")
    s.text(1130, 905, "Lead too short → splice in IP67 JB at mast, keep colors", size=9, color="#55606a")

    # S1 pilot lamp
    no5 = rows[4][0]
    s.wire([(tx, no5), (490, no5), (490, 725), (520, 725)], "RD", "305", tag_at=1)
    s.gland(530, 742, "G7")
    s.part(580, 660, 300, 130, "S1", "LOAD COMPLETE lamp (green)",
           ["22 mm illuminated PB, 12 V LED", "X1 +  /  X2 −    contacts: W3"])
    s.term(580, 725, "X1 +", "L"); s.term(580, 760, "X2 −", "L")
    s.lamp(820, 740, "#30c050", "")
    s.wire([(540, 725), (580, 725)], "RD", None)
    s.wire([(580, 760), (555, 760), (555, 812), (600, 812)], "BK", "308", tag_at=1)
    s.offsheet(600, 812, "TB1-13 0 V (W1)  ·  in cable W-CS (6-cond), see W3", right=True)

    # Notes
    s.note_box(470, 842, 580, "Stack-light notes", [
        "Lamp truth: firmware sets exactly ONE of CH1/CH2/CH3. CH4 = buzzer, CH5 = S1 lamp.",
        "HL1 + HL2 in parallel at TB2 (one wire in, two out per level). 4-level terminals,",
        "  or 2 stacked 2-level terminals with a bridge. Each tower ≈ 3 W → F2 2 A is plenty.",
        "Tower common polarity: meter it. If the common must be +12 V (common-anode tower):",
        "  move 205 to TB1 0 V and 306 to TB1 +12 V. Nothing else changes.",
        "Typical lead colors: RD red · YE amber · GN green · WH or BN buzzer · BK common.",
        "Relay NC contacts unused: leave empty. Don't wire anything to NC on CH1-CH3.",
    ], size=9.5, gap=15)
    return s


# =====================================================================
# W3  INPUTS: B1, B2, control station
# =====================================================================
def sheet_w3():
    s = Sheet("W3", "K1 DIGITAL INPUTS", "B1 truck → DI1 · B2 beam → DI2 · S1/S2/S3 control station → DI3-DI5")
    heading(s, 40, 60, "W3 · K1 digital inputs → sensors + operator controls",
            "Opto inputs switch when DIn is pulled to DGND (NPN sink / dry contact). DGND bonded to TB1 0 V.")

    # K1 DI section
    kx, ky = 790, 110
    s.part(kx, ky, 270, 760, "K1", "digital inputs (opto-isolated)",
           ["DI1-DI8 → GPIO 4-11", "firmware: INPUT_ACTIVE_LOW = true", "1 = input pulled to DGND"])
    names = ["DI1  truck (B1)", "DI2  beam (B2)", "DI3  S1 load complete", "DI4  S2 ack / silence",
             "DI5  S3 maint key", "DI6  spare", "DI7  spare", "DI8  spare", "DGND  input common"]
    dy = [190, 300, 560, 630, 700, 750, 785, 820, 850]
    for n, y in zip(names, dy):
        s.term(kx, y, n, "L", color="#e9eef2" if "DGND" not in n else "#d0d0d0")
    s.rect(kx + 170, 180, 80, 650, fill="#ffffff", stroke="#c9d1d8", sw=1, rx=4)
    s.text(kx + 210, 210, "opto", size=9, anchor="middle", color="#55606a")
    for y in dy[:8]:
        s.raw(f'<polygon points="{kx+200},{y-6} {kx+200},{y+6} {kx+212},{y}" fill="#fff" stroke="#26323d" '
              f'stroke-width="1"/>', "over")
        s.line(kx + 213, y - 6, kx + 213, y + 6, sw=1, layer="over")
        s.line(kx + 216, y - 2, kx + 226, y - 8, sw=0.8, layer="over")
        s.line(kx + 216, y + 2, kx + 226, y - 4, sw=0.8, layer="over")
    s.text(kx + 210, 846, "GPIO", size=9, anchor="middle", color="#55606a")

    # B1 truck sensor
    s.part(60, 120, 260, 150, "B1", "DIHOOL M16 laser diffuse",
           ["NPN NO · 10-30 VDC · 3-80 cm", "dock face by bumper", "80 cm lead → JB1 splice"])
    for y, lab in ((200, "BN +"), (225, "BU −"), (250, "BK out")):
        s.term(320, y, lab, "R")
    s.rect(380, 170, 60, 100, fill="#eef1f4", stroke="#26323d", sw=1.2, rx=4)
    s.text(410, 162, "JB1", size=10, weight="bold", anchor="middle")
    s.text(410, 286, "IP67 splice box", size=8.5, anchor="middle", color="#55606a")
    s.text(410, 298, "22/4 ext. cable", size=8.5, anchor="middle", color="#55606a")
    s.glandbar(480, 182, 268, "G3")
    s.wire([(320, 200), (380, 200)], "BN"); s.wire([(320, 225), (380, 225)], "BU"); s.wire([(320, 250), (380, 250)], "BK")
    s.wire([(440, 200), (620, 200), (620, 140), (660, 140)], "BN", "410", tag_at=0)
    s.offsheet(660, 140, "TB1-3 +12 F3", right=True)
    s.wire([(440, 225), (640, 225), (640, 165), (680, 165)], "BU", "411", tag_at=0)
    s.wire([(680, 165), (700, 165)], "BU")
    s.text(705, 169, "→ TB1-9 0V", size=9.5)
    s.wire([(440, 250), (700, 250), (700, 190), (kx, 190)], "BK", "401", tag_at=0)

    # B2 beam
    s.part(60, 330, 260, 190, "B2", "JUTAI IRR-7M retro-reflective",
           ["relay out 200 mA dry contact", "confirm IRR-7M vs IRR-7R", "reflector across the door"])
    for y, lab in ((390, "RD +"), (415, "BK −"), (440, "WH COM"), (465, "GN NO"), (490, "YE NC")):
        s.term(320, y, lab, "R")
    s.glandbar(400, 372, 483, "G2")
    s.wire([(320, 390), (620, 390), (620, 360), (660, 360)], "RD", "412", tag_at=0)
    s.offsheet(660, 360, "TB1-4 +12 F4", right=True)
    s.wire([(320, 415), (640, 415), (640, 385), (680, 385)], "BK", "413", tag_at=0)
    s.wire([(680, 385), (700, 385)], "BK"); s.text(705, 389, "→ TB1-10 0V", size=9.5)
    s.wire([(320, 440), (720, 440), (720, 850), (kx, 850)], "WH", "403", tag_at=0)
    # TB3: two diode terminals split the one B2 contact to K1 DI2 and U1 GPI1-
    tx3, ty3 = 450, 448
    s.part(tx3, ty3, 110, 96, "TB3", "1N4007", fill="#f4f7f9")
    s.term(tx3, 465 + 10, None)
    s.wire([(320, 465), (400, 465), (400, 475), (tx3, 475)], "GN", "402", tag_at=0)
    nx = tx3 + 30
    s.line(tx3 + 7, 475, nx, 475, sw=1.4, layer="over")
    s.line(nx, 475, nx, 530, sw=1.4, layer="over")
    s.dot(nx, 475)
    for yy, ref in ((490, "D1"), (530, "D2")):
        # cathode at the node, anode toward the input
        s.line(nx, yy, nx + 18, yy, sw=1.4, layer="over")
        s.raw(f'<polygon points="{nx+18},{yy} {nx+34},{yy-8} {nx+34},{yy+8}" fill="#26323d"/>', "over")
        s.line(nx + 18, yy - 8, nx + 18, yy + 8, sw=2, layer="over")
        s.line(nx + 34, yy, tx3 + 103, yy, sw=1.4, layer="over")
        s.text(nx + 26, yy - 11, ref, size=8.5, anchor="middle", weight="bold", layer="over")
        s.term(tx3 + 110, yy, None)
    s.wire([(tx3 + 110, 490), (740, 490), (740, 300), (kx, 300)], "GN", "402A", tag_at=0)
    s.wire([(tx3 + 110, 530), (578, 530), (578, 567), (445, 567)], "GN", None)
    s.offsheet(445, 567, "415 → U1 GPI1− pin 11 (W4)", right=False)
    s.text(326, 506, "YE NC: insulate + fold back (spare)", size=9, color="#55606a")
    s.rect(330, 484, 18, 12, fill="#fff3d6", stroke="#7a4a00", sw=1, rx=2, layer="over")

    # Control station
    cx, cy = 60, 580
    s.part(cx, cy, 470, 320, "CS1", "Operator control station (proposed)",
           ["3-hole 22 mm IP65 box beside the door, 48 in AFF", "cable W-CS: 18/6 SJOOW via G7"])
    s.rect(cx + 20, cy + 80, 430, 220, fill="#ffffff", stroke="#c9d1d8", sw=1, rx=4)
    comy = cy + 110
    s.line(cx + 60, comy, cx + 400, comy, sw=1.6, layer="over")
    s.text(cx + 66, comy - 8, "13 (common)", size=9, color="#55606a")
    pbs = [("S1", "LOAD COMPLETE", "green illum. PB · momentary", "404", "WH", 560, False),
           ("S2", "ACK / SILENCE", "yellow PB · momentary", "405", "GN", 630, False),
           ("S3", "MAINT", "2-pos keyswitch · maintained", "406", "OR", 700, True)]
    for k, (ref, lab, sub, num, c, ydi, maint) in enumerate(pbs):
        px = cx + 170 + k * 110
        s.dot(px, comy)
        s.nocontact(px, comy + 50, None, maintained=maint)
        s.text(px + 8, comy + 40, ref, size=11, weight="bold", layer="over")
        s.text(px + 8, comy + 54, "14", size=8.5, color="#55606a", layer="over")
        s.text(px - 8, comy + 115, lab, size=9, anchor="end", weight="bold", layer="over")
        s.text(px - 8, comy + 128, sub.split(" · ")[0], size=8, anchor="end", color="#55606a", layer="over")
        s.text(px - 8, comy + 140, sub.split(" · ")[1], size=8, anchor="end", color="#55606a", layer="over")
        s.line(px, comy + 80, px, comy + 100, sw=1.6, layer="over")
        s.wire([(px, comy + 100), (px, cy + 300 + 16 + k * 14), (600 + k * 20, cy + 300 + 16 + k * 14),
                (600 + k * 20, ydi), (kx, ydi)], c, num, tag_at=3)
    s.glandbar(560, cy + 302, cy + 372, "G7")
    s.wire([(cx + 60, comy), (cx + 40, comy), (cx + 40, cy + 300 + 60), (610, cy + 360)], "BK", "407", tag_at=2)
    s.offsheet(610, cy + 360, "TB1-12 0 V", right=True)
    s.text(cx + 20, cy + 395, "W-CS cores: BK 407 common · WH 404 · GN 405 · OR 406 · RD 305 lamp+ · BU 308 lamp− (W2)",
           size=9, color="#55606a")

    # Notes / tables
    s.table(1090, 120, ["Input", "Device", "Closed / 1 means", "Wire"],
            [["DI1", "B1 BK (NPN NO)", "truck present", "401"],
             ["DI2", "B2 NO via D1 / COM", "beam broken*", "402A/403"],
             ["DI3", "S1 13-14", "load complete pressed", "404"],
             ["DI4", "S2 13-14", "ack / silence pressed", "405"],
             ["DI5", "S3 13-14", "maintenance ON", "406"],
             ["DI6-8", "—", "spare (dry contact to DGND)", "—"],
             ["DGND", "TB1-8", "bonded to 0 V", "206"],
             ["U1 GPI1", "B2 NO via D2", "reader trigger (W4)", "415/416"]],
            [60, 150, 210, 70], title="Input map")
    s.note_box(1090, 290, 560, "Why it fails safe", [
        "B1 is NPN normally-open: cut cable / dead sensor reads 'no truck' → server shows RED.",
        "*B2 relay: pick NO or NC on the bench so 'beam broken' = 1. With NO + light-on,",
        "  a cut cable reads 'beam clear' → reader stays idle (no false green).",
        "S3 maint is maintained; key removable only in NORMAL.",
        "These inputs are NOT a safety circuit. Don't use them for machine guarding / E-stop.",
    ], size=9.5, gap=15)
    s.note_box(1090, 430, 560, "Bench test (README)  — do this before mounting", [
        "1. DGND→TB1 0 V landed (206). Hand in front of B1 → serial 'DI1 -> 1'.",
        "2. Block B2 → 'DI2' toggles. Move GN→YE (NC) if it reads backwards.",
        "3. Press S1, S2; turn S3 → DI3/DI4/DI5 → 1, inputs JSON release/ack/maint true.",
        "4. If every DI reads inverted, set INPUT_ACTIVE_LOW false in config.h.",
        "5. Block B2 with reader in trigger mode → U1 starts reading (W4).",
        "6. If a dry contact to DGND does NOT switch the opto, the board needs a",
        "   sourced input: see option B below.",
    ], size=9.5, gap=15)
    s.note_box(1090, 590, 560, "Option B — if K1 DI turns out to need an external voltage", [
        "Waveshare DI wiring is still UNVERIFIED (README 'known unknowns').",
        "If DIn needs +V to switch (opto anode at DIn, cathode at DGND):",
        "  · DGND stays on 0 V (206).",
        "  · B2 WH COM and S1-S3 common (407) move from 0 V to +12 V (TB1-5/6).",
        "  · B1 NPN can't source: swap to a PNP sensor (BK = +12 when target seen),",
        "    e.g. the PNP Heschen from PO 1811, or add a 12 V interposing relay.",
        "Mark the change on this sheet; firmware is unchanged.",
    ], size=9.5, gap=15)
    s.note_box(1090, 770, 560, "Why TB3 diodes (one beam contact, two inputs)", [
        "B2 has ONE relay contact. Tied straight to DI2 and GPI1−, the open contact leaves",
        "+12 → GPI1 LED → K1 DI2 LED → 0 V in series: both can false-trigger. D1/D2 block it.",
        "Contact closed: both cathodes at 0 V → DI2 = 1 and GPI1 on (≈ 0.7 V drop, fine).",
        "B2 22/5 lead · B1 22/4 ext · CS1 18/6 SJOOW. Keep away from AC + coax.",
    ], size=9.5, gap=15)
    return s


# =====================================================================
# W4  NETWORK, PoE, RF
# =====================================================================
def sheet_w4():
    s = Sheet("W4", "NETWORK · PoE · RF", "plant switch → G4 → SW1 → SPL1 → U1 · SW1 → K1 · U1 → 4 antennas")
    heading(s, 40, 60, "W4 · Network, PoE and antenna wiring",
            "Everything is copper Ethernet + PoE inside the box. Plant network enters on C4 through G4.")

    # plant switch
    s.part(40, 160, 200, 110, "—", "Plant network switch", ["IDF / MDF, by others", "VLAN for dock devices"])
    s.gland(330, 215, "G4", note="RJ45 / cord grip")
    # SW1
    sx, sy = 420, 120
    s.part(sx, sy, 230, 420, "SW1", "GoodTop PoE+ 5-port",
           ["802.3af/at, 4 × 30 W PoE out", "P5 = uplink (no PoE)", "power: W1 (203/204 48 V)"])
    ports = {}
    for i, p in enumerate(["P1", "P2", "P3", "P4", "P5"]):
        y = sy + 110 + i * 60
        s.rect(sx + 180, y - 16, 40, 32, fill="#2b2f33", stroke="#000", sw=1, rx=3)
        s.rect(sx + 188, y - 9, 24, 18, fill="#111", stroke="#555", sw=1, rx=2)
        s.text(sx + 200, y - 21, p + (" PoE" if i < 4 else " UPLINK"), size=10, anchor="middle", weight="bold")
        ports[p] = (sx + 220, y)
    s.wire([(240, 215), (310, 215)], "ETH", sw=4)
    s.wire([(350, 215), (380, 215), (380, ports["P5"][1]), (sx + 180, ports["P5"][1])], "ETH", "C4", tag_at=1, sw=4)
    s.text(245, 190, "Cat6 CMR, field-terminated", size=9, color="#55606a")
    s.text(380 - 4, ports["P5"][1] + 30, "C4 length per door (BOM TBD)", size=9, anchor="end", color="#55606a")

    # SPL1
    px, py = 760, 120
    s.part(px, py, 220, 200, "SPL1", "REVODATA PS5712BG-25",
           ["802.3bt PD splitter", "out: 12 V 3 A 5.5×2.5 plug", "+ data RJ45 pigtail"])
    s.rect(px - 6, py + 90, 30, 30, fill="#111", stroke="#555", sw=1, rx=2)
    s.text(px + 30, py + 110, "PoE IN", size=9.5)
    s.wire([ports["P1"], (720, ports["P1"][1]), (720, py + 105), (px - 6, py + 105)], "POE", "C1", tag_at=1, sw=4.5)
    s.text(720 - 6, ports["P1"][1] - 10, "Cat6a 0.5 ft", size=8.5, anchor="end", color="#55606a")
    s.term(px + 220, py + 150, "DATA", "R")
    s.term(px + 220, py + 180, "12 V", "R")

    # K1
    kx, ky = 760, 420
    s.part(kx, ky, 220, 150, "K1", "ESP32-S3-POE-ETH-8DI-8RO",
           ["W5500 10/100 · PoE PD", "DHCP reservation by MAC", "MAC printed in /info"])
    s.rect(kx - 6, ky + 80, 30, 30, fill="#111", stroke="#555", sw=1, rx=2)
    s.text(kx + 30, ky + 100, "RJ45 PoE", size=9.5)
    s.wire([ports["P2"], (720, ports["P2"][1]), (720, ky + 95), (kx - 6, ky + 95)], "POE", "C5", tag_at=1, sw=4.5)
    s.text(kx + 10, ky + 134, "7-36 V terminal: EMPTY (PoE only)", size=9, weight="bold", color="#b00000")

    # U1 reader
    ux, uy = 1080, 120
    s.part(ux, uy, 300, 420, "U1", "WYUAN M-808EK UHF reader",
           ["DC 9-24 V · 3 A · TCP/IP", "8 × SMA ANT · GPI1 = beam trigger", "on M4 standoffs, ports down"])
    s.term(ux, uy + 150, "LAN", "L")
    s.term(ux, uy + 180, "DC IN", "L")
    s.wire([(px + 220, py + 150), (ux, uy + 150)], "ETH", "C2", sw=4)
    s.wire([(px + 220, py + 180), (ux, uy + 180)], "RD", "C3", sw=3.2)
    s.text((px + 220 + ux) / 2 + 40, uy + 222, "5.5×2.5 plug: check U1 jack (often 5.5×2.1)", size=8.5, anchor="middle",
           color="#55606a")
    # Alt feed
    s.offsheet(ux - 30, uy + 250, "TB1-5 +12 / TB1-14 0 V", right=False)
    s.wire([(ux - 30, uy + 250), (ux, uy + 250)], "RD", dash="8 5")
    s.text(ux + 12, uy + 254, "ALT DC (dashed): only if SPL1 browns out;", size=9, color="#b00000")
    s.text(ux + 12, uy + 268, "then C3 unplugged, 16 AWG RD/BK, inline 4 A fuse", size=9, color="#b00000")

    # U1 GPIO 12-pin 3.81 mm terminal (from the reader sheet)
    gx, gy = 1450, 270
    s.part(gx, gy, 120, 262, "U1", "GPIO 3.81×12", fill="#f4f7f9")
    s.line(ux + 300, gy + 60, gx, gy + 60, sw=1.2, dash="5 4")
    s.text(ux + 306, gy + 54, "on U1", size=8.5, color="#55606a")
    gp = ["1 VOUT", "2 485A", "3 485B", "4 GND", "5 GPO2", "6 GPO2", "7 GPO1", "8 GPO1",
          "9 GPI2−", "10 GPI2+", "11 GPI1−", "12 GPI1+"]
    for i, lab in enumerate(gp):
        y = gy + 40 + i * 18
        used = i >= 10
        s.term(gx, y, lab + ("" if used else "  —"), "L", color="#ffe9a8" if used else "#e9eef2")
    y11, y12 = gy + 40 + 10 * 18, gy + 40 + 11 * 18
    s.wire([(gx, y11), (gx - 30, y11), (gx - 30, 575), (gx + 10, 575)], "GN", "415", tag_at=0)
    s.offsheet(gx + 10, 575, "TB3 D2 (W3)", right=True)
    s.wire([(gx, y12), (gx - 14, y12), (gx - 14, 605), (gx + 10, 605)], "RD", "416", tag_at=0)
    s.offsheet(gx + 10, 605, "TB1-6 +12 F5 (W1)", right=True)
    s.text(gx + 4, gy + 262 + 14, "— = leave empty", size=8.5, color="#55606a")

    # antenna ports
    ay = uy + 420
    for i in range(8):
        x = ux + 30 + i * 34
        s.circle(x, ay, 8, fill="#c8a24a", stroke="#5a4510")
        s.text(x, ay - 14, f"{i+1}", size=8.5, anchor="middle")
    s.text(ux + 150, ay - 30, "ANT1-8 SMA (bottom edge)", size=9, anchor="middle")
    bulk_y = 760
    for i in range(4):
        x = ux + 30 + i * 34
        bx = 600 + i * 150
        s.wire([(x, ay + 8), (x, 660 + i * 12), (bx, 660 + i * 12), (bx, bulk_y - 12)], "COAX",
               f"A{i+1}", tag_at=1, sw=2.6, dash="10 4")
        s.circle(bx, bulk_y, 11, fill="#c8a24a", stroke="#5a4510")
        s.text(bx + 16, bulk_y + 4, f"X{i+1}", size=10, weight="bold")
        s.wire([(bx, bulk_y + 12), (bx, 880)], "COAX", f"A{i+5}", tag_at=0, sw=3.4, dash="10 4")
        s.raw(f'<path d="M{bx-24},{900} L{bx+24},{900} L{bx+24},{940} L{bx-24},{940} Z" fill="#e8ebee" '
              f'stroke="#26323d" stroke-width="1.4"/>', "over")
        s.text(bx, 924, f"ANT {i+1}", size=10, anchor="middle", weight="bold")
    s.text(1100, bulk_y - 4, "Bulkheads X1-X4 in enclosure bottom (BNC/SMA)", size=9, color="#55606a")
    s.text(1100, bulk_y + 10, "A1-A4: RG316 SMA-M → bulkhead, inside the box", size=9, color="#55606a")
    s.text(600 - 30, 960, "A5-A8: field coax to 5 dBi panel antennas at the door (LMR-195/240, keep ≤ 20 ft)",
           size=9, color="#55606a")
    s.text(ux + 30 + 4 * 34 - 10, ay + 30, "ANT5-8 unused: terminate if reader requires", size=8.5, color="#55606a")

    # notes
    s.table(40, 640, ["Cable", "From", "To", "Type"],
            [["C1", "SW1 P1 (PoE)", "SPL1 PoE IN", "Cat6a 0.5 ft"],
             ["C2", "SPL1 DATA", "U1 LAN", "splitter pigtail"],
             ["C3", "SPL1 12 V", "U1 DC IN", "splitter pigtail"],
             ["C4", "plant switch", "G4 → SW1 P5", "Cat6 CMR, per door"],
             ["C5", "SW1 P2 (PoE)", "K1 RJ45", "Cat6a 0.5 ft"],
             ["A1-A4", "U1 ANT1-4", "X1-X4", "RG316 SMA"],
             ["A5-A8", "X1-X4", "ANT 1-4", "LMR-195/240"]],
            [60, 120, 120, 140], title="Cable list (network / RF)")
    s.note_box(40, 830, 470, "Addressing (fill in per door)", [
        "K1  doorXX  IP ____________  MAC (from /info) ____________",
        "U1  reader  IP ____________  port ______",
        "Broker 192.168.1.50:1883 (config.h MQTT_HOST)",
    ], size=9.5, gap=16)
    s.note_box(1410, 640, 260, "GPI1 trigger", [
        "Pin 12 GPI1+ = +12 V always.",
        "Pin 11 GPI1− → 0 V when the",
        "  beam breaks (B2 via D2).",
        "Reader app: GPI1 trigger →",
        "  start inventory, stop on",
        "  release (+ hold 2-3 s).",
        "Check GPI V range in the full",
        "  manual; meter ≤ 20 mA.",
    ], size=9.5, gap=15)
    s.note_box(1410, 120, 260, "PoE checks", [
        "SW1 budget ≥ SPL1 + K1",
        "  (25.5 W + ~5 W).",
        "Measure K1 draw on bench.",
        "Run U1 at 33 dBm, all 4",
        "  antennas, 10 min: no",
        "  reboot = splitter OK.",
        "Unused P3/P4: cap them.",
    ], size=9.5, gap=15)
    return s


# =====================================================================
# W5  SCHEDULES
# =====================================================================
def sheet_w5():
    s = Sheet("W5", "WIRE · TERMINAL · GLAND SCHEDULES", "every conductor, from → to, with color, gauge and sheet")
    heading(s, 40, 60, "W5 · Wire, terminal and gland schedules",
            "Build from this list. Check each row off as you land it, then ring it out end to end.")
    rows = [
        ["101", "G1 field L", "TB0-1", "BN", "18", "W1"],
        ["101", "TB0-1", "F1 in", "BN", "18", "W1"],
        ["101A", "F1 out", "PSU1 L", "BN", "18", "W1"],
        ["101B", "PSU1 L", "PSU2 L", "BN", "18", "W1"],
        ["102", "TB0-2", "PSU1 N", "BU", "18", "W1"],
        ["102B", "PSU1 N", "PSU2 N", "BU", "18", "W1"],
        ["103", "TB0-3", "PSU1 ⏚", "GN/YE", "18", "W1"],
        ["103B", "PSU1 ⏚", "PSU2 ⏚", "GN/YE", "18", "W1"],
        ["103C", "TB0-3", "backplate PE stud", "GN/YE", "14", "W1"],
        ["103D", "PE stud", "cover bond", "GN/YE", "14", "W1"],
        ["103E", "PE stud", "SW1 ground lug", "GN/YE", "18", "W1"],
        ["201", "PSU1 +V", "TB1-1", "RD", "18", "W1"],
        ["202", "PSU1 −V", "TB1-7", "BK", "18", "W1"],
        ["203", "PSU2 +V", "SW1 V+", "RD", "18", "W1"],
        ["204", "PSU2 −V", "SW1 V−", "BK", "18", "W1"],
        ["205", "TB1-2 (F2)", "K1 CH1 C", "RD", "18", "W2"],
        ["205", "K1 CH1 C", "CH2 C, CH3 C, CH4 C, CH5 C", "RD", "18", "W2"],
        ["206", "TB1-8", "K1 DGND", "BK", "18", "W3"],
        ["301", "K1 CH1 NO", "TB2-1 → HL1/HL2 red", "RD", "18", "W2"],
        ["302", "K1 CH2 NO", "TB2-2 → HL1/HL2 amber", "OR/YE", "18", "W2"],
        ["303", "K1 CH3 NO", "TB2-3 → HL1/HL2 green", "GN", "18", "W2"],
        ["304", "K1 CH4 NO", "TB2-4 → HL1/HL2 buzzer", "WH", "18", "W2"],
        ["305", "K1 CH5 NO", "G7 → S1 X1 (lamp +)", "RD", "18", "W2"],
        ["306", "TB1-11", "TB2-5 → HL1/HL2 common", "BK", "18", "W2"],
        ["308", "TB1-13", "G7 → S1 X2 (lamp −)", "BU", "18", "W2"],
    ]
    rows2 = [
        ["401", "B1 BK (JB1)", "G3 → K1 DI1", "BK", "22", "W3"],
        ["402", "B2 GN (NO)", "G2 → TB3 node (D1/D2 K)", "GN", "22", "W3"],
        ["402A", "TB3 D1 anode", "K1 DI2", "GN", "18", "W3"],
        ["415", "TB3 D2 anode", "U1 GPIO 11 GPI1−", "GN", "22", "W3/W4"],
        ["416", "TB1-6 (F5)", "U1 GPIO 12 GPI1+", "RD", "22", "W1/W4"],
        ["403", "B2 WH (COM)", "G2 → K1 DGND", "WH", "22", "W3"],
        ["404", "S1 14", "G7 → K1 DI3", "WH", "18", "W3"],
        ["405", "S2 14", "G7 → K1 DI4", "GN", "18", "W3"],
        ["406", "S3 14", "G7 → K1 DI5", "OR", "18", "W3"],
        ["407", "TB1-12", "G7 → S1/S2/S3 13 (jumpered)", "BK", "18", "W3"],
        ["410", "TB1-3 (F3)", "G3 → JB1 → B1 BN", "BN/RD", "22", "W3"],
        ["411", "TB1-9", "G3 → JB1 → B1 BU", "BU/BK", "22", "W3"],
        ["412", "TB1-4 (F4)", "G2 → B2 RD", "RD", "22", "W3"],
        ["413", "TB1-10", "G2 → B2 BK", "BK", "22", "W3"],
        ["—", "B2 YE (NC)", "insulated, spare", "YE", "22", "W3"],
        ["C1", "SW1 P1", "SPL1 PoE IN", "Cat6a", "—", "W4"],
        ["C2", "SPL1 data", "U1 LAN", "pigtail", "—", "W4"],
        ["C3", "SPL1 12 V", "U1 DC IN", "pigtail", "—", "W4"],
        ["C4", "plant switch", "G4 → SW1 P5", "Cat6", "—", "W4"],
        ["C5", "SW1 P2", "K1 RJ45", "Cat6a", "—", "W4"],
        ["A1-4", "U1 ANT1-4", "X1-X4", "RG316", "—", "W4"],
        ["A5-8", "X1-X4", "ANT 1-4", "LMR", "—", "W4"],
    ]
    cols = ["Wire", "From", "To", "Color", "AWG", "Sht"]
    wid = [52, 120, 210, 62, 40, 46]
    s.table(40, 110, cols, rows, wid, size=9.4, rowh=17.5, title="Wire schedule — power + outputs")
    s.table(40 + sum(wid) + 30, 110, cols, rows2, wid, size=9.4, rowh=17.5, title="Wire schedule — inputs + network")
    for col in (0, 1):
        n = len(rows if col == 0 else rows2)
        x = 40 + col * (sum(wid) + 30) + sum(wid) - 18
        for i in range(n):
            s.rect(x, 110 + 19 + i * 17.5 + 3, 11, 11, fill="#fff", stroke="#7d8790", sw=1, rx=1, layer="over")

    x3 = 40 + 2 * (sum(wid) + 30) - 10
    tb = [["TB0-1", "L in (G1)", "101 → F1"], ["TB0-2", "N in (G1)", "102 → PSU1"], ["TB0-3", "PE in (G1)", "103 ..."],
          ["TB1-1", "+12 feed", "201 PSU1 +V"], ["TB1-2", "+12 F2 2 A", "205 K1 COMs"],
          ["TB1-3", "+12 F3 ½ A", "410 B1"], ["TB1-4", "+12 F4 ½ A", "412 B2"], ["TB1-5", "+12", "spare / U1 alt"],
          ["TB1-6", "+12 F5 ½ A", "416 U1 GPI1+"], ["TB1-7", "0 V feed", "202 PSU1 −V"], ["TB1-8", "0 V", "206 K1 DGND"],
          ["TB1-9", "0 V", "411 B1"], ["TB1-10", "0 V", "413 B2"], ["TB1-11", "0 V", "306 TB2-5"],
          ["TB1-12", "0 V", "407 CS1 common"], ["TB1-13", "0 V", "308 S1 lamp −"], ["TB1-14", "0 V", "spare / U1 alt"],
          ["TB2-1", "red", "301 in / HL1 + HL2"], ["TB2-2", "amber", "302 in / HL1 + HL2"],
          ["TB2-3", "green", "303 in / HL1 + HL2"], ["TB2-4", "buzzer", "304 in / HL1 + HL2"],
          ["TB2-5", "lamp com", "306 in / HL1 + HL2"],
          ["TB3-D1", "diode → DI2", "402 K / 402A A"], ["TB3-D2", "diode → GPI1−", "402 K / 415 A"]]
    s.table(x3, 110, ["Terminal", "Function", "Wires"], tb, [70, 90, 150], size=9.4, rowh=17.5,
            title="Terminal strips")
    gl = [["G1", "AC in 120 V", "18/3 or 14/3", "PG9"], ["G2", "B2 beam", "22/5", "PG7"],
          ["G3", "B1 truck (JB1)", "22/4", "PG7"], ["G4", "C4 uplink", "Cat6", "PG11 split"],
          ["G5", "HL1 tower", "18/5", "PG9"], ["G6", "HL2 tower  NEW", "18/5", "PG9"],
          ["G7", "CS1 station  NEW", "18/6", "PG9"], ["X1-X4", "antenna bulkheads", "coax", "BNC/SMA"]]
    yb = s.table(x3, 590, ["Gland", "For", "Cable", "Size"], gl, [52, 120, 70, 70], size=9.4, rowh=17.5,
                 title="Glands (bottom face)")
    s.note_box(40, 600, 1000, "Rev 9 changes vs rev 8 (proposed — mark up the DXF when approved)", [
        "1. TB0 AC entry terminals (L / N / PE) and a backplate PE stud; PE to PSU1, PSU2, SW1, cover.",
        "2. TB1 grows to 14 positions (6 × +12 V, 8 × 0 V); TB1-2/3/4 become fused terminals F2/F3/F4.",
        "3. TB2 lamp marshalling (5 × 4-level terminals) so HL1 and HL2 each land on their own clamp.",
        "4. HL2 gets its own gland G6 (rev 8 shared G5 between two cables = not IP67).",
        "5. Operator control station CS1 (S1 load complete, S2 ack/silence, S3 maint key) on K1 DI3-DI5,",
        "    S1 lamp on K1 CH5. New gland G7, cable W-CS 18/6. Wires 305, 308, 404-407.",
        "6. 48 V return gets its own number 204 (rev 8 used 203 for both legs). Sensor supplies 410-413.",
        "7. Firmware 1.1.0: buzzer/pilot topics, blink states, server-presence fail-safe, /info fw + MAC.",
        "8. B2 beam also triggers U1 GPI1 (pin 12 +12 V F5, pin 11 sinks via TB3 diode D2). Wires 402A, 415, 416.",
    ], size=10, gap=16)
    s.note_box(40, 790, 1000, "Added parts for rev 9 (per box, not yet priced)", [
        "TB0: 2 × feed-thru + 1 × PE ground terminal, 2.5 mm² · TB1: 8 more terminals + 3 fused terminal holders",
        "TB2: 5 × 4-level (quattro) terminals + end plate · jumper bars · PE stud kit · TB3: 2 × 1N4007 diode terminals",
        "CS1: 3-hole 22 mm IP65 station, green illuminated 12 V PB, yellow PB, 2-pos keyswitch, legend plates",
        "Cable: 18/6 SJOOW for CS1 · 18/5 for HL2 · 2 × PG9 glands (G6, G7) · fuses 2 A + 2 × 0.5 A (5×20)",
    ], size=10, gap=16)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    for fn in (sheet_w1, sheet_w2, sheet_w3, sheet_w4, sheet_w5):
        sh = fn()
        with open(os.path.join(OUT, f"{sh.num}.svg"), "w") as f:
            f.write(sh.svg())
        print("wrote", sh.num)


if __name__ == "__main__":
    main()
