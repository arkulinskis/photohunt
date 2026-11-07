"""The kids' side: join a hunt with its code (or QR), play it, send finds. No account needed.

Kids never sign in (accounts are for grown-ups, 16+). Joining makes a player row with a random token; the tablet keeps
the token, and every call here takes it. A token only opens its own player in its own hunt.
Demo hunts (code CAKE42 etc.) accept any photo and never store photos from visitors; visitor players in a demo hunt
are tidied away after a day.
"""
import datetime as dt

import anvil
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import DemoData, Game, Media, Vision


def _player(token):
    if not isinstance(token, str) or not 20 <= len(token) <= 40:
        return None
    p = app_tables.players.get(token=token)
    if p is None or p["hunt"] is None:
        return None
    return p


def _tidy_demo(h):
    """Visitors who played a demo hunt more than a day ago are removed (with their finds)."""
    cutoff = C.now() - dt.timedelta(days=1)
    for p in app_tables.players.search(hunt=h, is_demo=False):
        if p["joined"] is not None and p["joined"] < cutoff:
            for f in app_tables.finds.search(player=p):
                f.delete()
            p.delete()


def preview(h):
    ts = Game.treasures(h)
    return {"title": h["title"] or "", "code": h["code"], "kind": h["kind"] or "photo",
            "kind_label": Game.KINDS.get(h["kind"] or "photo", ""), "birthday_name": h["birthday_name"] or "",
            "birthday_age": int(h["birthday_age"] or 0), "flavour": h["flavour"] or "strawberry",
            "status": h["status"] or "draft", "total": len(ts), "tasks": len([t for t in ts if t["kind"] == "task"]),
            "players": len(Game.players(h)), "time_limit": int(h["time_limit"] or 0), "message": h["message"] or "",
            "win_style": h["win_style"] or "race", "start_mode": h["start_mode"] or "together", "demo": bool(h["is_demo"])}


@anvil.server.callable
def hunt_preview(code):
    """What a kid sees after scanning or typing a code, before joining."""
    code = Game.norm_code(code)
    if len(code) != 6:
        return C.fail("A hunt code has 6 letters and numbers.")
    if C.rate_limited("preview", 60, 600):
        return C.fail("Too many tries. Wait a few minutes and try again.")
    DemoData.ensure_loaded()  # the Try-me Hunt (CAKE42) exists even before anyone opened Party HQ
    h = app_tables.hunts.get(code=code)
    if h is None:
        return C.fail("No hunt has that code. Check the letters with a grown-up.")
    if h["is_demo"]:
        _tidy_demo(h)
    Game.tick(h)
    return C.ok(hunt=preview(h))


def join(h, name, topper, colour, kid=None):
    """(player row, None) or (None, message). Shared with Family.kid_join."""
    if (h["status"] or "draft") == "finished":
        return None, "This hunt has finished. Ask a grown-up to start a new one."
    if not Game.treasures(h):
        return None, "This hunt has no treasures yet. Ask the grown-up to add some."
    if len(Game.players(h)) >= Game.MAX_PLAYERS:
        return None, "This hunt is full (%d players)." % Game.MAX_PLAYERS
    name = C.text(name, 30)
    if len(name) < 1:
        return None, "Type your name (or your team's name)."
    if kid is not None:
        for p in app_tables.players.search(hunt=h, kid=kid):
            return p, None  # this kid already joined: carry on
    now = C.now()
    started = None
    if (h["start_mode"] or "together") == "together" and h["status"] == "live":
        started = h["started"] or now
    p = app_tables.players.add_row(hunt=h, kid=kid, name=name, topper=topper if topper in Game.TOPPERS else "star",
                                   colour=colour if colour in Game.COLOURS else "pink", token=Game.token(), joined=now,
                                   started=started, last_seen=now, stickers=[], is_demo=False)
    return p, None


@anvil.server.callable
def join_hunt(code, name, topper="star", colour="pink"):
    code = Game.norm_code(code)
    h = app_tables.hunts.get(code=code) if len(code) == 6 else None
    if h is None:
        return C.fail("No hunt has that code. Check the letters with a grown-up.")
    if C.rate_limited("join", 20, 3600):
        return C.fail("That's a lot of joining. Wait a little and try again.")
    Game.tick(h)
    p, err = join(h, name, topper, colour)
    if err or p is None:
        return C.fail(err or "That didn't work.")
    return C.ok(token=p["token"], player=Game.player_dict(p))


