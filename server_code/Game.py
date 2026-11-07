"""The rules of a hunt, shared by the grown-up side (Hunts.py) and the kids' side (Play.py). No callables here.

A hunt (table hunts) has treasures (things to find or tasks to do), players (a kid, or a team sharing one tablet) and
finds (a player's photo or "I did it" for one treasure, status ok / review / rejected).

    win_style   "race"      every player fills their own cake; most candles wins, the first full cake wins outright
                "together"  one cake for everybody: a treasure counts once, whoever finds it
    start_mode  "together"  kids wait in the lobby until the grown-up presses Start (one shared clock)
                "self"      each player starts when they press Go (their own clock); no grown-up needed
    match_mode  "magic"     photos are compared with the grown-up's photo (Vision.py); close ones ask a grown-up
                "judge"     a grown-up says yes or no to every photo (live board, or on the kid's tablet)
                "honour"    every photo counts
Status: draft (being made; players can join and wait) -> live -> finished. Time runs out lazily: every read calls
tick(), which finishes a hunt (or a self-start player) whose clock has run out.
"""
import datetime as dt
import secrets

from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C

KINDS = {"photo": "Photo hunt", "voice": "Voice hunt", "task": "Task party", "mix": "Party mix"}
FLAVOURS = ["strawberry", "chocolate", "vanilla", "mint", "blueberry", "lemon"]
TOPPERS = ["star", "heart", "crown", "rocket", "flower", "balloon", "dino", "moon", "bolt", "fish", "cat", "rainbow"]
COLOURS = ["pink", "mint", "blue", "lemon", "orange", "berry"]
WIN_STYLES = ["race", "together"]
START_MODES = ["together", "self"]
MATCH_MODES = ["magic", "judge", "honour"]
STRICTNESS = ["easy", "normal", "tricky"]
TIME_LIMITS = [0, 5, 10, 15, 20, 30, 45, 60]
CODE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # no 0/O, 1/I/L: easy to read out and type
MAX_TREASURES = 30
MAX_PLAYERS = 40
ONLINE_SECONDS = 25


def new_code():
    for _ in range(50):
        code = "".join(secrets.choice(CODE_LETTERS) for _ in range(6))
        if app_tables.hunts.get(code=code) is None:
            return code
    raise RuntimeError("no free hunt code")


def norm_code(value):
    """'cake 42' -> 'CAKE42' (letters and digits only, at most 6)."""
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())[:6]


def token():
    return secrets.token_urlsafe(18)


def treasures(h):
    return list(app_tables.treasures.search(tables.order_by("position"), hunt=h))


def players(h):
    return list(app_tables.players.search(tables.order_by("joined"), hunt=h))


def finds(h):
    return list(app_tables.finds.search(tables.order_by("created"), hunt=h))


def demo_art_url(name):
    return ("_/theme/demo-%s.svg" % name) if name else None


# ---------------------------------------------------------------- shapes sent to the browser
def hunt_dict(h, counts=True):
    d = {"id": h.get_id(), "code": h["code"], "title": h["title"] or "", "kind": h["kind"] or "photo",
         "kind_label": KINDS.get(h["kind"] or "photo", "Photo hunt"), "birthday_name": h["birthday_name"] or "",
         "birthday_age": int(h["birthday_age"] or 0), "flavour": h["flavour"] or "strawberry",
         "time_limit": int(h["time_limit"] or 0), "win_style": h["win_style"] or "race",
         "start_mode": h["start_mode"] or "together", "match_mode": h["match_mode"] or "magic",
         "strictness": h["strictness"] or "normal", "status": h["status"] or "draft", "started": C.iso(h["started"]),
         "ends_at": C.iso(h["ends_at"]), "finished": C.iso(h["finished"]), "intro_key": h["intro_key"],
         "intro_seconds": h["intro_seconds"] or 0, "message": h["message"] or "", "created": C.iso(h["created"]),
         "demo": bool(h["is_demo"])}
    if counts:
        ts = treasures(h)
        fs = finds(h)
        d["counts"] = {"treasures": len(ts), "tasks": len([t for t in ts if t["kind"] == "task"]),
                       "players": len(players(h)), "finds": len([f for f in fs if f["status"] == "ok"]),
                       "review": len([f for f in fs if f["status"] == "review"])}
        d["cover"] = next(({"photo_key": t["photo_key"], "art": demo_art_url(t["demo_art"])} for t in ts
                           if t["photo_key"] or t["demo_art"]), None)
    return d


