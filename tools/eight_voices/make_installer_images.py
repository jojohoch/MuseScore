#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Create the Windows installer images of Octet, replacing the MuseScore Studio logo.

The background shows the voice 8 symbol (see add_voice_icons.py) and the name
Octet, set in FreeSans Bold (GNU FreeFont, GPLv3 with font exception), on
a dark panel at the left. The banner shows the app icon (see make_app_icon.py).

Usage: make_installer_images.py <repository root> FreeSansBold.ttf
Run make_app_icon.py first. Requires Pillow.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

VOICE_8 = 0xF4C6
NAME = "Octet"
PANEL = "#00081C"          # as on the loading screen
CONTENT = "#F8F8F8"        # the installer's content area, as before
SYMBOL_COLOR = "#19F3FF"
NAME_COLOR = "#F1F1EE"
OVERSAMPLE = 4


def draw_name(size, panel_width, symbol_font_path, name_font_path):
    width, height = size[0] * OVERSAMPLE, size[1] * OVERSAMPLE
    image = Image.new("RGBA", (width, height), CONTENT)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, panel_width * OVERSAMPLE - 1, height), fill=PANEL)

    symbol_font = ImageFont.truetype(symbol_font_path, 50 * OVERSAMPLE)
    name_font = ImageFont.truetype(name_font_path, 36 * OVERSAMPLE)
    symbol_box = draw.textbbox((0, 0), chr(VOICE_8), font=symbol_font)
    name_box = draw.textbbox((0, 0), NAME, font=name_font)
    gap = 14 * OVERSAMPLE

    total = (symbol_box[2] - symbol_box[0]) + gap + (name_box[2] - name_box[0])
    x = (panel_width * OVERSAMPLE - total) / 2
    middle = height / 2
    draw.text((x - symbol_box[0], middle - (symbol_box[1] + symbol_box[3]) / 2), chr(VOICE_8),
              font=symbol_font, fill=SYMBOL_COLOR)
    x += symbol_box[2] - symbol_box[0] + gap
    draw.text((x - name_box[0], middle - (name_box[1] + name_box[3]) / 2), NAME, font=name_font, fill=NAME_COLOR)

    return image.resize(size, Image.LANCZOS)


def draw_banner(size, icon_path):
    banner = Image.new("RGBA", size, "white")
    icon_size = 80
    icon = Image.open(icon_path).convert("RGBA").resize((icon_size, icon_size), Image.LANCZOS)
    margin = (size[1] - icon_size) // 2
    banner.paste(icon, (size[0] - icon_size - 24, margin), icon)
    return banner


def main(root, name_font_path):
    installer_dir = os.path.join(root, "buildscripts/packaging/Windows/Installer")
    symbol_font_path = os.path.join(root, "src/framework/ui/data/MusescoreIcon.ttf")
    icon_path = os.path.join(root, "share/icons/AppIcon/MS4_AppIcon_256x256.png")

    draw_name((986, 624), 324, symbol_font_path, name_font_path).save(
        os.path.join(installer_dir, "installer_background_wix.png"))
    draw_banner((986, 116), icon_path).save(os.path.join(installer_dir, "installer_banner_wix.png"))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
