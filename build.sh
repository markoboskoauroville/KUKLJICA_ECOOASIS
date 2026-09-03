#!/usr/bin/env bash
set -euo pipefail
rm -rf dist && mkdir -p dist
cp index.html dist/
cp -r img dist/
touch dist/.nojekyll
[ -f dist/index.html ] || { echo "FATAL: index.html missing from dist"; exit 1; }
echo "built dist/ — $(find dist -type f | wc -l) files, $(du -sh dist | cut -f1)"
