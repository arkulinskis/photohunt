"""Calibrate Magic match: the browser's fingerprint (theme/assets/ph-cam.js PH.sig64, run in Node) + the server's
score (server_code/Vision.py), on real photos and changed copies of them.

    python tools/testing/vision_test.py [photo folder ...]      (no -I: needs Pillow)

For every photo it makes the changes a second snapshot of the same thing has (moved frame, tilt, zoom, light, warm/cool
colour, blur), scores them against the original, and scores different photos against each other. It prints both
ranges and how many of each the strict/normal/easy bars accept, and fails if "normal" lets different photos through
too often or rejects too many retakes.
"""
import json
import pathlib
import random
import subprocess
import sys

from PIL import Image, ImageEnhance, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server_code"))
import Vision  # noqa: E402

DEFAULT = [pathlib.Path(r"C:/Users/arkvi/Documents/CLAUDE/csuitecoach-forms/theme/assets"),
           pathlib.Path(r"C:/Users/arkvi/Documents/CLAUDE/campfire/theme/assets")]


def crop64(img):
    """Like the browser: the middle 80%, scaled to 64x64."""
    w, h = img.size
    return img.crop((int(w * .1), int(h * .1), int(w * .9), int(h * .9))).resize((64, 64), Image.LANCZOS).convert("RGBA")


def variants(img, rnd):
    w, h = img.size
    out = {}
    dx, dy = int(w * .08), int(h * .08)
    out["moved"] = img.crop((dx, dy, w, h))
    out["tilted"] = img.rotate(rnd.choice([-9, 9]), resample=Image.BICUBIC, expand=False, fillcolor=(128, 128, 128))
    out["zoomed"] = img.crop((int(w * .1), int(h * .1), int(w * .9), int(h * .9)))
    out["darker"] = ImageEnhance.Brightness(img).enhance(.72)
    out["brighter"] = ImageEnhance.Brightness(img).enhance(1.25)
    r, g, b = img.split()
    out["warm"] = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.1))), g, b.point(lambda v: int(v * .88))))
    out["blurry"] = img.filter(ImageFilter.GaussianBlur(2.5))
    out["moved+dark"] = ImageEnhance.Brightness(img.crop((0, dy, w - dx, h))).enhance(.8)
    return out


def main():
    folders = [pathlib.Path(a) for a in sys.argv[1:]] or DEFAULT
    files = sorted(f for d in folders for f in d.glob("*.jpg") if not f.name.startswith("yt-"))[:24]
    rnd = random.Random(3)
    pics = {}
    for f in files:
        img = Image.open(f).convert("RGB")
        img.thumbnail((900, 900))
        pics[f.stem] = {"original": crop64(img)}
        for k, v in variants(img, rnd).items():
            pics[f.stem][k] = crop64(v)
    data = {"%s|%s" % (n, k): list(im.tobytes()) for n, vs in pics.items() for k, im in vs.items()}
    tmp = ROOT / "tools" / "testing" / ".vision-in.json"
    tmp.write_text(json.dumps(data), encoding="utf-8")
    js = ("global.window = global; require(%s);\n"
          "const d = JSON.parse(require('fs').readFileSync(%s, 'utf8')); const out = {};\n"
          "for (const k in d) out[k] = window.PH.sig64(d[k]);\n"
          "process.stdout.write(JSON.stringify(out));" % (json.dumps(str(ROOT / "theme" / "assets" / "ph-cam.js")), json.dumps(str(tmp))))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", check=True)
    tmp.unlink()
    sigs = json.loads(r.stdout)
    names = list(pics)
    same, diff = [], []
    for n in names:
        for k in pics[n]:
            if k != "original":
                same.append((Vision.score(sigs[n + "|original"], sigs[n + "|" + k]), n, k))
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            diff.append((Vision.score(sigs[a + "|original"], sigs[b + "|original"]), a, b))
            diff.append((Vision.score(sigs[a + "|moved"], sigs[b + "|darker"]), a, b))
    same.sort()
    diff.sort()
    print("%d photos, %d retakes, %d different pairs" % (len(names), len(same), len(diff)))
    print("retakes   min %.3f  10%% %.3f  median %.3f" % (same[0][0], same[len(same) // 10][0], same[len(same) // 2][0]))
    print("different median %.3f  90%% %.3f  max %.3f" % (diff[len(diff) // 2][0], diff[int(len(diff) * .9)][0], diff[-1][0]))
    print("lowest retakes:", ", ".join("%s/%s %.2f" % (n, k, s) for s, n, k in same[:5]))
    print("closest different:", ", ".join("%s~%s %.2f" % (a, b, s) for s, a, b in diff[-5:]))
    for level, bar in Vision.THRESHOLD.items():
        acc_same = len([1 for s, _, _ in same if s >= bar]) / len(same)
        acc_close = len([1 for s, _, _ in same if s >= bar - Vision.REVIEW_BAND]) / len(same)
        acc_diff = len([1 for s, _, _ in diff if s >= bar]) / len(diff)
        print("%-7s bar %.2f: retakes accepted %3.0f%% (+%3.0f%% 'ask a grown-up'), different accepted %3.0f%%"
              % (level, bar, acc_same * 100, (acc_close - acc_same) * 100, acc_diff * 100))
    bar = Vision.THRESHOLD["normal"]
    ok_same = len([1 for s, _, _ in same if s >= bar - Vision.REVIEW_BAND]) / len(same)
    ok_diff = len([1 for s, _, _ in diff if s >= bar]) / len(diff)
    assert ok_same >= 0.9, "normal rejects too many retakes outright"
    assert ok_diff <= 0.08, "normal accepts too many different photos"
    print("VISION OK")


if __name__ == "__main__":
    main()
