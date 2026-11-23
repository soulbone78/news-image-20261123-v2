"""Front page for Monday 23 November 2026, drawn in plain Python.

The program paints a single newspaper page -- six stories plus a
ticker -- and writes it as a 1024x1024 PNG. It uses nothing but
the standard library, reaches no network, reads no clock and
rolls no dice, so running it twice gives the same bytes twice.

What is on the page:
  * the masthead, dated Monday 23 November 2026
  * the lead: Iranian missiles hit a civilian plant in Sitra,
    Bahrain, and two tankers are struck near the Strait of Hormuz
  * COP31 in Antalya ends with no deal on fossil fuels
  * a Russian drone wrecks a flat block in the Kyiv region
  * NATO gathers in Brussels after missiles and a drone cross
    into Poland
  * Nepal's prime minister Balendra Shah meets Narendra Modi in
    New Delhi
  * India declare on 720 for 9 in the Wellington Test, a record
  * a footer ticker: a factory fire in Indonesia, a Seoul
    minister quitting over an AI exam row, and a march in Lisbon

How it is painted: every shape lands on a canvas twice the final
size, which is then averaged down 2x2 to soften the edges. Words
use a small 5x7 dot face built into this file and are drawn bold
with a one-pixel second pass. The PNG itself is packed by hand
with zlib and struct.

One quirk of the little face: a lowercase "g" comes out looking
like a "9", so the body copy simply never uses a lowercase "g".
Headlines are all capitals, where the G shape is unmistakable.
"""

import math
import os
import struct
import zlib

SIDE = 1024          # final page edge, in pixels
ZOOM = 2             # supersampling factor
EDGE = 10            # page margin
INNER = SIDE - 2 * EDGE


def _rgb(triple):
    return tuple(triple)


# Palette, as plain RGB triples.
PARCHMENT = _rgb((247, 242, 231))
CARDSTOCK = _rgb((255, 252, 245))
INK = _rgb((26, 26, 26))
BODYINK = _rgb((52, 52, 48))
FADED = _rgb((110, 104, 92))
SCARLET = _rgb((178, 44, 38))
WINERED = _rgb((122, 28, 24))
NAVY = _rgb((28, 78, 138))
SKYBLUE = _rgb((168, 205, 232))
OCEAN = _rgb((24, 68, 110))
ABYSS = _rgb((14, 46, 78))
EMBER = _rgb((224, 112, 32))
BRASS = _rgb((214, 158, 46))
MOSS = _rgb((46, 122, 62))
SAP = _rgb((74, 148, 74))
DUNE = _rgb((222, 200, 150))
ASH = _rgb((148, 142, 130))
FUME = _rgb((120, 116, 108))
SNOW = _rgb((255, 255, 255))
COAL = _rgb((10, 10, 10))

# ------------------------------------------------------------------ face
# A 5-wide by 7-tall dot face. Every character is seven strings of
# five bits; a "1" means ink. Capitals, digits, punctuation and
# lowercase letters are all covered.

GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "01110", "00100", "00100", "00000"],
    "=": ["00000", "00000", "01110", "00000", "01110", "00000", "00000"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    '"': ["01010", "01010", "00000", "00000", "00000", "00000", "00000"],
    "*": ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    "a": ["00000", "00000", "01110", "00001", "01111", "10001", "01111"],
    "b": ["10000", "10000", "11110", "10001", "10001", "10001", "11110"],
    "c": ["00000", "00000", "01110", "10000", "10000", "10001", "01110"],
    "d": ["00001", "00001", "01111", "10001", "10001", "10001", "01111"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "f": ["00110", "01001", "01000", "11110", "01000", "01000", "01000"],
    "g": ["00000", "01111", "10001", "10001", "01111", "00001", "01110"],
    "h": ["10000", "10000", "11110", "10001", "10001", "10001", "10001"],
    "i": ["00100", "00000", "01100", "00100", "00100", "00100", "01110"],
    "j": ["00010", "00000", "00110", "00010", "00010", "10010", "01100"],
    "k": ["10000", "10000", "10101", "11001", "10100", "10010", "10001"],
    "l": ["01100", "00100", "00100", "00100", "00100", "00100", "01110"],
    "m": ["00000", "00000", "11010", "10101", "10101", "10101", "10101"],
    "n": ["00000", "00000", "11110", "10001", "10001", "10001", "10001"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "p": ["00000", "00000", "11110", "10001", "11110", "10000", "10000"],
    "q": ["00000", "00000", "01111", "10001", "01111", "00001", "00001"],
    "r": ["00000", "00000", "10110", "11001", "10000", "10000", "10000"],
    "s": ["00000", "00000", "01111", "10000", "01110", "00001", "11110"],
    "t": ["01000", "01000", "11100", "01000", "01000", "01001", "00110"],
    "u": ["00000", "00000", "10001", "10001", "10001", "10011", "01101"],
    "v": ["00000", "00000", "10001", "10001", "10001", "01010", "00100"],
    "w": ["00000", "00000", "10001", "10101", "10101", "10101", "01010"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    "y": ["00000", "00000", "10001", "10001", "01111", "00001", "01110"],
    "z": ["00000", "00000", "11111", "00010", "00100", "01000", "11111"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
}
DOT = ["00000", "00000", "01100", "01100", "00000", "00000", "00000"]


def measure(text, scale, bold=False):
    """Width of a string in final pixels at the given face size."""
    width = len(text) * 6 * scale - scale
    if bold:
        width += max(0, len(text) - 1)
    return width


def split_lines(text, scale, max_width, bold=False):
    """Greedy word wrap; every returned line fits inside max_width."""
    out = []
    for piece in text.split("\n"):
        words = piece.split(" ")
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if measure(trial, scale, bold) <= max_width or not current:
                current = trial
            else:
                out.append(current)
                current = word
        if current:
            out.append(current)
    return out


# ------------------------------------------------------------------ sheet
class Sheet:
    """An RGB canvas at ZOOM times the final size. Every method
    below takes coordinates in final-page pixels and scales them
    up on the inside."""

    def __init__(self, size, background):
        self.size = size
        self.big = size * ZOOM
        self.pixels = bytearray(self.big * self.big * 3)
        red, green, blue = background
        stripe = bytes((red, green, blue)) * self.big
        for row_no in range(self.big):
            start = row_no * self.big * 3
            self.pixels[start:start + self.big * 3] = stripe

    def fill(self, x, y, w, h, colour):
        """Solid rectangle, x, y, w, h in final pixels."""
        left = max(0, x * ZOOM)
        top = max(0, y * ZOOM)
        right = min(self.big, (x + w) * ZOOM)
        bottom = min(self.big, (y + h) * ZOOM)
        if right <= left or bottom <= top:
            return
        stripe = bytes(colour) * (right - left)
        for row_no in range(top, bottom):
            start = (row_no * self.big + left) * 3
            self.pixels[start:start + (right - left) * 3] = stripe

    def disc(self, cx, cy, radius, colour):
        """Solid circle, centre and radius in final pixels."""
        cx *= ZOOM
        cy *= ZOOM
        radius *= ZOOM
        radius_sq = radius * radius
        for row_no in range(max(0, cy - radius),
                            min(self.big, cy + radius + 1)):
            dy = row_no - cy
            half = int(math.sqrt(max(0, radius_sq - dy * dy)))
            left = max(0, cx - half)
            right = min(self.big, cx + half + 1)
            start = (row_no * self.big + left) * 3
            self.pixels[start:start + (right - left) * 3] = (
                bytes(colour) * (right - left))

    def oval(self, cx, cy, rx, ry, colour):
        """Solid ellipse, centre and radii in final pixels."""
        cx *= ZOOM
        cy *= ZOOM
        rx *= ZOOM
        ry *= ZOOM
        for row_no in range(max(0, cy - ry),
                            min(self.big, cy + ry + 1)):
            ratio = (row_no - cy) / ry
            half = int(rx * math.sqrt(max(0.0, 1.0 - ratio * ratio)))
            left = max(0, cx - half)
            right = min(self.big, cx + half + 1)
            start = (row_no * self.big + left) * 3
            self.pixels[start:start + (right - left) * 3] = (
                bytes(colour) * (right - left))

    def poly(self, points, colour):
        """Filled polygon; points are (x, y) in final pixels."""
        scaled = [(px * ZOOM, py * ZOOM) for px, py in points]
        heights = [pt[1] for pt in scaled]
        first = max(0, min(heights))
        last = min(self.big - 1, max(heights))
        count = len(scaled)
        for row_no in range(first, last + 1):
            crossings = []
            for idx in range(count):
                x1, ya = scaled[idx]
                x2, yb = scaled[(idx + 1) % count]
                if ya == yb:
                    continue
                if (ya <= row_no < yb) or (yb <= row_no < ya):
                    crossings.append(
                        int(x1 + (row_no - ya) * (x2 - x1) / (yb - ya)))
            crossings.sort()
            for k in range(0, len(crossings) - 1, 2):
                left = max(0, crossings[k])
                right = min(self.big, crossings[k + 1] + 1)
                if right > left:
                    start = (row_no * self.big + left) * 3
                    self.pixels[start:start + (right - left) * 3] = (
                        bytes(colour) * (right - left))

    def stroke(self, x0, y0, x1, y1, width, colour):
        """Thick straight line, width in final pixels."""
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * ZOOM) + 1
        half = max(1, width * ZOOM // 2)
        for step in range(steps + 1):
            frac = step / max(1, steps)
            cx = int((x0 + (x1 - x0) * frac) * ZOOM)
            cy = int((y0 + (y1 - y0) * frac) * ZOOM)
            for row_no in range(max(0, cy - half),
                                min(self.big, cy + half + 1)):
                dy = row_no - cy
                span = int(math.sqrt(max(0, half * half - dy * dy)))
                left = max(0, cx - span)
                right = min(self.big, cx + span + 1)
                start = (row_no * self.big + left) * 3
                self.pixels[start:start + (right - left) * 3] = (
                    bytes(colour) * (right - left))

    def halo(self, cx, cy, radius, width, colour):
        """Circle outline, radius and width in final pixels."""
        steps = int(2 * math.pi * radius * ZOOM) + 8
        for step in range(steps):
            angle = 2 * math.pi * step / steps
            px = int((cx + radius * math.cos(angle)) * ZOOM)
            py = int((cy + radius * math.sin(angle)) * ZOOM)
            self.disc(px // ZOOM, py // ZOOM, max(1, width // 2), colour)

    # ------------------------------------------------------------ lettering
    def _letter(self, x, y, scale, rows, colour):
        """Paint one 5x7 character; x, y in final pixels, scale in
        final pixels per face pixel."""
        for row_i, row in enumerate(rows):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    self.fill(x + col_i * scale, y + row_i * scale,
                              scale, scale, colour)

    def write(self, x, y, scale, text, colour, bold=False, align="left"):
        """Paint a string; returns the width painted, in final pixels."""
        if align in ("center", "right"):
            full = measure(text, scale)
            if align == "center":
                x -= full // 2
            else:
                x -= full
        pen = x
        for char in text:
            rows = GLYPHS.get(char)
            if rows is None:
                rows = DOT if char == "\u2022" else GLYPHS[" "]
            self._letter(pen, y, scale, rows, colour)
            if bold and scale >= 2:
                # A second pass one final pixel to the right fattens
                # the strokes, which is what makes the face bold.
                self._letter(pen + 1, y, scale, rows, colour)
            pen += 6 * scale
        return pen - x - scale

    def write_block(self, x, y, scale, lines, colour, bold=False,
                    leading=None, align="left"):
        """Paint several lines, one under the next."""
        if leading is None:
            leading = 7 * scale + 4
        for line in lines:
            self.write(x, y, scale, line, colour, bold=bold, align=align)
            y += leading
        return y

    # ------------------------------------------------------------- encoding
    def png_bytes(self):
        """Average each 2x2 block down to one pixel, then pack a PNG
        with filter-0 rows, zlib level 9, and the usual chunks."""
        body = bytearray()
        wide = self.big
        src = self.pixels
        for out_y in range(SIDE):
            body.append(0)
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
                body.append(red // 4)
                body.append(green // 4)
                body.append(blue // 4)
        packed = zlib.compress(bytes(body), 9)

        def chunk(kind, data):
            out = struct.pack(">I", len(data)) + kind + data
            out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            return out

        header = struct.pack(">IIBBBBB", SIDE, SIDE, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", header)
        png += chunk(b"IDAT", packed)
        png += chunk(b"IEND", b"")
        return png


# ------------------------------------------------------------------- scenes
def blast(sheet, cx, cy, radius, core, mid, rim):
    """An explosion starburst, built from three jagged polygons
    layered from the outside in."""
    spikes = 12
    for size, colour in ((radius, rim), (int(radius * 0.72), mid),
                         (int(radius * 0.45), core)):
        outline = []
        for i in range(spikes * 2):
            angle = math.pi * i / spikes
            reach = size if i % 2 == 0 else int(size * 0.45)
            outline.append((cx + int(reach * math.cos(angle)),
                            cy + int(reach * math.sin(angle))))
        sheet.poly(outline, colour)


def scene_strait(sheet, x, y, w, h):
    """The Strait of Hormuz: two tankers on a dark sea, blasts, and
    the white trails of missiles arcing overhead."""
    sheet.fill(x, y, w, h, SKYBLUE)
    sheet.disc(x + w - 70, y + 42, 26, BRASS)          # low sun
    sheet.disc(x + w - 70, y + 42, 20, (232, 190, 90))
    # a distant shore
    sheet.poly([(x, y + 118), (x + 150, y + 96), (x + 320, y + 112),
                (x + w, y + 92), (x + w, y + 128), (x, y + 128)],
               (196, 178, 138))
    # the sea
    sheet.fill(x, y + 128, w, h - 128, OCEAN)
    sheet.fill(x, y + 128, w, 6, (64, 128, 178))
    for wave_y in range(y + 150, y + h - 8, 18):
        sheet.fill(x + 12 + ((wave_y * 7) % 40), wave_y, 60, 3,
                   (64, 128, 178))
    # the first tanker (left, on fire)
    tx, ty = x + 26, y + 168
    sheet.fill(tx, ty, 190, 34, (38, 38, 40))
    sheet.fill(tx + 128, ty - 34, 34, 34, (200, 200, 200))
    sheet.fill(tx + 136, ty - 44, 18, 10, SCARLET)
    sheet.fill(tx + 8, ty - 16, 26, 16, (220, 220, 210))
    sheet.fill(tx + 150, ty + 34, 12, 26, (38, 38, 40))
    blast(sheet, tx + 60, ty - 26, 46, (255, 214, 90), EMBER, SCARLET)
    sheet.disc(tx + 30, ty - 58, 16, FUME)
    sheet.disc(tx + 58, ty - 74, 22, FUME)
    sheet.disc(tx + 92, ty - 60, 15, FUME)
    # the second tanker (right, hit at the stern)
    tx2, ty2 = x + 252, y + 208
    sheet.fill(tx2, ty2, 210, 30, (52, 52, 56))
    sheet.fill(tx2 + 30, ty2 - 30, 30, 30, (200, 200, 200))
    sheet.fill(tx2 + 38, ty2 - 40, 14, 10, SCARLET)
    sheet.fill(tx2 + 150, ty2 - 14, 22, 14, (220, 220, 210))
    blast(sheet, tx2 + 205, ty2 - 8, 34, (255, 214, 90), EMBER, SCARLET)
    # missile arcs, drawn as white trails
    sheet.stroke(x + 60, y + 20, x + 130, y + 120, 3, SNOW)
    sheet.stroke(x + 130, y + 120, x + 150, y + 152, 3, SNOW)
    sheet.disc(x + 60, y + 20, 5, SNOW)
    sheet.stroke(x + 420, y + 26, x + 380, y + 110, 3, SNOW)
    sheet.stroke(x + 380, y + 110, x + 430, y + 176, 3, SNOW)
    sheet.disc(x + 420, y + 26, 5, SNOW)
    # wakes behind the tankers
    sheet.stroke(tx, ty + 40, tx + 190, ty + 40, 2, (140, 180, 210))
    sheet.stroke(tx2, ty2 + 36, tx2 + 210, ty2 + 36, 2, (140, 180, 210))
    # place labels
    sheet.write(x + 14, y + h - 26, 2, "BAHRAIN", SNOW, bold=True)
    sheet.write(x + w - 14, y + h - 26, 2, "HORMUZ", SNOW, bold=True,
                align="right")


def scene_summit(sheet, x, y, w, h):
    """A cracked globe hanging over a summit hall: the talks fail."""
    sheet.fill(x, y, w, h, (222, 232, 226))
    # the hall, a low silhouette with a row of windows
    sheet.fill(x, y + h - 26, w, 26, (120, 118, 112))
    for win_x in range(x + 18, x + w - 18, 34):
        sheet.fill(win_x, y + h - 22, 14, 18, (60, 60, 58))
    sheet.poly([(x, y + h - 26), (x + w // 2, y + h - 46),
                (x + w, y + h - 26)], (90, 88, 84))
    # the globe
    gx, gy = x + w // 2, y + h // 2 - 2
    globe_r = min(46, h // 2 - 6)
    sheet.disc(gx, gy, globe_r, NAVY)
    sheet.disc(gx - 14, gy - 10, 11, SAP)
    sheet.disc(gx + 15, gy + 6, 14, SAP)
    sheet.disc(gx - 6, gy + 18, 8, SAP)
    sheet.disc(gx + 19, gy - 18, 6, SAP)
    sheet.oval(gx, gy, globe_r, int(globe_r * 0.36), (120, 180, 220))
    # the crack running across it
    sheet.stroke(gx - globe_r + 4, gy - globe_r // 2, gx - 10, gy - 4, 3,
                 SCARLET)
    sheet.stroke(gx - 10, gy - 4, gx + 4, gy - 16, 3, SCARLET)
    sheet.stroke(gx + 4, gy - 16, gx + 18, gy + 2, 3, SCARLET)
    sheet.stroke(gx + 18, gy + 2, gx + globe_r - 4, gy + globe_r // 2, 3,
                 SCARLET)
    sheet.halo(gx, gy, globe_r, 3, INK)
    # factory smoke off to the left
    sheet.fill(x + 16, y + h - 52, 8, 30, ASH)
    sheet.disc(x + 20, y + h - 60, 8, FUME)
    sheet.disc(x + 34, y + h - 68, 9, FUME)
    # a dimmed sun
    sheet.disc(x + w - 30, y + 22, 12, (232, 190, 90))


def scene_kyiv(sheet, x, y, w, h):
    """A five-storey flat block with its corner smashed in, smoke
    rising and rescue lights below."""
    sheet.fill(x, y, w, h, (214, 208, 196))
    # sky band
    sheet.fill(x, y, w, 40, SKYBLUE)
    sheet.disc(x + w - 34, y + 20, 11, (240, 220, 150))
    # the block itself
    bx, by, bw = x + 46, y + 36, w - 92
    bh = h - 36
    sheet.fill(bx, by, bw, bh, (196, 178, 150))
    sheet.fill(bx, by, bw, 6, (160, 140, 114))
    rows = 4 if h >= 130 else (3 if h >= 110 else 2)
    cols = max(4, (bw - 28) // 40)
    step = max(20, (bh - 26) // rows)
    for row in range(rows):
        for col in range(cols):
            win_x = bx + 14 + col * 40
            win_y = by + 14 + row * step
            sheet.fill(win_x, win_y, 22, 16, (70, 84, 104))
            sheet.fill(win_x, win_y, 22, 3, (200, 210, 220))
    # the collapsed corner: a jagged dark hole and rubble, all
    # kept inside the block
    sheet.poly([(bx + bw, by + 8), (bx + bw - 52, by + int(bh * 0.30)),
                (bx + bw - 30, by + int(bh * 0.52)),
                (bx + bw - 56, by + int(bh * 0.72)),
                (bx + bw - 26, by + int(bh * 0.90)),
                (bx + bw, by + bh)], (52, 48, 44))
    sheet.poly([(bx + bw - 78, by + bh), (bx + bw - 34, by + bh - 40),
                (bx + bw + 8, by + bh - 14), (bx + bw + 8, by + bh),
                (bx + bw - 78, by + bh)], (120, 112, 100))
    sheet.poly([(bx + bw - 50, by + bh - 24), (bx + bw - 16, by + bh - 34),
                (bx + bw + 4, by + bh - 18), (bx + bw - 24, by + bh - 6)],
               (90, 84, 74))
    # smoke above the wreck
    sheet.disc(bx + bw - 26, by + 12, 14, FUME)
    sheet.disc(bx + bw - 48, by - 4, 18, FUME)
    sheet.disc(bx + bw - 8, by - 12, 11, FUME)
    # rescue lights at the foot of the block
    sheet.disc(bx + 26, by + bh - 10, 5, SCARLET)
    sheet.disc(bx + 44, by + bh - 10, 5, EMBER)
    # ground line
    sheet.fill(x, y + h - 6, w, 6, (120, 116, 106))


def scene_nato(sheet, x, y, w, h):
    """A NATO compass star in a blue roundel, jets above and a
    runway below."""
    sheet.fill(x, y, w, h, (222, 230, 238))
    cx, cy = x + w // 2, y + h // 2 - 2
    radius = max(18, h // 2 - 10)
    sheet.disc(cx, cy, radius, NAVY)
    sheet.halo(cx, cy, radius, 3, SNOW)
    # the four-point compass star
    for bearing in (90, 210, 330, -90):
        angle = math.radians(bearing)
        tip = radius - 4 if bearing != -90 else radius - 8
        sheet.poly([(cx, cy),
                    (cx + int(radius * 0.42 * math.cos(angle - 0.30)),
                     cy + int(radius * 0.42 * math.sin(angle - 0.30))),
                    (cx + int(tip * math.cos(angle)),
                     cy + int(tip * math.sin(angle))),
                    (cx + int(radius * 0.42 * math.cos(angle + 0.30)),
                     cy + int(radius * 0.42 * math.sin(angle + 0.30)))],
                   SNOW)
    sheet.disc(cx, cy, 4, SNOW)
    # two jets crossing the top
    for jx, jy in ((x + 24, y + 12), (x + w - 24, y + 16)):
        sheet.poly([(jx - 14, jy), (jx + 12, jy - 4), (jx + 17, jy),
                    (jx + 12, jy + 4)], (60, 60, 64))
        sheet.poly([(jx - 2, jy - 3), (jx + 5, jy - 10), (jx + 8, jy - 3)],
                   (60, 60, 64))
    # the runway
    sheet.fill(x, y + h - 14, w, 14, (70, 70, 72))
    for dash in range(8, w, 28):
        sheet.fill(x + dash, y + h - 9, 14, 3, SNOW)


def scene_delhi(sheet, x, y, w, h):
    """Nepal's red pennants and India's tricolour over Delhi's
    arch, with the Himalaya behind."""
    sheet.fill(x, y, w, h, (238, 228, 208))
    # the Himalaya ridge
    sheet.poly([(x, y + h), (x + 60, y + h - 52), (x + 120, y + h)],
               (120, 130, 140))
    sheet.poly([(x + 80, y + h), (x + 170, y + h - 64), (x + 260, y + h)],
               (90, 100, 114))
    sheet.poly([(x + 152, y + h - 40), (x + 170, y + h - 64),
                (x + 188, y + h - 40)], SNOW)
    # the India Gate arch
    ax = x + w // 2 - 30
    sheet.fill(ax, y + h - 48, 60, 48, (176, 140, 96))
    sheet.poly([(ax - 5, y + h - 48), (ax + 65, y + h - 48),
                (ax + 55, y + h - 60), (ax + 5, y + h - 60)],
               (160, 124, 84))
    sheet.fill(ax + 21, y + h - 34, 18, 34, PARCHMENT)
    sheet.disc(ax + 30, y + h - 34, 9, PARCHMENT)
    # Nepal's pennants on the left flagpole
    fx, fy = x + 20, y + 10
    sheet.fill(fx, fy, 3, 56, (90, 70, 60))
    sheet.poly([(fx + 3, fy + 2), (fx + 36, fy + 11), (fx + 3, fy + 20)],
               (200, 40, 50))
    sheet.poly([(fx + 3, fy + 22), (fx + 30, fy + 30), (fx + 3, fy + 40)],
               (200, 40, 50))
    sheet.disc(fx + 13, fy + 11, 2, SNOW)
    sheet.disc(fx + 11, fy + 30, 2, SNOW)
    # India's tricolour on the right flagpole
    fx2 = x + w - 58
    sheet.fill(fx2, fy, 3, 56, (90, 70, 60))
    sheet.fill(fx2 + 3, fy + 2, 38, 11, (230, 130, 40))
    sheet.fill(fx2 + 3, fy + 13, 38, 11, SNOW)
    sheet.fill(fx2 + 3, fy + 24, 38, 11, (20, 130, 70))
    sheet.halo(fx2 + 22, fy + 18, 5, 2, NAVY)


def scene_cricket(sheet, x, y, w, h):
    """A green outfield, the pitch, a leaning bat, a red ball in
    flight and the big score on a board."""
    sheet.fill(x, y, w, h, (96, 158, 74))
    sheet.oval(x + w // 2, y + h - 10, w // 2 - 6, 18, (74, 132, 58))
    # the pitch
    sheet.poly([(x + 96, y + h - 6), (x + 124, y + 20),
                (x + w - 124, y + 20), (x + w - 96, y + h - 6)], DUNE)
    sheet.fill(x + w // 2 - 2, y + 24, 4, h - 34, SNOW)
    # the stumps
    for sx in (x + w // 2 - 62, x + w // 2 - 54, x + w // 2 - 46):
        sheet.fill(sx, y + 26, 4, 18, BRASS)
    sheet.fill(x + w // 2 - 62, y + 23, 22, 3, BRASS)
    # a bat leaning on the pitch
    sheet.poly([(x + 60, y + h - 12), (x + 80, y + h - 18),
                (x + 116, y + 30), (x + 106, y + 26)], (196, 164, 110))
    sheet.fill(x + 104, y + 16, 7, 14, (120, 90, 60))
    # the red ball in flight
    sheet.disc(x + w - 56, y + 34, 9, SCARLET)
    sheet.disc(x + w - 59, y + 31, 3, (255, 200, 200))
    # the scoreboard
    bx, by = x + w - 132, y + h - 40
    sheet.fill(bx, by, 118, 32, INK)
    sheet.fill(bx + 3, by + 3, 112, 26, (30, 30, 30))
    sheet.write(bx + 59, by + 6, 3, "720/9", BRASS, bold=True,
                align="center")


# -------------------------------------------------------------------- page
def frame(sheet, x, y, w, h):
    """A story card: a pale face with a two-pixel ink border."""
    sheet.fill(x, y, w, h, CARDSTOCK)
    sheet.fill(x, y, w, 2, INK)
    sheet.fill(x, y, 2, h, INK)
    sheet.fill(x + w - 2, y, 2, h, INK)
    sheet.fill(x, y + h - 2, w, 2, INK)


def story_block(sheet, x, y, w, h, kicker, headline, brief, scene,
                art_h=118, head_size=3):
    """One story card: a picture strip on top, then a red kicker,
    a wrapped headline and a short brief underneath."""
    frame(sheet, x, y, w, h)
    scene(sheet, x + 2, y + 2, w - 4, art_h)
    ty = y + art_h + 10
    sheet.write(x + 12, ty, 2, kicker, SCARLET, bold=True)
    ty += 22
    head_lines = split_lines(headline, head_size, w - 24, bold=True)
    ty = sheet.write_block(x + 12, ty, head_size, head_lines, INK,
                           bold=True, leading=7 * head_size + 5)
    ty += 4
    brief_lines = split_lines(brief, 2, w - 24)
    sheet.write_block(x + 12, ty, 2, brief_lines, BODYINK, leading=18)


def build_page():
    """Lay out the whole front page and hand back the sheet."""
    sheet = Sheet(SIDE, PARCHMENT)

    # ---- masthead
    sheet.fill(EDGE, 10, INNER, 2, INK)
    sheet.write(SIDE // 2, 20, 6, "THE WORLD IN ONE DAY", INK, bold=True,
                align="center")
    sheet.write(SIDE // 2, 74, 3, "MONDAY 23 NOVEMBER 2026", SCARLET,
                bold=True, align="center")
    sheet.write(SIDE // 2, 104, 2,
                "SIX STORIES FROM A DAY OF WAR, CLIMATE FAILURE AND "
                "RECORD SPORT", FADED, align="center")
    sheet.fill(EDGE, 130, INNER, 4, INK)
    sheet.fill(EDGE, 138, INNER, 1, INK)

    # ---- the lead story: the Gulf war widens
    lx, ly, lw, lh = EDGE, 152, INNER, 300
    frame(sheet, lx, ly, lw, lh)
    scene_strait(sheet, lx + 2, ly + 2, 486, lh - 4)
    tx = lx + 502
    ty = ly + 16
    sheet.write(tx, ty, 2, "LEAD STORY: THE GULF WAR", SCARLET, bold=True)
    ty += 26
    head_lines = split_lines("IRAN HITS BAHRAIN AS TANKERS BURN IN THE "
                             "STRAIT", 3, lw - 514, bold=True)
    ty = sheet.write_block(tx, ty, 3, head_lines, INK, bold=True,
                           leading=27)
    ty += 8
    lead_copy = ("Iranian missiles hit a civilian plant in Sitra, "
                 "Bahrain, hurt two people and set it ablaze, as "
                 "Tehran says it aimed at US bases. Two tankers "
                 "were hit near Hormuz. Saudi jets down a Houthi "
                 "missile, and the US denies an Iranian claim it "
                 "hit a US jet.")
    brief_lines = split_lines(lead_copy, 2, lw - 514)
    ty = sheet.write_block(tx, ty, 2, brief_lines, BODYINK, leading=19)
    ty += 12
    sheet.fill(tx, ty, lw - 514, 2, SCARLET)
    ty += 10
    sheet.write(tx, ty, 2, "2 HURT, 2 TANKERS, 1 MISSILE DOWN", SCARLET,
                bold=True)

    # ---- second row: COP31 and Kyiv
    row_y, row_h = 462, 260
    half_w = (INNER - 8) // 2
    story_block(sheet, EDGE, row_y, half_w, row_h,
                "CLIMATE: ANTALYA, TURKEY",
                "COP31 COLLAPSES WITH NO DEAL ON FOSSIL FUELS",
                "The UN climate summit ends in failure as the EU "
                "rejects a final text with no mention of fossil "
                "fuels.",
                scene_summit, art_h=92)
    story_block(sheet, EDGE + half_w + 8, row_y, half_w, row_h,
                "WAR IN UKRAINE: KYIV REGION",
                "DRONE SMASHES FLAT BLOCK: 14 FEARED TRAPPED",
                "A Russian drone hits a five-storey home in the "
                "Kyiv area and part of it falls in. Rescuers hunt "
                "for survivors; nine people are safe.",
                scene_kyiv, art_h=92)

    # ---- third row: NATO, Nepal, cricket
    row3_y, row3_h = 732, 216
    third_w = (INNER - 16) // 3
    story_block(sheet, EDGE, row3_y, third_w, row3_h,
                "EUROPE: BRUSSELS",
                "NATO MEETS AS POLAND CITES INCURSION",
                "Allies meet after Russian missiles and a drone "
                "cross into Poland.",
                scene_nato, art_h=80, head_size=2)
    story_block(sheet, EDGE + third_w + 8, row3_y, third_w, row3_h,
                "SOUTH ASIA: NEW DELHI",
                "NEPAL PM MEETS MODI IN DELHI ON STATE VISIT",
                "Nepal PM Balendra Shah holds talks with PM "
                "Narendra Modi in Delhi.",
                scene_delhi, art_h=80, head_size=2)
    story_block(sheet, EDGE + 2 * (third_w + 8), row3_y, third_w, row3_h,
                "SPORT: WELLINGTON TEST",
                "INDIA 720 FOR 9: A RECORD TOTAL",
                "India declare on 720 for nine, the best in their "
                "Test history.",
                scene_cricket, art_h=80, head_size=2)

    # ---- footer ticker and source line
    sheet.fill(EDGE, 958, INNER, 2, INK)
    sheet.write(EDGE, 966, 2,
                "ALSO TODAY: FACTORY FIRE IN INDONESIA LEAVES 7 DEAD, "
                "50 UNACCOUNTED FOR",
                INK, bold=True)
    sheet.write(EDGE, 984, 2,
                "SEOUL MINISTER QUITS IN AI EXAM ROW - LISBON MARCHES "
                "ON COST OF LIFE",
                INK, bold=True)
    sheet.write(EDGE, 1002, 2,
                "DRAWN IN CODE - NO PHOTO - SOURCES: REUTERS, AP, CNBC - "
                "23 NOVEMBER 2026",
                FADED)
    return sheet


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = build_page().png_bytes()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as handle:
        handle.write(png)


if __name__ == "__main__":
    main()
