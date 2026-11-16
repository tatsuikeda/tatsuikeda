"""Regenerate banner-light.svg and banner-dark.svg in the site's type (techhealthventures.com, version 6).

Text is converted to outlines because GitHub serves README images without web fonts.
Type roles follow the site's DESIGN_LANGUAGE.md: Jost for the wordmark, name and tagline,
IBM Plex Mono for the small label. Fonts are read from the site repo (self-hosted, OFL).

Usage (from the repo root):
    source venv/bin/activate
    python tools/gen_banner.py [--site ~/proj/techhealthventures]
"""
import argparse
import io
import os
import re

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Layout of the 1200 x 320 banner (kept from the previous banner: same text, positions and decoration).
WORDMARK = dict(text="Tech Health Ventures", x=106, y=72, size=20, weight=560, track=0.0)
NAME = dict(text="Tatsu Ikeda", x=62, y=164, size=88, weight=480, track=-0.02)
TAG1 = dict(text="AI consulting and engineering in Boston.", x=64, y=212, size=25, weight=420, track=0.0)
TAG2 = dict(text="Free tools for networks, firewalls and Macs.", x=64, y=248, size=25, weight=420, track=0.0)

THEMES = {
    "light": {"bg": "#f9f5ee", "line": "#d6d0c7", "ink": "#28201a", "ink2": "#544b44"},
    "dark": {"bg": "#18140f", "line": "#3c3731", "ink": "#ede9e1", "ink2": "#c2bdb5"},
}


def instance(path, weight):
    font = TTFont(path)
    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, {"wght": weight})
    buf = io.BytesIO()
    font.flavor = None
    font.save(buf)
    return font, buf.getvalue()


def outline(font_path, spec, fill):
    font, data = instance(font_path, spec["weight"])
    upm = font["head"].unitsPerEm
    glyphs = font.getGlyphSet()
    face = hb.Face(data)
    hbfont = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(spec["text"])
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {"kern": True, "liga": True})
    scale = spec["size"] / upm
    track = spec["track"] * upm
    order = font.getGlyphOrder()
    x = 0.0
    pen = SVGPathPen(glyphs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        t = TransformPen(pen, (scale, 0, 0, -scale, spec["x"] + (x + pos.x_offset) * scale, spec["y"] - pos.y_offset * scale))
        glyphs[name].draw(t)
        x += pos.x_advance + track
    return '<path d="%s" fill="%s"/>' % (pen.getCommands(), fill), spec["x"] + x * scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=os.path.expanduser("~/proj/techhealthventures"))
    args = ap.parse_args()
    jost = os.path.join(args.site, "assets/fonts/jost-latin-wght-normal.woff2")
    for theme, c in THEMES.items():
        path = os.path.join(ROOT, f"banner-{theme}.svg")
        svg = open(path).read()
        texts = [m.group(0) for m in re.finditer(r'<path d="M[^"]{3000,}"[^>]*/>', svg)]
        assert len(texts) == 4, f"expected 4 outlined text paths in {path}, found {len(texts)}"
        new = [
            outline(jost, WORDMARK, c["ink2"])[0],
            outline(jost, NAME, c["ink"])[0],
            outline(jost, TAG1, c["ink2"])[0],
            outline(jost, TAG2, c["ink2"])[0],
        ]
        for old, rep in zip(texts, new):
            svg = svg.replace(old, rep, 1)
        open(path, "w").write(svg)
        print(f"wrote {path} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
