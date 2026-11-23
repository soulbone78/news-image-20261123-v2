"""The World in One Day: Monday 23 November 2026.

This file is a small press of its own. It sets one newspaper
front page -- six stories from a single Monday -- and prints
it as a square 1024 pixel PNG, using nothing but the Python
standard library. Nothing is read from the network, the clock
is never consulted, and there is no randomness anywhere, so
two runs produce the same file down to the last byte.

The page, from the top:

  * a masthead naming the paper and the day;
  * the lead: Iranian missiles hit a civilian plant in Sitra,
    Bahrain, two tankers are hit near the Strait of Hormuz,
    Saudi jets down a Houthi missile, and Washington denies
    an Iranian claim about a US jet;
  * COP31 in Antalya collapses with no deal on fossil fuels;
  * a Russian drone smashes a five-storey block of flats in
    the Kyiv region, with 14 people feared trapped;
  * NATO meets in Brussels after missiles and a drone cross
    into Poland;
  * Nepal's prime minister Balendra Shah meets Narendra Modi
    in New Delhi on a state visit;
  * India declare on 720 for 9 in the Wellington Test, a
    record total;
  * a footer ticker: a factory fire in Indonesia, a minister
    quitting in Seoul over an AI exam row, and a march in
    Lisbon about the cost of life.

Everything is drawn on a sheet twice the finished size and
then shrunk by averaging each 2 by 2 block, which softens the
edges. The lettering is a hand-made 5 by 7 dot face, stored
below as rows of ones and zeroes. The PNG bytes are assembled
by hand from zlib and struct.

A quirk of the little face: its lowercase "g" reads like a
"9" at body size, so the body copy is written without any
lowercase "g" at all. Headlines are all capitals, where the
capital G is unmistakable.
"""

import os
import struct
import zlib
from math import cos, pi, radians, sin, sqrt

SIDE = 1024              # finished page: a square of this many pixels
ZOOM = 2                 # the working sheet is this many times bigger
EDGE = 10                # plain border around the page
SPAN = SIDE - 2 * EDGE   # width of the printed area

# The inks used across the page, as plain RGB triples.
NEWSPRINT = (247, 242, 231)
CARD_BG = (255, 252, 245)
INK = (26, 26, 26)
SOFT_INK = (52, 52, 48)
FADED = (110, 104, 92)
CRIMSON = (178, 44, 38)
NAVY = (28, 78, 138)
PALE_SKY = (168, 205, 232)
DEEP_SEA = (24, 68, 110)
EMBER = (224, 112, 32)
BRASS = (214, 158, 46)
MOSS = (74, 148, 74)
BEACH = (222, 200, 150)
PEBBLE = (148, 142, 130)
ASH = (120, 116, 108)
SNOW = (255, 255, 255)

# -------------------------------------------------------------------- face
# The 5 by 7 dot face. Each character is seven strings, one per
# row, five cells each: "1" means ink, "0" means paper. The
# leftmost cell of a string is the leftmost column of the
# letter.

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10101", "11001", "10100", "10010", "10001"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
DOT = ("00000", "00000", "01100", "01100", "00000", "00000", "00000")


def measure(text, scale, heavy=False):
    """Width of a line of type in finished pixels."""
    total = len(text) * 6 * scale - scale
    if heavy:
        total += max(0, len(text) - 1)
    return total


def split_lines(text, scale, limit, heavy=False):
    """Greedy word wrap; every returned line fits inside limit."""
    out = []
    for part in text.split("\n"):
        words = part.split(" ")
        line = ""
        for word in words:
            attempt = word if not line else line + " " + word
            if measure(attempt, scale, heavy) <= limit or not line:
                line = attempt
            else:
                out.append(line)
                line = word
        if line:
            out.append(line)
    return out


