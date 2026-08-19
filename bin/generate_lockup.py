# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate qBraid product lockups: the brand mark followed by ``qBraid | PRODUCT``.

One template drives every product so the five lockups stay identical in mark size,
baseline, cap height and spacing. Emits a light and a dark SVG per product, plus
PNGs at ``--width`` if cairosvg is available.

The wordmark is typeset rather than reused from the official lockup, so the product
name can be set in the same face at a lighter weight. Nunito Sans matches the logo
artwork: at cap height 14 the advance for "qBraid" is 58.3 units against the
official lockup's measured 57.75.

Inputs (neither is vendored here)::

    --brand-svg   qbraid-dark.svg from the brand pack, vessa.design/brand/qbraid
    --font        Nunito Sans variable TTF, github.com/google/fonts/ofl/nunitosans

Usage::

    python bin/generate_lockup.py --brand-svg qbraid-dark.svg --font NunitoSans.ttf \\
        --out docs/_static --products SDK CLI QIR ALGORITHMS CORE

"""

import argparse
import pathlib
import re

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# Geometry in viewBox units, measured from the official lockup by rendering it
# against a calibration rect and mapping pixels back. Canvas height is 29.
HEIGHT = 29
MARK_LEFT, MARK_RIGHT = 1.54, 31.43
BASELINE, CAP = 21.0, 14.0
GAP_MARK = 4.82  # mark -> wordmark, preserved from the official lockup
GAP_PIPE_L = 7.8  # wordmark -> divider; "d" ends on a stem, so it needs more air
GAP_PIPE_R = 5.2  # divider -> product; caps curve away from the rule
PIPE_W = 0.9
RIGHT_PAD = 1.54  # mirror the left inset

WORD_WEIGHT, PRODUCT_WEIGHT = 400, 300
THEMES = {"light": "#171717", "dark": "#FFFFFF"}


def _face(font_path, weight):
    """Return a static instance of the variable font at one weight."""
    static = instancer.instantiateVariableFont(
        TTFont(font_path), {"wght": weight, "wdth": 100, "opsz": 12}
    )
    return static, static.getGlyphSet(), static.getBestCmap(), CAP / static["OS/2"].sCapHeight


def _typeset(font_path, text, weight, ink_left):
    """Lay out text as outlines, positioned by ink edge rather than advance origin."""
    static, glyphs, cmap, scale = _face(font_path, weight)
    glyf = static["glyf"]
    names = [cmap[ord(c)] for c in text]
    lsb = glyf[names[0]].xMin if glyf[names[0]].numberOfContours else 0
    pen_x, ink_right, out = ink_left - lsb * scale, ink_left, []
    for name in names:
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        if pen.getCommands():
            out.append(
                f'<path d="{pen.getCommands()}" transform="translate({pen_x:.3f} '
                f'{BASELINE}) scale({scale:.6f} {-scale:.6f})" fill="INK"/>'
            )
            ink_right = pen_x + glyf[name].xMax * scale
        pen_x += glyphs[name].width * scale
    return out, ink_right


def build(brand_svg, font_path, product):
    """Return {theme: svg_text} for one product lockup."""
    src = pathlib.Path(brand_svg).read_text(encoding="utf-8")
    wordmark = list(re.finditer(r'<path[^>]*fill="white"[^>]*/>', src))[1]
    mark = (src[: wordmark.start()] + src[wordmark.end() :]).replace(
        'width="109" height="29" viewBox="0 0 109 29"', "VIEWBOX"
    )

    word, word_right = _typeset(font_path, "qBraid", WORD_WEIGHT, MARK_RIGHT + GAP_MARK)
    pipe_x = word_right + GAP_PIPE_L
    name, name_right = _typeset(
        font_path, product.upper(), PRODUCT_WEIGHT, pipe_x + PIPE_W + GAP_PIPE_R
    )
    width = round(name_right + RIGHT_PAD, 2)

    body = (
        f'<rect x="{pipe_x:.3f}" y="{BASELINE - CAP}" width="{PIPE_W}" '
        f'height="{CAP}" fill="INK"/>' + "".join(word) + "".join(name)
    )
    out = {}
    for theme, ink in THEMES.items():
        svg = mark.replace("VIEWBOX", f'viewBox="0 0 {width} {HEIGHT}"')
        out[theme] = svg.replace("</svg>", body + "</svg>").replace("INK", ink)
    return out


def main():
    """Write an SVG (and PNG where possible) per product and theme."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--brand-svg", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--out", default="docs/_static")
    ap.add_argument("--products", nargs="+", default=["SDK"])
    ap.add_argument("--width", type=int, default=1600)
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg  # pylint: disable=import-outside-toplevel
    except (ImportError, OSError):
        cairosvg = None

    for product in args.products:
        for theme, svg in build(args.brand_svg, args.font, product).items():
            stem = f"qbraid_{product.lower()}_{theme}"
            path = out_dir / f"{stem}.svg"
            path.write_text(svg, encoding="utf-8")
            print(f"wrote {path}")
            if cairosvg is not None:
                cairosvg.svg2png(
                    url=str(path),
                    write_to=str(out_dir / f"{stem}.png"),
                    output_width=args.width,
                )


if __name__ == "__main__":
    main()
