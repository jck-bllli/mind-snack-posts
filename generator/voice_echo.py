"""Generate all voice lines with the matched 'Option A' voice (Kokoro am_echo, deepened + sped up)."""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__))
SPEED, PITCH, VOICE = 1.38, 0.875, "am_echo"
CHAIN = (f"aresample=48000,rubberband=pitch={PITCH}:formant=preserved,highpass=f=70,"
         "equalizer=f=180:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1.2:g=1.5,"
         "acompressor=threshold=-20dB:ratio=3:attack=5:release=80:makeup=3")
def main(lines_path, outdir):
    k = Kokoro(os.path.join(HERE, "tts_model/kokoro-v1.0.onnx"), os.path.join(HERE, "tts_model/voices-v1.0.bin"))
    quizzes = json.load(open(lines_path))
    with tempfile.TemporaryDirectory() as td:
        for q in quizzes:
            d = os.path.join(outdir, f"quiz_{q['quiz']}"); os.makedirs(d, exist_ok=True)
            for l in q["lines"]:
                y, sr = k.create(l["text"], voice=VOICE, speed=SPEED)
                src = os.path.join(td, "in.wav"); sf.write(src, y, sr)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", CHAIN, "-ac", "1",
                                os.path.join(d, l["id"] + ".wav")], check=True)
            print("voiced quiz", q["quiz"], flush=True)
if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
