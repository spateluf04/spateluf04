"""Photo -> ASCII -> self-typing SVG.

Run locally, once, and commit the output. The nightly workflow does not touch
this: your face does not change every night, and regenerating it in CI would
mean shipping a 176 MB model to a runner for no reason.

    python3 scripts/make_portrait.py photo/me.jpg

The photo decides everything. ASCII draws with shadow, not detail, and there
are only 13 brightness levels to work with:

  - side light, a window at roughly 45 degrees and everything else off. Flat
    frontal light gives one uniform mid-tone and the face renders as a hole.
  - crop tight, chin to just above the hair. At 90 columns a face filling 30%
    of the frame gets about 30 characters across and the eyes will not resolve.
  - high resolution, 1200px or more. Thin features like glasses frames get
    averaged away when a small source is downscaled.
  - plain background, and do not wear black against a dark wall.
  - slight angle rather than dead-on, which gives the nose and jaw a shadow edge.
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgkit as K  # noqa: E402

ROOT = K.ROOT
RAMP = K.RAMP

# The grid. CHAR_W is exactly 0.600 * FONT_SIZE, which is the whole reason the
# font has to be embedded: at Consolas' 0.55 advance a Windows visitor would
# see the portrait about 7% narrower than you do.
COLS = 90
FONT_SIZE = 12.9
CHAR_W = FONT_SIZE * 0.600      # 7.74
LINE_H = FONT_SIZE * 1.25       # 16.125, which preserves aspect given ROW_RATIO
ROW_RATIO = 0.48                # monospace cells are about twice as tall as wide
PAD = 8

STAGGER = 0.09                  # seconds between row starts
SWEEP = 0.55                    # seconds for one row to type


def cutout(img):
    """Force everything outside the subject to white, which maps to the blank
    end of the ramp. Skip this and the background fills with '@' and drowns
    the portrait."""
    try:
        from rembg import remove
    except ImportError:
        print("  rembg not installed, skipping cut-out (background will be noisy)")
        return img.convert("RGB")

    cut = remove(img)                                  # RGBA, subject only
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    return Image.alpha_composite(white, cut.convert("RGBA")).convert("RGB")


def prepare(img, gamma):
    import cv2

    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    # Smooth skin without losing edges.
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # Local contrast per tile. Global autocontrast leaves a flatly-lit face as
    # a single tone.
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)

    # The fix. Without this curve the face comes out washed out and
    # featureless; this is what makes glasses, brows and lips survive.
    gray = (np.power(gray / 255.0, gamma) * 255.0).astype(np.uint8)
    return gray


def to_ascii(gray, cols):
    import cv2

    h, w = gray.shape
    rows = max(1, int(round(cols * (h / float(w)) * ROW_RATIO)))
    small = cv2.resize(gray, (cols, rows), interpolation=cv2.INTER_AREA)

    levels = len(RAMP) - 1
    idx = np.clip((small / 255.0) * levels, 0, levels)
    idx = (levels - np.round(idx)).astype(int)        # dark pixel -> dense glyph
    return ["".join(RAMP[i] for i in row) for row in idx]


def render(lines, cols, theme):
    colour = K.THEMES[theme]["ink"]
    width = cols * CHAR_W + PAD * 2
    height = len(lines) * LINE_H + PAD * 2

    clips, texts, cursors = [], [], []

    for i, raw in enumerate(lines):
        line = raw.rstrip()
        y = PAD + i * LINE_H
        baseline = y + FONT_SIZE
        start = i * STAGGER

        if not line:
            continue

        span = len(line) * CHAR_W

        # Each row lives in a clipPath whose rect wipes open from zero width.
        # fill="freeze" everywhere, so the portrait prints once and stops.
        # No looping: a face that retypes itself forever is a novelty, not a
        # design.
        clips.append(
            '<clipPath id="r%d"><rect x="%s" y="%s" width="0" height="%s">'
            '<animate attributeName="width" from="0" to="%s" dur="%ss" '
            'begin="%ss" fill="freeze"/></rect></clipPath>'
            % (i, K.n(PAD), K.n(y), K.n(LINE_H), K.n(span), SWEEP, K.n(start))
        )

        texts.append(
            '<text x="%s" y="%s" clip-path="url(#r%d)" xml:space="preserve">%s</text>'
            % (K.n(PAD), K.n(baseline), i, K.esc(line))
        )

        # A block riding the wipe edge, then gone.
        cursors.append(
            '<rect x="%s" y="%s" width="%s" height="%s" opacity="0">'
            '<set attributeName="opacity" to="1" begin="%ss" fill="freeze"/>'
            '<animate attributeName="x" from="%s" to="%s" dur="%ss" begin="%ss" fill="freeze"/>'
            '<set attributeName="opacity" to="0" begin="%ss" fill="freeze"/>'
            "</rect>"
            % (K.n(PAD), K.n(y + 2.5), K.n(CHAR_W), K.n(FONT_SIZE * 0.95),
               K.n(start),
               K.n(PAD), K.n(PAD + span - CHAR_W), SWEEP, K.n(start),
               K.n(start + SWEEP))
        )

    style = (
        K.ramp_face()
        + "text{font-family:'Ramp',ui-monospace,monospace;font-size:%spx;"
          "white-space:pre;}" % K.n(FONT_SIZE)
    )
    body = (
        "<defs>%s</defs>"
        '<g fill="%s">%s</g>'
        '<g fill="%s">%s</g>'
    ) % ("".join(clips), colour, "".join(texts), colour, "".join(cursors))

    return K.document(width, height, style, body, "ASCII portrait")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--cols", type=int, default=COLS)
    ap.add_argument("--gamma", type=float, default=1.7,
                    help="darkening curve exponent; raise it if the face looks washed out")
    ap.add_argument("--no-cutout", action="store_true")
    args = ap.parse_args()

    cols = args.cols

    img = Image.open(args.photo)
    img = img.convert("RGB") if args.no_cutout else cutout(img)
    gray = prepare(img, args.gamma)
    lines = to_ascii(gray, cols)

    # A rough density read. Well below 20% and the portrait is washed out;
    # well above 60% and it is a black blob. Either way, adjust --gamma.
    ink = sum(1 for row in lines for ch in row if ch != " ")
    density = ink / float(len(lines) * cols)

    print("  %d columns x %d rows" % (cols, len(lines)))
    print("  ink density %.0f%%" % (density * 100))
    if density < 0.20:
        print("  -> washed out. try --gamma 2.1")
    elif density > 0.62:
        print("  -> too dark. try --gamma 1.4")
    print("  types for %.1fs" % ((len(lines) - 1) * STAGGER + SWEEP))

    with open(os.path.join(ROOT, "portrait.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    for theme in ("light", "dark"):
        name = "portrait.svg" if theme == "light" else "portrait-dark.svg"
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as fh:
            fh.write(render(lines, cols, theme))
        print("  wrote %s" % name)


if __name__ == "__main__":
    main()
