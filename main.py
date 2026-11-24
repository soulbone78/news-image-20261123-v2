#!/usr/bin/env python3
"""The World in One Day -- Monday 23 November 2026.

A one-page newspaper front page drawn entirely in code for the
make.fun news-image-20261123 competition. Thirty-nine stories
from one day of war, a rescue in Dymer and a drawn Test in
Wellington: a large lead, five medium stories, twenty-seven
small stories and a ticker of briefs. Denser edition: more
stories for blind round 3.

Writes a 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (or
/output/entry.png when the variable is unset). Python standard
library only. Everything is painted on a canvas three times the
final size and shrunk by 3x3 averaging, so the lettering has
smooth, anti-aliased edges.

The masthead, date line, headlines and section labels are set in
Lemon Milk (donationware, Marsnev), a real geometric sans the user
supplied; the body copy is set in Creato Display (SIL Open Font
License, Anugrah Pasau), a real humanist sans he supplied next.
Both fonts' glyph outlines were extracted with fontTools and
baked into lemonmilk_data.py and creato_data.py as polylines,
which this program fills with its own polygon renderer. Lemon
Milk is caps-only, so the body copy uses Creato, which has full
lowercase.
"""

import math
import os
import struct
import sys
import zlib
from math import isqrt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import creato_data
import lemonmilk_data

W = 1024
H = 1024
SUPER = 3            # render scale; the final image is W x H
CW = W * SUPER       # canvas width in device pixels
CH = H * SUPER       # canvas height in device pixels

# ---- palette ---------------------------------------------------
PAPER = (247, 243, 232)
INK = (26, 26, 26)
RED = (198, 32, 32)
GREY = (112, 107, 94)
WHITE = (255, 255, 255)
SKY = (169, 209, 233)
SKY2 = (216, 233, 241)
SEA = (15, 72, 128)
SAND = (216, 196, 150)
HULL = (30, 30, 34)
DECK = (198, 200, 202)
SUN = (242, 196, 66)
SMOKE = (130, 130, 130)
SMOKE2 = (104, 104, 104)
FIRE1 = (220, 60, 20)
FIRE2 = (245, 140, 30)
FIRE3 = (255, 220, 60)
WAVE = (140, 190, 225)
HALL = (152, 144, 130)
ROOF = (96, 90, 80)
GLOBE = (52, 110, 190)
LAND = (96, 180, 96)
TAN = (206, 178, 138)
WINDOW = (70, 120, 170)
RUBBLE = (70, 66, 60)
NAVY = (22, 66, 148)
RUNWAY = (60, 60, 62)
GREEN = (110, 180, 90)
GREEN2 = (88, 150, 70)
PITCH = (214, 190, 140)
ARCH = (196, 160, 110)
MOUNT = (150, 150, 150)
MOUNT2 = (172, 172, 172)
SAFFRON = (255, 153, 51)
IGREEN = (19, 136, 8)
BOARD = (10, 10, 10)
YELLOW = (255, 210, 40)

# ---- canvas ----------------------------------------------------
# All drawing calls take final-pixel coordinates; the sheet scales
# them by SUPER internally. Text sizes are given in "dots": one dot
# is one device pixel per font cell, so dot=2 draws each font cell
# as a single final pixel.


