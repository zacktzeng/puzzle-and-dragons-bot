#!/bin/bash

START_SCRCPY=false
ROUNDS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scrcpy)
      START_SCRCPY=true
      shift
      ;;
    --round)
      ROUNDS="$2"
      shift 2
      ;;
    *)
      echo "⚠️ Unknown option: $1"
      shift
      ;;
  esac
done

if $START_SCRCPY; then
  echo "📺 Starting scrcpy screen mirror..."
  scrcpy --max-fps 60 --video-bit-rate 16M --window-title "PAD Bot Stream" &
  sleep 2
fi

echo "🐉 Launching Puzzle and Dragons Bot..."

if [ -d "venv" ]; then
  echo "📦 Activating Python venv..."
  source venv/bin/activate
fi

if [ -z "$ROUNDS" ]; then
  python3.11 bot.py
else
  python3.11 bot.py "$ROUNDS"
fi
