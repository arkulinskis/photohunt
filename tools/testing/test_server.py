"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402

M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
assert ana["last_seen"] is not None
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- feedback
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#home", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and fb["email"] == "guest@example.com" and "evil" not in fb["context"] and fb["status"] == "new"
for i in range(4):
    ok(call("submit_feedback", "idea", "Idea number %d" % i))
bad(call("submit_feedback", "idea", "One too many this hour"), "rate limit")
as_user(ana)
ok(call("submit_feedback", "nonsense-kind", "Signed-in feedback"))
assert T.feedback.get(message="Signed-in feedback")["kind"] == "other"
assert denied("list_feedback")
as_user(admin)
lst = call("list_feedback")
assert lst["counts"]["new"] == 6 and len(lst["items"]) == 6
fid = lst["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
assert call("list_feedback", "done")["items"][0]["note"] == "Fixed it"
bad(call("set_feedback_status", fid, "weird"))
bad(call("set_feedback_status", "nope", "done"))
ok(call("delete_feedback", fid))
assert len(call("list_feedback")["items"]) == 5

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("demo_load", ()), ("demo_remove", ())]:
    assert denied(fn, *args), fn
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 3 and ov["admins"] == 1 and ov["feedback_new"] == 5
assert len(call("list_users")["users"]) == 3 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
assert bob["is_admin"] is True
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
assert bob["enabled"] is False
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))
assert bob["is_admin"] is False

# ---------------------------------------------------------------------------------- PhotoHunt
import random  # noqa: E402

random.seed(7)
import anvil as _anvil  # noqa: E402


def sig(seed=1, tweak=0.0):
    rnd = random.Random(seed)
    c = [rnd.random() for _ in range(20)]
    sc = sum(c)
    e = [rnd.random() for _ in range(128)]
    l_ = [rnd.gauss(0, 1) for _ in range(64)]
    if tweak:
        rnd2 = random.Random(seed * 100 + 1)
        c = [max(0.0, x + rnd2.uniform(-tweak, tweak) * x) for x in c]
        e = [max(0.0, x + rnd2.uniform(-tweak, tweak)) for x in e]
        l_ = [x + rnd2.gauss(0, tweak) for x in l_]
    return {"v": 1, "c": [x / sc for x in c], "e": e, "l": l_}


JPEG = _anvil.BlobMedia("image/jpeg", b"\xff\xd8" + b"x" * 600, name="t.jpg")
WEBM = _anvil.BlobMedia("audio/webm", b"y" * 900, name="v.webm")

# vision
V = M["Vision"]
assert V.score(sig(1), sig(1)) == 1.0
assert V.score(sig(1), sig(1, 0.05)) > 0.85, V.score(sig(1), sig(1, 0.05))
assert V.score(sig(1), sig(2)) < 0.85
assert V.score(sig(1), {"v": 1, "c": [1]}) == 0.0 and V.valid({"c": [float("nan")] * 20, "e": [0] * 128, "l": [0] * 64}) is None
assert V.verdict(0.9, "normal") == "found" and V.verdict(V.THRESHOLD["normal"] - 0.05, "normal") == "close" and V.verdict(0.1, "easy") == "miss"

# task library (public)
as_user(None)
lib = call("task_library")
assert len(lib["tasks"]) == 100 and len({t["id"] for t in lib["tasks"]}) == 100 and sum(c["count"] for c in lib["categories"]) == 100
missing_voice = [t["id"] for t in lib["tasks"] if not (PROJECT / "theme" / "assets" / "voices" / (t["id"] + ".mp3")).exists()]
assert not missing_voice, "tasks without a recorded voice (run tools/make_task_voices.py): %s" % missing_voice

# Party HQ + demo
assert denied("get_hq")
as_user(ana)
hq = call("get_hq")
assert M["DemoData"].state() == "loaded" and len(hq["examples"]) == 5 and hq["hunts"] == [] and hq["kids"] == []
mia = next(h for h in hq["examples"] if h["birthday_name"] == "Mia")
assert mia["counts"]["players"] == 5 and mia["cover"]["art"].endswith("demo-teapot.svg")
bad(call("update_hunt", mia["id"], {"title": "Mine now"}), "demo hunts are read-only")
assert ok(call("get_hunt", mia["id"]))["mine"] is False
alb = ok(call("album", mia["id"]))
assert alb["players"][0]["name"] == "Mia" and "cake" in alb["players"][0]["stickers"] and alb["photos"] > 20

