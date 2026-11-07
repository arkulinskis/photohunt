"""The grown-up side: Party HQ, making a hunt, its treasures, the live board, the party album.

Only the hunt's owner can change it or see its kids' photos. Demo hunts (DemoData) can be opened read-only by any
signed-in person and copied into their own hunt ("Make one like this"); their album shows only the demo players.
"""
import datetime as dt

import anvil
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import DemoData, Game, Media, TaskLibrary, Vision


def _hunt(hunt_id, me, write=True):
    """The hunt if `me` may open it (owner; demo hunts read-only for everyone signed in), else None."""
    h = C.row_by_id(app_tables.hunts, hunt_id)
    if h is None:
        return None
    if h["owner"] == me and not h["is_demo"]:
        return h
    if not write and h["is_demo"]:
        return h
    return None


def _treasure(treasure_id, me):
    t = C.row_by_id(app_tables.treasures, treasure_id)
    if t is None or t["hunt"] is None or t["hunt"]["owner"] != me or t["hunt"]["is_demo"]:
        return None
    return t


def _settings(d, old=None):
    """Clean hunt settings from the browser. Returns (dict, error)."""
    d = d if isinstance(d, dict) else {}
    o = old or {}

    def pick(key, allowed, default):
        v = d.get(key, o.get(key, default))
        return v if v in allowed else default

    title = C.text(d.get("title", o.get("title", "")), 70)
    if len(title) < 2:
        return None, "Give the hunt a name (at least 2 letters)."
    age = d.get("birthday_age", o.get("birthday_age", 0))
    try:
        age = max(0, min(18, int(age or 0)))
    except (TypeError, ValueError):
        age = 0
    limit = d.get("time_limit", o.get("time_limit", 15))
    try:
        limit = int(limit or 0)
    except (TypeError, ValueError):
        limit = 15
    if limit not in Game.TIME_LIMITS:
        limit = 15
    return {"title": title, "kind": pick("kind", list(Game.KINDS), "photo"),
            "birthday_name": C.text(d.get("birthday_name", o.get("birthday_name", "")), 30), "birthday_age": age,
            "flavour": pick("flavour", Game.FLAVOURS, "strawberry"), "time_limit": limit,
            "win_style": pick("win_style", Game.WIN_STYLES, "race"), "start_mode": pick("start_mode", Game.START_MODES, "together"),
            "match_mode": pick("match_mode", Game.MATCH_MODES, "magic"), "strictness": pick("strictness", Game.STRICTNESS, "normal"),
            "message": C.text(d.get("message", o.get("message", "")), 160)}, None


# ---------------------------------------------------------------- Party HQ
@anvil.server.callable(require_user=True)
def get_hq():
    """Party HQ: my hunts, my kids, and the example hunts."""
    me = C.require_user()
    DemoData.ensure_loaded()
    mine = [Game.hunt_dict(Game.tick(h)) for h in app_tables.hunts.search(tables.order_by("created", ascending=False), owner=me)
            if not h["is_demo"]]
    from . import Family
    kids = [Family.kid_dict(k, owner=True) for k in app_tables.kids.search(tables.order_by("created"), owner=me) if not k["is_demo"]]
    examples = [Game.hunt_dict(h) for h in app_tables.hunts.search(tables.order_by("created"), is_demo=True)]
    return {"hunts": mine, "kids": kids, "examples": examples}


@anvil.server.callable(require_user=True)
def create_hunt(settings):
    me = C.require_user()
    s, err = _settings(settings)
    if err:
        return C.fail(err)
    if C.rate_limited("create_hunt", 30, 3600):
        return C.fail("That's a lot of new hunts in one hour. Try again a little later.")
    if len([h for h in app_tables.hunts.search(owner=me) if not h["is_demo"]]) >= 60:
        return C.fail("You have 60 hunts. Delete an old one to make room.")
    s = s or {}
    h = app_tables.hunts.add_row(owner=me, code=Game.new_code(), status="draft", created=C.now(), updated=C.now(),
                                 is_demo=False, **s)
    return C.ok(hunt=Game.hunt_dict(h))


