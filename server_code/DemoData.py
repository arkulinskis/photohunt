"""Demo content, so the app never looks empty. Loaded automatically the first time anyone opens Party HQ
(ensure_loaded), removed or reloaded from Admin -> Demo data. Removing it is remembered: it doesn't come back.

The demo family (a demo user that can't sign in) owns four example hunts, drawn with the cartoon objects in
theme/assets/demo-*.svg instead of photos:
  - Mia's 6th Birthday Hunt: a finished photo race with five players, so the album and results have something to show
    (incl. a very long team name and a player with a single find: the design kit's worst cases);
  - Try-me Hunt, code CAKE42: open to anyone from the landing page. Any photo counts and visitors' photos are never
    stored (Play.py); visitor players are tidied away after a day;
  - Leo's Dino Party: a task party waiting in the lobby;
  - Grandpa's Riddle Hunt: a voice hunt with spoken riddles (read by the device's voice: demo hunts have no recordings).
Every demo row has is_demo=True; remove() deletes demo hunts with everything in them (visitors' plays too).
"""
import datetime as dt

from anvil.tables import app_tables

from . import common as C
from . import Game, TaskLibrary

DEMO_EMAIL = "demo.family@example.com"
TRY_CODE = "CAKE42"
DEMO_TABLES = ["finds", "players", "treasures", "hunts", "kids"]

MIA_TREASURES = [
    ("teapot", "The spotty teapot", "It's in the kitchen, near the kettle."),
    ("teddy", "Mr. Buttons the bear", "He naps on a bed."),
    ("duck", "The yellow rubber duck", "Splish splash! Where do ducks swim in a house?"),
    ("ball", "The stripy beach ball", ""),
    ("book", "The big dinosaur book", "On a shelf with lots of friends."),
    ("sock", "A rainbow sock", "Look where clean clothes live."),
    ("banana", "A banana", "Yellow, curvy and yummy."),
    ("plant", "The cactus in a pot", "It's prickly! Don't touch, just snap."),
]
MIA_PLAYERS = [  # name, topper, colour, how many of the treasures they found (in order)
    ("Mia", "star", "pink", 8),
    ("Leo", "dino", "mint", 7),
    ("Zoe & Sam", "rocket", "blue", 6),
    ("Noah", "crown", "lemon", 4),
    ("Team Maximilian-Alexander-Geburtstagskuchen", "fish", "orange", 1),
]
TRY_TREASURES = [
    ("teapot", "A teapot or a cup", "Something you drink from."),
    ("duck", "Something yellow", "A duck, a banana, a sock... anything yellow!"),
    ("ball", "A ball", "Round and bouncy."),
    ("sock", "A sock", "Your own feet count!"),
    ("banana", "A piece of fruit", "From the fruit bowl."),
]
RIDDLES = [
    ("teapot", "The teapot", "I have a spout and a handle, and I love tea parties. What am I?"),
    ("clock", "The clock", "I have hands but no fingers, and a face but no nose. What am I?"),
    ("toothbrush", "A toothbrush", "I help you smile at night and in the morning. I live near the sink."),
    ("plant", "The plant", "I drink water but never get up for a glass. I'm green!"),
]
LEO_TASKS = ["m01", "s01", "f02", "k02", "p01", "h02"]


def state():
    return C.get_setting("demo", "never")  # "never" | "loaded" | "removed"


def ensure_loaded():
    """Call from the app's main data callables: loads the demo once, unless an admin removed it."""
    if state() == "never":
        load()


def _hunt(owner, code, created, **kw):
    base: dict = dict(owner=owner, code=code or Game.new_code(), created=created, updated=created, is_demo=True,
                birthday_age=0, birthday_name="", message="", time_limit=15, win_style="race", start_mode="together",
                match_mode="magic", strictness="normal", status="draft")
    base.update(kw)
    return app_tables.hunts.add_row(**base)


def _treasures(h, rows, created):
    out = []
    for i, (art, name, clue) in enumerate(rows):
        out.append(app_tables.treasures.add_row(hunt=h, position=i + 1, kind="find", name=name, clue=clue, demo_art=art,
                                                proof="photo", timer=0, created=created, is_demo=True))
    return out


