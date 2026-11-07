"""Magic match: is the kid's photo the same thing the grown-up photographed?

The browser turns every photo into a small fingerprint (theme/assets/ph-cam.js, PH.signature) and sends it with the
picture; the score is worked out here, so the rules live in one place and a page can't decide its own result.

Fingerprint (version 1), all from the middle 80% of the picture:
  c: 20 colour bins (8 hues x 2 saturation levels + 4 greys), weighted toward the centre, summing to 1
  e: 128 edge numbers (4x4 cells x 8 edge directions on a 32x32 grey copy), length 1
  l: 64 brightness numbers (8x8 grid, zero mean, unit spread): the rough layout
Score = 0.5 colour overlap + 0.3 edge similarity + 0.2 layout similarity, 0..1.
Calibrated on photos with crops, tilts, zooms and light changes (tools/testing/vision_test.mjs): the same thing scores
about 0.75-0.95, different things about 0.35-0.65.
"""
import math

THRESHOLD = {"easy": 0.6, "normal": 0.68, "tricky": 0.76}
REVIEW_BAND = 0.1   # this far below the bar, the kid can ask a grown-up (or it goes to the grown-up's queue)
SIZES = {"c": 20, "e": 128, "l": 64}


def valid(sig):
    """The fingerprint cleaned up (floats, right lengths), or None."""
    if not isinstance(sig, dict):
        return None
    out = {"v": 1}
    for k, n in SIZES.items():
        vals = sig.get(k)
        if not isinstance(vals, (list, tuple)) or len(vals) != n:
            return None
        clean = []
        for v in vals:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
                return None
            clean.append(round(float(v), 5))
        out[k] = clean
    return out


def _cos(a, b):
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, sum(x * y for x, y in zip(a, b)) / (na * nb)))


def _pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    da = [x - ma for x in a]
    db = [y - mb for y in b]
    sa = math.sqrt(sum(x * x for x in da))
    sb = math.sqrt(sum(y * y for y in db))
    if sa == 0 or sb == 0:
        return 0.0
    return sum(x * y for x, y in zip(da, db)) / (sa * sb)


def score(a, b):
    """0..1: how alike two fingerprints are."""
    a, b = valid(a), valid(b)
    if a is None or b is None:
        return 0.0
    colour = sum(min(x, y) for x, y in zip(a["c"], b["c"])) / max(1e-9, min(sum(a["c"]), sum(b["c"])))
    edges = _cos(a["e"], b["e"])
    layout = (_pearson(a["l"], b["l"]) + 1) / 2
    return round(max(0.0, min(1.0, 0.5 * min(1.0, colour) + 0.3 * edges + 0.2 * layout)), 3)


def verdict(value, strictness):
    """"found", "close" (a grown-up may say yes) or "miss"."""
    bar = THRESHOLD.get(strictness or "normal", THRESHOLD["normal"])
    if value >= bar:
        return "found"
    if value >= bar - REVIEW_BAND:
        return "close"
    return "miss"
