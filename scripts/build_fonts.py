"""Subset the typeface into the four roles the page needs, then commit the
results. Run this once (and again only if you change fonts or heading words).

Why subset at all: every SVG has to carry its own copy of the font, because an
<img>-loaded SVG cannot fetch a subresource. Inlining a full TTF into each file
is about 4.5 MB across the page. Subsetting per role is about 57 KB per theme.

Licence matters. The font file lands in a public repo, so it has to be OFL or
similar, and the licence file ships next to it. JetBrains Mono, IBM Plex Mono,
Fira Code, Source Code Pro and Noto Sans Mono all qualify. Commercial fonts do
not.

Advance width matters too. The portrait grid bakes in exactly 0.600 em. Fonts
that match: JetBrains Mono (600/1000), Noto Sans Mono (600/1000), Liberation
Mono (1229/2048), DejaVu Sans Mono (1233/2048, close enough). Fonts that do
not: Ubuntu Mono (0.560), Consolas (about 0.55). Pick from the first list.

Usage:
    python3 scripts/build_fonts.py
    python3 scripts/build_fonts.py --font assets/fonts/JetBrainsMono-Regular.ttf \
                                   --bold assets/fonts/JetBrainsMono-Bold.ttf
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
OUT_DIR = os.path.join(FONT_DIR, "subsets")

RAMP_CHARS = " .`:-=+*cs#%@"
BASIC_LATIN = "".join(chr(c) for c in range(0x20, 0x7F)) + "·"  # plus a middle dot for separators

# Heading words. Keep this in sync with make_headings.py, or the heading SVGs
# will render with missing glyphs.
HEADING_CHARS = sorted(set("whoami work signal stack ledger contact archive" + "0123456789/-_. "))

# Search order for a system fallback, all 0.600 em or within a rounding error,
# all redistributable.
FALLBACKS = [
    ("/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
     "/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
]


def advance_em(path):
    """Measure the advance width of 'M' in em units, so a wrong font is caught
    here rather than as a 7% squeeze on somebody else's machine."""
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    upem = font["head"].unitsPerEm
    glyph = font.getBestCmap()[ord("M")]
    return font["hmtx"][glyph][0] / float(upem)


def resolve(explicit_regular, explicit_bold):
    if explicit_regular:
        return explicit_regular, explicit_bold or explicit_regular

    jb_r = os.path.join(FONT_DIR, "JetBrainsMono-Regular.ttf")
    jb_b = os.path.join(FONT_DIR, "JetBrainsMono-Bold.ttf")
    if os.path.exists(jb_r):
        return jb_r, jb_b if os.path.exists(jb_b) else jb_r

    for regular, bold in FALLBACKS:
        if os.path.exists(regular):
            return regular, bold if os.path.exists(bold) else regular

    sys.exit(
        "No usable font found.\n"
        "Run scripts/fetch_fonts.sh to download JetBrains Mono, or pass --font."
    )


def subset(src, chars, out_name):
    out = os.path.join(OUT_DIR, out_name)
    cmd = [
        sys.executable, "-m", "fontTools.subset", src,
        "--text=" + chars,
        "--flavor=woff2",
        "--layout-features=",
        "--no-hinting",
        "--desubroutinize",
        "--output-file=" + out,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    return out, os.path.getsize(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--font", help="regular weight TTF/OTF")
    ap.add_argument("--bold", help="bold weight TTF/OTF")
    args = ap.parse_args()

    regular, bold = resolve(args.font, args.bold)
    os.makedirs(OUT_DIR, exist_ok=True)

    adv = advance_em(regular)
    print("font:    %s" % regular)
    print("advance: %.4f em" % adv)
    if abs(adv - 0.600) > 0.005:
        print("\nWARNING: the portrait grid assumes exactly 0.600 em.")
        print("At %.3f the portrait will render %.0f%% off.\n"
              % (adv, abs(adv - 0.6) / 0.6 * 100))

    jobs = [
        (regular, RAMP_CHARS,                  "ramp.woff2",       "portrait ramp, 13 chars"),
        (regular, "".join(HEADING_CHARS),      "headings.woff2",   "heading letters only"),
        (regular, BASIC_LATIN,                 "ui-regular.woff2", "basic latin, regular"),
        (bold,    BASIC_LATIN,                 "ui-bold.woff2",    "basic latin, bold"),
    ]

    total = 0
    print()
    for src, chars, name, why in jobs:
        _, size = subset(src, chars, name)
        total += size
        print("  %-18s %6.1f KB   %s" % (name, size / 1024.0, why))
    print("\n  total per theme    %6.1f KB" % (total / 1024.0))

    # Ship the licence next to the subsets. This is not optional.
    for candidate in ("OFL.txt", "LICENSE", "LICENSE.txt", "LICENSE_DEJAVU"):
        src = os.path.join(os.path.dirname(regular), candidate)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(FONT_DIR, "FONT-LICENSE.txt"))
            print("  licence copied from %s" % src)
            break
    else:
        print("\n  NOTE: no licence file found next to the font. Add one to")
        print("        assets/fonts/FONT-LICENSE.txt before making the repo public.")


if __name__ == "__main__":
    main()
