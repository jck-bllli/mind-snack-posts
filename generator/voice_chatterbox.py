"""Generate all voice lines with Chatterbox. Each quiz gets its voice from its number (chatterbox_voice.voice_for)."""
import json
import os
import sys

import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from chatterbox_voice import SR, say, voice_for


def main(lines_path, outdir):
    for q in json.load(open(lines_path)):
        voice = voice_for(q["quiz"])
        d = os.path.join(outdir, f"quiz_{q['quiz']}")
        os.makedirs(d, exist_ok=True)
        for line in q["lines"]:
            sf.write(os.path.join(d, line["id"] + ".wav"), say(line["text"], voice), SR)
        print("voiced quiz", q["quiz"], "with", voice, flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
