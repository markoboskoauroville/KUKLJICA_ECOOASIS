#!/usr/bin/env bash
# Builds dist/ from index.template.html + content/*.json
set -euo pipefail

python3 tools/inject.py

rm -rf dist && mkdir -p dist
cp .build/index.html dist/
mkdir -p dist/karta && cp .build/karta.html dist/karta/index.html
cp -r img dist/
cp -r admin dist/
touch dist/.nojekyll

[ -f dist/index.html ] || { echo "FATAL: index.html missing from dist"; exit 1; }
[ -f dist/admin/index.html ] || { echo "FATAL: admin missing from dist"; exit 1; }
[ -f dist/karta/index.html ] || { echo "FATAL: karta missing from dist"; exit 1; }
grep -q '__KARTA__' dist/karta/index.html && { echo "FATAL: karta content was not injected"; exit 1; }
grep -q 'const PARCELS = \[' dist/karta/index.html || { echo "FATAL: karta has no parcel data"; exit 1; }
grep -q '__CONTENT__' dist/index.html && { echo "FATAL: content was not injected"; exit 1; }


# Arhiva ne smije nikad završiti u dist/
if [ -e dist/arhiva ]; then echo "FATAL: arhiva je u dist/, to se ne objavljuje"; exit 1; fi

echo "built dist/ — $(find dist -type f | wc -l) files, $(du -sh dist | cut -f1)"
