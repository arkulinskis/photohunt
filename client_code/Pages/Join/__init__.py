import random

import anvil.server
from anvil import *

from ._anvil_designer import JoinTemplate
from ... import ph, router, state


class Join(JoinTemplate):
    """#join (type or scan a code) and #join/<code> (the hunt's card: who's playing, cake topper, colour, Let's hunt!).
    Games and Kids' corners this tablet remembers show up as one-tap shortcuts."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.code = ph.code_from_text(args[0]) if args else ""
        self.topper = random.choice([k for k, _ in ph.TOPPERS])
        self.colour = random.choice([k for k, _ in ph.COLOURS])
        self.hunt: dict = {}
        self.toppers_panel.add_event_handler("x-pick", self._pick_topper)
        self.colours_panel.add_event_handler("x-pick", self._pick_colour)
        state.set_control_attr(self.code_box, "autocomplete", "off")
        state.set_control_attr(self.code_box, "autocapitalize", "characters")
        state.set_control_attr(self.code_box, "maxlength", "6")
        state.set_control_attr(self.name_box, "autocomplete", "nickname")
        self.scan_box.visible = False
        if self.code:
            self._preview()
        else:
            self._ask()

    def _ask(self, error=""):
        self.ask_box.visible, self.hunt_box.visible = True, False
        state.heading(self.ask_title, 1)
        self.ask_error.text, self.ask_error.visible = error, bool(error)
        saved = [{"href": router.href("kid", k["token"]), "title": "%s's corner" % k["name"], "sub": "Kids' corner",
                  "topper": k.get("topper"), "colour": k.get("colour")} for k in ph.kid_corners()]
        saved += [{"href": router.href("play", g["token"]), "title": g.get("title") or ("Hunt " + c),
                   "sub": "Keep playing as %s" % g.get("name", ""), "topper": "star", "colour": "lemon"} for c, g in ph.games().items()]
        self.saved_panel.items = saved[:8]
        self.saved_box.visible = bool(saved)

    def _preview(self):
        r = anvil.server.call("hunt_preview", self.code)
        if not r.get("ok"):
            self.code_box.text = self.code
            self._ask(r.get("error") or "No hunt has that code.")
            return
        h = self.hunt = r["hunt"]
        self.ask_box.visible, self.hunt_box.visible = False, True
        state.heading(self.title, 1)
        self.cake.flavour, self.cake.total, self.cake.lit = h["flavour"], h["total"], 0
        self.title.text = h["title"]
        bits = []
        if h["birthday_name"]:
            bits.append("For %s's%s birthday" % (h["birthday_name"], (" %s" % _nth(h["birthday_age"])) if h["birthday_age"] else ""))
        bits.append("%s with %s" % (h["kind_label"], state.plural(h["total"], "treasure" if h["kind"] != "task" else "task")))
        if h["time_limit"]:
            bits.append("%d minutes" % h["time_limit"])
        self.meta.text = " · ".join(bits)
        self.message_label.text = h["message"]
        self.message_label.visible = bool(h["message"])
        game = ph.games().get(h["code"])
        self.continue_link.visible = bool(game)
        if game:
            state.set_attr(self.continue_link, "href", router.href("play", game["token"]))
            self.dom_nodes["continue_text"].textContent = "Keep playing as %s" % game.get("name", "you")
        kids = ph.kid_corners()
        self.kids_panel.items = [{"href": router.href("kid", k["token"], h["code"]), "title": k["name"], "sub": "From the Kids' corner",
                                  "topper": k.get("topper"), "colour": k.get("colour")} for k in kids]
        self.kids_box.visible = bool(kids) and h["status"] != "finished"
        closed = h["status"] == "finished"
        self.form_box.visible = not closed
        if closed:
            self.message_label.text = "This hunt has finished. Ask a grown-up to start a new one."
            self.message_label.visible = True
        self._draw_picks()

    def _draw_picks(self):
        self.toppers_panel.items = [{"key": k, "label": label, "colour": self.colour, "on": k == self.topper} for k, label in ph.TOPPERS]
        self.colours_panel.items = [{"key": k, "label": label, "kind": "colour", "on": k == self.colour} for k, label in ph.COLOURS]

    def _pick_topper(self, key, **event_args):
        self.topper = key
        ph.sfx("pop")
        self._draw_picks()
        state.refocus(self.toppers_panel, key)

    def _pick_colour(self, key, **event_args):
        self.colour = key
        self._draw_picks()
        state.refocus(self.colours_panel, key)

    @handle("go_button", "click")
    def go_button_click(self, **event_args):
        code = ph.code_from_text(self.code_box.text)
        if not code:
            self._ask("A hunt code has 6 letters and numbers, like CAKE42.")
            return
        router.go("join", code)

    @handle("code_box", "pressed_enter")
    def code_box_pressed_enter(self, **event_args):
        self.go_button_click()

    @handle("scan_button", "click")
    def scan_button_click(self, **event_args):
        self.scan_box.visible = True
        self.scan_button.visible = False
        self.scanner.start()

    @handle("scanner", "scanned")
    def scanner_scanned(self, text, **event_args):
        self.scan_box.visible, self.scan_button.visible = False, True
        kid = ph.kid_token_from_text(text)
        if kid:
            router.go("kid", kid)
            return
        code = ph.code_from_text(text)
        if code:
            router.go("join", code)
        else:
            self._ask("That QR code isn't a PhotoHunt code. Try another one, or type the code.")

    @handle("scanner", "closed")
    def scanner_closed(self, **event_args):
        self.scan_box.visible, self.scan_button.visible = False, True

    @handle("join_button", "click")
    def join_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if not name:
            self.join_error.text, self.join_error.visible = "Type your name (or your team's name).", True
            self.name_box.focus()
            return
        self.join_button.enabled = False
        try:
            r = anvil.server.call("join_hunt", self.code, name, self.topper, self.colour)
        finally:
            self.join_button.enabled = True
        if not r.get("ok"):
            self.join_error.text, self.join_error.visible = r.get("error") or "That didn't work.", True
            return
        ph.remember_game(self.code, r["token"], name, self.hunt.get("title", ""))
        router.go("play", r["token"])

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.join_button_click()


def _nth(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        return "%dth" % n
    return "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))
