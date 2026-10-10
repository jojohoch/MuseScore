#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Create the Octet app icon, replacing the MuseScore Studio logo.

The icon is the voice 8 symbol (see add_voice_icons.py) in white on a rounded
square. It is written to every place the MuseScore Studio logo was used:
the PNG sizes, .ico and .icns in share/icons/AppIcon, the symbol layer of the
macOS icon bundle, and the logo in the About dialog.

Usage: make_app_icon.py <repository root>
Requires fontTools and Pillow.
"""

import os
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

VOICE_8 = 0xF4C6
BACKGROUND = "#00695C"
SYMBOL = "#FFFFFF"
CANVAS = 1024           # icon size in SVG units
CORNER_RADIUS = 225     # rounded square, like the MuseScore Studio icon
SYMBOL_HEIGHT = 0.62    # height of the symbol relative to the icon

PNG_SIZES = [16, 24, 32, 48, 64, 96, 128, 256, 512, 1024, 2048]
ICO_SIZES = [16, 24, 32, 48, 64, 96, 128, 256]


def symbol_geometry(font):
    glyph_set = font.getGlyphSet()
    name = font.getBestCmap()[VOICE_8]
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[name].draw(bounds_pen)
    x_min, y_min, x_max, y_max = bounds_pen.bounds

    scale = CANVAS * SYMBOL_HEIGHT / (y_max - y_min)
    # Font units point up, SVG units point down: flip and center
    dx = (CANVAS - scale * (x_max - x_min)) / 2 - scale * x_min
    dy = (CANVAS + scale * (y_max - y_min)) / 2 + scale * y_min

    path_pen = SVGPathPen(glyph_set)
    glyph_set[name].draw(path_pen)
    transform = "matrix(%.4f 0 0 %.4f %.2f %.2f)" % (scale, -scale, dx, dy)
    return path_pen.getCommands(), transform


def svg(path, transform, with_background):
    background = ""
    if with_background:
        background = '<rect width="%d" height="%d" rx="%d" fill="%s"/>\n' % (CANVAS, CANVAS, CORNER_RADIUS, BACKGROUND)
    return ('<svg width="%d" height="%d" viewBox="0 0 %d %d" fill="none" xmlns="http://www.w3.org/2000/svg">\n'
            '%s<path transform="%s" fill="%s" d="%s"/>\n'
            '</svg>\n') % (CANVAS, CANVAS, CANVAS, CANVAS, background, transform, SYMBOL, path)


def raster(font_path, font, size):
    # Draw at a larger size and scale down for smooth edges
    big = max(size, 512) * 2
    image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    radius = big * CORNER_RADIUS / CANVAS
    draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius, fill=BACKGROUND)

    glyph_set = font.getGlyphSet()
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[font.getBestCmap()[VOICE_8]].draw(bounds_pen)
    x_min, y_min, x_max, y_max = bounds_pen.bounds
    units_per_em = font["head"].unitsPerEm

    pixels_per_unit = big * SYMBOL_HEIGHT / (y_max - y_min)
    image_font = ImageFont.truetype(font_path, round(pixels_per_unit * units_per_em))
    left, top, right, bottom = draw.textbbox((0, 0), chr(VOICE_8), font=image_font)
    draw.text(((big - (right - left)) / 2 - left, (big - (bottom - top)) / 2 - top), chr(VOICE_8),
              font=image_font, fill=SYMBOL)

    return image.resize((size, size), Image.LANCZOS)


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main(root):
    font_path = os.path.join(root, "src/framework/ui/data/MusescoreIcon.ttf")
    icons_dir = os.path.join(root, "share/icons/AppIcon")
    font = TTFont(font_path)

    path, transform = symbol_geometry(font)
    write(os.path.join(root, "src/appshell/qml/MuseScore/AppShell/resources/mu_logo.svg"), svg(path, transform, True))
    write(os.path.join(icons_dir, "AppIcon.icon/Assets/1x1 Colour.svg"), svg(path, transform, False))

    images = {size: raster(font_path, font, size) for size in PNG_SIZES}
    for size, image in images.items():
        image.save(os.path.join(icons_dir, "MS4_AppIcon_%dx%d.png" % (size, size)))
    images[256].save(os.path.join(icons_dir, "MS4_AppIcon.ico"), sizes=[(s, s) for s in ICO_SIZES])
    images[1024].save(os.path.join(icons_dir, "MS4_AppIcon.icns"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
