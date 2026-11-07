import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import LiveTemplate
from ... import ph, router, state

STATUS = {"draft": ("Waiting to start", "badge-warn"), "live": ("Hunt on!", "badge-good"), "finished": ("Finished", "badge")}


class Live(LiveTemplate):
    """#live/<id>, the grown-up's live board: start / extend / end, the clock, photos to check, players and their
    candles, the join QR for latecomers, and what's happening. Asks the server again every 3 seconds."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hid = args[0] if args else ""
        self.h: dict = {}
        self._poll = 0
        self._shown = False
        self._tick = 0
        self._left = -1
        self._last_review = 0
        state.heading(self.title, 1)
        self.review_panel.add_event_handler("x-review", self._review)
        self.players_panel.add_event_handler("x-remove", self._remove)
        r: dict = {"ok": False}
        if self.hid:
            r = anvil.server.call("live_board", self.hid)
        self.gone.visible = not r.get("ok")
        self.main.visible = bool(r.get("ok"))
        if r.get("ok"):
            self._draw(r)

    @handle("", "show")
    def form_show(self, **event_args):
        self._shown = True
        if self.hid and not self._poll:
            self._poll = window.setInterval(self._refresh, 3000)
            self._tick = window.setInterval(self._count, 1000)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._shown = False
        if self._poll:
            window.clearInterval(self._poll)
            window.clearInterval(self._tick)
            self._poll = self._tick = 0

    def _refresh(self):
        if not self._shown:
            return
        try:
            r = anvil.server.call_s("live_board", self.hid)
        except Exception:
            return
        if r.get("ok"):
            self._draw(r)

    def _count(self):
        if self._left > 0 and self.h.get("status") == "live":
            self._left -= 1
            self.clock.text = ph.clock(self._left)
            if self._left == 0:
                self._refresh()

    def _draw(self, r):
        h = self.h = r["hunt"]
        self.title.text = h["title"]
        label, role = STATUS.get(h["status"], STATUS["draft"])
        self.status.text, self.status.role = label, ["badge", role]
        ps = r["players"]
        self.players_count.text = state.plural(len(ps), "player")
        left = r.get("seconds_left")
        self._left = left if left is not None else -1
        together_clock = h["start_mode"] == "together"
        if h["status"] == "finished":
            self.clock.text, self.clock_sub.text = "Done", "The hunt is over"
        elif left is not None:
            self.clock.text, self.clock_sub.text = ph.clock(left), "left"
        elif h["status"] == "draft" and together_clock:
            self.clock.text = ph.clock(h["time_limit"] * 60) if h["time_limit"] else "Ready"
            self.clock_sub.text = "starts when you press Start" if h["time_limit"] else "no time limit"
        else:
            self.clock.text = "Go!" if h["status"] == "live" else "Ready"
            self.clock_sub.text = "each kid has their own clock" if (not together_clock and h["time_limit"]) else "no time limit"
        draft, live, done = h["status"] == "draft", h["status"] == "live", h["status"] == "finished"
        self.start_button.visible = draft and together_clock
        self.extend_button.visible = live and bool(h["time_limit"])
        self.end_button.visible = live or (draft and not together_clock and bool(ps))
        self.reset_button.visible = done
        if draft and together_clock:
            self.hint.text = "Kids who scan the code wait in the lobby. Press Start when everyone is ready."
        elif not together_clock and not done:
            self.hint.text = "Each kid's clock starts when they press Go on their tablet."
        elif done:
            self.hint.text = "Open the party album for everyone's photos and printable certificates."
        else:
            self.hint.text = ""
        self.hint.visible = bool(self.hint.text)
        state.set_attr(self.back_link, "href", router.href("hunt", h["id"]))
        state.set_attr(self.album_link, "href", router.href("album", h["id"]))
        together = h["win_style"] == "together"
        self.team_box.visible = together
        if together:
            self.team_cake.flavour, self.team_cake.total, self.team_cake.lit = h["flavour"], r["total"], len(r["team"])
            self.team_text.text = "%d of %d candles lit together" % (len(r["team"]), r["total"])
        key = state.focus_key()
        self.players_panel.items = [dict(p, _mine=True, _together=together, total=r["total"], _status=h["status"]) for p in ps]
        self.no_players.visible = not ps
        self.review_panel.items = r["review"]
        self.review_count.text = str(len(r["review"]))
        self.review_count.visible = bool(r["review"])
        self.no_review.visible = not r["review"]
        if len(r["review"]) > self._last_review:
            ph.sfx("pop")
        self._last_review = len(r["review"])
        self.feed_panel.items = r["feed"]
        self.no_feed.visible = not r["feed"]
        if self.qr.text != ph.join_url(h["code"]):
            self.qr.text = ph.join_url(h["code"])
        self.code.text = h["code"]
        if key:
            state.refocus(self.main, key)

    @handle("start_button", "click")
    def start_button_click(self, **event_args):
        r = state.call("start_hunt", self.hid)
        if r:
            ph.sfx("go")
            state.toast("The hunt is on!", "ok")
            self._refresh()

    @handle("extend_button", "click")
    def extend_button_click(self, **event_args):
        if state.call("extend_hunt", self.hid, 5):
            state.toast("5 more minutes", "ok")
            self._refresh()

    @handle("end_button", "click")
    def end_button_click(self, **event_args):
        if confirm("Everyone's results are final and the kids see their cakes.", title="End the hunt now?",
                   buttons=[("Keep going", False), ("End the hunt", True)]):
            if state.call("end_hunt", self.hid):
                ph.sfx("tada")
                self._refresh()

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        if confirm("Players and their finds are cleared, the treasures stay. Kids scan the same code again.",
                   title="Play again?", buttons=[("Cancel", False), ("Play again", True)]):
            if state.call("reset_hunt", self.hid):
                self._refresh()

    def _review(self, find, approve, **event_args):
        if state.call("review_find", find["id"], approve) is not None:
            if approve:
                ph.sfx("ding")
            self._refresh()

    def _remove(self, player, **event_args):
        if confirm("Their finds are removed too.", title="Remove %s?" % player["name"],
                   buttons=[("Cancel", False), ("Remove", True)]):
            if state.call("remove_player", player["id"]) is not None:
                self._refresh()
