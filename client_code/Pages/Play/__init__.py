import anvil.js
import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import PlayTemplate
from ... import ph, router, state


def _ordinal(n):
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


class Play(PlayTemplate):
    """#play/<token>, the kids' screen (no header or footer). Phases from the server:
    lobby (wait for the grown-up's Start), ready (press Go: your own clock), hunt (the cake + a tile per treasure;
    a tile opens Dialogs/Find), done (blow out the candles, stickers, results). Asks the server every 3 seconds
    and counts the clock down in between."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.token = args[0] if args else ""
        self.st: dict = {}
        self.phase = ""
        self._poll = 0
        self._shown = False
        self._tick = 0
        self._left = -1
        self._busy = False
        self._celebrated = False
        self._tiles_sig = ""
        self._bingos = -1   # photo bingo: lines already celebrated (-1 = not drawn yet)
        self.tiles_panel.add_event_handler("x-open", self._open)
        self._level = anvil.js.report_exceptions(self._on_level)
        self._blown_cb = anvil.js.report_exceptions(self._blown)
        r: dict = {"ok": False, "error": "This link has no game in it."}
        if self.token:
            r = anvil.server.call("play_state", self.token)
        if not r.get("ok"):
            self._gone(r.get("error") or "")
            return
        self.gone_box.visible = False
        self._draw(r, True)
        self._mute_draw()

    def _gone(self, msg):
        self.game_box.visible = False
        self.gone_box.visible = True
        self.gone_text.text = msg + " Ask a grown-up for the hunt's code."
        ph.forget_game(token=self.token)

    # ---- polling and the clock
    @handle("", "show")
    def form_show(self, **event_args):
        self._shown = True
        if self.st and not self._poll:
            self._poll = window.setInterval(self._refresh, 3000)
            self._tick = window.setInterval(self._count, 1000)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._shown = False
        if self._poll:
            window.clearInterval(self._poll)
            window.clearInterval(self._tick)
            self._poll = self._tick = 0
        window.PH.blowStop()

    def _refresh(self):
        if self._busy or not self._shown:
            return
        try:
            r = anvil.server.call_s("play_state", self.token)
        except Exception:
            return
        if r.get("ok"):
            self._draw(r)
        else:
            self._gone(r.get("error") or "")

    def _count(self):
        if self.phase != "hunt" or self._left < 0:
            return
        if self._left > 0:
            self._left -= 1
        self.clock.text = ph.clock(self._left)
        self.clock.role = ["play-clock"] + (["hurry"] if self._left <= 30 else [])
        if 0 < self._left <= 5:
            ph.sfx("tick")
        if self._left == 0:
            self._refresh()

    # ---- drawing
    def _draw(self, r, first=False):
        self.st = r
        p, h = r["player"], r["hunt"]
        phase = r["phase"]
        self.me_topper.topper, self.me_topper.colour = p["topper"], p["colour"]
        self.me_name.text = p["name"]
        self.count.text = "%d of %d" % (r["found"], r["total"])
        left = r.get("seconds_left")
        if left is not None and phase == "hunt":
            self._left = left
            self.clock.text = ph.clock(left)
            self.clock.visible = True
        else:
            self._left = -1
            self.clock.visible = False
        self.cake.flavour, self.cake.total = h["flavour"], r["total"]
        self.cake.lit = r["found"]
        together = h["win_style"] == "together"
        self.intro_voice.voice_key = h.get("intro_key") or ""
        self.intro_voice.text = h.get("message") or ""
        self.intro_voice.visible = phase in ("lobby", "ready") and bool(h.get("intro_key") or h.get("message"))
        self.go_button.visible = phase == "ready"
        self.blow_button.visible = self.tap_button.visible = False
        self.level_box.visible = False
        self.tiles_box.visible = phase == "hunt"
        self.stickers_box.visible = phase == "done"
        self.after_box.visible = phase == "done"
        team = [dict(t, _show_rank=(phase == "done" and not together), _total=r["total"] if not together else 0,
                     _show_found=phase != "lobby") for t in r["team"]]
        self.team_panel.items = team
        self.team_box.visible = len(team) > 1 or phase == "lobby"
        if phase == "lobby":
            self.headline.text = h["title"]
            self.subline.text = "Waiting for the grown-up to press Start..."
            self.team_title.text = "Who's here"
        elif phase == "ready":
            self.headline.text = h["title"]
            self.subline.text = "Find all %d %s! When you press Go, your clock starts." % (
                r["total"], "treasures" if h["kind"] != "task" else "tasks") if h["time_limit"] else "Find all %d! Press Go when you're ready." % r["total"]
            self.team_title.text = "Also playing"
        elif phase == "hunt" and r.get("bingo"):
            n = r["bingo"]["count"]
            self.headline.text = "Photo bingo!" if not n else ("BINGO!" if n == 1 else "%d BINGOs!" % n)
            self.subline.text = "Find a whole row for a BINGO. Find them all to light every candle!"
            self.team_title.text = "Team" if together else "Also playing"
            self._tiles(r)
        elif phase == "hunt":
            self.headline.text = "Find them all!" if h["kind"] != "task" else "Do them all!"
            self.subline.text = ("Every find lights a candle on the cake. %s" % ("Team cake: everyone's finds count!" if together else "")).strip()
            self.team_title.text = "Team" if together else "The race"
            self._tiles(r)
        else:
            self._done(r, together)
        if phase != self.phase:
            old = self.phase
            self.phase = phase
            if not first and old in ("lobby", "ready") and phase == "hunt":
                self._start_show(h)
            elif first and phase == "hunt" and r["found"] == 0:
                pass
        if first:
            self.phase = phase

    def _tiles(self, r):
        sig = "|".join("%s:%s:%s" % (t["id"], t["state"], t.get("by") or "") for t in r["treasures"])
        if sig != self._tiles_sig:
            key = state.focus_key()
            self._tiles_sig = sig
            b = r.get("bingo")
            if b:
                cells = set(i for line in b["lines"] for i in line)
                self.tiles_panel.role = ["play-grid", "play-bingo", "bingo-c%d" % b["cols"]]
                self.tiles_panel.items = [dict(t, _bingo=True, _line=i in cells) for i, t in enumerate(r["treasures"])]
                if 0 <= self._bingos < b["count"]:
                    window.PH.banner("BINGO!")
                self._bingos = b["count"]
            else:
                self.tiles_panel.items = r["treasures"]
            if key:
                state.refocus(self.tiles_panel, key)

    def _start_show(self, h):
        """3, 2, 1, Go! then the welcome message."""
        def after():
            if h.get("intro_key") or h.get("message"):
                ph.say_clue(h.get("intro_key"), h.get("message"))
        window.PH.countdown(3, anvil.js.report_exceptions(after))

    def _done(self, r, together):
        p = r["player"]
        me = next((t for t in r["team"] if t.get("me")), {})
        full = r["found"] >= r["total"] > 0
        if together:
            self.headline.text = "Team cake complete!" if full else "Your team lit %d candles!" % r["found"]
        elif full and me.get("rank") == 1:
            self.headline.text = "You lit every candle first!"
        elif full and r.get("bingo"):
            self.headline.text = "Full card! Every candle is lit!"
        elif full:
            self.headline.text = "You lit every candle!"
        else:
            self.headline.text = "Time's up! You lit %s!" % state.plural(r["found"], "candle")
        rank = me.get("rank")
        if not together and rank and len(r["team"]) > 1:
            self.subline.text = "You came %s out of %d. Now blow out the candles!" % (_ordinal(rank), len(r["team"]))
        else:
            self.subline.text = "Now blow out the candles and make a wish!"
        self.team_title.text = "Results"
        self.stickers_panel.items = [{"id": s, "size": 72} for s in (p.get("stickers") or [])]
        if not self.cake.blown:
            self.blow_button.visible = r["found"] > 0
            self.tap_button.visible = False
        corners = [k for k in ph.kid_corners() if k.get("name") == p["name"]] if p.get("kid") else []
        self.corner_link.visible = bool(corners)
        if corners:
            state.set_attr(self.corner_link, "href", router.href("kid", corners[0]["token"]))
        if not self._celebrated:
            self._celebrated = True
            ph.sfx("tada")
            ph.confetti()

    # ---- the kid opens a treasure
    def _open(self, treasure, **event_args):
        if self.phase != "hunt":
            return
        from ...Dialogs.Find import Find
        self._busy = True
        try:
            r = alert(Find(treasure=treasure, hunt=self.st["hunt"], token=self.token, total=self.st["total"]),
                      large=True, buttons=[], role="app-dialog")
        finally:
            self._busy = False
        if r and r.get("ok"):
            self._draw(r)
        else:
            self._refresh()

    @handle("go_button", "click")
    def go_button_click(self, **event_args):
        r = state.call("go", self.token)
        if r:
            self.phase = "ready"
            self._draw(r)
            self.phase = r["phase"]
            self._start_show(r["hunt"])

    # ---- blowing out the candles
    @handle("blow_button", "click")
    def blow_button_click(self, **event_args):
        self.blow_button.visible = False
        self.tap_button.visible = True
        self.level_box.visible = True
        self.subline.text = "Blow on the tablet, hard!"
        try:
            window.PH.blowStart(self._level, self._blown_cb)
        except Exception:
            self.level_box.visible = False
            self.subline.text = "Tap the button to blow them out!"

    def _on_level(self, level):
        self.dom_nodes["level"].style.transform = "scaleX(%.2f)" % max(0.03, float(level))

    @handle("tap_button", "click")
    def tap_button_click(self, **event_args):
        window.PH.blowStop()
        self._blown()

    def _blown(self):
        self.cake.blown = True
        self.tap_button.visible = self.blow_button.visible = False
        self.level_box.visible = False
        self.subline.text = "Hooray! Happy birthday%s!" % ((" " + self.st["hunt"]["birthday_name"]) if self.st["hunt"].get("birthday_name") else "")
        ph.sfx("whoosh")
        window.setTimeout(lambda: (ph.sfx("tada"), ph.confetti()), 500)

    # ---- sound on / off
    @handle("mute_button", "click")
    def mute_button_click(self, **event_args):
        ph.set_muted(not ph.muted())
        self._mute_draw()

    def _mute_draw(self):
        m = ph.muted()
        self.mute_button.text = "Sound off" if m else "Sound on"
        self.mute_button.role = ["btn", "btn-icon", "btn-sm", "ic-mute" if m else "ic-volume", "play-mute"]
        state.set_control_attr(self.mute_button, "aria-pressed", "true" if m else "false")
