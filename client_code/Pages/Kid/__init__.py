import anvil.server
from anvil import *

from ._anvil_designer import KidTemplate
from ... import ph, router, state

ORDER = ["cake", "winner", "bingo", "first", "speedy", "sharp", "voice", "task", "team", "party"]


class Kid(KidTemplate):
    """#kid/<token>[/<code>], the Kids' corner on a tablet: hello, join a hunt (one tap, no name to type), my hunts,
    my sticker book. The tablet remembers the corner. With a code it joins that hunt straight away."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.token = args[0] if args else ""
        self.scan_box.visible = False
        state.set_control_attr(self.code_box, "autocomplete", "off")
        state.set_control_attr(self.code_box, "maxlength", "6")
        r: dict = {"ok": False, "error": "This link has no Kids' corner in it."}
        if self.token:
            r = anvil.server.call("kid_corner", self.token)
        if not r.get("ok"):
            self.main_box.visible = False
            self.gone_text.text = r.get("error") or ""
            ph.forget_kid(self.token)
            return
        self.gone_box.visible = False
        k = r["kid"]
        ph.remember_kid(self.token, k["name"], k["topper"], k["colour"])
        self.topper.topper, self.topper.colour = k["topper"], k["colour"]
        self.hello.text = "Hi %s!" % k["name"]
        state.heading(self.hello, 1)
        self.hunts_panel.items = r["hunts"]
        self.no_hunts.visible = not r["hunts"]
        counts = k.get("sticker_counts") or {}
        self.stickers_panel.items = [{"id": s, "count": counts[s], "size": 64} for s in ORDER if counts.get(s)]
        self.no_stickers.visible = not counts
        if len(args) > 1 and args[1]:
            self._join(args[1])

    def _join(self, code):
        code = ph.code_from_text(code)
        if not code:
            self.error.text, self.error.visible = "A hunt code has 6 letters and numbers, like CAKE42.", True
            return
        r = anvil.server.call("kid_join", self.token, code)
        if not r.get("ok"):
            self.error.text, self.error.visible = r.get("error") or "That didn't work.", True
            return
        router.go("play", r["token"])

    @handle("go_button", "click")
    def go_button_click(self, **event_args):
        self._join(self.code_box.text)

    @handle("code_box", "pressed_enter")
    def code_box_pressed_enter(self, **event_args):
        self._join(self.code_box.text)

    @handle("scan_button", "click")
    def scan_button_click(self, **event_args):
        self.scan_box.visible, self.scan_button.visible = True, False
        self.scanner.start()

    @handle("scanner", "scanned")
    def scanner_scanned(self, text, **event_args):
        self.scan_box.visible, self.scan_button.visible = False, True
        self._join(text)

    @handle("scanner", "closed")
    def scanner_closed(self, **event_args):
        self.scan_box.visible, self.scan_button.visible = False, True