@anvil.server.callable(require_user=True)
def update_hunt(hunt_id, settings):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    s, err = _settings(settings, Game.hunt_dict(h, counts=False))
    if err:
        return C.fail(err)
    s = s or {}
    if h["status"] == "live" and s["start_mode"] != (h["start_mode"] or "together"):
        return C.fail("The hunt is running. End it first to change how it starts.")
    h.update(updated=C.now(), **s)
    return C.ok(hunt=Game.hunt_dict(h))


@anvil.server.callable(require_user=True)
def delete_hunt(hunt_id):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only delete your own hunts.")
    Game.delete_hunt_rows(h)
    return C.ok()


@anvil.server.callable(require_user=True)
def copy_hunt(hunt_id):
    """A new draft hunt with the same treasures (yours, or an example's): for the next party."""
    me = C.require_user()
    h = _hunt(hunt_id, me, write=False)
    if h is None:
        return C.fail("That hunt isn't available.")
    if C.rate_limited("create_hunt", 30, 3600):
        return C.fail("That's a lot of new hunts in one hour. Try again a little later.")
    s = Game.hunt_dict(h, counts=False)
    keep = ("kind", "birthday_name", "birthday_age", "flavour", "time_limit", "win_style", "start_mode", "match_mode",
            "strictness", "message")
    title = ("Copy of " + s["title"]) if h["owner"] == me else s["title"]
    new = app_tables.hunts.add_row(owner=me, code=Game.new_code(), status="draft", title=title[:70], created=C.now(),
                                   updated=C.now(), is_demo=False, **{k: s[k] for k in keep})
    if h["intro_audio"] is not None:
        new.update(intro_audio=anvil.BlobMedia(h["intro_audio"].content_type, h["intro_audio"].get_bytes()),
                   intro_key=Media.new_key(), intro_seconds=h["intro_seconds"])
    for t in Game.treasures(h):
        row = app_tables.treasures.add_row(hunt=new, position=t["position"], kind=t["kind"], name=t["name"], clue=t["clue"],
                                           signature=t["signature"], task_id=t["task_id"], timer=t["timer"], proof=t["proof"],
                                           demo_art=t["demo_art"], created=C.now(), is_demo=False)
        if t["photo"] is not None:
            row.update(photo=anvil.BlobMedia(t["photo"].content_type, t["photo"].get_bytes(), name="photo.jpg"),
                       photo_key=Media.new_key())
        if t["voice"] is not None:
            row.update(voice=anvil.BlobMedia(t["voice"].content_type, t["voice"].get_bytes(), name="voice"),
                       voice_key=Media.new_key(), voice_seconds=t["voice_seconds"])
    return C.ok(hunt=Game.hunt_dict(new))


# ---------------------------------------------------------------- the hunt kitchen (editor)
@anvil.server.callable(require_user=True)
def get_hunt(hunt_id):
    me = C.require_user()
    h = _hunt(hunt_id, me, write=False)
    if h is None:
        return C.fail("That hunt isn't yours, or it was deleted.")
    Game.tick(h)
    return C.ok(hunt=Game.hunt_dict(h), mine=h["owner"] == me and not h["is_demo"],
                treasures=[Game.treasure_dict(t) for t in Game.treasures(h)])


