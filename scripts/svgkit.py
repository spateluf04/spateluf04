"""Shared SVG helpers. Standard library only, so generate_stats.py can run in CI
with no dependencies to break.

Everything here exists to enforce two rules from the design:

  1. One fill colour per theme. No per-element colouring, no rainbows.
  2. Every SVG carries its own font, base64-inlined. SVGs loaded through an
     <img> tag cannot fetch subresources, so an external font URL silently
     does nothing. A data URI works.
"""

import base64
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts", "subsets")

# GitHub's own light/dark surface colours, so the graphics sit on the page
# rather than on top of it. Selected via <picture> in the README, not via a
# media query, because GitHub's theme setting is independent of the OS setting
# and an <img>-loaded SVG only ever sees the OS one.
THEMES = {
    "light": {
        "ink":   "#1f2328",   # the one fill colour
        "dim":   "#6e7781",   # labels, axis text
        "rule":  "#d0d7de",   # hairlines
        "faint": "#eaeef2",   # empty-state fills
    },
    "dark": {
        "ink":   "#e6edf3",
        "dim":   "#7d8590",
        "rule":  "#30363d",
        "faint": "#21262d",
    },
}

RAMP = " .`:-=+*cs#%@"  # 13 levels; the leading space clears background to nothing


# --------------------------------------------------------------------------
# fonts
# --------------------------------------------------------------------------

def font_face(family, weight, filename):
    """Return an @font-face rule with the woff2 inlined as base64."""
    path = os.path.join(FONT_DIR, filename)
    with open(path, "rb") as fh:
        blob = base64.b64encode(fh.read()).decode("ascii")
    return (
        "@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
        "src:url(data:font/woff2;base64,%s) format('woff2');}"
        % (family, weight, blob)
    )


def ui_faces(bold=True):
    """Basic-latin subset for the data graphics. Only pull in the bold weight
    where a graphic actually uses it; every SVG carries its own copy, so an
    unused 4.6 KB face is 4.6 KB paid twice, once per theme."""
    css = font_face("UI", 400, "ui-regular.woff2")
    if bold:
        css += font_face("UI", 700, "ui-bold.woff2")
    return css


def ramp_face():
    """13-character subset, for the portrait only. About 1.3 KB."""
    return font_face("Ramp", 400, "ramp.woff2")


def heading_face():
    return font_face("Head", 400, "headings.woff2")


# --------------------------------------------------------------------------
# xml
# --------------------------------------------------------------------------

def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def n(value):
    """Round coordinates hard. Sub-pixel drift is the difference between a
    quiet repo and a commit every single night."""
    return ("%.2f" % float(value)).rstrip("0").rstrip(".") or "0"


def document(width, height, style, body, label):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 %s %s" width="%s" height="%s" '
        'role="img" aria-label="%s">'
        "<style>%s</style>%s</svg>"
    ) % (n(width), n(height), n(width), n(height), esc(label), style, body)


def text(x, y, content, fill="var-ink", size=12, weight=400,
         anchor="start", family="UI", extra=""):
    return (
        '<text x="%s" y="%s" font-family="%s, monospace" font-size="%s" '
        'font-weight="%s" text-anchor="%s" fill="%s"%s>%s</text>'
    ) % (n(x), n(y), family, n(size), weight, anchor, fill,
         (" " + extra) if extra else "", esc(content))


def rect(x, y, w, h, fill, extra=""):
    return '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>' % (
        n(x), n(y), n(w), n(h), fill, (" " + extra) if extra else ""
    )


def rule(x, y, w, stroke):
    """A hairline. 1px, not 2, and aligned to a half pixel so it stays crisp."""
    return '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>' % (
        n(x), n(y + 0.5), n(x + w), n(y + 0.5), stroke
    )
