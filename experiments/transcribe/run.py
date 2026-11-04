from faster_whisper import WhisperModel
m = WhisperModel("small", compute_type="int8")
seg, _ = m.transcribe("ref.mp3", vad_filter=True)
import os; os.makedirs("out", exist_ok=True)
with open("out/transcript.txt", "w", encoding="utf-8") as f:
    for s in seg: f.write(f"{s.start:6.1f} {s.text.strip()}\n")
