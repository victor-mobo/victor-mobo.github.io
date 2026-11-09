#!/usr/bin/env bash
# Usage: ./publish.sh "message"   (builds as a sanity check, commits, asks before pushing)
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python build.py
git add -A
if git diff --cached --quiet; then echo "Nothing to publish."; exit 0; fi
git commit -m "${1:-Update site}"
read -r -p "Push to GitHub (goes live in ~1 min)? [y/N] " ans
[[ "$ans" == [yY] ]] && git push || echo "Committed locally, not pushed."
