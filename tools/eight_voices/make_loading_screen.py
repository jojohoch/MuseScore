#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Create the Octet loading screen, replacing the MuseScore Studio logo.

The loading screen shows the voice 8 symbol (see add_voice_icons.py) and the
name Octet, set in FreeSans Bold (GNU FreeFont, GPLv3 with font
exception) and converted to paths, so it does not depend on installed fonts.
The program draws the version and the website at the bottom right.

Usage: make_loading_screen.py <repository root> FreeSansBold.ttf
Requires fontTools.
"""

import os
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

VOICE_8 = 0xF4C6
NAME = "Octet"
WIDTH, HEIGHT = 800, 380
BACKGROUND = "#00081C"
SYMBOL_COLOR = "#19F3FF"   # same as the version number on the loading screen
NAME_COLOR = "#F1F1EE"     # same as the messages on the loading screen
LEFT = 48
SYMBOL_HEIGHT = 72
CAP_HEIGHT = 50
GAP = 22


def bounds(glyph_set, name):
    pen = BoundsPen(glyph_set)
    glyph_set[name].draw(pen)
    return pen.bounds


def path(glyph_set, name, scale, dx, dy):
    pen = SVGPathPen(glyph_set)
    glyph_set[name].draw(pen)
    return '<path transform="matrix(%.5f 0 0 %.5f %.2f %.2f)" d="%s"/>' % (scale, -scale, dx, dy, pen.getCommands())


def main(root, name_font_path):
    icon_font = TTFont(os.path.join(root, "src/framework/ui/data/MusescoreIcon.ttf"))
    icons = icon_font.getGlyphSet()
    symbol = icon_font.getBestCmap()[VOICE_8]
    x_min, y_min, x_max, y_max = bounds(icons, symbol)

    middle = HEIGHT / 2
    scale = SYMBOL_HEIGHT / (y_max - y_min)
    symbol_path = path(icons, symbol, scale, LEFT - scale * x_min, middle + SYMBOL_HEIGHT / 2 + scale * y_min)
    x = LEFT + scale * (x_max - x_min) + GAP

    name_font = TTFont(name_font_path)
    letters = name_font.getGlyphSet()
    cmap = name_font.getBestCmap()
    cap = bounds(letters, cmap[ord("A")])
    scale = CAP_HEIGHT / (cap[3] - cap[1])
    baseline = middle + CAP_HEIGHT / 2
    name_paths = []
    for char in NAME:
        glyph = cmap[ord(char)]
        name_paths.append(path(letters, glyph, scale, x, baseline))
        x += scale * name_font["hmtx"][glyph][0]

    svg = ('<svg width="%d" height="%d" viewBox="0 0 %d %d" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
           '<rect width="%d" height="%d" fill="%s"/>\n'
           '<g fill="%s">%s</g>\n'
           '<g fill="%s">\n%s\n</g>\n'
           '</svg>\n') % (WIDTH, HEIGHT, WIDTH, HEIGHT, WIDTH, HEIGHT, BACKGROUND,
                          SYMBOL_COLOR, symbol_path, NAME_COLOR, "\n".join(name_paths))

    with open(os.path.join(root, "src/appshell/resources/LoadingScreen.svg"), "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