def load():
    remove(remember=False)
    now = C.now()
    fam = app_tables.users.get(email=DEMO_EMAIL) or app_tables.users.add_row(email=DEMO_EMAIL, enabled=False)
    fam.update(display_name="The Demo Family", is_demo=True, signed_up=now - dt.timedelta(days=40))
    kid_rows = {}
    for name, topper, colour in (("Mia", "star", "pink"), ("Leo", "dino", "mint")):
        kid_rows[name] = app_tables.kids.add_row(owner=fam, name=name, topper=topper, colour=colour, token=Game.token(),
                                                 created=now - dt.timedelta(days=30), is_demo=True)

    # 1. Mia's party: finished photo race
    t0 = now - dt.timedelta(days=3, hours=2)
    mia = _hunt(fam, None, t0 - dt.timedelta(days=1), title="Mia's 6th Birthday Hunt", kind="photo", birthday_name="Mia",
                birthday_age=6, flavour="strawberry", time_limit=15, status="finished", started=t0,
                ends_at=t0 + dt.timedelta(minutes=15), finished=t0 + dt.timedelta(minutes=13),
                message="Happy birthday Mia! Find all eight treasures to light the candles.")
    ts = _treasures(mia, MIA_TREASURES, t0 - dt.timedelta(days=1))
    for j, (name, topper, colour, n) in enumerate(MIA_PLAYERS):
        p = app_tables.players.add_row(hunt=mia, kid=kid_rows.get(name), name=name, topper=topper, colour=colour,
                                       token=Game.token(), joined=t0 - dt.timedelta(minutes=5), started=t0,
                                       last_seen=t0 + dt.timedelta(minutes=13), stickers=[], is_demo=True)
        for i in range(n):
            app_tables.finds.add_row(hunt=mia, player=p, treasure=ts[i], demo_art=ts[i]["demo_art"],
                                     score=round(0.93 - 0.03 * ((i + j) % 4), 2), status="ok",
                                     created=t0 + dt.timedelta(seconds=40 + 75 * i + 23 * j), checked=None, is_demo=True)
        if n == len(ts):
            p["finished"] = t0 + dt.timedelta(seconds=40 + 75 * (n - 1) + 23 * j)
        else:
            p["finished"] = t0 + dt.timedelta(minutes=13)
    Game.award(mia, Game.players(mia))

    # 2. Try-me hunt: anyone can play from the landing page
    _try = _hunt(fam, TRY_CODE, now - dt.timedelta(days=20), title="Try-me Hunt", kind="photo", flavour="lemon",
                 time_limit=10, start_mode="self", match_mode="honour", status="live", started=now - dt.timedelta(days=20),
                 message="This is a demo: any photo counts, and your photos aren't kept. Have fun!")
    _treasures(_try, TRY_TREASURES, now - dt.timedelta(days=20))

    # 3. Leo's task party, waiting in the lobby
    leo = _hunt(fam, None, now - dt.timedelta(days=1), title="Leo's Dino Party", kind="task", birthday_name="Leo",
                birthday_age=5, flavour="mint", time_limit=20, win_style="together", match_mode="judge",
                message="Roar! Do all the dino tasks together to light Leo's candles.")
    for i, tid in enumerate(LEO_TASKS):
        task = TaskLibrary.BY_ID[tid]
        app_tables.treasures.add_row(hunt=leo, position=i + 1, kind="task", name=task["text"][:60], clue=task["text"],
                                     task_id=tid, timer=task["timer"], proof=task["proof"], created=now, is_demo=True)
    for name, topper, colour in (("Leo", "dino", "mint"), ("Ava", "flower", "berry")):
        app_tables.players.add_row(hunt=leo, kid=kid_rows.get(name), name=name, topper=topper, colour=colour,
                                   token=Game.token(), joined=now - dt.timedelta(minutes=3), last_seen=now - dt.timedelta(hours=2),
                                   stickers=[], is_demo=True)

    # 4. Grandpa's riddles: a voice hunt (the device reads the riddles aloud)
    gp = _hunt(fam, None, now - dt.timedelta(days=8), title="Grandpa's Riddle Hunt", kind="voice", flavour="blueberry",
               time_limit=0, start_mode="self", strictness="easy",
               message="Listen to each riddle, then find the answer and snap it.")
    _treasures(gp, RIDDLES, now - dt.timedelta(days=8))
    C.set_setting("demo", "loaded")
    return counts()


def remove(remember=True):
    for h in app_tables.hunts.search(is_demo=True):
        Game.delete_hunt_rows(h)
    for name in DEMO_TABLES:
        for r in getattr(app_tables, name).search(is_demo=True):
            r.delete()
    for u in app_tables.users.search(is_demo=True):
        u.delete()
    if remember:
        C.set_setting("demo", "removed")
    return counts()


def counts():
    out = {"users": len(app_tables.users.search(is_demo=True))}
    for name in DEMO_TABLES:
        out[name] = len(getattr(app_tables, name).search(is_demo=True))
    return out