def treasure_dict(t, hide_photo=False):
    hidden = hide_photo and t["kind"] != "task"
    return {"id": t.get_id(), "position": int(t["position"] or 0), "kind": t["kind"] or "find", "name": t["name"] or "",
            "clue": t["clue"] or "", "photo_key": None if hidden else t["photo_key"],
            "art": None if hidden else demo_art_url(t["demo_art"]), "has_photo": bool(t["photo_key"] or t["demo_art"]),
            "voice_key": t["voice_key"], "voice_seconds": t["voice_seconds"] or 0, "task_id": t["task_id"],
            "timer": int(t["timer"] or 0), "proof": t["proof"] or "photo", "has_target": bool(t["signature"])}


def player_dict(p):
    return {"id": p.get_id(), "name": p["name"] or "Player", "topper": p["topper"] or "star", "colour": p["colour"] or "pink",
            "joined": C.iso(p["joined"]), "started": C.iso(p["started"]), "finished": C.iso(p["finished"]),
            "stickers": list(p["stickers"] or []), "kid": p["kid"] is not None}


# ---------------------------------------------------------------- clocks
def end_time(h, p=None):
    """When the clock runs out for this player (or the hunt), or None (no time limit / not started)."""
    limit = int(h["time_limit"] or 0)
    if not limit:
        return None
    if (h["start_mode"] or "together") == "together":
        return h["ends_at"]
    if p is not None and p["started"] is not None:
        return p["started"] + dt.timedelta(minutes=limit)
    return None


def seconds_left(h, p=None):
    end = end_time(h, p)
    if end is None:
        return None
    return max(0, int((end - C.now()).total_seconds()))


def tick(h):
    """Finish whatever ran out of time. Returns the hunt."""
    if (h["status"] or "draft") != "live":
        return h
    now = C.now()
    if (h["start_mode"] or "together") == "together":
        if h["ends_at"] is not None and now >= h["ends_at"]:
            finish(h, at=h["ends_at"])
        return h
    limit = int(h["time_limit"] or 0)
    if limit:
        for p in players(h):
            if p["started"] is not None and p["finished"] is None and now >= p["started"] + dt.timedelta(minutes=limit):
                p["finished"] = p["started"] + dt.timedelta(minutes=limit)
                award(h, [p])
    return h


# ---------------------------------------------------------------- progress
def progress(h):
    """Who has which treasure: {"by_player": {pid: {tid: status}}, "team": {tid: (player row, find row)},
    "ok": [ok find rows]} where status is "ok", "review" or "rejected" (the best one wins)."""
    rank = {"ok": 3, "review": 2, "rejected": 1}
    by_player: dict = {}
    team: dict = {}
    oks = []
    for f in finds(h):
        if f["player"] is None or f["treasure"] is None:
            continue
        pid, tid, st = f["player"].get_id(), f["treasure"].get_id(), f["status"] or "review"
        cur = by_player.setdefault(pid, {})
        if rank.get(st, 0) >= rank.get(cur.get(tid, ""), 0):
            cur[tid] = st
        if st == "ok":
            oks.append(f)
            if tid not in team:
                team[tid] = (f["player"], f)
    return {"by_player": by_player, "team": team, "ok": oks}


def found_count(h, p, prog=None, total=None):
    prog = prog or progress(h)
    if (h["win_style"] or "race") == "together":
        return len(prog["team"])
    return len([1 for st in prog["by_player"].get(p.get_id(), {}).values() if st == "ok"])