# make a hunt
bad(call("create_hunt", {"title": " "}))
h1 = ok(call("create_hunt", {"title": "Ana's party hunt", "kind": "photo", "flavour": "chocolate", "time_limit": 15,
                             "win_style": "race", "start_mode": "together", "match_mode": "magic", "birthday_name": "Ana",
                             "birthday_age": "7", "flavour_bad": 1}))["hunt"]
assert h1["flavour"] == "chocolate" and h1["birthday_age"] == 7 and len(h1["code"]) == 6 and h1["status"] == "draft"
assert ok(call("create_hunt", {"title": "Weird", "flavour": "pickle", "time_limit": 7}))["hunt"]["flavour"] == "strawberry"
as_user(bob)
bad(call("update_hunt", h1["id"], {"title": "Bob was here"}))
bad(call("save_treasure", h1["id"], None, {"name": "x"}))
bad(call("get_hunt", h1["id"]))
as_user(ana)
ok(call("update_hunt", h1["id"], {"title": "Ana's 7th party"}))
bad(call("save_treasure", h1["id"], None, {"name": ""}))
bad(call("save_treasure", h1["id"], None, {"name": "Bad file"}, _anvil.BlobMedia("text/plain", b"z" * 500)))
t1 = ok(call("save_treasure", h1["id"], None, {"name": "Red teapot", "clue": "Kitchen"}, JPEG, sig(1), WEBM, 3.2))["treasure"]
assert t1["photo_key"] and t1["voice_key"] and t1["voice_seconds"] == 3.2 and t1["has_target"] and t1["position"] == 1
t2 = ok(call("save_treasure", h1["id"], None, {"name": "Teddy"}, JPEG, sig(2)))["treasure"]
t3 = ok(call("save_treasure", h1["id"], None, {"name": "Blue book"}, JPEG, sig(3)))["treasure"]
ok(call("move_treasure", t3["id"], -1))
assert [t["name"] for t in call("get_hunt", h1["id"])["treasures"]] == ["Red teapot", "Blue book", "Teddy"]
t2b = ok(call("save_treasure", h1["id"], t2["id"], {"name": "Teddy bear", "remove_voice": True}))["treasure"]
assert t2b["name"] == "Teddy bear" and t2b["photo_key"] == t2["photo_key"]
bad(call("add_library_tasks", h1["id"], ["nope"]))
ok(call("set_intro", h1["id"], WEBM, 4))
assert T.hunts.get_by_id(h1["id"])["intro_key"]

# photo + voice endpoints
r = anvil.server.ENDPOINTS["/photo/:key"](key=t1["photo_key"])
assert r.status == 200 and r.headers["Content-Type"] == "image/jpeg"
assert anvil.server.ENDPOINTS["/photo/:key"](key="nope").status == 404
assert anvil.server.ENDPOINTS["/voice/:key"](key=t1["voice_key"]).status == 200
assert anvil.server.ENDPOINTS["/voice/:key"](key=T.hunts.get_by_id(h1["id"])["intro_key"]).status == 200
assert M["Media"]._range(b"0123456789", "bytes=2-4") == (206, b"234", {"Content-Range": "bytes 2-4/10"})

