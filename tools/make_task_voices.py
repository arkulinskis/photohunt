"""Record a friendly voice for every task in the library (server_code/TaskLibrary.py) into theme/assets/voices/<id>.mp3.

    "C:\\Program Files\\Python311\\python.exe" tools/make_task_voices.py [ids...] [--check]

Uses Kokoro (voice af_heart, a little slower than normal for small listeners) and saves 40 kbps mono MP3s (~15 KB each).
With no ids it records only the tasks that have no file yet; pass ids (m01 s07 ...) to re-record those, or --all.
--check transcribes every file with faster-whisper and lists any whose words don't match the task's text.
Run it after adding or rewording a task, then `python tools/assets.py`.
Needs Python 3.11 with kokoro, soundfile, faster_whisper, imageio_ffmpeg (the video kit's setup).
"""
import pathlib
import re
import subprocess
import sys
import tempfile
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "theme" / "assets" / "voices"
VOICE = "af_heart"
SPEED = 0.92


def tasks():
    anvil = types.ModuleType("anvil")
    server = types.ModuleType("anvil.server")
    server.callable = lambda f: f
    anvil.server = server
    sys.modules.setdefault("anvil", anvil)
    sys.modules.setdefault("anvil.server", server)
    ns: dict = {}
    exec(compile((ROOT / "server_code" / "TaskLibrary.py").read_text(encoding="utf-8"), "TaskLibrary.py", "exec"), ns)
    return ns["TASKS"]


SAY = {  # spoken differently from the written text, where the voice slurred it
    "p09": "Do a conga line! Dance around the room with everyone.",
}


def spoken(text, tid=""):
    """What the voice says: the task as written, with a few symbols spelled out."""
    if tid in SAY:
        return SAY[tid]
    return text.replace("&", "and").replace("(", ", ").replace(")", ",").replace(" ,", ",")


def words(s):
    s = s.lower().replace("&", " and ")
    nums = {"10": "ten", "3": "three", "5": "five", "15": "fifteen", "20": "twenty", "2": "two", "4": "four", "1": "one",
            "6": "six", "30": "thirty", "100": "hundred", "8": "eight", "7": "seven", "9": "nine", "12": "twelve"}
    out = []
    for w in re.findall(r"[a-z0-9']+", s):
        out.append(nums.get(w, w).replace("'", ""))
    return out


def record(todo):
    import numpy as np
    import soundfile as sf
    import imageio_ffmpeg
    from kokoro import KPipeline
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp())
    for t in todo:
        audio = np.concatenate([r.audio.numpy() for r in pipe(spoken(t["text"], t["id"]), voice=VOICE, speed=SPEED)])
        pad = np.zeros(int(24000 * 0.12), dtype=audio.dtype)
        wav = tmp / (t["id"] + ".wav")
        sf.write(str(wav), np.concatenate([pad, audio, pad]), 24000)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-ar", "24000", "-b:a", "40k",
                        str(OUT / (t["id"] + ".mp3"))], check=True)
        print("recorded", t["id"], "%.1fs" % (len(audio) / 24000))


def check(all_tasks):
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", device="cuda", compute_type="float16")
    bad = 0
    for t in all_tasks:
        f = OUT / (t["id"] + ".mp3")
        if not f.exists():
            print("MISSING", t["id"])
            bad += 1
            continue
        segs, _ = m.transcribe(str(f), beam_size=5)
        heard = " ".join(s.text for s in segs).strip()
        want, got = words(t["text"]), words(heard)
        missing = [w for w in want if w not in got]
        if len(missing) > max(1, len(want) // 8):
            bad += 1
            print("CHECK", t["id"], "| want:", t["text"], "| heard:", heard)
    print("voices checked: %d, to listen to: %d" % (len(all_tasks), bad))
    return bad


def main(argv):
    all_tasks = tasks()
    ids = [a for a in argv if not a.startswith("--")]
    if "--all" in argv:
        todo = all_tasks
    elif ids:
        todo = [t for t in all_tasks if t["id"] in ids]
    else:
        todo = [t for t in all_tasks if not (OUT / (t["id"] + ".mp3")).exists()]
    if todo:
        record(todo)
    known = {t["id"] for t in all_tasks}
    for f in OUT.glob("*.mp3"):
        if f.stem not in known:
            print("no task for", f.name, "(left in place)")
    if "--check" in argv:
        check(all_tasks)


if __name__ == "__main__":
    main(sys.argv[1:])