def state(p):
    """The whole play screen for one player."""
    h = Game.tick(p["hunt"])
    now = C.now()
    if p["last_seen"] is None or (now - p["last_seen"]).total_seconds() > 8:
        p["last_seen"] = now
    together_win = (h["win_style"] or "race") == "together"
    hide = (h["kind"] or "") == "voice"
    prog = Game.progress(h)
    mine = prog["by_player"].get(p.get_id(), {})
    my_finds: dict = {}
    for f in Game.finds(h):
        if f["player"] == p and f["treasure"] is not None:
            my_finds[f["treasure"].get_id()] = f
    out = []
    for t in Game.treasures(h):
        tid = t.get_id()
        st = mine.get(tid, "")
        by = None
        if together_win and tid in prog["team"]:
            st = "ok"
            by = prog["team"][tid][0]["name"]
        found = st == "ok"
        d = Game.treasure_dict(t, hide_photo=hide and not found)
        f = my_finds.get(tid)
        d.update(state={"ok": "found", "review": "review", "rejected": "rejected"}.get(st, "todo"), by=by,
                 find_id=f.get_id() if f is not None else None,
                 find_photo_key=f["photo_key"] if f is not None else None)
        out.append(d)
    found = len([t for t in out if t["state"] == "found"])
    finished = (h["status"] == "finished") or (p["finished"] is not None)
    ranking = Game.results(h, prog)
    team = [{"id": r["id"], "name": r["name"], "topper": r["topper"], "colour": r["colour"], "found": r["found"],
             "rank": r["rank"], "winner": r["winner"], "me": r["id"] == p.get_id(), "finished": r["finished"]}
            for r in ranking]
    me = Game.player_dict(p)
    if finished and not me["stickers"]:
        me["stickers"] = Game.stickers_for(h, p, prog, len(out), ranking)
    waiting = (h["start_mode"] or "together") == "together" and h["status"] == "draft"
    ready = (h["start_mode"] or "together") == "self" and p["started"] is None and not finished
    return C.ok(player=me, hunt=dict(preview(h), intro_key=h["intro_key"], match_mode=h["match_mode"] or "magic"),
                treasures=out, found=found, total=len(out), team=team, seconds_left=Game.seconds_left(h, p),
                phase="done" if finished else ("lobby" if waiting else ("ready" if ready else "hunt")))


@anvil.server.callable
def play_state(token):
    p = _player(token)
    if p is None:
        return C.fail("This game was removed. Scan the hunt's code again to join.")
    return state(p)


@anvil.server.callable
def go(token):
    """A self-start player presses Go: their clock starts."""
    p = _player(token)
    if p is None:
        return C.fail("This game was removed. Scan the hunt's code again to join.")
    h = p["hunt"]
    if h["status"] == "finished":
        return state(p)
    if (h["start_mode"] or "together") == "together" and h["status"] != "live":
        return C.fail("Wait for the grown-up to press Start.")
    if p["started"] is None:
        p["started"] = C.now()
    if h["status"] == "draft":
        h.update(status="live", started=h["started"] or C.now())
    return state(p)


def _can_play(p):
    h = Game.tick(p["hunt"])
    if h["status"] == "finished" or p["finished"] is not None:
        return "The hunt is over! Look at your cake."
    if (h["start_mode"] or "together") == "together" and h["status"] != "live":
        return "Wait for the grown-up to press Start."
    if (h["start_mode"] or "together") == "self" and p["started"] is None:
        return "Press Go first!"
    return None


@anvil.server.callable
def submit_find(token, treasure_id, photo=None, signature=None, ask=False):
    """A kid's photo (or "I did it!") for one treasure. Result: found / review (a grown-up checks) / miss (try again),
    plus the fresh play state."""
    p = _player(token)
    if p is None:
        return C.fail("This game was removed. Scan the hunt's code again to join.")
    err = _can_play(p)
    if err:
        return C.fail(err)
    h = p["hunt"]
    t = C.row_by_id(app_tables.treasures, treasure_id)
    if t is None or t["hunt"] != h:
        return C.fail("That treasure isn't in this hunt any more.")
    if C.rate_limited("find", 120, 600):
        return C.fail("Whoa, lots of photos! Take a little break and try again.")
    prog = Game.progress(h)
    already = prog["by_player"].get(p.get_id(), {}).get(t.get_id())
    if already == "ok" or ((h["win_style"] or "race") == "together" and t.get_id() in prog["team"]):
        r = state(p)
        r.update(result="found", message="Already found!")
        return r
    mode = h["match_mode"] or "magic"
    demo = bool(h["is_demo"])
    pm = None
    if photo is not None and not demo:
        pm, perr = Media.photo(photo)
        if perr:
            return C.fail(perr)
    needs_photo = (t["proof"] or "photo") == "photo"
    if needs_photo and photo is None:
        return C.fail("Take a picture to show you found it!")
    score = None
    status = "ok"
    if demo or mode == "honour":
        status = "ok"
    elif mode == "judge":
        status = "review"
    elif t["kind"] == "task" or not t["signature"]:
        status = "ok"  # nothing to compare with: tasks and photo-less treasures count (judge mode checks them)
    else:
        score = Vision.score(signature, t["signature"])
        v = Vision.verdict(score, h["strictness"])
        if v == "found":
            status = "ok"
        elif ask or v == "close":
            status = "review" if ask else "close"
        else:
            status = "miss"
    if status in ("miss", "close"):
        r = state(p)
        r.update(result=status, score=score,
                 message="So close! Ask a grown-up to check it." if status == "close" else "Hmm, not quite. Try again!")
        return r
    for old in app_tables.finds.search(player=p, treasure=t, status="review"):
        old.delete()
    app_tables.finds.add_row(hunt=h, player=p, treasure=t, photo=pm, photo_key=Media.new_key() if pm is not None else None,
                             score=score, status=status, created=C.now(), is_demo=False)
    if status == "ok":
        Game.after_find(h, p)
    r = state(p)
    r.update(result="found" if status == "ok" else "review", score=score,
             message="You found it!" if status == "ok" else "A grown-up will check your photo.")
    return r


@anvil.server.callable
def grownup_check(token, find_id, approve):
    """A grown-up said yes or no on the kid's own tablet (after the grown-up question)."""
    p = _player(token)
    if p is None:
        return C.fail("This game was removed. Scan the hunt's code again to join.")
    f = C.row_by_id(app_tables.finds, find_id)
    if f is None or f["player"] != p:
        return C.fail("That photo was already checked.")
    if f["status"] == "review":
        f.update(status="ok" if approve else "rejected", checked=C.now())
        if approve:
            Game.after_find(p["hunt"], p)
    return state(p)