# kids join
as_user(None)
bad(call("hunt_preview", "abc"))
bad(call("hunt_preview", "ZZZZZZ"))
pv = ok(call("hunt_preview", h1["code"].lower()))["hunt"]
assert pv["total"] == 3 and pv["status"] == "draft"
bad(call("join_hunt", h1["code"], "  "))
mia_tok = ok(call("join_hunt", h1["code"], "Mia", "unicorn", "pink"))["token"]
leo_tok = ok(call("join_hunt", h1["code"], "Leo", "dino", "mint"))["token"]
st = ok(call("play_state", mia_tok))
assert st["phase"] == "lobby" and st["player"]["topper"] == "star" and st["total"] == 3
bad(call("play_state", "x" * 24))
bad(call("submit_find", mia_tok, t1["id"], JPEG, sig(1)), "can't play before Start")
as_user(bob)
bad(call("start_hunt", h1["id"]))
as_user(ana)
ok(call("start_hunt", h1["id"]))
as_user(None)
st = ok(call("play_state", mia_tok))
assert st["phase"] == "hunt" and 890 <= st["seconds_left"] <= 900
bad(call("submit_find", mia_tok, t1["id"]), "a photo is needed")
r = ok(call("submit_find", mia_tok, t1["id"], JPEG, sig(1, 0.03)))
assert r["result"] == "found" and r["found"] == 1 and r["treasures"][0]["state"] == "found"
r = ok(call("submit_find", mia_tok, t3["id"], JPEG, sig(9)))
assert r["result"] in ("miss", "close") and r["found"] == 1 and not T.finds.search(treasure=T.treasures.get_by_id(t3["id"]))
r = ok(call("submit_find", mia_tok, t3["id"], JPEG, sig(9), True))
assert r["result"] == "review" and r["treasures"][1]["state"] == "review"
as_user(ana)
lb = ok(call("live_board", h1["id"]))
assert len(lb["review"]) == 1 and lb["players"][0]["name"] == "Mia" and lb["players"][0]["online"] and lb["total"] == 3
as_user(bob)
bad(call("review_find", lb["review"][0]["id"], True))
bad(call("live_board", h1["id"]))
as_user(ana)
assert ok(call("review_find", lb["review"][0]["id"], True))["status"] == "ok"
as_user(None)
r = ok(call("submit_find", leo_tok, t2["id"], JPEG, sig(2)))
assert r["result"] == "found" and r["found"] == 1, "race: Leo has his own cake"
r = ok(call("submit_find", mia_tok, t2["id"], JPEG, sig(2)))
assert r["phase"] == "done" and r["found"] == 3 and "cake" in r["player"]["stickers"] and "winner" in r["player"]["stickers"]
bad(call("submit_find", mia_tok, t2["id"], JPEG, sig(2)), "finished players can't send more")
as_user(ana)
lb = call("live_board", h1["id"])
assert lb["players"][0]["name"] == "Mia" and lb["players"][0]["winner"] and lb["hunt"]["status"] == "live"
ok(call("extend_hunt", h1["id"], 5))
alb = ok(call("album", h1["id"]))
assert alb["mine"] and len(alb["treasures"][0]["finds"]) == 1 and alb["players"][0]["rank"] == 1
as_user(bob)
bad(call("album", h1["id"]))
as_user(ana)
ok(call("end_hunt", h1["id"]))
as_user(None)
assert call("play_state", leo_tok)["phase"] == "done"
bad(call("join_hunt", h1["code"], "Late"), "finished hunts are closed")
as_user(ana)
assert ok(call("delete_kid_photos", h1["id"]))["deleted"] == 4
ok(call("reset_hunt", h1["id"]))
assert not T.players.search(hunt=T.hunts.get_by_id(h1["id"])) and call("get_hunt", h1["id"])["hunt"]["status"] == "draft"

# together + time running out + judge + tasks
h2 = ok(call("create_hunt", {"title": "Task party", "kind": "task", "time_limit": 5, "win_style": "together",
                             "start_mode": "together", "match_mode": "magic"}))["hunt"]