# ------------------------------------------------------------------- sheet
class Sheet:
    """A working surface ZOOM times the finished size. Every
    drawing method here takes finished-page coordinates and
    scales them up before touching the buffer."""

    def __init__(self, side, fill):
        self.side = side * ZOOM
        self.pixels = bytearray(self.side * self.side * 3)
        band = bytes(fill) * self.side
        row_len = self.side * 3
        for row in range(self.side):
            at = row * row_len
            self.pixels[at:at + row_len] = band

    def run(self, row, start, stop, colour):
        """Paint one horizontal stretch of one working row."""
        at = (row * self.side + start) * 3
        self.pixels[at:at + (stop - start) * 3] = (
            bytes(colour) * (stop - start))

    def box(self, x, y, wide, tall, colour):
        """A solid rectangle, x, y, wide, tall in finished pixels."""
        left = max(0, x * ZOOM)
        top = max(0, y * ZOOM)
        right = min(self.side, (x + wide) * ZOOM)
        bottom = min(self.side, (y + tall) * ZOOM)
        if right <= left or bottom <= top:
            return
        band = bytes(colour) * (right - left)
        width = (right - left) * 3
        for row in range(top, bottom):
            at = (row * self.side + left) * 3
            self.pixels[at:at + width] = band

    def disc(self, cx, cy, radius, colour):
        """A solid disc, centre and radius in finished pixels."""
        cx *= ZOOM
        cy *= ZOOM
        radius *= ZOOM
        square = radius * radius
        for row in range(max(0, cy - radius),
                         min(self.side, cy + radius + 1)):
            dy = row - cy
            half = int(sqrt(max(0, square - dy * dy)))
            self.run(row, max(0, cx - half),
                     min(self.side, cx + half + 1), colour)

    def oval(self, cx, cy, rx, ry, colour):
        """A solid ellipse, centre and radii in finished pixels."""
        cx *= ZOOM
        cy *= ZOOM
        rx *= ZOOM
        ry *= ZOOM
        for row in range(max(0, cy - ry),
                         min(self.side, cy + ry + 1)):
            frac = (row - cy) / ry
            half = int(rx * sqrt(max(0.0, 1.0 - frac * frac)))
            self.run(row, max(0, cx - half),
                     min(self.side, cx + half + 1), colour)

    def shape(self, points, colour):
        """A filled polygon; points are (x, y) in finished pixels."""
        scaled = [(px * ZOOM, py * ZOOM) for px, py in points]
        tops = [pt[1] for pt in scaled]
        first = max(0, min(tops))
        last = min(self.side - 1, max(tops))
        count = len(scaled)
        for row in range(first, last + 1):
            cuts = []
            for i in range(count):
                x1, y1 = scaled[i]
                x2, y2 = scaled[(i + 1) % count]
                if y1 == y2:
                    continue
                if (y1 <= row < y2) or (y2 <= row < y1):
                    cuts.append(
                        int(x1 + (row - y1) * (x2 - x1) / (y2 - y1)))
            cuts.sort()
            for k in range(0, len(cuts) - 1, 2):
                left = max(0, cuts[k])
                right = min(self.side, cuts[k + 1] + 1)
                if right > left:
                    self.run(row, left, right, colour)

    def stroke(self, x0, y0, x1, y1, width, colour):
        """A thick straight line, width in finished pixels."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * ZOOM) + 1
        half = max(1, width * ZOOM // 2)
        for step in range(steps + 1):
            t = step / max(1, steps)
            cx = int((x0 + (x1 - x0) * t) * ZOOM)
            cy = int((y0 + (y1 - y0) * t) * ZOOM)
            for row in range(max(0, cy - half),
                             min(self.side, cy + half + 1)):
                dy = row - cy
                span = int(sqrt(max(0, half * half - dy * dy)))
                self.run(row, max(0, cx - span),
                         min(self.side, cx + span + 1), colour)

    def hoop(self, cx, cy, radius, width, colour):
        """A circle outline, radius and width in finished pixels."""
        steps = int(2 * pi * radius * ZOOM) + 8
        for step in range(steps):
            angle = 2 * pi * step / steps
            px = int((cx + radius * cos(angle)) * ZOOM)
            py = int((cy + radius * sin(angle)) * ZOOM)
            self.disc(px // ZOOM, py // ZOOM,
                      max(1, width // 2), colour)

    # ------------------------------------------------------------ lettering
    def letter(self, x, y, scale, rows, colour):
        """One 5 by 7 character; x, y in finished pixels and
        scale in finished pixels per face dot."""
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell == "1":
                    self.box(x + c * scale, y + r * scale,
                             scale, scale, colour)

    def write(self, x, y, scale, text, colour, heavy=False, align="left"):
        """Paint a string; returns the width painted, in pixels."""
        if align in ("center", "right"):
            full = measure(text, scale)
            if align == "center":
                x -= full // 2
            else:
                x -= full
        pen = x
        for ch in text:
            rows = GLYPHS.get(ch)
            if rows is None:
                rows = DOT if ch == "\u2022" else GLYPHS[" "]
            self.letter(pen, y, scale, rows, colour)
            if heavy and scale >= 2:
                # A second pass one finished pixel to the right
                # fattens the strokes; that is what makes it bold.
                self.letter(pen + 1, y, scale, rows, colour)
            pen += 6 * scale
        return pen - x - scale

    def block(self, x, y, scale, lines, colour, heavy=False,
              gap=None, align="left"):
        """Paint several lines, one under the next; returns the
        y where the next line would go."""
        if gap is None:
            gap = 7 * scale + 4
        for line in lines:
            self.write(x, y, scale, line, colour, heavy=heavy,
                       align=align)
            y += gap
        return y


# ----------------------------------------------------------------- encoding
def _pack(kind, data):
    """One PNG chunk: length, type, data, CRC."""
    body = struct.pack(">I", len(data)) + kind + data
    return body + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def render_png(sheet):
    """Average each 2 by 2 block down to one pixel, then pack the
    result as a PNG with filter-0 rows and zlib level 9."""
    raw = bytearray()
    wide = sheet.side
    src = sheet.pixels
    for out_y in range(SIDE):
        raw.append(0)
        top = out_y * ZOOM
        for out_x in range(SIDE):
            left = out_x * ZOOM
            red = green = blue = 0
            for dy in range(ZOOM):
                base = ((top + dy) * wide + left) * 3
                for dx in range(ZOOM):
                    pos = base + dx * 3
                    red += src[pos]
                    green += src[pos + 1]
                    blue += src[pos + 2]
            raw.append(red // 4)
            raw.append(green // 4)
            raw.append(blue // 4)
    packed = zlib.compress(bytes(raw), 9)
    head = struct.pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _pack(b"IHDR", head)
    png += _pack(b"IDAT", packed)
    png += _pack(b"IEND", b"")
    return png


# ------------------------------------------------------------------- scenes
def starburst(sheet, cx, cy, radius, core, mid, rim):
    """An explosion: three jagged stars layered from the
    outside in."""
    points = 12
    for size, colour in ((radius, rim), (int(radius * 0.72), mid),
                         (int(radius * 0.45), core)):
        outline = []
        for i in range(points * 2):
            angle = pi * i / points
            reach = size if i % 2 == 0 else int(size * 0.45)
            outline.append((cx + int(reach * cos(angle)),
                            cy + int(reach * sin(angle))))
        sheet.shape(outline, colour)


def paint_gulf(sheet, left, top, wide, tall):
    """The Strait of Hormuz: two tankers on a dark sea, blasts
    above them, and white missile trails arcing overhead."""
    sheet.box(left, top, wide, tall, PALE_SKY)
    sheet.disc(left + wide - 70, top + 42, 26, BRASS)   # low sun
    sheet.disc(left + wide - 70, top + 42, 20, (232, 190, 90))
    # a distant shore
    sheet.shape([(left, top + 118), (left + 150, top + 96),
                 (left + 320, top + 112), (left + wide, top + 92),
                 (left + wide, top + 128), (left, top + 128)],
                (196, 178, 138))
    # the sea
    sheet.box(left, top + 128, wide, tall - 128, DEEP_SEA)
    sheet.box(left, top + 128, wide, 6, (64, 128, 178))
    for wy in range(top + 150, top + tall - 8, 18):
        sheet.box(left + 12 + ((wy * 7) % 40), wy, 60, 3,
                  (64, 128, 178))
    # the first tanker (left, on fire)
    hx, hy = left + 26, top + 168
    sheet.box(hx, hy, 190, 34, (38, 38, 40))
    sheet.box(hx + 128, hy - 34, 34, 34, (200, 200, 200))
    sheet.box(hx + 136, hy - 44, 18, 10, CRIMSON)
    sheet.box(hx + 8, hy - 16, 26, 16, (220, 220, 210))
    sheet.box(hx + 150, hy + 34, 12, 26, (38, 38, 40))
    starburst(sheet, hx + 60, hy - 26, 46, (255, 214, 90), EMBER,
              CRIMSON)
    sheet.disc(hx + 30, hy - 58, 16, ASH)
    sheet.disc(hx + 58, hy - 74, 22, ASH)
    sheet.disc(hx + 92, hy - 60, 15, ASH)
    # the second tanker (right, hit at the stern)
    sx, sy = left + 252, top + 208
    sheet.box(sx, sy, 210, 30, (52, 52, 56))
    sheet.box(sx + 30, sy - 30, 30, 30, (200, 200, 200))
    sheet.box(sx + 38, sy - 40, 14, 10, CRIMSON)
    sheet.box(sx + 150, sy - 14, 22, 14, (220, 220, 210))
    starburst(sheet, sx + 205, sy - 8, 34, (255, 214, 90), EMBER,
              CRIMSON)
    # missile arcs, drawn as white trails
    sheet.stroke(left + 60, top + 20, left + 130, top + 120, 3, SNOW)
    sheet.stroke(left + 130, top + 120, left + 150, top + 152, 3, SNOW)
    sheet.disc(left + 60, top + 20, 5, SNOW)
    sheet.stroke(left + 420, top + 26, left + 380, top + 110, 3, SNOW)
    sheet.stroke(left + 380, top + 110, left + 430, top + 176, 3, SNOW)
    sheet.disc(left + 420, top + 26, 5, SNOW)
    # wakes behind the tankers
    sheet.stroke(hx, hy + 40, hx + 190, hy + 40, 2, (140, 180, 210))
    sheet.stroke(sx, sy + 36, sx + 210, sy + 36, 2, (140, 180, 210))
    # place labels
    sheet.write(left + 14, top + tall - 26, 2, "BAHRAIN", SNOW,
                heavy=True)
    sheet.write(left + wide - 14, top + tall - 26, 2, "HORMUZ", SNOW,
                heavy=True, align="right")


def paint_climate(sheet, left, top, wide, tall):
    """A cracked globe hanging over a summit hall: the talks
    fail."""
    sheet.box(left, top, wide, tall, (222, 232, 226))
    # the hall, a low silhouette with a row of windows
    sheet.box(left, top + tall - 26, wide, 26, (120, 118, 112))
    for wx in range(left + 18, left + wide - 18, 34):
        sheet.box(wx, top + tall - 22, 14, 18, (60, 60, 58))
    sheet.shape([(left, top + tall - 26),
                 (left + wide // 2, top + tall - 46),
                 (left + wide, top + tall - 26)], (90, 88, 84))
    # the globe
    gx, gy = left + wide // 2, top + tall // 2 - 2
    gr = min(46, tall // 2 - 6)
    sheet.disc(gx, gy, gr, NAVY)
    sheet.disc(gx - 14, gy - 10, 11, MOSS)
    sheet.disc(gx + 15, gy + 6, 14, MOSS)
    sheet.disc(gx - 6, gy + 18, 8, MOSS)
    sheet.disc(gx + 19, gy - 18, 6, MOSS)
    sheet.oval(gx, gy, gr, int(gr * 0.36), (120, 180, 220))
    # the crack running across it
    sheet.stroke(gx - gr + 4, gy - gr // 2, gx - 10, gy - 4, 3,
                 CRIMSON)
    sheet.stroke(gx - 10, gy - 4, gx + 4, gy - 16, 3, CRIMSON)
    sheet.stroke(gx + 4, gy - 16, gx + 18, gy + 2, 3, CRIMSON)
    sheet.stroke(gx + 18, gy + 2, gx + gr - 4, gy + gr // 2, 3,
                 CRIMSON)
    sheet.hoop(gx, gy, gr, 3, INK)
    # factory smoke off to the left
    sheet.box(left + 16, top + tall - 52, 8, 30, PEBBLE)
    sheet.disc(left + 20, top + tall - 60, 8, ASH)
    sheet.disc(left + 34, top + tall - 68, 9, ASH)
    # a dimmed sun
    sheet.disc(left + wide - 30, top + 22, 12, (232, 190, 90))


def paint_kyiv(sheet, left, top, wide, tall):
    """A five-storey block of flats with its corner smashed in,
    smoke rising and rescue lights below."""
    sheet.box(left, top, wide, tall, (214, 208, 196))
    # sky band
    sheet.box(left, top, wide, 40, PALE_SKY)
    sheet.disc(left + wide - 34, top + 20, 11, (240, 220, 150))
    # the block itself
    bx, by, bw = left + 46, top + 36, wide - 92
    bh = tall - 36
    sheet.box(bx, by, bw, bh, (196, 178, 150))
    sheet.box(bx, by, bw, 6, (160, 140, 114))
    floors = 4 if tall >= 130 else (3 if tall >= 110 else 2)
    across = max(4, (bw - 28) // 40)
    gap = max(20, (bh - 26) // floors)
    for floor in range(floors):
        for col in range(across):
            wx = bx + 14 + col * 40
            wy = by + 14 + floor * gap
            sheet.box(wx, wy, 22, 16, (70, 84, 104))
            sheet.box(wx, wy, 22, 3, (200, 210, 220))
    # the collapsed corner: a jagged dark hole and rubble, all
    # kept inside the block
    sheet.shape([(bx + bw, by + 8),
                 (bx + bw - 52, by + int(bh * 0.30)),
                 (bx + bw - 30, by + int(bh * 0.52)),
                 (bx + bw - 56, by + int(bh * 0.72)),
                 (bx + bw - 26, by + int(bh * 0.90)),
                 (bx + bw, by + bh)], (52, 48, 44))
    sheet.shape([(bx + bw - 78, by + bh),
                 (bx + bw - 34, by + bh - 40),
                 (bx + bw + 8, by + bh - 14), (bx + bw + 8, by + bh),
                 (bx + bw - 78, by + bh)], (120, 112, 100))
    sheet.shape([(bx + bw - 50, by + bh - 24),
                 (bx + bw - 16, by + bh - 34),
                 (bx + bw + 4, by + bh - 18),
                 (bx + bw - 24, by + bh - 6)], (90, 84, 74))
    # smoke above the wreck
    sheet.disc(bx + bw - 26, by + 12, 14, ASH)
    sheet.disc(bx + bw - 48, by - 4, 18, ASH)
    sheet.disc(bx + bw - 8, by - 12, 11, ASH)
    # rescue lights at the foot of the block
    sheet.disc(bx + 26, by + bh - 10, 5, CRIMSON)
    sheet.disc(bx + 44, by + bh - 10, 5, EMBER)
    # ground line
    sheet.box(left, top + tall - 6, wide, 6, (120, 116, 106))


def paint_nato(sheet, left, top, wide, tall):
    """A NATO compass star in a blue roundel, jets above and a
    runway below."""
    sheet.box(left, top, wide, tall, (222, 230, 238))
    cx, cy = left + wide // 2, top + tall // 2 - 2
    radius = max(18, tall // 2 - 10)
    sheet.disc(cx, cy, radius, NAVY)
    sheet.hoop(cx, cy, radius, 3, SNOW)
    # the four-point compass star
    for bearing in (90, 210, 330, -90):
        angle = radians(bearing)
        tip = radius - 4 if bearing != -90 else radius - 8
        sheet.shape([(cx, cy),
                     (cx + int(radius * 0.42 * cos(angle - 0.30)),
                      cy + int(radius * 0.42 * sin(angle - 0.30))),
                     (cx + int(tip * cos(angle)),
                      cy + int(tip * sin(angle))),
                     (cx + int(radius * 0.42 * cos(angle + 0.30)),
                      cy + int(radius * 0.42 * sin(angle + 0.30)))],
                    SNOW)
    sheet.disc(cx, cy, 4, SNOW)
    # two jets crossing the top
    for jx, jy in ((left + 24, top + 12), (left + wide - 24, top + 16)):
        sheet.shape([(jx - 14, jy), (jx + 12, jy - 4), (jx + 17, jy),
                     (jx + 12, jy + 4)], (60, 60, 64))
        sheet.shape([(jx - 2, jy - 3), (jx + 5, jy - 10),
                     (jx + 8, jy - 3)], (60, 60, 64))
    # the runway
    sheet.box(left, top + tall - 14, wide, 14, (70, 70, 72))
    for dash in range(8, wide, 28):
        sheet.box(left + dash, top + tall - 9, 14, 3, SNOW)


def paint_delhi(sheet, left, top, wide, tall):
    """Nepal's red pennants and India's tricolour over Delhi's
    arch, with the Himalaya behind."""
    sheet.box(left, top, wide, tall, (238, 228, 208))
    # the Himalaya ridge
    sheet.shape([(left, top + tall), (left + 60, top + tall - 52),
                 (left + 120, top + tall)], (120, 130, 140))
    sheet.shape([(left + 80, top + tall),
                 (left + 170, top + tall - 64),
                 (left + 260, top + tall)], (90, 100, 114))
    sheet.shape([(left + 152, top + tall - 40),
                 (left + 170, top + tall - 64),
                 (left + 188, top + tall - 40)], SNOW)
    # the India Gate arch
    ax = left + wide // 2 - 30
    sheet.box(ax, top + tall - 48, 60, 48, (176, 140, 96))
    sheet.shape([(ax - 5, top + tall - 48), (ax + 65, top + tall - 48),
                 (ax + 55, top + tall - 60), (ax + 5, top + tall - 60)],
                (160, 124, 84))
    sheet.box(ax + 21, top + tall - 34, 18, 34, NEWSPRINT)
    sheet.disc(ax + 30, top + tall - 34, 9, NEWSPRINT)
    # Nepal's pennants on the left flagpole
    fx, fy = left + 20, top + 10
    sheet.box(fx, fy, 3, 56, (90, 70, 60))
    sheet.shape([(fx + 3, fy + 2), (fx + 36, fy + 11),
                 (fx + 3, fy + 20)], (200, 40, 50))
    sheet.shape([(fx + 3, fy + 22), (fx + 30, fy + 30),
                 (fx + 3, fy + 40)], (200, 40, 50))
    sheet.disc(fx + 13, fy + 11, 2, SNOW)
    sheet.disc(fx + 11, fy + 30, 2, SNOW)
    # India's tricolour on the right flagpole
    gx = left + wide - 58
    sheet.box(gx, fy, 3, 56, (90, 70, 60))
    sheet.box(gx + 3, fy + 2, 38, 11, (230, 130, 40))
    sheet.box(gx + 3, fy + 13, 38, 11, SNOW)
    sheet.box(gx + 3, fy + 24, 38, 11, (20, 130, 70))
    sheet.hoop(gx + 22, fy + 18, 5, 2, NAVY)


def paint_cricket(sheet, left, top, wide, tall):
    """A green outfield, the pitch, a leaning bat, a red ball in
    flight and the big score on a board."""
    sheet.box(left, top, wide, tall, (96, 158, 74))
    sheet.oval(left + wide // 2, top + tall - 10, wide // 2 - 6, 18,
               (74, 132, 58))
    # the pitch
    sheet.shape([(left + 96, top + tall - 6), (left + 124, top + 20),
                 (left + wide - 124, top + 20),
                 (left + wide - 96, top + tall - 6)], BEACH)
    sheet.box(left + wide // 2 - 2, top + 24, 4, tall - 34, SNOW)
    # the stumps
    for sx in (left + wide // 2 - 62, left + wide // 2 - 54,
               left + wide // 2 - 46):
        sheet.box(sx, top + 26, 4, 18, BRASS)
    sheet.box(left + wide // 2 - 62, top + 23, 22, 3, BRASS)
    # a bat leaning on the pitch
    sheet.shape([(left + 60, top + tall - 12),
                 (left + 80, top + tall - 18),
                 (left + 116, top + 30), (left + 106, top + 26)],
                (196, 164, 110))
    sheet.box(left + 104, top + 16, 7, 14, (120, 90, 60))
    # the red ball in flight
    sheet.disc(left + wide - 56, top + 34, 9, CRIMSON)
    sheet.disc(left + wide - 59, top + 31, 3, (255, 200, 200))
    # the scoreboard
    bx, by = left + wide - 132, top + tall - 40
    sheet.box(bx, by, 118, 32, INK)
    sheet.box(bx + 3, by + 3, 112, 26, (30, 30, 30))
    sheet.write(bx + 59, by + 6, 3, "720/9", BRASS, heavy=True,
                align="center")


# -------------------------------------------------------------------- page
def frame(sheet, x, y, wide, tall):
    """A story card: a pale face with a two-pixel ink border."""
    sheet.box(x, y, wide, tall, CARD_BG)
    sheet.box(x, y, wide, 2, INK)
    sheet.box(x, y, 2, tall, INK)
    sheet.box(x + wide - 2, y, 2, tall, INK)
    sheet.box(x, y + tall - 2, wide, 2, INK)


def article(sheet, x, y, wide, tall, kicker, headline, brief, scene,
            art_h=118, head_size=3):
    """One story card: a picture strip on top, then a red kicker,
    a wrapped headline and a short brief underneath."""
    frame(sheet, x, y, wide, tall)
    scene(sheet, x + 2, y + 2, wide - 4, art_h)
    ty = y + art_h + 10
    sheet.write(x + 12, ty, 2, kicker, CRIMSON, heavy=True)
    ty += 22
    head_lines = split_lines(headline, head_size, wide - 24,
                             heavy=True)
    ty = sheet.block(x + 12, ty, head_size, head_lines, INK,
                     heavy=True, gap=7 * head_size + 5)
    ty += 4
    brief_lines = split_lines(brief, 2, wide - 24)
    sheet.block(x + 12, ty, 2, brief_lines, SOFT_INK, gap=18)


# The two lower rows, as data: kicker, headline, brief, scene.
SECOND_ROW = [
    ("CLIMATE: ANTALYA, TURKEY",
     "COP31 COLLAPSES WITH NO DEAL ON FOSSIL FUELS",
     "The UN climate summit ends in failure as the EU "
     "rejects a final text with no mention of fossil "
     "fuels.",
     paint_climate),
    ("WAR IN UKRAINE: KYIV REGION",
     "DRONE SMASHES FLAT BLOCK: 14 FEARED TRAPPED",
     "A Russian drone hits a five-storey home in the "
     "Kyiv area and part of it falls in. Rescuers hunt "
     "for survivors; nine people are safe.",
     paint_kyiv),
]

THIRD_ROW = [
    ("EUROPE: BRUSSELS",
     "NATO MEETS AS POLAND CITES INCURSION",
     "Allies meet after Russian missiles and a drone "
     "cross into Poland.",
     paint_nato),
    ("SOUTH ASIA: NEW DELHI",
     "NEPAL PM MEETS MODI IN DELHI ON STATE VISIT",
     "Nepal PM Balendra Shah holds talks with PM "
     "Narendra Modi in Delhi.",
     paint_delhi),
    ("SPORT: WELLINGTON TEST",
     "INDIA 720 FOR 9: A RECORD TOTAL",
     "India declare on 720 for nine, the best in their "
     "Test history.",
     paint_cricket),
]

LEAD_COPY = ("Iranian missiles hit a civilian plant in Sitra, "
             "Bahrain, hurt two people and set it ablaze, as "
             "Tehran says it aimed at US bases. Two tankers "
             "were hit near Hormuz. Saudi jets down a Houthi "
             "missile, and the US denies an Iranian claim it "
             "hit a US jet.")


def build_page():
    """Lay out the whole front page and hand back the sheet."""
    sheet = Sheet(SIDE, NEWSPRINT)

    # ---- masthead
    sheet.box(EDGE, 10, SPAN, 2, INK)
    sheet.write(SIDE // 2, 20, 6, "THE WORLD IN ONE DAY", INK,
                heavy=True, align="center")
    sheet.write(SIDE // 2, 74, 3, "MONDAY 23 NOVEMBER 2026", CRIMSON,
                heavy=True, align="center")
    sheet.write(SIDE // 2, 104, 2,
                "SIX STORIES FROM A DAY OF WAR, CLIMATE FAILURE AND "
                "RECORD SPORT", FADED, align="center")
    sheet.box(EDGE, 130, SPAN, 4, INK)
    sheet.box(EDGE, 138, SPAN, 1, INK)

    # ---- the lead story: the Gulf war widens
    lx, ly, lw, lh = EDGE, 152, SPAN, 300
    frame(sheet, lx, ly, lw, lh)
    paint_gulf(sheet, lx + 2, ly + 2, 486, lh - 4)
    tx = lx + 502
    ty = ly + 16
    sheet.write(tx, ty, 2, "LEAD STORY: THE GULF WAR", CRIMSON,
                heavy=True)
    ty += 26
    head_lines = split_lines("IRAN HITS BAHRAIN AS TANKERS BURN IN THE "
                             "STRAIT", 3, lw - 514, heavy=True)
    ty = sheet.block(tx, ty, 3, head_lines, INK, heavy=True, gap=27)
    ty += 8
    brief_lines = split_lines(LEAD_COPY, 2, lw - 514)
    ty = sheet.block(tx, ty, 2, brief_lines, SOFT_INK, gap=19)
    ty += 12
    sheet.box(tx, ty, lw - 514, 2, CRIMSON)
    ty += 10
    sheet.write(tx, ty, 2, "2 HURT, 2 TANKERS, 1 MISSILE DOWN", CRIMSON,
                heavy=True)

    # ---- second row: COP31 and Kyiv
    half = (SPAN - 8) // 2
    for i, (kicker, headline, brief, scene) in enumerate(SECOND_ROW):
        article(sheet, EDGE + i * (half + 8), 462, half, 260,
                kicker, headline, brief, scene, art_h=92)

    # ---- third row: NATO, Nepal, cricket
    third = (SPAN - 16) // 3
    for i, (kicker, headline, brief, scene) in enumerate(THIRD_ROW):
        article(sheet, EDGE + i * (third + 8), 732, third, 216,
                kicker, headline, brief, scene, art_h=80, head_size=2)

    # ---- footer ticker and source line
    sheet.box(EDGE, 958, SPAN, 2, INK)
    sheet.write(EDGE, 966, 2,
                "ALSO TODAY: FACTORY FIRE IN INDONESIA LEAVES 7 DEAD, "
                "50 UNACCOUNTED FOR",
                INK, heavy=True)
    sheet.write(EDGE, 984, 2,
                "SEOUL MINISTER QUITS IN AI EXAM ROW - LISBON MARCHES "
                "ON COST OF LIFE",
                INK, heavy=True)
    sheet.write(EDGE, 1002, 2,
                "DRAWN IN CODE - NO PHOTO - SOURCES: REUTERS, AP, CNBC - "
                "23 NOVEMBER 2026",
                FADED)
    return sheet


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = render_png(build_page())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(png)


if __name__ == "__main__":
    main()
