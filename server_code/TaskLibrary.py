"""The library of 100 child-friendly party tasks a grown-up can drop into a hunt.

Each task: id (stable, stored on treasures as task_id), cat (category key), text (what the child hears or reads),
timer (seconds of countdown shown while doing it, 0 = none) and proof ("photo" = snap a picture to show it,
"done" = a grown-up-free "I did it!" tap). Kept indoors-safe: no climbing, no running on stairs, nothing hot or sharp.
Change wording here freely; never reuse an id for a different task (old hunts keep their copied text anyway).
"""
import anvil.server

CATEGORIES = [
    ("move", "Wiggle and move"),
    ("silly", "Super silly"),
    ("find", "Seek and snap"),
    ("make", "Make and build"),
    ("kind", "Kind hearts"),
    ("brainy", "Brain teasers"),
    ("party", "Party time"),
]

_RAW = {
    "move": [
        ("Do 10 jumping jacks!", 0, "done"),
        ("Hop on one foot while you count to 10.", 10, "done"),
        ("Walk like a crab from one side of the room to the other.", 0, "done"),
        ("Do 5 big frog jumps.", 0, "done"),
        ("Spin around 3 times, then try to stand like a statue.", 0, "done"),
        ("Tiptoe across the room without making a sound.", 0, "done"),
        ("Touch your toes, then reach for the sky. Do it 5 times.", 0, "done"),
        ("Dance like nobody is watching until the timer ends!", 20, "done"),
        ("Balance a soft toy on your head and walk 10 steps.", 0, "photo"),
        ("Do a bear crawl to the door and back.", 0, "done"),
        ("Pretend to swim like a fish for 15 seconds.", 15, "done"),
        ("Stand like a flamingo on one leg. Can you last 15 seconds?", 15, "done"),
        ("March like a toy soldier and count to 20.", 0, "done"),
        ("Roll a ball (or a sock ball) to someone and back 5 times.", 0, "done"),
        ("Wiggle every part of your body, from your head to your toes!", 15, "done"),
        ("Jump as high as you can 5 times. Say a number on every jump.", 0, "done"),
        ("Slither like a snake across the floor.", 0, "done"),
        ("Stretch like a sleepy cat, then pounce!", 0, "done"),
        ("Do 3 forward rolls on something soft (ask a grown-up where).", 0, "done"),
        ("Freeze dance: dance, and freeze when the timer ends!", 20, "done"),
    ],
    "silly": [
        ("Make the funniest face you can and take a picture of it.", 0, "photo"),
        ("Talk like a robot until the timer ends.", 15, "done"),
        ("Give a grown-up a silly new name and say it 3 times.", 0, "done"),
        ("Moo like a cow, quack like a duck and roar like a lion!", 0, "done"),
        ("Walk backwards to the nearest door.", 0, "done"),
        ("Put a sock on your hand and make it say hello.", 0, "photo"),
        ("Laugh like a giant: ho ho ho!", 0, "done"),
        ("Pretend the floor is lava and get to the sofa!", 0, "done"),
        ("Tell a joke to someone and make them smile.", 0, "done"),
        ("Do your best penguin waddle.", 0, "done"),
        ("Say 'birthday cake' 5 times really fast!", 0, "done"),
        ("Wear something on your head that isn't a hat and snap a picture.", 0, "photo"),
        ("Pretend you are a statue in a museum. Don't move!", 15, "done"),
        ("Sing a song in your silliest voice.", 0, "done"),
        ("Make an animal noise and let someone guess the animal.", 0, "done"),
    ],
    "find": [
        ("Find something round and take a picture of it.", 0, "photo"),
        ("Find something red and snap it.", 0, "photo"),
        ("Find something soft and fluffy.", 0, "photo"),
        ("Find something that starts with the letter B.", 0, "photo"),
        ("Find something smaller than your thumb.", 0, "photo"),
        ("Find something you can read.", 0, "photo"),
        ("Find something with stripes or spots.", 0, "photo"),
        ("Find something that makes a sound.", 0, "photo"),
        ("Find something green, like a leaf or a toy.", 0, "photo"),
        ("Find something shaped like a square.", 0, "photo"),
        ("Find a spoon.", 0, "photo"),
        ("Find something shiny.", 0, "photo"),
        ("Find a toy with wheels.", 0, "photo"),
        ("Find something yellow, like the sun.", 0, "photo"),
        ("Find something you wear on your feet.", 0, "photo"),
        ("Find a picture of an animal (in a book, on a cup, anywhere).", 0, "photo"),
        ("Find something that has a number on it.", 0, "photo"),
        ("Find something heavy (but not too heavy to hold).", 0, "photo"),
        ("Find something that smells nice. Ask before you sniff!", 0, "photo"),
        ("Find two things that are the same colour and snap them together.", 0, "photo"),
    ],
    "make": [
        ("Build a tower of 5 things and take a picture before it falls.", 0, "photo"),
        ("Draw a birthday cake with candles on it.", 60, "photo"),
        ("Make a smiley face out of things on the table.", 0, "photo"),
        ("Line up 5 toys from smallest to biggest.", 0, "photo"),
        ("Make a crown out of paper.", 0, "photo"),
        ("Build a little house for a toy.", 0, "photo"),
        ("Make a pattern with socks: one colour, then another.", 0, "photo"),
        ("Draw the birthday person as a superhero.", 60, "photo"),
        ("Make a snake out of things that are blue.", 0, "photo"),
        ("Make a letter from your name using toys or blocks.", 0, "photo"),
        ("Fold a paper airplane and fly it.", 0, "photo"),
        ("Make a rainbow from things you find: red, orange, yellow, green, blue.", 0, "photo"),
        ("Build a bridge for a toy car.", 0, "photo"),
        ("Draw your favourite animal wearing a party hat.", 60, "photo"),
        ("Make a cosy nest out of pillows (put them back after!).", 0, "photo"),
    ],
    "kind": [
        ("Give someone a big hug (if they want one).", 0, "done"),
        ("Tell the birthday person one thing you love about them.", 0, "done"),
        ("Help tidy up 5 things.", 0, "done"),
        ("Say thank you to a grown-up for the party.", 0, "done"),
        ("Draw a little card for someone and give it to them.", 60, "photo"),
        ("High-five everyone in the room!", 0, "done"),
        ("Share a toy with a friend.", 0, "done"),
        ("Give someone a compliment.", 0, "done"),
        ("Help a grown-up carry something light.", 0, "done"),
        ("Find a friend and do a secret handshake together.", 0, "done"),
    ],
    "brainy": [
        ("Count all the windows in the room.", 0, "done"),
        ("Say the alphabet as fast as you can.", 0, "done"),
        ("Name 5 animals that live in the sea.", 0, "done"),
        ("Count backwards from 10 and shout 'Blast off!'", 0, "done"),
        ("Name 3 things that are cold.", 0, "done"),
        ("How many candles are on a cake for a 6 year old? Hold up that many fingers.", 0, "done"),
        ("Name a fruit for every colour of the rainbow you can.", 0, "done"),
        ("Find 3 things that are taller than you.", 0, "photo"),
        ("Guess how many steps it is to the door, then walk it and count.", 0, "done"),
        ("Name 5 things you can find in a kitchen.", 0, "done"),
    ],
    "party": [
        ("Sing Happy Birthday to a toy.", 0, "done"),
        ("Blow up an imaginary balloon and let it fly around the room!", 0, "done"),
        ("Do your best party dance move and take a picture mid-move.", 0, "photo"),
        ("Wear a party hat (or make one) and snap a picture.", 0, "photo"),
        ("Pretend to blow out 10 candles, one at a time.", 0, "done"),
        ("Wrap a toy in a blanket like a present.", 0, "photo"),
        ("Make a wish and whisper it to a teddy.", 0, "done"),
        ("Clap the birthday person's age as loud as you can.", 0, "done"),
        ("Do a conga line around the room with everyone.", 20, "done"),
        ("Strike a pose like a pop star for the party photo!", 0, "photo"),
    ],
}