ok(call("add_library_tasks", h2["id"], ["m01", "f01"]))
tk = call("get_hunt", h2["id"])["treasures"]
assert tk[0]["kind"] == "task" and tk[0]["proof"] == "done" and tk[1]["proof"] == "photo"
assert tk[0]["lib_voice"] == "m01", "library tasks play their recorded voice"
ok(call("save_treasure", h2["id"], tk[1]["id"], {"kind": "task", "name": tk[1]["name"], "clue": tk[1]["clue"] + " Go!", "proof": "photo"}))
assert call("get_hunt", h2["id"])["treasures"][1]["lib_voice"] == "", "a reworded task falls back to the device voice"
ok(call("start_hunt", h2["id"]))
as_user(None)
a_tok = ok(call("join_hunt", h2["code"], "Ava", "flower", "berry"))["token"]
b_tok = ok(call("join_hunt", h2["code"], "Ben", "bolt", "blue"))["token"]
assert call("play_state", a_tok)["phase"] == "hunt", "late joiners of a running hunt play at once"
assert ok(call("submit_find", a_tok, tk[0]["id"]))["result"] == "found", "done-tasks need no photo"
st = call("play_state", b_tok)
assert st["found"] == 1 and st["treasures"][0]["by"] == "Ava", "together: one cake for everyone"
r = ok(call("submit_find", b_tok, tk[1]["id"], JPEG, None))
assert r["phase"] == "done" and "team" in r["player"]["stickers"]
assert T.hunts.get_by_id(h2["id"])["status"] == "finished"
as_user(ana)
ok(call("reset_hunt", h2["id"]))
ok(call("update_hunt", h2["id"], {"title": "Task party", "match_mode": "judge"}))
ok(call("start_hunt", h2["id"]))
as_user(None)
c_tok = ok(call("join_hunt", h2["code"], "Cy", "cat", "lemon"))["token"]
r = ok(call("submit_find", c_tok, tk[0]["id"]))
assert r["result"] == "review"
r = ok(call("grownup_check", c_tok, r["treasures"][0]["find_id"], True))
assert r["treasures"][0]["state"] == "found"
T.hunts.get_by_id(h2["id"])["ends_at"] = now - dt.timedelta(seconds=1)
assert call("play_state", c_tok)["phase"] == "done", "time running out finishes the hunt"

# self start
as_user(ana)
h3 = ok(call("create_hunt", {"title": "Solo hunt", "start_mode": "self", "time_limit": 10, "match_mode": "honour"}))["hunt"]
s1 = ok(call("save_treasure", h3["id"], None, {"name": "Sock"}))["treasure"]
as_user(None)
s_tok = ok(call("join_hunt", h3["code"], "Sol", "moon", "orange"))["token"]
assert call("play_state", s_tok)["phase"] == "ready"
st = ok(call("go", s_tok))
assert st["phase"] == "hunt" and st["seconds_left"] >= 590 and T.hunts.get_by_id(h3["id"])["status"] == "live"
assert ok(call("submit_find", s_tok, s1["id"], JPEG, None))["phase"] == "done", "honour: any photo counts"
as_user(ana)
ok(call("remove_player", T.players.get(token=s_tok).get_id()))
as_user(None)
bad(call("play_state", s_tok))

# copy an example, delete
as_user(bob)
cp = ok(call("copy_hunt", mia["id"]))["hunt"]
assert cp["title"] == "Mia's 6th Birthday Hunt" and cp["counts"]["treasures"] == 8 and not cp["demo"] and cp["code"] != mia["code"]
assert call("get_hunt", cp["id"])["treasures"][0]["art"].endswith("demo-teapot.svg")
bad(call("delete_hunt", h1["id"]))
as_user(ana)
ok(call("delete_hunt", h1["id"]))
assert T.hunts.get_by_id(h1["id"]) is None and not T.treasures.search(name="Red teapot")

# the demo try-me hunt: any photo counts, nothing kept
as_user(None)
try_tok = ok(call("join_hunt", "cake42", "Visitor", "star", "pink"))["token"]
st = ok(call("go", try_tok))
r = ok(call("submit_find", try_tok, st["treasures"][0]["id"], JPEG, sig(5)))
assert r["result"] == "found" and T.finds.search(player=T.players.get(token=try_tok))[0]["photo"] is None

# library tasks carry their recorded voice, unless the grown-up reworded them
G = M["Game"]
assert G.bingo_cols(4) == 2 and G.bingo_cols(9) == 3 and G.bingo_cols(12) == 4
assert len(G.bingo_lines(9)) == 8 and len(G.bingo_lines(4)) == 6 and len(G.bingo_lines(6)) == 5
assert G.bingo_done(9, [0, 1, 2]) == [[0, 1, 2]] and G.bingo_done(9, [0, 4, 8]) == [[0, 4, 8]] and G.bingo_done(9, [0, 1, 5]) == []
assert all(max(line) < 7 for line in G.bingo_lines(7)), "lines never point past the last picture"

