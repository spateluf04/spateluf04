#!/usr/bin/env bash
# Download JetBrains Mono (SIL OFL 1.1) into assets/fonts/.
#
# Optional. If you skip this, build_fonts.py falls back to a system monospace
# with the same 0.600 em advance (Noto Sans Mono, Liberation Mono or DejaVu
# Sans Mono), all of which are redistributable.
set -euo pipefail

VERSION="2.304"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/assets/fonts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$DEST"

URL="https://github.com/JetBrains/JetBrainsMono/releases/download/v${VERSION}/JetBrainsMono-${VERSION}.zip"
echo "downloading $URL"
curl -fsSL -o "$TMP/jbm.zip" "$URL"
unzip -q -o "$TMP/jbm.zip" -d "$TMP/jbm"

find "$TMP/jbm" -name 'JetBrainsMono-Regular.ttf' -exec cp {} "$DEST/" \;
find "$TMP/jbm" -name 'JetBrainsMono-Bold.ttf'    -exec cp {} "$DEST/" \;
find "$TMP/jbm" -name 'OFL.txt'                   -exec cp {} "$DEST/FONT-LICENSE.txt" \;

echo "done. now run: python3 scripts/build_fonts.py"
