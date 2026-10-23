#!/usr/bin/env bash
# Pack rendered tiles into batch tarballs for CDN/deploy (not committed to git).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TILES="${1:-$ROOT/web/public/tiles}"
OUT="${2:-$ROOT/web/public}"
BATCH_SIZE="${BATCH_SIZE:-500}"

if [[ ! -d "$TILES" ]]; then
  echo "Tiles directory not found: $TILES" >&2
  exit 1
fi

mapfile -t SLUGS < <(find "$TILES" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
total=${#SLUGS[@]}
batch=0
for ((i = 0; i < total; i += BATCH_SIZE)); do
  batch=$((batch + 1))
  archive="$OUT/tiles-batch-$(printf '%04d' "$batch").tar.gz"
  tmp="$(mktemp -d)"
  for ((j = i; j < i + BATCH_SIZE && j < total; j++)); do
    ln -s "$TILES/${SLUGS[j]}" "$tmp/${SLUGS[j]}"
  done
  tar -czf "$archive" -C "$tmp" .
  rm -rf "$tmp"
  echo "Wrote $archive (${SLUGS[i]:-?} … batch $batch)"
done