def after_find(h, p):
    """A find was accepted: finish the player or the whole hunt if their cake is complete."""
    total = len(treasures(h))
    if not total:
        return
    prog = progress(h)
    if (h["win_style"] or "race") == "together":
        if len(prog["team"]) >= total:
            finish(h)
        return
    if p["finished"] is None and found_count(h, p, prog) >= total:
        p["finished"] = C.now()
        award(h, [p], prog)
        # A shared-start race ends when everyone is done. Self-start hunts stay open: a sibling may play later.
        if (h["start_mode"] or "together") == "together" and all(q["finished"] is not None for q in players(h)):
            finish(h)


def finish(h, at=None):
    if (h["status"] or "") == "finished":
        return
    when = at or C.now()
    h.update(status="finished", finished=when)
    ps = players(h)
    for p in ps:
        if p["finished"] is None:
            p["finished"] = when
    award(h, ps)


# ---------------------------------------------------------------- results and stickers
def results(h, prog=None):
    """Ranking: [{player..., found, total, rank, winner}] best first."""
    prog = prog or progress(h)
    total = len(treasures(h))
    together = (h["win_style"] or "race") == "together"
    rows = []
    for p in players(h):
        mine = len([1 for st in prog["by_player"].get(p.get_id(), {}).values() if st == "ok"])
        d = player_dict(p)
        d.update(found=mine, team_found=len(prog["team"]), total=total)
        rows.append((p, d))

    def key(item):
        p, d = item
        fin = p["finished"] if (p["finished"] is not None and d["found"] >= total and total) else None
        return (-d["found"], fin is None, fin or C.now())

    rows.sort(key=key)
    out = []
    rank = 0
    last = None
    for i, (p, d) in enumerate(rows):
        k = d["found"] if not together else 0
        if k != last:
            rank = i + 1
            last = k
        d["rank"] = 1 if together else rank
        d["winner"] = (len(prog["team"]) >= total > 0) if together else (rank == 1 and d["found"] > 0)
        out.append(d)
    return out


def stickers_for(h, p, prog, total, ranking=None):
    """The stickers a player earned in this hunt (ids; the browser draws and names them)."""
    out = ["party"]
    together = (h["win_style"] or "race") == "together"
    mine = [f for f in prog["ok"] if f["player"] == p]
    full = (len(prog["team"]) >= total) if together else (len(mine) >= total)
    if total and full:
        out.append("team" if together else "cake")
    if prog["ok"] and prog["ok"][0]["player"] == p:
        out.append("first")
    limit = int(h["time_limit"] or 0)
    if not together and total and len(mine) >= total and p["started"] is not None and p["finished"] is not None:
        took = (p["finished"] - p["started"]).total_seconds()
        if took <= (limit * 30 if limit else 300):
            out.append("speedy")
    if not together and ranking:
        me = next((r for r in ranking if r["id"] == p.get_id()), None)
        if me and me["rank"] == 1 and me["found"] > 0:
            out.append("winner")
    scored = [f["score"] for f in mine if f["score"]]
    if len(scored) >= 3 and sum(scored) / len(scored) >= 0.8:
        out.append("sharp")
    if (h["kind"] or "") == "voice" and len([f for f in mine if f["treasure"]["kind"] != "task"]) >= 3:
        out.append("voice")
    if len([f for f in mine if f["treasure"]["kind"] == "task"]) >= 3:
        out.append("task")
    return out


def award(h, ps, prog=None):
    prog = prog or progress(h)
    total = len(treasures(h))
    ranking = results(h, prog)
    for p in ps:
        p["stickers"] = stickers_for(h, p, prog, total, ranking)


def delete_hunt_rows(h):
    for f in app_tables.finds.search(hunt=h):
        f.delete()
    for p in app_tables.players.search(hunt=h):
        p.delete()
    for t in app_tables.treasures.search(hunt=h):
        t.delete()
    h.delete()


def renumber(h):
    for i, t in enumerate(treasures(h)):
        if t["position"] != i + 1:
            t["position"] = i + 1