@anvil.server.callable(require_user=True)
def save_treasure(hunt_id, treasure_id, fields, photo=None, signature=None, voice=None, voice_seconds=0):
    """Adds (treasure_id None) or changes a treasure. fields: kind, name, clue, timer, proof, remove_photo, remove_voice.
    photo/voice: new Media (or None to keep what's there)."""
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    t = None
    if treasure_id:
        t = _treasure(treasure_id, me)
        if t is None or t["hunt"] != h:
            return C.fail("That treasure was deleted.")
    elif len(Game.treasures(h)) >= Game.MAX_TREASURES:
        return C.fail("A hunt can have up to %d treasures. That's a lot of running!" % Game.MAX_TREASURES)
    f = fields if isinstance(fields, dict) else {}
    kind = f.get("kind") if f.get("kind") in ("find", "task") else (t["kind"] if t else "find")
    name = C.text(f.get("name", t["name"] if t else ""), 60)
    clue = C.text(f.get("clue", t["clue"] if t else ""), 240, multiline=True)
    if len(name) < 1 and not clue:
        return C.fail("Give it a name, like \"the red teapot\"." if kind == "find" else "Say what the task is.")
    try:
        timer = max(0, min(300, int(f.get("timer", t["timer"] if t else 0) or 0)))
    except (TypeError, ValueError):
        timer = 0
    proof = f.get("proof") if f.get("proof") in ("photo", "done") else ((t["proof"] if t else None) or ("photo" if kind == "find" else "done"))
    if kind == "find":
        proof = "photo"
    changes: dict = {"kind": kind, "name": name, "clue": clue, "timer": timer if kind == "task" else 0, "proof": proof}
    if photo is not None:
        pm, err = Media.photo(photo)
        if err:
            return C.fail(err)
        sig = Vision.valid(signature)
        changes.update(photo=pm, photo_key=Media.new_key(), signature=sig, demo_art=None)
    elif f.get("remove_photo"):
        changes.update(photo=None, photo_key=None, signature=None, demo_art=None)
    if voice is not None:
        vm, secs, err = Media.audio(voice, voice_seconds)
        if err:
            return C.fail(err)
        changes.update(voice=vm, voice_key=Media.new_key(), voice_seconds=secs)
    elif f.get("remove_voice"):
        changes.update(voice=None, voice_key=None, voice_seconds=0)
    if t is None:
        t = app_tables.treasures.add_row(hunt=h, position=len(Game.treasures(h)) + 1, created=C.now(), is_demo=False, **changes)
    else:
        t.update(**changes)
    h["updated"] = C.now()
    return C.ok(treasure=Game.treasure_dict(t))


@anvil.server.callable(require_user=True)
def delete_treasure(treasure_id):
    me = C.require_user()
    t = _treasure(treasure_id, me)
    if t is None:
        return C.ok()
    h = t["hunt"]
    for f in app_tables.finds.search(treasure=t):
        f.delete()
    t.delete()
    Game.renumber(h)
    return C.ok()


@anvil.server.callable(require_user=True)
def move_treasure(treasure_id, step):
    me = C.require_user()
    t = _treasure(treasure_id, me)
    if t is None:
        return C.fail("That treasure was deleted.")
    ts = Game.treasures(t["hunt"])
    i = ts.index(t)
    j = i + (1 if step and int(step) > 0 else -1)
    if 0 <= j < len(ts):
        ts[i], ts[j] = ts[j], ts[i]
        for n, row in enumerate(ts):
            row["position"] = n + 1
    return C.ok()


@anvil.server.callable(require_user=True)
def add_library_tasks(hunt_id, task_ids):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    ids = [i for i in (task_ids or []) if isinstance(i, str) and i in TaskLibrary.BY_ID][:Game.MAX_TREASURES]
    if not ids:
        return C.fail("Pick at least one task.")
    n = len(Game.treasures(h))
    if n + len(ids) > Game.MAX_TREASURES:
        return C.fail("That would make more than %d treasures. Pick fewer tasks." % Game.MAX_TREASURES)
    for i, tid in enumerate(ids):
        task = TaskLibrary.BY_ID[tid]
        app_tables.treasures.add_row(hunt=h, position=n + i + 1, kind="task", name=task["text"][:60], clue=task["text"],
                                     task_id=tid, timer=task["timer"], proof=task["proof"], created=C.now(), is_demo=False)
    h["updated"] = C.now()
    return C.ok(added=len(ids))