class Sheet:
    def __init__(self):
        self.buf = bytearray(CW * CH * 3)
        self.fill(PAPER)

    def fill(self, color):
        self.buf[:] = bytes(color) * (CW * CH)

    def _span(self, yy, x0, x1, color):
        """One horizontal run of device pixels on row yy."""
        if x1 <= x0 or yy < 0 or yy >= CH:
            return
        x0 = max(0, x0)
        x1 = min(CW, x1)
        if x1 <= x0:
            return
        i = yy * CW * 3 + x0 * 3
        self.buf[i:i + (x1 - x0) * 3] = bytes(color) * (x1 - x0)

    def rect(self, x, y, w, h, color):
        x0 = x * SUPER
        y0 = y * SUPER
        x1 = (x + w) * SUPER
        y1 = (y + h) * SUPER
        for yy in range(y0, y1):
            self._span(yy, x0, x1, color)

    def frame(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def cell(self, x, y, d, color):
        """A d-by-d block of device pixels (one font cell)."""
        for yy in range(y, y + d):
            self._span(yy, x, x + d, color)

    def disc(self, cx, cy, r, color):
        cx2, cy2, r2 = cx * SUPER, cy * SUPER, r * SUPER
        for yy in range(cy2 - r2, cy2 + r2 + 1):
            dy = yy - cy2
            dx = isqrt(max(0, r2 * r2 - dy * dy))
            self._span(yy, cx2 - dx, cx2 + dx + 1, color)

    def poly(self, pts, color):
        """Filled polygon, even-odd scanline fill."""
        pts = [(int(round(x * SUPER)), int(round(y * SUPER)))
               for x, y in pts]
        ymin = max(0, min(p[1] for p in pts))
        ymax = min(CH - 1, max(p[1] for p in pts))
        n = len(pts)
        for yy in range(ymin, ymax + 1):
            xs = []
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self._span(yy, int(xs[k]), int(xs[k + 1]) + 1, color)

    def polys(self, contours, color):
        """Filled glyph: several contours at once, even-odd
        scanline fill, so counters (the holes in A, D, O, R, B)
        stay empty. Horizontal edges never cross a scanline, so
        they are dropped when the edge list is built."""
        edges = []
        ymin, ymax = CH, -1
        for pts in contours:
            dev = [(int(round(x * SUPER)), int(round(y * SUPER)))
                   for x, y in pts]
            for i, (x0, y0) in enumerate(dev):
                x1, y1 = dev[(i + 1) % len(dev)]
                if y0 != y1:
                    edges.append((x0, y0, x1, y1))
            ymin = min(ymin, min(p[1] for p in dev))
            ymax = max(ymax, max(p[1] for p in dev))
        ymin = max(0, ymin)
        ymax = min(CH - 1, ymax)
        for yy in range(ymin, ymax + 1):
            xs = []
            for x0, y0, x1, y1 in edges:
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self._span(yy, int(xs[k]), int(xs[k + 1]) + 1, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        """Bresenham line, t final pixels thick."""
        x0, y0, x1, y1 = x0 * SUPER, y0 * SUPER, x1 * SUPER, y1 * SUPER
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = t * SUPER // 2
        while True:
            for yy in range(y0 - half, y0 + half + 1):
                self._span(yy, x0 - half, x0 + half + 1, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy


# ---- Creato Display --------------------------------------------
# Real font outlines (baked into creato_data.py by
# extract_creato.py). A glyph is [advance, contour, ...] with y
# running down from the cap line, so `size` is the cap height in
# final pixels and y is the top of the capitals; descenders run
# below y + size. Creato has full lowercase and is proportional,
# so body copy is wrapped by real measured advances (wrap_creato
# / para_creato below), never by character count.

CREATO = {"regular": creato_data.REGULAR, "bold": creato_data.BOLD}
CREATO_CAP = creato_data.CAP


def creato_w(s, size, weight="regular"):
    """Width of a string in final pixels at the given cap height."""
    face = CREATO[weight]
    scale = size / CREATO_CAP
    return int(round(sum(face[ch][0] for ch in s) * scale))


def draw_creato(sh, s, x, y, size, weight, color):
    face = CREATO[weight]
    scale = size / CREATO_CAP
    cx = float(x)
    for ch in s:
        glyph = face.get(ch)
        if glyph is None:
            continue
        if len(glyph) > 1:
            contours = []
            for contour in glyph[1:]:
                pts = []
                for i in range(0, len(contour), 2):
                    pts.append((cx + contour[i] * scale,
                                y + contour[i + 1] * scale))
                contours.append(pts)
            sh.polys(contours, color)
        cx += glyph[0] * scale


def centre_creato(sh, s, cx, y, size, weight, color):
    draw_creato(sh, s, cx - creato_w(s, size, weight) // 2, y, size,
                weight, color)


# ---- Lemon Milk ------------------------------------------------
# Real font outlines (baked into lemonmilk_data.py by
# extract_lemonmilk.py). A glyph is [advance, contour, ...] with
# y running down from the cap line, so `size` is the cap height
# in final pixels and y is the top of the capitals. Lemon Milk is
# caps-only: callers pass uppercase text (lowercase would render
# as capitals anyway, since the font maps them to the same glyphs).

LEMON = {"bold": lemonmilk_data.BOLD, "regular": lemonmilk_data.REGULAR}
LEMON_CAP = lemonmilk_data.CAP


def lemon_w(s, size, weight):
    """Width of a string in final pixels at the given cap height."""
    face = LEMON[weight]
    scale = size / LEMON_CAP
    return int(round(sum(face[ch][0] for ch in s) * scale))


def fit_size(s, max_w, size, weight):
    """The largest cap height at or below `size` that fits s into
    max_w final pixels (never below 6, so a headline stays legible)."""
    while size > 6 and lemon_w(s, size, weight) > max_w:
        size -= 1
    return size


def draw_lemon(sh, s, x, y, size, weight, color):
    face = LEMON[weight]
    scale = size / LEMON_CAP
    cx = float(x)
    for ch in s:
        glyph = face.get(ch)
        if glyph is None:
            continue
        if len(glyph) > 1:
            contours = []
            for contour in glyph[1:]:
                pts = []
                for i in range(0, len(contour), 2):
                    pts.append((cx + contour[i] * scale,
                                y + contour[i + 1] * scale))
                contours.append(pts)
            sh.polys(contours, color)
        cx += glyph[0] * scale


def centre_lemon(sh, s, cx, y, size, weight, color):
    draw_lemon(sh, s, cx - lemon_w(s, size, weight) // 2, y, size,
               weight, color)


def wrap_creato(s, max_w, size, weight="regular"):
    """Greedy word wrap to at most `max_w` final pixels a line,
    measured with the font's real advances."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if creato_w(trial, size, weight) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para_creato(sh, s, x, y, w, size, weight, color, leading):
    """Draw wrapped body copy in a box of width w; return the y
    just below the last line."""
    for ln in wrap_creato(s, w, size, weight):
        draw_creato(sh, ln, x, y, size, weight, color)
        y += leading
    return y


def burst_points(cx, cy, r_out, r_in, spikes, rot=0.0):
    """Alternating-radius polygon: an explosion starburst."""
    pts = []
    for i in range(spikes * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + math.pi * i / spikes
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def explosion(sh, cx, cy, r):
    sh.poly(burst_points(cx, cy, r, r * 0.45, 9, 0.2), FIRE1)
    sh.poly(burst_points(cx, cy, r * 0.62, r * 0.30, 8, 0.5), FIRE2)
    sh.poly(burst_points(cx, cy, r * 0.34, r * 0.16, 7, 0.1), FIRE3)


def _yo(y, v, s):
    """A y-offset inside an illustration, scaled by s."""
    return y + int(round(v * s))


def _sz(v, s):
    """A size inside an illustration, scaled by s (never 0)."""
    return max(1, int(round(v * s)))


# ---- illustrations ---------------------------------------------
# Flat vector scenes, one per story. Each takes the sheet and the
# box it may paint in (final pixels).

def art_gulf(sh, x, y, w, h):
    """The Strait: two tankers burning under a desert sun.

    Drawn for a 288 px tall box and scaled to the height given,
    so the lead art can shrink as the page gains stories.
    """
    s = h / 288.0
    sea_top = _yo(y, 140, s)
    sh.rect(x, y, w, _sz(140, s), SKY)
    sh.disc(x + 414, _yo(y, 42, s), _sz(26, s), SUN)
    sh.poly([(x, _yo(y, 130, s)), (x + 170, _yo(y, 112, s)),
             (x + 320, _yo(y, 124, s)), (x + w, _yo(y, 108, s)),
             (x + w, sea_top), (x, sea_top)], SAND)
    sh.rect(x, sea_top, w, h - _sz(140, s), SEA)
    # missile trails arcing down from the sky
    sh.line(x + 44, _yo(y, 22, s), x + 94, _yo(y, 172, s), WHITE, 2)
    sh.line(x + 414, _yo(y, 26, s), x + 434, _yo(y, 196, s), WHITE, 2)
    sh.disc(x + 44, _yo(y, 22, s), _sz(3, s), WHITE)
    sh.disc(x + 414, _yo(y, 26, s), _sz(3, s), WHITE)
    # tanker one, off Bahrain
    sh.rect(x + 24, _yo(y, 192, s), 180, _sz(34, s), HULL)
    sh.rect(x + 134, _yo(y, 168, s), 34, _sz(24, s), DECK)
    sh.rect(x + 142, _yo(y, 160, s), 18, _sz(8, s), RED)
    sh.rect(x + 24, _yo(y, 192, s), 180, _sz(5, s), DECK)
    # tanker two, near Hormuz
    sh.rect(x + 284, _yo(y, 212, s), 170, _sz(30, s), HULL)
    sh.rect(x + 304, _yo(y, 188, s), 30, _sz(24, s), DECK)
    sh.rect(x + 311, _yo(y, 180, s), 16, _sz(8, s), RED)
    sh.rect(x + 284, _yo(y, 212, s), 170, _sz(5, s), DECK)
    # smoke over the first tanker
    sh.disc(x + 64, _yo(y, 136, s), _sz(16, s), SMOKE)
    sh.disc(x + 84, _yo(y, 122, s), _sz(20, s), SMOKE2)
    sh.disc(x + 108, _yo(y, 138, s), _sz(14, s), SMOKE)
    sh.disc(x + 420, _yo(y, 168, s), _sz(13, s), SMOKE)
    # explosions
    explosion(sh, x + 94, _yo(y, 178, s), _sz(30, s))
    explosion(sh, x + 434, _yo(y, 200, s), _sz(22, s))
    # wave lines and place labels
    for wx, wy, wl in [(36, 252, 120), (102, 266, 74), (296, 258, 130),
                       (330, 268, 64)]:
        sh.rect(x + wx, _yo(y, wy, s), wl, _sz(3, s), WAVE)
    draw_creato(sh, "BAHRAIN", x + 10, y + h - 20, 11, "regular", WHITE)
    draw_creato(sh, "HORMUZ", x + w - 10 - creato_w("HORMUZ", 11),
                y + h - 20, 11, "regular", WHITE)


def art_climate(sh, x, y, w, h):
    """Antalya: the summit hall under a falling-earth globe.

    Drawn for a 100 px tall box and scaled to the height given.
    """
    s = h / 100.0
    sh.rect(x, y, w, h, SKY2)
    sh.disc(x + w - 42, _yo(y, 24, s), _sz(14, s), SUN)
    # smokestacks with drifting smoke
    sh.rect(x + 26, _yo(y, 26, s), 14, _sz(44, s), GREY)
    sh.rect(x + 46, _yo(y, 34, s), 14, _sz(36, s), GREY)
    sh.disc(x + 33, _yo(y, 18, s), _sz(9, s), SMOKE)
    sh.disc(x + 50, _yo(y, 12, s), _sz(7, s), SMOKE2)
    # the hall: long low block with a roof and a row of windows
    sh.rect(x + 10, _yo(y, 56, s), w - 20, _sz(44, s), HALL)
    sh.poly([(x + 4, _yo(y, 56, s)), (x + w - 4, _yo(y, 56, s)),
             (x + w - 30, _yo(y, 42, s)), (x + 30, _yo(y, 42, s))], ROOF)
    for i in range(9):
        sh.rect(x + 26 + i * 46, _yo(y, 70, s), 26, _sz(16, s), WINDOW)
    # the globe, with a red line falling across it
    gx, gy = x + w // 2, _yo(y, 50, s)
    sh.disc(gx, gy, _sz(34, s), GLOBE)
    sh.disc(gx - 12, gy - _sz(10, s), _sz(9, s), LAND)
    sh.disc(gx + 12, gy + _sz(8, s), _sz(11, s), LAND)
    sh.disc(gx + 4, gy - _sz(16, s), _sz(6, s), LAND)
    sh.line(gx - 24, gy - _sz(18, s), gx - 6, gy + _sz(2, s), RED, 3)
    sh.line(gx - 6, gy + _sz(2, s), gx + 8, gy - _sz(6, s), RED, 3)
    sh.line(gx + 8, gy - _sz(6, s), gx + 24, gy + _sz(14, s), RED, 3)
    sh.poly([(gx + 24, gy + _sz(14, s)), (gx + 14, gy + _sz(12, s)),
             (gx + 20, gy + _sz(4, s))], RED)


def art_kyiv(sh, x, y, w, h):
    """A five-storey flat block, its corner smashed away.

    Drawn for a 100 px tall box and scaled to the height given.
    """
    s = h / 100.0
    sh.rect(x, y, w, h, SKY2)
    sh.disc(x + w - 36, _yo(y, 20, s), _sz(13, s), SUN)
    bx, by, bw, bh = x + 26, _yo(y, 20, s), w - 52, _sz(80, s)
    sh.rect(bx, by, bw, bh, TAN)
    for row in range(4):
        for col in range(11):
            wx = bx + 12 + col * 38
            wy = by + _sz(10, s) + row * _sz(18, s)
            if col >= 9 and row <= 1:
                continue  # the smashed corner has no windows
            sh.rect(wx, wy, 22, _sz(11, s), WINDOW)
    # the smashed corner: dark rubble and smoke
    sh.poly([(bx + bw - 70, by), (bx + bw, by), (bx + bw, by + _sz(44, s)),
             (bx + bw - 44, by + _sz(30, s)), (bx + bw - 62, by + _sz(16, s))],
            RUBBLE)
    sh.disc(bx + bw - 30, by - _sz(6, s), _sz(16, s), SMOKE)
    sh.disc(bx + bw - 52, by - _sz(12, s), _sz(12, s), SMOKE2)
    sh.disc(bx + bw - 12, by + _sz(6, s), _sz(10, s), SMOKE)
    # rescue lights at the foot of the block
    sh.disc(bx + 60, y + h - 8, _sz(5, s), RED)
    sh.disc(bx + 82, y + h - 8, _sz(5, s), FIRE2)
    sh.disc(bx + 104, y + h - 8, _sz(5, s), RED)


def art_nato(sh, x, y, w, h):
    """Brussels: the compass star over a runway, jets overhead.

    Drawn for an 88 px tall box and scaled to the height given.
    """
    s = h / 88.0
    sh.rect(x, y, w, h, SKY2)
    cx, cy = x + w // 2, _yo(y, 36, s)
    sh.disc(cx, cy, _sz(30, s), NAVY)
    r = _sz(26, s)
    q = _sz(5, s)
    sh.poly([(cx, cy - r), (cx + q, cy - q), (cx + r, cy),
             (cx + q, cy + q), (cx, cy + r), (cx - q, cy + q),
             (cx - r, cy), (cx - q, cy - q)], WHITE)
    # two jets crossing the sky
    for jx, jy in [(x + 18, _yo(y, 12, s)), (x + w - 52, _yo(y, 18, s))]:
        sh.poly([(jx, jy + _sz(4, s)), (jx + 26, jy),
                 (jx + 30, jy + _sz(3, s)), (jx + 12, jy + _sz(7, s)),
                 (jx + 16, jy + _sz(12, s)), (jx + 9, jy + _sz(8, s)),
                 (jx, jy + _sz(8, s))], INK)
    # the runway with its dashed centre line
    sh.rect(x, y + h - _sz(22, s), w, _sz(22, s), RUNWAY)
    for i in range(8):
        sh.rect(x + 10 + i * 40, y + h - _sz(12, s), 20, _sz(3, s), WHITE)


def art_delhi(sh, x, y, w, h):
    """New Delhi: mountains, the Gate, and two flags.

    Drawn for an 88 px tall box and scaled to the height given.
    """
    s = h / 88.0
    sh.rect(x, y, w, h, (240, 230, 205))
    sh.poly([(x, y + h), (x + 90, _yo(y, 26, s)), (x + 180, y + h)], MOUNT)
    sh.poly([(x + 120, y + h), (x + 230, _yo(y, 18, s)), (x + 320, y + h)],
            MOUNT2)
    # the Gate: arch, dome and doorway
    gx = x + w // 2
    sh.rect(gx - 30, _yo(y, 40, s), 60, _sz(44, s), ARCH)
    sh.rect(gx - 36, _yo(y, 32, s), 72, _sz(10, s), ARCH)
    sh.disc(gx, _yo(y, 32, s), _sz(10, s), ARCH)
    sh.rect(gx - 8, _yo(y, 56, s), 16, _sz(28, s), SKY2)
    sh.disc(gx, _yo(y, 56, s), _sz(8, s), SKY2)
    # Nepal's pennant on the left, India's tricolour on the right
    px = x + 22
    sh.line(px, _yo(y, 16, s), px, y + h - 6, INK, 2)
    sh.poly([(px, _yo(y, 18, s)), (px + 26, _yo(y, 26, s)),
             (px, _yo(y, 34, s))], RED)
    sh.poly([(px, _yo(y, 34, s)), (px + 20, _yo(y, 40, s)),
             (px, _yo(y, 46, s))], RED)
    fx = x + w - 58
    sh.line(fx, _yo(y, 16, s), fx, y + h - 6, INK, 2)
    sh.rect(fx, _yo(y, 18, s), 34, _sz(8, s), SAFFRON)
    sh.rect(fx, _yo(y, 26, s), 34, _sz(8, s), WHITE)
    sh.rect(fx, _yo(y, 34, s), 34, _sz(8, s), IGREEN)
    sh.disc(fx + 17, _yo(y, 30, s), _sz(3, s), NAVY)


def art_cricket(sh, x, y, w, h):
    """Wellington: the pitch, the stumps, and 720 for 9.

    Drawn for an 88 px tall box and scaled to the height given.
    """
    s = h / 88.0
    sh.rect(x, y, w, h, GREEN)
    sh.rect(x, y + h - _sz(26, s), w, _sz(26, s), GREEN2)
    # the pitch, a pale strip down the middle
    sh.rect(x + w // 2 - 20, _yo(y, 8, s), 40, h - _sz(16, s), PITCH)
    # stumps at each end
    for sy in (_yo(y, 14, s), y + h - _sz(26, s)):
        for k in range(3):
            sh.rect(x + w // 2 - 9 + k * 7, sy, 3, _sz(12, s), WHITE)
    # the ball, mid-flight
    sh.disc(x + w - 46, _yo(y, 22, s), _sz(7, s), RED)
    sh.disc(x + w - 48, _yo(y, 20, s), _sz(2, s), WHITE)
    # the scoreboard, Creato Bold centred in the black box
    bx, by = x + w - 106, _yo(y, 34, s)
    sh.frame(bx, by, 96, _sz(34, s), WHITE, 1)
    sh.rect(bx + 1, by + 1, 94, _sz(32, s), BOARD)
    score = "720/9"
    draw_creato(sh, score, bx + (96 - creato_w(score, 9, "bold")) // 2,
                by + 5, 9, "bold", YELLOW)


def art_libya(sh, x, y, w, h):
    """Benghazi: a Russian warship sinking, hit by a sea drone.

    Drawn for a 48 px tall box and scaled to the height given.
    A grey corvette lists with its bow rising out of a dark sea,
    an explosion starburst amidships, smoke above, and a small
    drone in the sky over a thin sandy coast.
    """
    s = h / 48.0
    sh.rect(x, y, w, _sz(12, s), SKY2)
    sh.rect(x, y + _sz(12, s), w, _sz(4, s), SAND)
    sh.rect(x, y + _sz(16, s), w, h - _sz(16, s), SEA)
    # the drone: a small dark cross in the sky
    dx, dy = x + w - 52, _yo(y, 5, s)
    sh.rect(dx - 7, dy, 14, _sz(2, s), INK)
    sh.rect(dx - 2, dy - 2, 4, _sz(6, s), INK)
    sh.disc(dx - 7, dy, _sz(2, s), INK)
    sh.disc(dx + 7, dy, _sz(2, s), INK)
    # the listing corvette: hull tilted, bow (right) rising
    sh.poly([(x + 46, _yo(y, 34, s)), (x + 276, _yo(y, 20, s)),
             (x + 276, _yo(y, 28, s)), (x + 46, _yo(y, 42, s))], HULL)
    sh.poly([(x + 120, _yo(y, 29, s)), (x + 180, _yo(y, 25, s)),
             (x + 180, _yo(y, 31, s)), (x + 120, _yo(y, 34, s))], DECK)
    sh.line(x + 210, _yo(y, 24, s), x + 214, _yo(y, 12, s), HULL, 2)
    # smoke above the blast
    sh.disc(x + 150, _yo(y, 10, s), _sz(9, s), SMOKE)
    sh.disc(x + 166, _yo(y, 6, s), _sz(7, s), SMOKE2)
    sh.disc(x + 138, _yo(y, 16, s), _sz(6, s), SMOKE)
    # the explosion amidships
    explosion(sh, x + 158, _yo(y, 28, s), _sz(13, s))
    # wave lines and the bow wake
    for wx, wy, wl in [(24, 40, 90), (220, 38, 80), (120, 44, 60)]:
        sh.rect(x + wx, _yo(y, wy, s), wl, _sz(2, s), WAVE)


# ---- the page --------------------------------------------------

LEAD_BODY = (
    "Bahrain demands Iran pay full compensation for the Sitra "
    "strike and urges UN action, as Houthis claim a hit on Saudi "
    "Arabia's Rabigh refinery. Two tankers burn near Hormuz, and "
    "Trump warns of new US strikes in 2027 if no deal is reached."
)
COP_BODY = (
    "The UN climate summit in Antalya fails as the EU rejects "
    "a final text with no fossil fuels and no new money."
)
KYIV_BODY = (
    "A boy of seven is pulled alive after 14 hours under a flat "
    "block in Dymer; a woman of 79 is also saved."
)
NATO_BODY = "Allies meet in Brussels after Russian missiles and a drone cross into Poland."
LIBYA_BODY = "Zelenskyy says sea drones sank a Russian corvette at Benghazi and hit a cargo ship."
CRICKET_BODY = "Mitchell and Phillips bat 43 overs as New Zealand hold on for a draw."

# ---- small stories: 27 in a 3 x 9 grid ------------------------
# Each is (headline, body): the headline fits one line of Lemon
# Milk Bold at cap 10 in 314 px, the body two lines of Creato
# Regular at cap 10 (both measured, not guessed). All 27 are real
# news of Monday 23 November 2026, researched for this denser
# edition: 19 are kept from the evening overhaul, 8 are fresh
# Monday stories. No detail is used that could not be verified;
# where a figure was unconfirmed it was left out.
SMALL_STORIES = [
    # row 1
    ("DEMOCRATS WIN BIG HOUSE MAJORITY",
     "Foxx concedes after a recount confirms Hubbard's 330-vote "
     "win; Democrats hold 258 seats."),
    ("WALL STREET FUTURES REBOUND",
     "Dow futures jump 798 points as stocks rebound after the "
     "worst week in six years."),
    ("BURNHAM HAILS LANDMARK EU DEAL",
     "The PM tells MPs the 17 billion pound deal is the biggest "
     "growth measure of this parliament."),
    # row 2
    ("KOSPI PLUNGES, SIDECAR TRIPS AGAIN",
     "Seoul's index falls as much as 5.8% intraday and closes "
     "down 3.31%; a 10 trillion won fund is readied."),
    ("ANTHROPIC SHARES FALL AFTER IPO",
     "Shares slide after a record 81.3 billion dollar listing "
     "briefly minted decabillionaires."),
    ("BEPICOLOMBO ENTERS MERCURY ORBIT",
     "The European-Japanese probe reaches Mercury after eight "
     "years in space; a glitch is under study."),
    # row 3
    ("NHS LAUNCHES HUGE AI CANCER TRIAL",
     "The world's largest trial asks whether AI can spot breast "
     "cancer earlier, the BBC reports."),
    ("49ERS TROUNCE VIKINGS 35-10",
     "San Francisco dominate Minnesota 35-10 in Mexico City; "
     "the Chiefs and Bills also win."),
    ("LIVERPOOL THRASH MAN UTD 4-0",
     "Liverpool rout Manchester United at Anfield in Mauricio "
     "Pochettino's first game as United coach."),
    # row 4
    ("KENYA, DR CONGO RESTORE TIES",
     "Ruto and Tshisekedi agree at an Oyo summit to restore "
     "full diplomatic ties after a three-year rift."),
    ("FIFA TO CONFIRM UK AS 2035 HOST",
     "The UK's four home nations will stage the 2035 Women's "
     "World Cup, the first in Britain since 1966."),
    ("METS SIGN SKUBAL FOR RECORD 450M",
     "The New York Mets agree a record nine-year, 450 million "
     "dollar deal for pitcher Tarik Skubal."),
    # row 5
    ("BOLSONARO STILL IN INTENSIVE CARE",
     "Brazil's jailed ex-president is stable in intensive care "
     "with a bowel obstruction."),
    ("IG METALL STRIKES WIDEN",
     "Germany's biggest union calls 23,000 car and shipyard "
     "workers out as industrial strikes spread."),
    ("PROTEST AT SEATTLE AIRPORT",
     "Crowds gather after footage shows ICE agents detaining a "
     "father and daughter boarding a flight."),
    # row 6
    ("IOWA BLAST PUT OFF TO WEDNESDAY",
     "A controlled detonation of unstable munitions at an Iowa "
     "Army plant is postponed after a court order."),
    ("INDIA, CHINA OPEN BORDER TALKS",
     "Commanders meet in Arunachal Pradesh for 10 days of talks "
     "to ease border tensions."),
    ("INDONESIA FIRE: 24 BODY BAGS FOUND",
     "Rescuers recover 24 body bags from the candy factory fire "
     "in Cikande; dozens are still missing."),
    # row 7
    ("BITCOIN ETFS SHED 1.79BN IN A WEEK",
     "Spot bitcoin funds record 1.79 billion dollars in weekly "
     "outflows as sentiment turns sharply."),
    ("AUSTRALIA BACK IN WTC TOP TWO",
     "Australia move up to second in the World Test "
     "Championship after the Wellington draw."),
    ("NEPAL PM MEETS MODI IN DELHI",
     "Nepal PM Balendra Shah holds talks with PM Modi in Delhi "
     "on a state visit."),
    # row 8
    ("DRONES HIT COLOMBIA POLICE BASE",
     "Explosive drones hit a police base in Cucuta, injuring "
     "civilians and damaging 60 homes."),
    ("EU AND INDONESIA SIGN TRADE DEAL",
     "After a decade of talks, the EU and Indonesia sign a pact "
     "scrapping most tariffs on goods."),
    ("EURO INFLATION RISES TO 4.0%",
     "Euro area inflation climbs to 4.0% in new Eurostat "
     "figures, adding pressure on rates."),
    # row 9
    ("DRONES HIT UN SITE IN KHARTOUM",
     "Drone strikes hit homes and a United Nations building in "
     "Sudan's capital."),
    ("M6.5 QUAKE STRIKES VANUATU REGION",
     "A deep earthquake shakes the Vanuatu region, 598 km down."),
    ("US LEAD OVER CHINA NARROWS",
     "America's edge over China in Asia falls to its lowest "
     "since 2018, the Lowy Index finds."),
]

# Ticker briefs: six more items, three per line.
TICKER_1 = "GOLD REBOUNDS PAST 3,600 - AVENGERS TRAILER OUT - COWBOYS SCORE 51"
TICKER_2 = "TRUMP HEADS TO LA FOR REAGAN SPEECH - CENTRICA BOSS WARNS ON ENERGY BILLS - PANAMA MINE TALKS"


def small_box(sh, bx, ry, headline, body):
    """One small story in the grid: a Lemon Milk headline over
    Creato body copy, 314 px of text width, at most 2 body lines
    so nothing can spill into the row below."""
    draw_lemon(sh, headline, bx + 8, ry + 3,
               fit_size(headline, 314, 10, "bold"), "bold", INK)
    y = ry + 16
    for ln in wrap_creato(body, 314, 10)[:2]:
        draw_creato(sh, ln, bx + 8, y, 10, "regular", INK)
        y += 12


def build_page(sh):
    sh.frame(4, 4, 1016, 1016, INK, 2)

    # masthead: Lemon Milk Bold, fitted to the page width
    mast_size = fit_size("THE WORLD IN ONE DAY", 1000, 44, "bold")
    centre_lemon(sh, "THE WORLD IN ONE DAY", 512, 6, mast_size, "bold", INK)
    date_size = fit_size("MONDAY 23 NOVEMBER 2026", 1000, 22, "regular")
    centre_lemon(sh, "MONDAY 23 NOVEMBER 2026", 512, 54, date_size,
                 "regular", RED)
    centre_creato(sh, "THIRTY-NINE STORIES FROM A DAY OF WAR, A RESCUE IN DYMER AND A DRAW IN WELLINGTON",
                  512, 82, 11, "regular", GREY)
    sh.rect(12, 100, 1000, 3, INK)
    sh.rect(12, 104, 1000, 1, INK)

    # ---- lead story --------------------------------------------
    sh.frame(10, 108, 1004, 180, INK, 2)
    art_gulf(sh, 12, 110, 480, 176)
    sh.rect(492, 110, 2, 176, INK)
    tx = 504
    draw_lemon(sh, "LEAD STORY: THE GULF WAR", tx, 114,
               fit_size("LEAD STORY: THE GULF WAR", 498, 12, "regular"),
               "regular", RED)
    for i, line in enumerate(("BAHRAIN DEMANDS IRAN", "PAY FOR THE STRIKES",
                              "AS GULF WAR WIDENS")):
        draw_lemon(sh, line, tx, 130 + i * 22,
                   fit_size(line, 498, 19, "bold"), "bold", INK)
    para_creato(sh, LEAD_BODY, tx, 200, 498, 12, "regular", INK, 15)
    sh.rect(tx, 264, 498, 2, RED)
    draw_creato(sh, "2 HURT, 2 TANKERS, 1 REFINERY HIT CLAIMED", tx, 268, 12, "bold", RED)

    # ---- middle row: climate and Kyiv --------------------------
    sh.frame(10, 296, 498, 155, INK, 2)
    art_climate(sh, 12, 298, 494, 52)
    sh.rect(12, 350, 494, 2, INK)
    draw_lemon(sh, "CLIMATE: ANTALYA, TURKEY", 20, 354,
               fit_size("CLIMATE: ANTALYA, TURKEY", 474, 12, "regular"),
               "regular", RED)
    for i, line in enumerate(("COP31 COLLAPSES WITH NO",
                              "DEAL ON FOSSIL FUELS")):
        draw_lemon(sh, line, 20, 372 + i * 20,
                   fit_size(line, 474, 14, "bold"), "bold", INK)
    para_creato(sh, COP_BODY, 20, 414, 474, 12, "regular", INK, 15)

    sh.frame(516, 296, 498, 155, INK, 2)
    art_kyiv(sh, 518, 298, 494, 52)
    sh.rect(518, 350, 494, 2, INK)
    draw_lemon(sh, "WAR IN UKRAINE: KYIV REGION", 526, 354,
               fit_size("WAR IN UKRAINE: KYIV REGION", 474, 12, "regular"),
               "regular", RED)
    for i, line in enumerate(("BOY, 7, PULLED ALIVE",
                              "AS DYMER TOLL HITS 11")):
        draw_lemon(sh, line, 526, 372 + i * 20,
                   fit_size(line, 474, 14, "bold"), "bold", INK)
    para_creato(sh, KYIV_BODY, 526, 414, 474, 12, "regular", INK, 15)

    # ---- bottom row: NATO, Libya, cricket ----------------------
    boxes = [
        (10, "EUROPE: BRUSSELS", "NATO MEETS AS POLAND",
         "CITES INCURSION", NATO_BODY, art_nato),
        (348, "WAR AT SEA: LIBYA", "UKRAINE SINKS RUSSIAN WARSHIP",
         "OFF LIBYA, KYIV SAYS", LIBYA_BODY, art_libya),
        (686, "SPORT: WELLINGTON TEST", "NZ BAT OUT 120 OVERS",
         "TO DENY INDIA A WIN", CRICKET_BODY, art_cricket),
    ]
    for bx, kicker, head1, head2, body, art in boxes:
        sh.frame(bx, 459, 330, 135, INK, 2)
        art(sh, bx + 2, 461, 326, 44)
        sh.rect(bx + 2, 505, 326, 2, INK)
        draw_lemon(sh, kicker, bx + 10, 511,
                   fit_size(kicker, 314, 12, "regular"), "regular", RED)
        draw_lemon(sh, head1, bx + 10, 529,
                   fit_size(head1, 314, 11, "bold"), "bold", INK)
        draw_lemon(sh, head2, bx + 10, 547,
                   fit_size(head2, 314, 11, "bold"), "bold", INK)
        para_creato(sh, body, bx + 10, 565, 314, 11, "regular", INK, 14)

    # ---- small stories: 27 in a 3 x 9 grid --------------------
    # One outer frame, 1 px rules between rows and columns, and
    # the stories in reading order (row-major).
    grid_y, grid_h = 602, 367
    sh.frame(10, grid_y, 1006, grid_h, INK, 1)
    rows = [grid_y + round(i * grid_h / 9) for i in range(10)]
    for ry in rows[1:-1]:
        sh.rect(11, ry, 1004, 1, INK)
    for vx in (344, 682):
        sh.rect(vx, grid_y + 1, 1, grid_h - 2, INK)
    for i, (headline, body) in enumerate(SMALL_STORIES):
        row, col = divmod(i, 3)
        small_box(sh, 10 + col * 338, rows[row], headline, body)

    # ---- ticker and footer -------------------------------------
    sh.frame(10, 976, 1004, 32, INK, 2)
    lead = "ALSO TODAY:"
    draw_lemon(sh, lead, 20, 981, 11, "bold", INK)
    # A full 12 px gap after the Lemon Milk lead-in: the font's
    # own space advance (under 5 px at this size) reads as no
    # gap at all next to the Creato text that follows.
    rest_x = 20 + lemon_w(lead, 11, "bold") + 12
    draw_creato(sh, TICKER_1, rest_x, 981, 10, "regular", INK)
    draw_creato(sh, TICKER_2, 20, 993, 10, "regular", INK)
    centre_creato(sh, "DRAWN IN CODE - NO PHOTO - SOURCES: REUTERS, AP, CNBC - "
                      "23 NOVEMBER 2026", 512, 1010, 8, "regular", GREY)


# ---- output ----------------------------------------------------

def shrink(sh):
    """Average each 3x3 device block down to one final pixel."""
    out = bytearray(W * H * 3)
    src = sh.buf
    for fy in range(H):
        r0 = fy * 3 * CW * 3
        r1 = r0 + CW * 3
        r2 = r1 + CW * 3
        o = fy * W * 3
        for fx in range(W):
            i0 = r0 + fx * 9
            j0 = r1 + fx * 9
            k0 = r2 + fx * 9
            out[o] = (src[i0] + src[i0 + 3] + src[i0 + 6]
                      + src[j0] + src[j0 + 3] + src[j0 + 6]
                      + src[k0] + src[k0 + 3] + src[k0 + 6] + 4) // 9
            out[o + 1] = (src[i0 + 1] + src[i0 + 4] + src[i0 + 7]
                          + src[j0 + 1] + src[j0 + 4] + src[j0 + 7]
                          + src[k0 + 1] + src[k0 + 4] + src[k0 + 7] + 4) // 9
            out[o + 2] = (src[i0 + 2] + src[i0 + 5] + src[i0 + 8]
                          + src[j0 + 2] + src[j0 + 5] + src[j0 + 8]
                          + src[k0 + 2] + src[k0 + 5] + src[k0 + 8] + 4) // 9
            o += 3
    return bytes(out)


def write_png(path, rgb):
    """Encode RGB bytes as a PNG (8-bit, colour type 2)."""
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    sh = Sheet()
    build_page(sh)
    n = write_png(os.path.join(out_dir, "entry.png"), shrink(sh))
    print("wrote %d bytes to %s" % (n, os.path.join(out_dir, "entry.png")))


if __name__ == "__main__":
    main()
