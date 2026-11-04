import wave, os
import numpy as np
from faster_whisper import WhisperModel
w = wave.open("ref.wav"); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
m = WhisperModel("small", compute_type="int8")
seg, _ = m.transcribe(a, vad_filter=False)
os.makedirs("out", exist_ok=True)
with open("out/transcript.txt", "w", encoding="utf-8") as f:
    for s in seg: f.write(f"{s.start:6.1f} {s.text.strip()}\n")
