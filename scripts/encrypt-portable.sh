#!/usr/bin/env bash
# Encrypt the excerpted portable reader for the password page at private/reader.html.
#
# The plaintext file stays gitignored. Only the StatiCrypt ciphertext is committed.
#
# Usage:
#   TWT_PASSWORD='your-passphrase' ./scripts/encrypt-portable.sh
#   TWT_PASSWORD='your-passphrase' ./scripts/encrypt-portable.sh path/to/plaintext.html
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOT/portable/talking-with-teens-shareable.html}"
OUT_DIR="$ROOT/private"
TEMPLATE="$ROOT/scripts/staticrypt-template.html"

if [[ -z "${TWT_PASSWORD:-}" ]]; then
  echo "Set TWT_PASSWORD to the passphrase colleagues will type." >&2
  echo "Example:" >&2
  echo "  TWT_PASSWORD='your-passphrase' $0" >&2
  exit 1
fi

if [[ ! -f "$SRC" ]]; then
  echo "Missing plaintext reader: $SRC" >&2
  echo >&2
  echo "Build it locally (needs excerpts/):" >&2
  echo "  python3 scripts/build-portable.py" >&2
  echo >&2
  echo "Or restore the last committed copy from git history:" >&2
  echo "  git show da199db:portable/talking-with-teens-shareable.html > portable/talking-with-teens-shareable.html" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

npx --yes staticrypt "$SRC" \
  --config false \
  --password "$TWT_PASSWORD" \
  --short \
  --remember 30 \
  --directory "$OUT_DIR" \
  --template "$TEMPLATE" \
  --template-title "Talking with Teens" \
  --template-instructions "Department copy. Ask Mr. B for the password. Don't post it or forward the unlocked page." \
  --template-button "Open the reader" \
  --template-placeholder "Password" \
  --template-remember "Remember this browser for 30 days" \
  --template-error "That password didn't work." \
  --template-color-primary "#7A1F1F" \
  --template-color-secondary "#F8F1E2"

# staticrypt keeps the source basename; publish at a stable URL.
generated="$(find "$OUT_DIR" -maxdepth 1 -name '*.html' ! -name 'reader.html' -print -quit)"
if [[ -n "${generated:-}" && "$generated" != "$OUT_DIR/reader.html" ]]; then
  mv "$generated" "$OUT_DIR/reader.html"
fi

# GitHub Pages runs Jekyll, which would eat JS `{{` in the decrypt engine.
# Wrap the whole file so it is published as-is.
python3 - "$OUT_DIR/reader.html" << 'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if "{% raw %}" not in text:
    path.write_text("---\nlayout: null\n---\n{% raw %}\n" + text + "\n{% endraw %}\n", encoding="utf-8")
PY

echo "Wrote $OUT_DIR/reader.html"
echo "Keep the plaintext out of git. private/reader.html is ciphertext only."
