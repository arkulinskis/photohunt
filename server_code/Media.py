"""Photos and voice clips: checking uploads, and serving them by random key.

Photos (treasure pictures the grown-up took, finds the kids snapped) and voice clips (clues, the welcome message)
are stored as Media on their rows, each with its own random key. Only the key reaches the browser, and only to
people allowed to see it (the hunt's owner, the players of that hunt). The endpoints answer /_/api/photo/<key> and
/_/api/voice/<key>. A new photo or a new recording always gets a new key, so the key doubles as the ETag;
"no-cache" makes the browser check again each time, so a deleted photo stops at once.
Voice clips are served with byte ranges (Safari and iPhones won't play audio without them).
"""
import re
import secrets

import anvil
import anvil.server
from anvil.tables import app_tables

from . import common as C

MAX_PHOTO = 3 * 1024 * 1024    # the browser shrinks photos to ~1024 px JPEG (~150 KB) before sending
MAX_AUDIO = 3 * 1024 * 1024    # a clue is a few seconds; 3 MB is minutes
MAX_SECONDS = 90
KEY_RE = re.compile(r"^[A-Za-z0-9_-]{20,40}$")
PHOTO_TYPES = ("image/jpeg", "image/png", "image/webp")


def new_key():
    return secrets.token_urlsafe(18)


def photo(media):
    """(BlobMedia, None) for an acceptable photo, or (None, message)."""
    if not isinstance(media, anvil.Media):
        return None, "The picture didn't arrive. Please try again."
    ctype = (media.content_type or "").split(";")[0].strip().lower()
    if ctype not in PHOTO_TYPES:
        return None, "That file isn't a photo."
    size = media.length or 0
    if size < 100:
        return None, "The picture was empty. Please try again."
    if size > MAX_PHOTO:
        return None, "That picture is too big. Please try a smaller one."
    return anvil.BlobMedia(ctype, media.get_bytes(), name="photo.jpg"), None


def audio(media, seconds):
    """(BlobMedia, seconds, None) for an acceptable recording, or (None, 0, message)."""
    if not isinstance(media, anvil.Media):
        return None, 0, "The recording didn't arrive. Please try again."
    ctype = (media.content_type or "").split(";")[0].strip().lower()
    if not ctype.startswith("audio/") and ctype != "video/webm":  # some browsers label sound-only WebM as video
        return None, 0, "That isn't a sound recording."
    if ctype == "video/webm":
        ctype = "audio/webm"
    size = media.length or 0
    if size < 200:
        return None, 0, "The recording was empty. Check the microphone and try again."
    if size > MAX_AUDIO:
        return None, 0, "That recording is too long. Keep clues under a minute."
    try:
        secs = float(seconds)
    except (TypeError, ValueError):
        secs = 0.0
    secs = max(0.0, min(float(MAX_SECONDS), secs))
    return anvil.BlobMedia(ctype, media.get_bytes(), name="voice"), round(secs, 1), None


def _range(raw, header):
    """(status, body bytes, extra headers) honouring a single "Range: bytes=a-b" request."""
    m = re.match(r"^bytes=(\d*)-(\d*)$", (header or "").strip())
    n = len(raw)
    if not m or (not m.group(1) and not m.group(2)):
        return 200, raw, {}
    if m.group(1):
        a = int(m.group(1))
        b = min(int(m.group(2)), n - 1) if m.group(2) else n - 1
    else:
        a, b = max(0, n - int(m.group(2))), n - 1
    if a >= n or a > b:
        return 416, b"", {"Content-Range": "bytes */%d" % n}
    return 206, raw[a:b + 1], {"Content-Range": "bytes %d-%d/%d" % (a, b, n)}


def _serve(media, key, ranges=False):
    etag = '"%s"' % key
    ctype = media.content_type or "application/octet-stream"
    headers = {"Content-Type": ctype, "Cache-Control": "private, no-cache", "ETag": etag}
    if ranges:
        headers["Accept-Ranges"] = "bytes"
    req = getattr(anvil.server, "request", None)
    req_headers = (getattr(req, "headers", None) or {}) if req is not None else {}
    if req_headers.get("if-none-match") == etag:
        return anvil.server.HttpResponse(304, "", headers=headers)
    raw = media.get_bytes()
    status, body, extra = (200, raw, {})
    if ranges and req_headers.get("range"):
        status, body, extra = _range(raw, req_headers.get("range"))
    headers.update(extra)
    return anvil.server.HttpResponse(status, anvil.BlobMedia(ctype, body), headers=headers)


def _missing():
    return anvil.server.HttpResponse(404, "Not found", headers={"Content-Type": "text/plain"})


@anvil.server.http_endpoint("/photo/:key")
def photo_file(key, **kw):
    key = str(key or "")
    if not KEY_RE.match(key):
        return _missing()
    row = app_tables.treasures.get(photo_key=key) or app_tables.finds.get(photo_key=key)
    if row is None or row["photo"] is None:
        return _missing()
    return _serve(row["photo"], key)


@anvil.server.http_endpoint("/voice/:key")
def voice_file(key, **kw):
    key = str(key or "")
    if not KEY_RE.match(key):
        return _missing()
    row = app_tables.treasures.get(voice_key=key)
    media = row["voice"] if row is not None else None
    if media is None:
        hunt = app_tables.hunts.get(intro_key=key)
        media = hunt["intro_audio"] if hunt is not None else None
    if media is None:
        return _missing()
    return _serve(media, key, ranges=True)


def clear_photo(row):
    row.update(photo=None, photo_key=None)


def now():
    return C.now()