@anvil.server.callable(require_user=True)
def set_intro(hunt_id, audio=None, seconds=0):
    """The grown-up's welcome message, played to kids when they start (audio None = remove it)."""
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    if audio is None:
        h.update(intro_audio=None, intro_key=None, intro_seconds=0)
        return C.ok(hunt=Game.hunt_dict(h, counts=False))
    vm, secs, err = Media.audio(audio, seconds)
    if err:
        return C.fail(err)
    h.update(intro_audio=vm, intro_key=Media.new_key(), intro_seconds=secs)
    return C.ok(hunt=Game.hunt_dict(h, counts=False))


# ---------------------------------------------------------------- running the hunt
@anvil.server.callable(require_user=True)
def start_hunt(hunt_id):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only start your own hunts.")
    if not Game.treasures(h):
        return C.fail("Add at least one treasure first.")
    if h["status"] == "finished":
        return C.fail("This hunt has finished. Press Play again to reset it.")
    now = C.now()
    limit = int(h["time_limit"] or 0)
    together = (h["start_mode"] or "together") == "together"
    h.update(status="live", started=h["started"] or now,
             ends_at=(now + dt.timedelta(minutes=limit)) if (limit and together) else None)
    if together:
        for p in Game.players(h):
            if p["started"] is None:
                p["started"] = now
    return C.ok(hunt=Game.hunt_dict(h, counts=False))


@anvil.server.callable(require_user=True)
def extend_hunt(hunt_id, minutes=5):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    try:
        m = max(1, min(30, int(minutes)))
    except (TypeError, ValueError):
        m = 5
    if h["status"] != "live":
        return C.fail("The hunt isn't running.")
    if (h["start_mode"] or "together") == "together":
        base = max(h["ends_at"] or C.now(), C.now())
        h["ends_at"] = base + dt.timedelta(minutes=m)
        if not h["time_limit"]:
            h["time_limit"] = m
    else:
        for p in Game.players(h):
            if p["started"] is not None and p["finished"] is None:
                p["started"] = p["started"] + dt.timedelta(minutes=m)
    return C.ok(hunt=Game.hunt_dict(h, counts=False))


@anvil.server.callable(require_user=True)
def end_hunt(hunt_id):
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only end your own hunts.")
    Game.finish(h)
    return C.ok(hunt=Game.hunt_dict(h, counts=False))


@anvil.server.callable(require_user=True)
def reset_hunt(hunt_id):
    """Play again: same treasures, no players, back to the lobby."""
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only reset your own hunts.")
    for f in app_tables.finds.search(hunt=h):
        f.delete()
    for p in app_tables.players.search(hunt=h):
        p.delete()
    h.update(status="draft", started=None, ends_at=None, finished=None, updated=C.now())
    return C.ok(hunt=Game.hunt_dict(h, counts=False))


def _online(p):
    return p["last_seen"] is not None and (C.now() - p["last_seen"]).total_seconds() < Game.ONLINE_SECONDS


@anvil.server.callable(require_user=True)
def live_board(hunt_id):
    """Everything the live board shows; it asks again every few seconds."""
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("That hunt isn't yours, or it was deleted.")
    Game.tick(h)
    prog = Game.progress(h)
    ts = Game.treasures(h)
    tmap = {t.get_id(): t for t in ts}
    ranking = Game.results(h, prog)
    online = {p.get_id(): _online(p) for p in Game.players(h)}
    for r in ranking:
        r["online"] = online.get(r["id"], False)
        r["seconds_left"] = None
    if (h["start_mode"] or "together") == "self":
        pmap = {p.get_id(): p for p in Game.players(h)}
        for r in ranking:
            if r["id"] in pmap:
                r["seconds_left"] = Game.seconds_left(h, pmap[r["id"]])
    review = []
    feed = []
    for f in reversed(Game.finds(h)):
        t = f["treasure"]
        p = f["player"]
        if t is None or p is None:
            continue
        row = {"id": f.get_id(), "player": p["name"], "topper": p["topper"], "colour": p["colour"], "treasure": t["name"],
               "treasure_photo_key": t["photo_key"], "treasure_art": Game.demo_art_url(t["demo_art"]), "kind": t["kind"],
               "photo_key": f["photo_key"], "art": Game.demo_art_url(f["demo_art"]), "score": f["score"],
               "status": f["status"], "created": C.iso(f["created"])}
        if f["status"] == "review":
            review.append(row)
        if len(feed) < 12:
            feed.append(row)
    team = [{"id": tid, "name": tmap[tid]["name"], "by": pf[0]["name"]} for tid, pf in prog["team"].items() if tid in tmap]
    return C.ok(hunt=Game.hunt_dict(h, counts=False), seconds_left=Game.seconds_left(h), players=ranking,
                review=list(reversed(review)), feed=feed, team=team, total=len(ts), now=C.iso(C.now()))


