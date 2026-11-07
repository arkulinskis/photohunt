"""PhotoHunt's client helpers: names and labels, photo/voice addresses, the browser engines (theme/assets/ph-art.js and
ph-cam.js, reached as window.PH), and the games this tablet remembers.

    ph.photo_url(key, art)      a photo's address (or the demo drawing when there's no photo)
    ph.voice_url(key)           a voice clip's address
    ph.games() / remember_game  hunts joined on this tablet: {code: {"token", "name", "title"}}
    ph.kid_corners()            Kids' corner links opened on this tablet
    ph.say_clue(key, text, cb)  play the grown-up's recording, or read the text with the device's voice
    ph.err_text(e)              the readable message of a failed engine call (a rejected Promise)
"""
import json

import anvil.js
import anvil.server
from anvil.js import window

KINDS = [
    ("photo", "Photo hunt", "You snap things around the house. Kids find them and snap the same thing.", "camera"),
    ("voice", "Voice hunt", "You record a spoken clue for each thing. Kids listen, find it and snap it.", "volume"),
    ("task", "Task party", "Kids do fun tasks you record, or pick from 100 party tasks.", "star"),
    ("mix", "Party mix", "Things to find and tasks to do, all in one hunt.", "gift"),
]
KIND_LABEL = {k: label for k, label, _, _ in KINDS}
FLAVOURS = [("strawberry", "Strawberry"), ("chocolate", "Chocolate"), ("vanilla", "Vanilla"), ("mint", "Mint choc"),
            ("blueberry", "Blueberry"), ("lemon", "Lemon")]
TOPPERS = [("star", "Star"), ("heart", "Heart"), ("crown", "Crown"), ("rocket", "Rocket"), ("flower", "Flower"),
           ("balloon", "Balloon"), ("dino", "Dino"), ("moon", "Moon"), ("bolt", "Lightning"), ("fish", "Fish"),
           ("cat", "Cat"), ("rainbow", "Rainbow")]
COLOURS = [("pink", "Pink"), ("mint", "Mint"), ("blue", "Blue"), ("lemon", "Lemon"), ("orange", "Orange"), ("berry", "Berry")]
STICKERS = {
    "party": ("Party hat", "Played a PhotoHunt"),
    "cake": ("Whole cake", "Lit every candle"),
    "first": ("First find", "Found the very first treasure"),
    "speedy": ("Speedy", "Finished in half the time"),
    "winner": ("Winner", "Lit the most candles"),
    "sharp": ("Sharp eyes", "Super close photo matches"),
    "voice": ("Good ears", "Solved spoken clues"),
    "task": ("Task star", "Did three or more tasks"),
    "team": ("Team cake", "Filled the cake together"),
}
TIME_LIMITS = [(0, "No time limit"), (5, "5 minutes"), (10, "10 minutes"), (15, "15 minutes"), (20, "20 minutes"),
               (30, "30 minutes"), (45, "45 minutes"), (60, "1 hour")]
_base: dict = {}


def api_base():
    """<app>/_/api (get_api_origin() already ends in /_/api on hosted Anvil and the App Server)."""
    if "v" not in _base:
        o = str(anvil.server.get_api_origin() or "").rstrip("/")
        _base["v"] = o if o.endswith("/_/api") else o + "/_/api"
    return _base["v"]


def photo_url(key, art=None):
    if key:
        return api_base() + "/photo/" + str(key)
    return art or None


def voice_url(key):
    return (api_base() + "/voice/" + str(key)) if key else None


def app_url(hash_part):
    """An absolute link to a page of this app (QR codes, copy link)."""
    origin = str(window.location.origin) + str(window.location.pathname)
    return origin.split("#")[0].rstrip("/") + "/" + hash_part


def join_url(code):
    return app_url("#join/" + str(code))


def kid_url(token):
    return app_url("#kid/" + str(token))


def code_from_text(text):
    """A hunt code from a scanned QR (a join link) or typed text, or ''."""
    s = str(text or "").strip()
    if "#join/" in s:
        s = s.split("#join/")[1].split("/")[0].split("?")[0]
    elif "#kid/" in s:
        return ""
    cleaned = "".join(ch for ch in s.upper() if ch.isalnum())
    return cleaned[:6] if len(cleaned) >= 6 else ""


def kid_token_from_text(text):
    s = str(text or "")
    return s.split("#kid/")[1].split("/")[0].split("?")[0] if "#kid/" in s else ""


def clock(seconds):
    """'4:07' from seconds (None -> '')."""
    if seconds is None:
        return ""
    s = max(0, int(seconds))
    return "%d:%02d" % (s // 60, s % 60)


def err_text(e):
    """The message of a failed JS call (a rejected Promise arrives as an exception)."""
    orig = getattr(e, "original_error", None)
    msg = getattr(orig, "message", None) if orig is not None else None
    text = str(msg if msg else e)
    for prefix in ("Error: ", "ExternalError: "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return text or "Something went wrong."


def jget(obj, name, default=None):
    """A field of a JS object, or default when it's missing (reading a missing field raises in Python)."""
    try:
        v = getattr(obj, name)
    except AttributeError:
        return default
    return default if v is None else v


# ---------------------------------------------------------------- this tablet's memory (localStorage, JSON)
def _load(key, default):
    try:
        raw = window.localStorage.getItem("photohunt." + key)
    except Exception:
        return default
    if not raw:
        return default
    try:
        v = json.loads(str(raw))
    except Exception:
        return default
    return v if isinstance(v, type(default)) else default


def _save(key, value):
    try:
        window.localStorage.setItem("photohunt." + key, json.dumps(value))
    except Exception:
        pass


def games():
    return _load("games", {})


def remember_game(code, token, name, title=""):
    g = games()
    g[str(code)] = {"token": token, "name": name, "title": title}
    _save("games", g)


def forget_game(code=None, token=None):
    g = games()
    for c in list(g):
        if c == code or (token and g[c].get("token") == token):
            del g[c]
    _save("games", g)


def kid_corners():
    return _load("kids", [])


def remember_kid(token, name, topper, colour):
    ks = [k for k in kid_corners() if k.get("token") != token]
    ks.insert(0, {"token": token, "name": name, "topper": topper, "colour": colour})
    _save("kids", ks[:8])


def forget_kid(token):
    _save("kids", [k for k in kid_corners() if k.get("token") != token])


# ---------------------------------------------------------------- engines
def PH():
    return window.PH


def to_media(blob):
    return anvil.js.to_media(blob)


def sig_of(result):
    """The fingerprint dict from an engine photo result ({blob, url, sig})."""
    raw = jget(result, "sig", "")
    try:
        return json.loads(str(raw)) if raw else None
    except Exception:
        return None


def sfx(name):
    window.PH.sfx(name)


def confetti():
    window.PH.confetti()


def stop_sound():
    window.PH.stopSound()


def say_clue(key=None, text=None, on_end=None):
    """Play the recorded clue, or read the text aloud. on_end(ok) is called when it stops."""
    cb = anvil.js.report_exceptions(on_end) if on_end else None
    if key:
        window.PH.playUrl(voice_url(key), cb)
    elif text:
        window.PH.say(text, cb)
    elif on_end:
        on_end(False)


def muted():
    return bool(window.PH.muted())


def set_muted(value):
    window.PH.setMuted(bool(value))
