#!/bin/bash
# Reliable fetcher for Stitch HTML/screenshot files.
# Handles Google Cloud Storage redirects and TLS/SNI quirks
# that can break internal AI fetch tools.
#
# Usage: bash fetch-stitch.sh <url> <output_path>

URL=$1
OUTPUT=$2
if [ -z "$URL" ] || [ -z "$OUTPUT" ]; then
  echo "Usage: $0 <url> <output_path>"
  exit 1
fi

# Create parent directory
mkdir -p "$(dirname "$OUTPUT")"

echo "Fetching from Stitch..."
curl -L -f -sS --connect-timeout 10 --compressed "$URL" -o "$OUTPUT"
if [ $? -eq 0 ]; then
  SIZE=$(wc -c < "$OUTPUT" | tr -d ' ')
  echo "OK: $OUTPUT ($SIZE bytes)"
  exit 0
else
  echo "ERROR: Failed to fetch. Check URL or API key expiration."
  exit 1
fi
