"""Section headings as SVG, because it is the only way to put your own
typeface on a heading. GitHub strips <style> blocks, style="" attributes,
class="", <font> and inline <svg>, so README text is stuck with GitHub's sans
or its monospace. An image is the only exit.

Stated plainly, since no guide admits it: image headings have no anchor links,
so GitHub's README outline goes empty. The alt text carries the word for
screen readers. That is the trade, and it is worth making once you have
decided the page should look like one thing rather than five.

    python3 scripts/make_headings.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svgkit as K  # noqa: E402

WORDS = ["whoami", "work", "signal", "stack", "contact"]

WIDTH = 860
HEIGHT = 34
SIZE = 13
TRACKING = 2.4     # letter-spacing, in px
GAP = 14           # space between the word and the start of the rule


def draw(word, theme):
    t = K.THEMES[theme]

    # Advance is exactly 0.600 em by construction, plus tracking per character.
    span = len(word) * (SIZE * 0.600 + TRACKING)

    body = (
        '<text x="0" y="22" font-family="Head, ui-monospace, monospace" '
        'font-size="%s" letter-spacing="%s" fill="%s">%s</text>'
        "%s"
    ) % (K.n(SIZE), K.n(TRACKING), t["ink"], K.esc(word),
         K.rule(span + GAP, 16, WIDTH - span - GAP, t["rule"]))

    style = K.heading_face()
    return K.document(WIDTH, HEIGHT, style, body, word)


def main():
    for word in WORDS:
        for theme in ("light", "dark"):
            name = "hd-%s.svg" % word if theme == "light" else "hd-%s-dark.svg" % word
            with open(os.path.join(K.ROOT, name), "w", encoding="utf-8") as fh:
                fh.write(draw(word, theme))
            print("  wrote %s" % name)


if __name__ == "__main__":
    main()
