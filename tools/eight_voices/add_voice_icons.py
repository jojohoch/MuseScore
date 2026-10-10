#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Add icons for voices 5-8 to MusescoreIcon.ttf.

Each new icon combines the note of an existing voice icon (stem up for odd
voices, stem down for even voices, like voices 1 and 2) with a digit from
FreeSans Bold (GNU FreeFont, GPLv3 with font exception). The digits of the
existing icons have the proportions of FreeSans Bold, so the new digits are
scaled and placed to match them.

Usage: add_voice_icons.py MusescoreIcon.ttf FreeSansBold.ttf
The icon font is rewritten in place. Requires fontTools.
"""

import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

VOICE_1 = 0xF391          # stem-up note with "1"
VOICE_2 = 0xF392          # stem-down note with "2"
FIRST_NEW_CODE = 0xF4C3   # VOICE_5 .. VOICE_8, see IconCode in iconcodes.h

DIGIT_LEFT = 606          # left edge of the digits in the existing icons
DIGIT_BASELINE = 249      # baseline of the digits in the existing icons
DIGIT_HEIGHT = 519        # height of "1" in the existing icons


def contours(glyph_set, glyph_name):
    pen = RecordingPen()
    glyph_set[glyph_name].draw(pen)
    result, current = [], []
    for op, args in pen.value:
        current.append((op, args))
        if op in ("closePath", "endPath"):
            result.append(current)
            current = []
    return result


def note_contour(glyph_set, glyph_name):
    # The note is left of the digit
    def x_min(contour):
        return min(x for _, args in contour for x, _ in args)
    return min(contours(glyph_set, glyph_name), key=x_min)


def bounds(glyph_set, glyph_name):
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.bounds


def main(icon_path, digits_path):
    icons = TTFont(icon_path)
    digits = TTFont(digits_path)
    icon_glyphs = icons.getGlyphSet()
    digit_glyphs = digits.getGlyphSet()
    icon_cmap = icons.getBestCmap()
    digit_cmap = digits.getBestCmap()

    one = bounds(digit_glyphs, digit_cmap[ord("1")])
    scale = DIGIT_HEIGHT / (one[3] - one[1])

    for voice in range(5, 9):
        code = FIRST_NEW_CODE + voice - 5
        name = "uni%04X" % code
        if code in icon_cmap:
            sys.exit("%s already exists in %s" % (name, icon_path))

        template = icon_cmap[VOICE_1 if voice % 2 else VOICE_2]
        digit = digit_cmap[ord(str(voice))]
        digit_bounds = bounds(digit_glyphs, digit)

        pen = TTGlyphPen(None)
        for op, args in note_contour(icon_glyphs, template):
            getattr(pen, op)(*args)
        dx = DIGIT_LEFT - scale * digit_bounds[0]
        digit_glyphs[digit].draw(TransformPen(pen, (scale, 0, 0, scale, dx, DIGIT_BASELINE)))

        glyph = pen.glyph()
        glyph.recalcBounds(icons["glyf"])
        icons["glyf"][name] = glyph  # also appends name to the glyph order
        icons["hmtx"][name] = (icons["hmtx"][template][0], glyph.xMin)
        for table in icons["cmap"].tables:
            if table.isUnicode():
                table.cmap[code] = name

    icons.save(icon_path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
