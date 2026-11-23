"""Monday 23 November 2026, as a one-page newspaper front page.

This program draws the whole page in code and saves it as a
1024 by 1024 PNG. It is deliberately boring about its inputs:
only the Python standard library, nothing fetched, no clock,
no dice. Run it twice and the two files are the same byte for
byte.

What the page carries, top to bottom:

  * a masthead with the date, Monday 23 November 2026
  * the lead story: Iranian missiles strike a civilian plant in
    Sitra, Bahrain, and two tankers burn near the Strait of
    Hormuz, while Saudi jets down a Houthi missile and the US
    denies an Iranian claim that it hit a US jet
  * COP31 in Antalya ending with no deal on fossil fuels
  * a Russian drone wrecking a five-storey flat block in the
    Kyiv region, 14 feared trapped
  * NATO meeting in Brussels after missiles and a drone cross
    into Poland
  * Nepal prime minister Balendra Shah meeting Narendra Modi in
    New Delhi on a state visit
  * India declaring on 720 for 9 in the Wellington Test, a
    record total for them
  * a footer ticker: a factory fire in Indonesia, a Seoul
    minister quitting over an AI exam row, and a march in
    Lisbon about the cost of life

How the page is painted: every mark lands on a buffer twice the
final size, then each block of four buffer pixels is averaged
into one output pixel, which softens the edges. Lettering comes
from a tiny 5 by 7 face held in this file as numbers, one
integer per row, with the leftmost column in the top bit. The
PNG file itself is assembled by hand with zlib and struct.

One thing to know about the little face: its lowercase "g"
looks like a "9" at body size, so the body copy never uses a
lowercase "g" at all. Headlines are set in capitals, where the
G is perfectly clear.
"""

import math
import os
import struct
import zlib

PAGE = 1024          # the finished page is square, this many pixels
UPSCALE = 2          # the buffer is this many times wider than the page
MARGIN = 10          # the white edge around the page
CONTENT = PAGE - 2 * MARGIN

# Colours used across the page, as plain RGB triples.
PAPER = (247, 242, 231)
CARD = (255, 252, 245)
NOIR = (26, 26, 26)
CHARCOAL = (52, 52, 48)
MUTED = (110, 104, 92)
RED = (178, 44, 38)
DEEPBLUE = (28, 78, 138)
SKY = (168, 205, 232)
SEA = (24, 68, 110)
ORANGE = (224, 112, 32)
GOLD = (214, 158, 46)
LEAF = (74, 148, 74)
SAND = (222, 200, 150)
STONE = (148, 142, 130)
SMOKE = (120, 116, 108)
WHITE = (255, 255, 255)

# -------------------------------------------------------------------- face
# The 5 by 7 face. Each character is seven integers, one per row,
# holding five bits; bit 4 (value 16) is the leftmost column and
# bit 0 (value 1) the rightmost. A set bit means ink.

FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 21, 10),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "%": (25, 26, 2, 4, 8, 11, 19),
    "+": (0, 4, 4, 14, 4, 4, 0),
    "=": (0, 0, 14, 0, 14, 0, 0),
    "?": (14, 17, 1, 6, 4, 0, 4),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "&": (12, 18, 20, 8, 21, 18, 13),
    '"': (10, 10, 0, 0, 0, 0, 0),
    "*": (0, 4, 21, 14, 21, 4, 0),
    "a": (0, 0, 14, 1, 15, 17, 15),
    "b": (16, 16, 30, 17, 17, 17, 30),
    "c": (0, 0, 14, 16, 16, 17, 14),
    "d": (1, 1, 15, 17, 17, 17, 15),
    "e": (0, 0, 14, 17, 31, 16, 14),
    "f": (6, 9, 8, 30, 8, 8, 8),
    "g": (0, 15, 17, 17, 15, 1, 14),
    "h": (16, 16, 30, 17, 17, 17, 17),
    "i": (4, 0, 12, 4, 4, 4, 14),
    "j": (2, 0, 6, 2, 2, 18, 12),
    "k": (16, 16, 21, 25, 20, 18, 17),
    "l": (12, 4, 4, 4, 4, 4, 14),
    "m": (0, 0, 26, 21, 21, 21, 21),
    "n": (0, 0, 30, 17, 17, 17, 17),
    "o": (0, 0, 14, 17, 17, 17, 14),
    "p": (0, 0, 30, 17, 30, 16, 16),
    "q": (0, 0, 15, 17, 15, 1, 1),
    "r": (0, 0, 22, 25, 16, 16, 16),
    "s": (0, 0, 15, 16, 14, 1, 30),
    "t": (8, 8, 28, 8, 8, 9, 6),
    "u": (0, 0, 17, 17, 17, 19, 13),
    "v": (0, 0, 17, 17, 17, 10, 4),
    "w": (0, 0, 17, 21, 21, 21, 10),
    "x": (0, 0, 17, 10, 4, 10, 17),
    "y": (0, 0, 17, 17, 15, 1, 14),
    "z": (0, 0, 31, 2, 4, 8, 31),
    " ": (0, 0, 0, 0, 0, 0, 0),
}
BULLET = (0, 0, 12, 12, 0, 0, 0)


