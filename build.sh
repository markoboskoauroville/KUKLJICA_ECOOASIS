#!/usr/bin/env bash
# Builds dist/ from index.template.html + content/*.json
set -euo pipefail

python3 tools/inject.py

rm -rf dist && mkdir -p dist
cp .build/index.html dist/
cp -r img dist/
cp -r admin dist/
touch dist/.nojekyll

[ -f dist/index.html ] || { echo "FATAL: index.html missing from dist"; exit 1; }
[ -f dist/admin/index.html ] || { echo "FATAL: admin missing from dist"; exit 1; }
grep -q '__CONTENT__' dist/index.html && { echo "FATAL: content was not injected"; exit 1; }

echo "built dist/ — $(find dist -type f | wc -l) files, $(du -sh dist | cut -f1)"
