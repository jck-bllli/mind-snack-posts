#!/bin/bash
# One-time setup on a fresh Linux machine: Python packages + the Kokoro voice model (~350 MB, from GitHub).
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q kokoro-onnx soundfile scipy pillow numpy 2>/dev/null \
  || pip install -q kokoro-onnx soundfile scipy pillow numpy
mkdir -p tts_model
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s "tts_model/$f" ] || curl -sSL --max-time 600 -o "tts_model/$f" \
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
done
command -v ffmpeg >/dev/null || { echo "ffmpeg is required (with the rubberband filter)"; exit 1; }
ffmpeg -hide_banner -filters 2>/dev/null | grep -q rubberband || echo "warning: ffmpeg lacks rubberband; voice pitch shift will fail"
echo "generator setup ok"
