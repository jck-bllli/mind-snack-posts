"""Generate all voice lines with the matched 'Option A' voice (Kokoro am_echo, deepened + sped up)."""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
HERE = os.path.dirname(os.path.abspath(__file__))
SPEED, PITCH, VOICE = 1.38, 0.93, "am_echo"
# "Max clarity" chain: high-quality resample + pitch shift, cut mud, boost consonants, add air, tame "s".
CHAIN = ("aresample=48000:resampler=soxr:precision=28,"
         f"rubberband=pitch={PITCH}:formant=preserved:pitchq=quality:transients=crisp:detector=compound:window=standard,"
         "highpass=f=90:poles=2,equalizer=f=280:t=q:w=1.0:g=-6,equalizer=f=650:t=q:w=1.4:g=-2,"
         "equalizer=f=2500:t=q:w=1.0:g=6,equalizer=f=4500:t=q:w=1.2:g=3,highshelf=f=9500:g=4,"
         "deesser=i=0.25:m=0.5:f=0.6,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=60:makeup=2,"
         "alimiter=limit=0.95")
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