# photo bingo (demo BINGO9): a card of 9, a row is a BINGO, the bingo sticker
as_user(None)
b_tok2 = ok(call("join_hunt", "bingo9", "Little One", "heart", "pink"))["token"]
st = ok(call("go", b_tok2))
assert st["bingo"]["cols"] == 3 and st["bingo"]["count"] == 0 and st["total"] == 9 and st["hunt"]["kind"] == "bingo"
for i in range(3):
    st = ok(call("submit_find", b_tok2, st["treasures"][i]["id"], JPEG, sig(7)))
assert st["bingo"]["count"] == 1 and st["bingo"]["lines"] == [[0, 1, 2]] and st["phase"] == "hunt"
for i in range(3, 9):
    st = ok(call("submit_find", b_tok2, st["treasures"][i]["id"], JPEG, sig(7)))
assert st["phase"] == "done" and st["bingo"]["count"] == 8 and "bingo" in st["player"]["stickers"], st["player"]["stickers"]
assert call("play_state", b_tok2)["treasures"][0]["lib_voice"] == "", "finds have no library voice"

# family + Kids' corner
as_user(ana)
bad(call("add_kid", " "))
kid = ok(call("add_kid", "Mimi", "heart", "pink"))["kid"]
assert kid["token"] and kid["hunts"] == 0
as_user(bob)
bad(call("update_kid", kid["id"], "Bob", "star", "pink"))
as_user(None)
kc = ok(call("kid_corner", kid["token"]))
assert kc["kid"]["name"] == "Mimi" and kc["hunts"] == [] and "token" not in kc["kid"]
k_tok = ok(call("kid_join", kid["token"], h3["code"]))["token"]
assert ok(call("kid_join", kid["token"], h3["code"]))["token"] == k_tok, "joining twice carries on the same game"
assert len(call("kid_corner", kid["token"])["hunts"]) == 1
bad(call("kid_join", kid["token"], "ZZZZZZ"))
as_user(ana)
new_tok = ok(call("new_kid_link", kid["id"]))["kid"]["token"]
as_user(None)
bad(call("kid_corner", kid["token"]), "the old link stops working")
ok(call("kid_corner", new_tok))
as_user(ana)
assert len(call("get_hq")["kids"]) == 1
ok(call("update_kid", kid["id"], "Mimi B", "crown", "blue"))
ok(call("delete_kid", kid["id"]))
assert T.players.get(token=k_tok)["kid"] is None

# admin + demo data
as_user(admin)
ov = call("admin_overview")
assert ov["hunts"] >= 3 and ov["demo"]["state"] == "loaded"
ok(call("demo_remove"))
assert M["DemoData"].state() == "removed" and not T.hunts.search(is_demo=True) and not T.players.get(token=try_tok)
assert not T.users.search(is_demo=True) and T.hunts.get_by_id(cp["id"]) is not None, "removing demo data keeps real hunts"
as_user(ana)
assert call("get_hq")["examples"] == [] and M["DemoData"].state() == "removed", "removed demo data doesn't come back"
as_user(admin)
ok(call("demo_load"))
ok(call("demo_load"))
assert len(T.hunts.search(is_demo=True)) == 5 and T.hunts.get(code="CAKE42") is not None, "reloading replaces the demo"

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup" and call("legal_state")["accepted_version"] == st["version"]

# ---------------------------------------------------------------------------------- schema check (App Board): names only, never data
r = anvil.server.ENDPOINTS["/schema-check"](tables="users, hunts,no_such_table")
json.dumps(r)
assert "email" in r["tables"]["users"] and "code" in r["tables"]["hunts"] and r["tables"]["no_such_table"] is None, r

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"get_me", "submit_feedback", "legal_state", "legal_accept", "task_library", "hunt_preview", "join_hunt",
          "play_state", "go", "submit_find", "grownup_check", "kid_corner", "kid_join"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
