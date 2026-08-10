"""Check the output before it goes near a public profile.

Four things worth catching automatically:

  1. Every SVG parses, and none of them reaches out to the network. An
     <img>-loaded SVG cannot fetch subresources, so an external reference is
     not a slow path, it is a silently missing font.
  2. Every embedded font actually decodes and opens as a real woff2.
  3. No animation loops. fill="freeze" everywhere, repeatCount nowhere.
  4. The README only uses markup GitHub's sanitiser keeps.

    python3 scripts/verify.py
"""

import base64
import glob
import io
import os
import re
import sys
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Measured by posting markdown to GitHub's own rendering endpoint
# (POST /markdown) and reading back what survived.
KEPT = {
    "sub", "sup", "kbd", "samp", "blockquote", "details", "summary", "hr",
    "picture", "source", "img", "a", "b", "i", "em", "strong", "code", "pre",
    "br", "p", "div", "table", "thead", "tbody", "tr", "td", "th", "ul", "ol",
    "li", "h1", "h2", "h3", "h4", "h5", "h6", "q", "cite", "del", "ins",
}
STRIPPED = {"style", "svg", "font", "small", "big", "script", "iframe", "form"}

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def check_svgs():
    files = sorted(glob.glob(os.path.join(ROOT, "*.svg")))
    if not files:
        fail("no SVGs found. run the generators first.")
        return 0

    total = 0
    for path in files:
        name = os.path.basename(path)
        raw = open(path, encoding="utf-8").read()
        total += len(raw.encode("utf-8"))

        try:
            xml.dom.minidom.parseString(raw)
        except Exception as exc:
            fail("%s: not well-formed XML: %s" % (name, exc))
            continue

        if "<script" in raw:
            fail("%s: contains a script. GitHub strips them; animation has to "
                 "be SMIL." % name)

        for url in re.findall(r'url\((["\']?)(https?:[^)]+)\1\)', raw):
            fail("%s: external reference %s. An <img>-loaded SVG cannot fetch "
                 "subresources." % (name, url[1]))

        if 'xlink:href="http' in raw or re.search(r'<image[^>]+href="http', raw):
            fail("%s: external image reference." % name)

        # fonts
        faces = re.findall(r"base64,([A-Za-z0-9+/=]+)\)", raw)
        if not faces:
            fail("%s: no embedded font. It will render in whatever monospace "
                 "the visitor happens to have, at whatever advance width." % name)
        for blob in faces:
            data = base64.b64decode(blob)
            if data[:4] != b"wOF2":
                fail("%s: embedded font is not woff2." % name)
                continue
            try:
                from fontTools.ttLib import TTFont
                TTFont(io.BytesIO(data))
            except ImportError:
                notes.append("fontTools not installed, skipped deep font check")
                break
            except Exception as exc:
                fail("%s: embedded font will not open: %s" % (name, exc))

        # animation
        if "repeatCount" in raw or "repeatDur" in raw:
            fail("%s: a looping animation. The portrait should print once and "
                 "stop." % name)
        for tag in re.findall(r"<(?:animate|set)\b[^>]*>", raw):
            if 'fill="freeze"' not in tag:
                fail("%s: an animation without fill=\"freeze\"; it will snap "
                     "back when it finishes." % name)
                break

    return total


def check_readme():
    path = os.path.join(ROOT, "README.md")
    if not os.path.exists(path):
        fail("README.md missing")
        return 0

    raw = open(path, encoding="utf-8").read()

    for attr in ('style="', "style='", 'class="', "class='"):
        if attr in raw:
            fail("README uses %s, which the sanitiser strips." % attr.rstrip("=\"'"))

    for tag in sorted(set(re.findall(r"</?([a-zA-Z][a-zA-Z0-9]*)", raw))):
        low = tag.lower()
        if low in STRIPPED:
            fail("README uses <%s>, which the sanitiser strips." % low)
        elif low not in KEPT:
            notes.append("README uses <%s>, which is not on the verified "
                         "keep-list. Check it with POST /markdown." % low)

    for src in re.findall(r'(?:src|srcset)="([^"]+)"', raw):
        if src.startswith("http"):
            notes.append("README pulls %s from another server. That is the "
                         "failure mode this whole design avoids." % src)
            continue
        local = os.path.join(ROOT, src.lstrip("./"))
        if not os.path.exists(local):
            fail("README references %s, which does not exist yet." % src)

    return len(raw.encode("utf-8"))


def main():
    svg_bytes = check_svgs()
    check_readme()

    print("page weight: %.1f KB of SVG" % (svg_bytes / 1024.0))
    if svg_bytes > 400 * 1024:
        notes.append("that is heavy. subset the fonts tighter, or drop a graphic.")

    for note in dict.fromkeys(notes):
        print("  note: %s" % note)

    if failures:
        print("\n%d problem(s):" % len(failures))
        for problem in failures:
            print("  - %s" % problem)
        sys.exit(1)

    print("\nall checks passed")


if __name__ == "__main__":
    main()