PREFIX = {"move": "m", "silly": "s", "find": "f", "make": "k", "kind": "h", "brainy": "b", "party": "p"}
TASKS: list = []
for _cat, _rows in _RAW.items():
    for _i, (_text, _timer, _proof) in enumerate(_rows):
        TASKS.append({"id": "%s%02d" % (PREFIX[_cat], _i + 1), "cat": _cat, "text": _text, "timer": _timer, "proof": _proof})
BY_ID: dict = {t["id"]: t for t in TASKS}
assert len(TASKS) == 100, len(TASKS)


# ---------------------------------------------------------------- ready-made packs ("Ready in a minute")
# One tap makes a task hunt from a pack: 8 library tasks picked for the kids' ages, no photos to take first.
AGES: list = [
    {"key": "little", "label": "Ages 3-5", "settings": {"win_style": "together", "start_mode": "together", "time_limit": 0,
                                                        "match_mode": "honour", "strictness": "easy"},
     "note": "one cake for everyone, no clock, every photo counts"},
    {"key": "middle", "label": "Ages 6-8", "settings": {"win_style": "race", "start_mode": "together", "time_limit": 15,
                                                        "match_mode": "honour", "strictness": "normal"},
     "note": "a race, 15 minutes"},
    {"key": "big", "label": "Ages 9-12", "settings": {"win_style": "race", "start_mode": "together", "time_limit": 10,
                                                      "match_mode": "honour", "strictness": "tricky"},
     "note": "a race, 10 minutes, the trickier tasks"},
]
PACKS: list = [
    {"key": "rainy", "title": "Rainy-day indoor mix", "icon": "balloon", "flavour": "blueberry",
     "text": "Seek, wiggle and giggle without leaving the house.",
     "message": "It's raining treasure! Find, wiggle and giggle your way round the house.",
     "ids": {"little": ["f02", "m04", "f03", "s04", "f13", "p01", "m15", "f15"],
             "middle": ["f01", "m12", "s01", "f07", "k01", "b04", "p03", "f12"],
             "big": ["f04", "k04", "b09", "f17", "k12", "s11", "m20", "f20"]}},
    {"key": "colours", "title": "Colour and shape hunt", "icon": "brush", "flavour": "lemon",
     "text": "Snap something red, something round, something shiny.",
     "message": "Rainbow detectives, go! Snap every colour and shape you can find.",
     "ids": {"little": ["f02", "f09", "f14", "f01", "f03", "f15", "f13", "f12"],
             "middle": ["f02", "f09", "f14", "f10", "f07", "f12", "f20", "k09"],
             "big": ["f04", "f10", "f20", "k12", "k09", "f17", "f05", "b07"]}},
    {"key": "wiggle", "title": "Wiggle party", "icon": "music", "flavour": "strawberry",
     "text": "Burn off the sugar: animal walks, freeze dance, a conga line.",
     "message": "Time to wiggle! Hop, crawl and dance to light the candles.",
     "ids": {"little": ["m04", "m11", "m17", "m15", "s10", "m13", "s04", "p02"],
             "middle": ["m01", "m02", "m12", "m08", "m03", "s08", "m20", "p09"],
             "big": ["m01", "m10", "m12", "m16", "m05", "s13", "m20", "p09"]}},
    {"key": "calm", "title": "Kind and calm", "icon": "heart", "flavour": "mint",
     "text": "Wind down before cake: kind deeds, cards and quiet tasks.",
     "message": "Kind hearts hunt! Every kind thing you do lights a candle.",
     "ids": {"little": ["h01", "h06", "p07", "m18", "h07", "f03", "p01", "h04"],
             "middle": ["h02", "h05", "h08", "h03", "m06", "k03", "s09", "h04"],
             "big": ["h02", "h05", "h10", "h08", "k08", "b01", "h09", "h04"]}},
    {"key": "brainy", "title": "Brainy builders", "icon": "bulb", "flavour": "chocolate",
     "text": "Counting, building and puzzling for clever kids.",
     "message": "Calling all clever clogs! Count, build and think to fill the cake.",
     "ids": {"little": ["b04", "f05", "k04", "f11", "b05", "f16", "k03", "b03"],
             "middle": ["b03", "b07", "b08", "k04", "k10", "f17", "b10", "k13"],
             "big": ["b02", "b06", "b08", "b09", "k10", "k12", "f04", "k11"]}},
]
PACKS_BY_KEY: dict = {p["key"]: p for p in PACKS}
AGES_BY_KEY: dict = {a["key"]: a for a in AGES}
for _p in PACKS:
    for _ids in _p["ids"].values():
        assert len(_ids) == len(set(_ids)) == 8 and all(i in BY_ID for i in _ids), _p["key"]


def packs_public():
    """The packs as the browser shows them (each age's task texts, so the card can say what's inside)."""
    return {"ages": [{"key": a["key"], "label": a["label"], "note": a["note"]} for a in AGES],
            "packs": [{"key": p["key"], "title": p["title"], "text": p["text"], "icon": p["icon"], "flavour": p["flavour"],
                       "tasks": {age: [BY_ID[i]["text"] for i in ids] for age, ids in p["ids"].items()}} for p in PACKS]}


@anvil.server.callable
def task_library():
    """The whole library (public: the Tasks page is open to visitors too), plus the ready-made packs."""
    return {"categories": [{"key": k, "label": label, "count": len(_RAW[k])} for k, label in CATEGORIES], "tasks": TASKS,
            "packs": packs_public()}