def text_width(s, size, bold=False):
    """How wide a string is in finished pixels at this face size."""
    width = len(s) * 6 * size - size
    if bold:
        width += max(0, len(s) - 1)
    return width


def wrap(s, size, max_width, bold=False):
    """Wrap a string greedily; each returned line fits max_width."""
    lines = []
    for chunk in s.split("\n"):
        words = chunk.split(" ")
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if text_width(trial, size, bold) <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB buffer UPSCALE times the finished size. Every method
    here takes finished-page coordinates and scales them up
    before touching the buffer."""

    def __init__(self, edge, background):
        self.edge = edge * UPSCALE
        self.buf = bytearray(self.edge * self.edge * 3)
        red, green, blue = background
        stripe = bytes((red, green, blue)) * self.edge
        for row in range(self.edge):
            start = row * self.edge * 3
            self.buf[start:start + self.edge * 3] = stripe

    def _span(self, row, left, right, colour):
        """Paint one horizontal run on one buffer row."""
        start = (row * self.edge + left) * 3
        self.buf[start:start + (right - left) * 3] = (
            bytes(colour) * (right - left))

    def rect(self, x, y, w, h, colour):
        """A solid rectangle, x, y, w, h in finished pixels."""
        left = max(0, x * UPSCALE)
        top = max(0, y * UPSCALE)
        right = min(self.edge, (x + w) * UPSCALE)
        bottom = min(self.edge, (y + h) * UPSCALE)
        if right <= left or bottom <= top:
            return
        stripe = bytes(colour) * (right - left)
        for row in range(top, bottom):
            start = (row * self.edge + left) * 3
            self.buf[start:start + (right - left) * 3] = stripe

    def circle(self, cx, cy, radius, colour):
        """A solid disc, centre and radius in finished pixels."""
        cx *= UPSCALE
        cy *= UPSCALE
        radius *= UPSCALE
        radius_sq = radius * radius
        for row in range(max(0, cy - radius),
                         min(self.edge, cy + radius + 1)):
            dy = row - cy
            half = int(math.sqrt(max(0, radius_sq - dy * dy)))
            left = max(0, cx - half)
            right = min(self.edge, cx + half + 1)
            self._span(row, left, right, colour)

    def ellipse(self, cx, cy, rx, ry, colour):
        """A solid ellipse, centre and radii in finished pixels."""
        cx *= UPSCALE
        cy *= UPSCALE
        rx *= UPSCALE
        ry *= UPSCALE
        for row in range(max(0, cy - ry),
                         min(self.edge, cy + ry + 1)):
            ratio = (row - cy) / ry
            half = int(rx * math.sqrt(max(0.0, 1.0 - ratio * ratio)))
            left = max(0, cx - half)
            right = min(self.edge, cx + half + 1)
            self._span(row, left, right, colour)

    def poly(self, points, colour):
        """A filled polygon; points are (x, y) in finished pixels."""
        scaled = [(px * UPSCALE, py * UPSCALE) for px, py in points]
        tops = [pt[1] for pt in scaled]
        first = max(0, min(tops))
        last = min(self.edge - 1, max(tops))
        count = len(scaled)
        for row in range(first, last + 1):
            hits = []
            for idx in range(count):
                x1, ya = scaled[idx]
                x2, yb = scaled[(idx + 1) % count]
                if ya == yb:
                    continue
                if (ya <= row < yb) or (yb <= row < ya):
                    hits.append(
                        int(x1 + (row - ya) * (x2 - x1) / (yb - ya)))
            hits.sort()
            for k in range(0, len(hits) - 1, 2):
                left = max(0, hits[k])
                right = min(self.edge, hits[k + 1] + 1)
                if right > left:
                    self._span(row, left, right, colour)

    def line(self, x0, y0, x1, y1, width, colour):
        """A thick straight line, width in finished pixels."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * UPSCALE) + 1
        half = max(1, width * UPSCALE // 2)
        for step in range(steps + 1):
            t = step / max(1, steps)
            cx = int((x0 + (x1 - x0) * t) * UPSCALE)
            cy = int((y0 + (y1 - y0) * t) * UPSCALE)
            for row in range(max(0, cy - half),
                             min(self.edge, cy + half + 1)):
                dy = row - cy
                span = int(math.sqrt(max(0, half * half - dy * dy)))
                left = max(0, cx - span)
                right = min(self.edge, cx + span + 1)
                self._span(row, left, right, colour)

    def ring(self, cx, cy, radius, width, colour):
        """A circle outline, radius and width in finished pixels."""
        steps = int(2 * math.pi * radius * UPSCALE) + 8
        for step in range(steps):
            angle = 2 * math.pi * step / steps
            px = int((cx + radius * math.cos(angle)) * UPSCALE)
            py = int((cy + radius * math.sin(angle)) * UPSCALE)
            self.circle(px // UPSCALE, py // UPSCALE,
                        max(1, width // 2), colour)

    # ------------------------------------------------------------ lettering
    def glyph(self, x, y, size, rows, colour):
        """Paint one 5 by 7 character; x, y in finished pixels and
        size in finished pixels per face pixel."""
        for r, bits in enumerate(rows):
            for c in range(5):
                if (bits >> (4 - c)) & 1:
                    self.rect(x + c * size, y + r * size,
                              size, size, colour)

    def text(self, x, y, size, s, colour, bold=False, align="left"):
        """Paint a string; returns the width painted, in pixels."""
        if align in ("center", "right"):
            full = text_width(s, size)
            if align == "center":
                x -= full // 2
            else:
                x -= full
        pen = x
        for ch in s:
            rows = FONT.get(ch)
            if rows is None:
                rows = BULLET if ch == "\u2022" else FONT[" "]
            self.glyph(pen, y, size, rows, colour)
            if bold and size >= 2:
                # A second pass one finished pixel to the right
                # fattens the strokes; that is what makes it bold.
                self.glyph(pen + 1, y, size, rows, colour)
            pen += 6 * size
        return pen - x - size

    def para(self, x, y, size, lines, colour, bold=False,
             leading=None, align="left"):
        """Paint several lines, one under the next."""
        if leading is None:
            leading = 7 * size + 4
        for line in lines:
            self.text(x, y, size, line, colour, bold=bold, align=align)
            y += leading
        return y


# ----------------------------------------------------------------- encoding
def _chunk(kind, data):
    """One PNG chunk: length, type, data, CRC."""
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    """Shrink the buffer 2 by 2 with plain averaging, then pack
    the result as a PNG with filter-0 rows and zlib level 9."""
    body = bytearray()
    wide = canvas.edge
    src = canvas.buf
    for out_y in range(PAGE):
        body.append(0)
        top = out_y * UPSCALE
        for out_x in range(PAGE):
            left = out_x * UPSCALE
            red = green = blue = 0
            for dy in range(UPSCALE):
                base = ((top + dy) * wide + left) * 3
                for dx in range(UPSCALE):
                    pos = base + dx * 3
                    red += src[pos]
                    green += src[pos + 1]
                    blue += src[pos + 2]
            body.append(red // 4)
            body.append(green // 4)
            body.append(blue // 4)
    packed = zlib.compress(bytes(body), 9)
    header = struct.pack(">IIBBBBB", PAGE, PAGE, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", header)
    png += _chunk(b"IDAT", packed)
    png += _chunk(b"IEND", b"")
    return png


# ------------------------------------------------------------------- scenes
def burst(canvas, cx, cy, radius, core, mid, rim):
    """An explosion starburst: three jagged polygons layered from
    the outside in."""
    spikes = 12
    for size, colour in ((radius, rim), (int(radius * 0.72), mid),
                         (int(radius * 0.45), core)):
        outline = []
        for i in range(spikes * 2):
            angle = math.pi * i / spikes
            reach = size if i % 2 == 0 else int(size * 0.45)
            outline.append((cx + int(reach * math.cos(angle)),
                            cy + int(reach * math.sin(angle))))
        canvas.poly(outline, colour)


def draw_strait(canvas, x, y, w, h):
    """The Strait of Hormuz: two tankers on a dark sea, blasts,
    and the white trails of missiles arcing overhead."""
    canvas.rect(x, y, w, h, SKY)
    canvas.circle(x + w - 70, y + 42, 26, GOLD)          # low sun
    canvas.circle(x + w - 70, y + 42, 20, (232, 190, 90))
    # a distant shore
    canvas.poly([(x, y + 118), (x + 150, y + 96), (x + 320, y + 112),
                 (x + w, y + 92), (x + w, y + 128), (x, y + 128)],
                (196, 178, 138))
    # the sea
    canvas.rect(x, y + 128, w, h - 128, SEA)
    canvas.rect(x, y + 128, w, 6, (64, 128, 178))
    for wave_y in range(y + 150, y + h - 8, 18):
        canvas.rect(x + 12 + ((wave_y * 7) % 40), wave_y, 60, 3,
                    (64, 128, 178))
    # the first tanker (left, on fire)
    tx, ty = x + 26, y + 168
    canvas.rect(tx, ty, 190, 34, (38, 38, 40))
    canvas.rect(tx + 128, ty - 34, 34, 34, (200, 200, 200))
    canvas.rect(tx + 136, ty - 44, 18, 10, RED)
    canvas.rect(tx + 8, ty - 16, 26, 16, (220, 220, 210))
    canvas.rect(tx + 150, ty + 34, 12, 26, (38, 38, 40))
    burst(canvas, tx + 60, ty - 26, 46, (255, 214, 90), ORANGE, RED)
    canvas.circle(tx + 30, ty - 58, 16, SMOKE)
    canvas.circle(tx + 58, ty - 74, 22, SMOKE)
    canvas.circle(tx + 92, ty - 60, 15, SMOKE)
    # the second tanker (right, hit at the stern)
    tx2, ty2 = x + 252, y + 208
    canvas.rect(tx2, ty2, 210, 30, (52, 52, 56))
    canvas.rect(tx2 + 30, ty2 - 30, 30, 30, (200, 200, 200))
    canvas.rect(tx2 + 38, ty2 - 40, 14, 10, RED)
    canvas.rect(tx2 + 150, ty2 - 14, 22, 14, (220, 220, 210))
    burst(canvas, tx2 + 205, ty2 - 8, 34, (255, 214, 90), ORANGE, RED)
    # missile arcs, drawn as white trails
    canvas.line(x + 60, y + 20, x + 130, y + 120, 3, WHITE)
    canvas.line(x + 130, y + 120, x + 150, y + 152, 3, WHITE)
    canvas.circle(x + 60, y + 20, 5, WHITE)
    canvas.line(x + 420, y + 26, x + 380, y + 110, 3, WHITE)
    canvas.line(x + 380, y + 110, x + 430, y + 176, 3, WHITE)
    canvas.circle(x + 420, y + 26, 5, WHITE)
    # wakes behind the tankers
    canvas.line(tx, ty + 40, tx + 190, ty + 40, 2, (140, 180, 210))
    canvas.line(tx2, ty2 + 36, tx2 + 210, ty2 + 36, 2, (140, 180, 210))
    # place labels
    canvas.text(x + 14, y + h - 26, 2, "BAHRAIN", WHITE, bold=True)
    canvas.text(x + w - 14, y + h - 26, 2, "HORMUZ", WHITE, bold=True,
                align="right")


def draw_summit(canvas, x, y, w, h):
    """A cracked globe hanging over a summit hall: the talks fail."""
    canvas.rect(x, y, w, h, (222, 232, 226))
    # the hall, a low silhouette with a row of windows
    canvas.rect(x, y + h - 26, w, 26, (120, 118, 112))
    for win_x in range(x + 18, x + w - 18, 34):
        canvas.rect(win_x, y + h - 22, 14, 18, (60, 60, 58))
    canvas.poly([(x, y + h - 26), (x + w // 2, y + h - 46),
                 (x + w, y + h - 26)], (90, 88, 84))
    # the globe
    gx, gy = x + w // 2, y + h // 2 - 2
    globe_r = min(46, h // 2 - 6)
    canvas.circle(gx, gy, globe_r, DEEPBLUE)
    canvas.circle(gx - 14, gy - 10, 11, LEAF)
    canvas.circle(gx + 15, gy + 6, 14, LEAF)
    canvas.circle(gx - 6, gy + 18, 8, LEAF)
    canvas.circle(gx + 19, gy - 18, 6, LEAF)
    canvas.ellipse(gx, gy, globe_r, int(globe_r * 0.36), (120, 180, 220))
    # the crack running across it
    canvas.line(gx - globe_r + 4, gy - globe_r // 2, gx - 10, gy - 4, 3,
                RED)
    canvas.line(gx - 10, gy - 4, gx + 4, gy - 16, 3, RED)
    canvas.line(gx + 4, gy - 16, gx + 18, gy + 2, 3, RED)
    canvas.line(gx + 18, gy + 2, gx + globe_r - 4, gy + globe_r // 2, 3,
                RED)
    canvas.ring(gx, gy, globe_r, 3, NOIR)
    # factory smoke off to the left
    canvas.rect(x + 16, y + h - 52, 8, 30, STONE)
    canvas.circle(x + 20, y + h - 60, 8, SMOKE)
    canvas.circle(x + 34, y + h - 68, 9, SMOKE)
    # a dimmed sun
    canvas.circle(x + w - 30, y + 22, 12, (232, 190, 90))


def draw_kyiv(canvas, x, y, w, h):
    """A five-storey flat block with its corner smashed in, smoke
    rising and rescue lights below."""
    canvas.rect(x, y, w, h, (214, 208, 196))
    # sky band
    canvas.rect(x, y, w, 40, SKY)
    canvas.circle(x + w - 34, y + 20, 11, (240, 220, 150))
    # the block itself
    bx, by, bw = x + 46, y + 36, w - 92
    bh = h - 36
    canvas.rect(bx, by, bw, bh, (196, 178, 150))
    canvas.rect(bx, by, bw, 6, (160, 140, 114))
    rows = 4 if h >= 130 else (3 if h >= 110 else 2)
    cols = max(4, (bw - 28) // 40)
    step = max(20, (bh - 26) // rows)
    for row in range(rows):
        for col in range(cols):
            win_x = bx + 14 + col * 40
            win_y = by + 14 + row * step
            canvas.rect(win_x, win_y, 22, 16, (70, 84, 104))
            canvas.rect(win_x, win_y, 22, 3, (200, 210, 220))
    # the collapsed corner: a jagged dark hole and rubble, all
    # kept inside the block
    canvas.poly([(bx + bw, by + 8), (bx + bw - 52, by + int(bh * 0.30)),
                 (bx + bw - 30, by + int(bh * 0.52)),
                 (bx + bw - 56, by + int(bh * 0.72)),
                 (bx + bw - 26, by + int(bh * 0.90)),
                 (bx + bw, by + bh)], (52, 48, 44))
    canvas.poly([(bx + bw - 78, by + bh), (bx + bw - 34, by + bh - 40),
                 (bx + bw + 8, by + bh - 14), (bx + bw + 8, by + bh),
                 (bx + bw - 78, by + bh)], (120, 112, 100))
    canvas.poly([(bx + bw - 50, by + bh - 24),
                 (bx + bw - 16, by + bh - 34),
                 (bx + bw + 4, by + bh - 18), (bx + bw - 24, by + bh - 6)],
                (90, 84, 74))
    # smoke above the wreck
    canvas.circle(bx + bw - 26, by + 12, 14, SMOKE)
    canvas.circle(bx + bw - 48, by - 4, 18, SMOKE)
    canvas.circle(bx + bw - 8, by - 12, 11, SMOKE)
    # rescue lights at the foot of the block
    canvas.circle(bx + 26, by + bh - 10, 5, RED)
    canvas.circle(bx + 44, by + bh - 10, 5, ORANGE)
    # ground line
    canvas.rect(x, y + h - 6, w, 6, (120, 116, 106))


def draw_nato(canvas, x, y, w, h):
    """A NATO compass star in a blue roundel, jets above and a
    runway below."""
    canvas.rect(x, y, w, h, (222, 230, 238))
    cx, cy = x + w // 2, y + h // 2 - 2
    radius = max(18, h // 2 - 10)
    canvas.circle(cx, cy, radius, DEEPBLUE)
    canvas.ring(cx, cy, radius, 3, WHITE)
    # the four-point compass star
    for bearing in (90, 210, 330, -90):
        angle = math.radians(bearing)
        tip = radius - 4 if bearing != -90 else radius - 8
        canvas.poly([(cx, cy),
                     (cx + int(radius * 0.42 * math.cos(angle - 0.30)),
                      cy + int(radius * 0.42 * math.sin(angle - 0.30))),
                     (cx + int(tip * math.cos(angle)),
                      cy + int(tip * math.sin(angle))),
                     (cx + int(radius * 0.42 * math.cos(angle + 0.30)),
                      cy + int(radius * 0.42 * math.sin(angle + 0.30)))],
                    WHITE)
    canvas.circle(cx, cy, 4, WHITE)
    # two jets crossing the top
    for jx, jy in ((x + 24, y + 12), (x + w - 24, y + 16)):
        canvas.poly([(jx - 14, jy), (jx + 12, jy - 4), (jx + 17, jy),
                     (jx + 12, jy + 4)], (60, 60, 64))
        canvas.poly([(jx - 2, jy - 3), (jx + 5, jy - 10), (jx + 8, jy - 3)],
                    (60, 60, 64))
    # the runway
    canvas.rect(x, y + h - 14, w, 14, (70, 70, 72))
    for dash in range(8, w, 28):
        canvas.rect(x + dash, y + h - 9, 14, 3, WHITE)


def draw_delhi(canvas, x, y, w, h):
    """Nepal's red pennants and India's tricolour over Delhi's
    arch, with the Himalaya behind."""
    canvas.rect(x, y, w, h, (238, 228, 208))
    # the Himalaya ridge
    canvas.poly([(x, y + h), (x + 60, y + h - 52), (x + 120, y + h)],
                (120, 130, 140))
    canvas.poly([(x + 80, y + h), (x + 170, y + h - 64), (x + 260, y + h)],
                (90, 100, 114))
    canvas.poly([(x + 152, y + h - 40), (x + 170, y + h - 64),
                 (x + 188, y + h - 40)], WHITE)
    # the India Gate arch
    ax = x + w // 2 - 30
    canvas.rect(ax, y + h - 48, 60, 48, (176, 140, 96))
    canvas.poly([(ax - 5, y + h - 48), (ax + 65, y + h - 48),
                 (ax + 55, y + h - 60), (ax + 5, y + h - 60)],
                (160, 124, 84))
    canvas.rect(ax + 21, y + h - 34, 18, 34, PAPER)
    canvas.circle(ax + 30, y + h - 34, 9, PAPER)
    # Nepal's pennants on the left flagpole
    fx, fy = x + 20, y + 10
    canvas.rect(fx, fy, 3, 56, (90, 70, 60))
    canvas.poly([(fx + 3, fy + 2), (fx + 36, fy + 11), (fx + 3, fy + 20)],
                (200, 40, 50))
    canvas.poly([(fx + 3, fy + 22), (fx + 30, fy + 30), (fx + 3, fy + 40)],
                (200, 40, 50))
    canvas.circle(fx + 13, fy + 11, 2, WHITE)
    canvas.circle(fx + 11, fy + 30, 2, WHITE)
    # India's tricolour on the right flagpole
    fx2 = x + w - 58
    canvas.rect(fx2, fy, 3, 56, (90, 70, 60))
    canvas.rect(fx2 + 3, fy + 2, 38, 11, (230, 130, 40))
    canvas.rect(fx2 + 3, fy + 13, 38, 11, WHITE)
    canvas.rect(fx2 + 3, fy + 24, 38, 11, (20, 130, 70))
    canvas.ring(fx2 + 22, fy + 18, 5, 2, DEEPBLUE)


def draw_cricket(canvas, x, y, w, h):
    """A green outfield, the pitch, a leaning bat, a red ball in
    flight and the big score on a board."""
    canvas.rect(x, y, w, h, (96, 158, 74))
    canvas.ellipse(x + w // 2, y + h - 10, w // 2 - 6, 18, (74, 132, 58))
    # the pitch
    canvas.poly([(x + 96, y + h - 6), (x + 124, y + 20),
                 (x + w - 124, y + 20), (x + w - 96, y + h - 6)], SAND)
    canvas.rect(x + w // 2 - 2, y + 24, 4, h - 34, WHITE)
    # the stumps
    for sx in (x + w // 2 - 62, x + w // 2 - 54, x + w // 2 - 46):
        canvas.rect(sx, y + 26, 4, 18, GOLD)
    canvas.rect(x + w // 2 - 62, y + 23, 22, 3, GOLD)
    # a bat leaning on the pitch
    canvas.poly([(x + 60, y + h - 12), (x + 80, y + h - 18),
                 (x + 116, y + 30), (x + 106, y + 26)], (196, 164, 110))
    canvas.rect(x + 104, y + 16, 7, 14, (120, 90, 60))
    # the red ball in flight
    canvas.circle(x + w - 56, y + 34, 9, RED)
    canvas.circle(x + w - 59, y + 31, 3, (255, 200, 200))
    # the scoreboard
    bx, by = x + w - 132, y + h - 40
    canvas.rect(bx, by, 118, 32, NOIR)
    canvas.rect(bx + 3, by + 3, 112, 26, (30, 30, 30))
    canvas.text(bx + 59, by + 6, 3, "720/9", GOLD, bold=True,
                align="center")


# -------------------------------------------------------------------- page
def card(canvas, x, y, w, h):
    """A story card: a pale face with a two-pixel ink border."""
    canvas.rect(x, y, w, h, CARD)
    canvas.rect(x, y, w, 2, NOIR)
    canvas.rect(x, y, 2, h, NOIR)
    canvas.rect(x + w - 2, y, 2, h, NOIR)
    canvas.rect(x, y + h - 2, w, 2, NOIR)


def story(canvas, x, y, w, h, kicker, headline, brief, scene,
          art_h=118, head_size=3):
    """One story card: a picture strip on top, then a red kicker,
    a wrapped headline and a short brief underneath."""
    card(canvas, x, y, w, h)
    scene(canvas, x + 2, y + 2, w - 4, art_h)
    ty = y + art_h + 10
    canvas.text(x + 12, ty, 2, kicker, RED, bold=True)
    ty += 22
    head_lines = wrap(headline, head_size, w - 24, bold=True)
    ty = canvas.para(x + 12, ty, head_size, head_lines, NOIR,
                     bold=True, leading=7 * head_size + 5)
    ty += 4
    brief_lines = wrap(brief, 2, w - 24)
    canvas.para(x + 12, ty, 2, brief_lines, CHARCOAL, leading=18)


def compose():
    """Lay out the whole front page and hand back the canvas."""
    canvas = Canvas(PAGE, PAPER)

    # ---- masthead
    canvas.rect(MARGIN, 10, CONTENT, 2, NOIR)
    canvas.text(PAGE // 2, 20, 6, "THE WORLD IN ONE DAY", NOIR, bold=True,
                align="center")
    canvas.text(PAGE // 2, 74, 3, "MONDAY 23 NOVEMBER 2026", RED,
                bold=True, align="center")
    canvas.text(PAGE // 2, 104, 2,
                "SIX STORIES FROM A DAY OF WAR, CLIMATE FAILURE AND "
                "RECORD SPORT", MUTED, align="center")
    canvas.rect(MARGIN, 130, CONTENT, 4, NOIR)
    canvas.rect(MARGIN, 138, CONTENT, 1, NOIR)

    # ---- the lead story: the Gulf war widens
    lx, ly, lw, lh = MARGIN, 152, CONTENT, 300
    card(canvas, lx, ly, lw, lh)
    draw_strait(canvas, lx + 2, ly + 2, 486, lh - 4)
    tx = lx + 502
    ty = ly + 16
    canvas.text(tx, ty, 2, "LEAD STORY: THE GULF WAR", RED, bold=True)
    ty += 26
    head_lines = wrap("IRAN HITS BAHRAIN AS TANKERS BURN IN THE "
                      "STRAIT", 3, lw - 514, bold=True)
    ty = canvas.para(tx, ty, 3, head_lines, NOIR, bold=True,
                     leading=27)
    ty += 8
    lead_copy = ("Iranian missiles hit a civilian plant in Sitra, "
                 "Bahrain, hurt two people and set it ablaze, as "
                 "Tehran says it aimed at US bases. Two tankers "
                 "were hit near Hormuz. Saudi jets down a Houthi "
                 "missile, and the US denies an Iranian claim it "
                 "hit a US jet.")
    brief_lines = wrap(lead_copy, 2, lw - 514)
    ty = canvas.para(tx, ty, 2, brief_lines, CHARCOAL, leading=19)
    ty += 12
    canvas.rect(tx, ty, lw - 514, 2, RED)
    ty += 10
    canvas.text(tx, ty, 2, "2 HURT, 2 TANKERS, 1 MISSILE DOWN", RED,
                bold=True)

    # ---- second row: COP31 and Kyiv
    row_y, row_h = 462, 260
    half_w = (CONTENT - 8) // 2
    story(canvas, MARGIN, row_y, half_w, row_h,
          "CLIMATE: ANTALYA, TURKEY",
          "COP31 COLLAPSES WITH NO DEAL ON FOSSIL FUELS",
          "The UN climate summit ends in failure as the EU "
          "rejects a final text with no mention of fossil "
          "fuels.",
          draw_summit, art_h=92)
    story(canvas, MARGIN + half_w + 8, row_y, half_w, row_h,
          "WAR IN UKRAINE: KYIV REGION",
          "DRONE SMASHES FLAT BLOCK: 14 FEARED TRAPPED",
          "A Russian drone hits a five-storey home in the "
          "Kyiv area and part of it falls in. Rescuers hunt "
          "for survivors; nine people are safe.",
          draw_kyiv, art_h=92)

    # ---- third row: NATO, Nepal, cricket
    row3_y, row3_h = 732, 216
    third_w = (CONTENT - 16) // 3
    story(canvas, MARGIN, row3_y, third_w, row3_h,
          "EUROPE: BRUSSELS",
          "NATO MEETS AS POLAND CITES INCURSION",
          "Allies meet after Russian missiles and a drone "
          "cross into Poland.",
          draw_nato, art_h=80, head_size=2)
    story(canvas, MARGIN + third_w + 8, row3_y, third_w, row3_h,
          "SOUTH ASIA: NEW DELHI",
          "NEPAL PM MEETS MODI IN DELHI ON STATE VISIT",
          "Nepal PM Balendra Shah holds talks with PM "
          "Narendra Modi in Delhi.",
          draw_delhi, art_h=80, head_size=2)
    story(canvas, MARGIN + 2 * (third_w + 8), row3_y, third_w, row3_h,
          "SPORT: WELLINGTON TEST",
          "INDIA 720 FOR 9: A RECORD TOTAL",
          "India declare on 720 for nine, the best in their "
          "Test history.",
          draw_cricket, art_h=80, head_size=2)

    # ---- footer ticker and source line
    canvas.rect(MARGIN, 958, CONTENT, 2, NOIR)
    canvas.text(MARGIN, 966, 2,
                "ALSO TODAY: FACTORY FIRE IN INDONESIA LEAVES 7 DEAD, "
                "50 UNACCOUNTED FOR",
                NOIR, bold=True)
    canvas.text(MARGIN, 984, 2,
                "SEOUL MINISTER QUITS IN AI EXAM ROW - LISBON MARCHES "
                "ON COST OF LIFE",
                NOIR, bold=True)
    canvas.text(MARGIN, 1002, 2,
                "DRAWN IN CODE - NO PHOTO - SOURCES: REUTERS, AP, CNBC - "
                "23 NOVEMBER 2026",
                MUTED)
    return canvas


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(compose())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(png)


if __name__ == "__main__":
    main()