@anvil.server.callable(require_user=True)
def review_find(find_id, approve):
    me = C.require_user()
    f = C.row_by_id(app_tables.finds, find_id)
    if f is None or f["hunt"] is None or f["hunt"]["owner"] != me or f["hunt"]["is_demo"]:
        return C.fail("That photo was already checked or deleted.")
    if f["status"] != "review":
        return C.ok(status=f["status"])
    f.update(status="ok" if approve else "rejected", checked=C.now())
    if approve and f["player"] is not None:
        Game.after_find(f["hunt"], f["player"])
    return C.ok(status=f["status"])


@anvil.server.callable(require_user=True)
def remove_player(player_id):
    me = C.require_user()
    p = C.row_by_id(app_tables.players, player_id)
    if p is None or p["hunt"] is None or p["hunt"]["owner"] != me or p["hunt"]["is_demo"]:
        return C.fail("That player already left.")
    for f in app_tables.finds.search(player=p):
        f.delete()
    p.delete()
    return C.ok()


# ---------------------------------------------------------------- the party album
@anvil.server.callable(require_user=True)
def album(hunt_id):
    me = C.require_user()
    h = _hunt(hunt_id, me, write=False)
    if h is None:
        return C.fail("That hunt isn't yours, or it was deleted.")
    Game.tick(h)
    demo_only = bool(h["is_demo"])
    prog = Game.progress(h)
    shown = [f for f in Game.finds(h) if f["status"] in ("ok", "review") and (f["is_demo"] or not demo_only)]
    by_t: dict = {}
    for f in shown:
        if f["treasure"] is None or f["player"] is None:
            continue
        by_t.setdefault(f["treasure"].get_id(), []).append(
            {"id": f.get_id(), "player": f["player"]["name"], "topper": f["player"]["topper"], "colour": f["player"]["colour"],
             "photo_key": f["photo_key"], "art": Game.demo_art_url(f["demo_art"]), "status": f["status"], "score": f["score"]})
    ts = []
    for t in Game.treasures(h):
        d = Game.treasure_dict(t)
        d["finds"] = by_t.get(t.get_id(), [])
        ts.append(d)
    ranking = [r for r in Game.results(h, prog)]
    if demo_only:
        demo_ids = {p.get_id() for p in Game.players(h) if p["is_demo"]}
        ranking = [r for r in ranking if r["id"] in demo_ids]
    for r in ranking:
        if not r["stickers"]:
            p = C.row_by_id(app_tables.players, r["id"])
            if p is not None:
                r["stickers"] = Game.stickers_for(h, p, prog, len(ts), ranking)
    photos = len([f for f in shown if f["photo_key"] or f["demo_art"]])
    return C.ok(hunt=Game.hunt_dict(h, counts=False), mine=h["owner"] == me and not h["is_demo"], treasures=ts,
                players=ranking, photos=photos)


@anvil.server.callable(require_user=True)
def delete_kid_photos(hunt_id):
    """Removes every photo the kids took in this hunt (the finds stay, so the results don't change)."""
    me = C.require_user()
    h = _hunt(hunt_id, me)
    if h is None:
        return C.fail("You can only change your own hunts.")
    n = 0
    for f in app_tables.finds.search(hunt=h):
        if f["photo"] is not None:
            f.update(photo=None, photo_key=None)
            n += 1
    return C.ok(deleted=n)
