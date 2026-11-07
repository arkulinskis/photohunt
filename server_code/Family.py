"""Kid profiles and the Kids' corner.

Kids don't have accounts. A grown-up adds a kid profile (first name or nickname, a cake topper, a colour); each
profile has a private Kids' corner link (/#kid/<token>) the grown-up opens on the kids' tablet, usually by scanning its
QR code. In the Kids' corner a kid joins hunts with one tap (scan or type the code), and keeps the stickers they win.
Making a new link stops the old one.
"""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import Game, Play


def kid_dict(k, owner=False):
    d = {"id": k.get_id(), "name": k["name"] or "Kid", "topper": k["topper"] or "star", "colour": k["colour"] or "pink"}
    ps = list(app_tables.players.search(kid=k))
    stickers: dict = {}
    for p in ps:
        for s in (p["stickers"] or []):
            stickers[s] = stickers.get(s, 0) + 1
    d.update(hunts=len(ps), stickers=sum(stickers.values()), sticker_counts=stickers)
    if owner:
        d["token"] = k["token"]
    return d


def _mine(kid_id, me):
    k = C.row_by_id(app_tables.kids, kid_id)
    return k if (k is not None and k["owner"] == me and not k["is_demo"]) else None


def _clean(name, topper, colour):
    name = C.text(name, 24)
    if len(name) < 1:
        return None, "Type the kid's first name or a nickname."
    return {"name": name, "topper": topper if topper in Game.TOPPERS else "star",
            "colour": colour if colour in Game.COLOURS else "pink"}, None


@anvil.server.callable(require_user=True)
def add_kid(name, topper="star", colour="pink"):
    me = C.require_user()
    d, err = _clean(name, topper, colour)
    if err or d is None:
        return C.fail(err or "That didn't work.")
    if len(list(app_tables.kids.search(owner=me))) >= 12:
        return C.fail("A family can have up to 12 kid profiles.")
    k = app_tables.kids.add_row(owner=me, token=Game.token(), created=C.now(), is_demo=False, **d)
    return C.ok(kid=kid_dict(k, owner=True))


@anvil.server.callable(require_user=True)
def update_kid(kid_id, name, topper, colour):
    me = C.require_user()
    k = _mine(kid_id, me)
    if k is None:
        return C.fail("That profile was deleted.")
    d, err = _clean(name, topper, colour)
    if err or d is None:
        return C.fail(err or "That didn't work.")
    k.update(**d)
    return C.ok(kid=kid_dict(k, owner=True))


@anvil.server.callable(require_user=True)
def delete_kid(kid_id):
    """Removes the profile and its Kids' corner link. Hunts they played keep their results under the same name."""
    me = C.require_user()
    k = _mine(kid_id, me)
    if k is None:
        return C.ok()
    for p in app_tables.players.search(kid=k):
        p["kid"] = None
    k.delete()
    return C.ok()


@anvil.server.callable(require_user=True)
def new_kid_link(kid_id):
    me = C.require_user()
    k = _mine(kid_id, me)
    if k is None:
        return C.fail("That profile was deleted.")
    k["token"] = Game.token()
    return C.ok(kid=kid_dict(k, owner=True))


def _kid(token):
    if not isinstance(token, str) or not 20 <= len(token) <= 40:
        return None
    return app_tables.kids.get(token=token)


@anvil.server.callable
def kid_corner(token):
    """The Kids' corner: who I am, my hunts (newest first), my stickers."""
    k = _kid(token)
    if k is None:
        return C.fail("This Kids' corner link was changed or removed. Ask a grown-up for the new one.")
    hunts = []
    for p in app_tables.players.search(tables.order_by("joined", ascending=False), kid=k):
        h = p["hunt"]
        if h is None:
            continue
        Game.tick(h)
        prog = Game.progress(h)
        hunts.append({"token": p["token"], "title": h["title"] or "", "flavour": h["flavour"] or "strawberry",
                      "kind_label": Game.KINDS.get(h["kind"] or "photo", ""), "status": h["status"] or "draft",
                      "found": Game.found_count(h, p, prog), "total": len(Game.treasures(h)),
                      "done": h["status"] == "finished" or p["finished"] is not None,
                      "stickers": list(p["stickers"] or []), "joined": C.iso(p["joined"])})
    return C.ok(kid=kid_dict(k), hunts=hunts)


@anvil.server.callable
def kid_join(token, code):
    """A kid in the Kids' corner joins a hunt (scanned or typed code). Returns the player token to play with."""
    k = _kid(token)
    if k is None:
        return C.fail("This Kids' corner link was changed or removed. Ask a grown-up for the new one.")
    code = Game.norm_code(code)
    h = app_tables.hunts.get(code=code) if len(code) == 6 else None
    if h is None:
        return C.fail("No hunt has that code. Check the letters with a grown-up.")
    if C.rate_limited("join", 20, 3600):
        return C.fail("That's a lot of joining. Wait a little and try again.")
    Game.tick(h)
    p, err = Play.join(h, k["name"], k["topper"], k["colour"], kid=k)
    if err or p is None:
        return C.fail(err or "That didn't work.")
    return C.ok(token=p["token"])
