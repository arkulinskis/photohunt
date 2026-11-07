from anvil import *

from ._anvil_designer import HomeTemplate
from ... import router, state


class Home(HomeTemplate):
    """#home, Party HQ: my hunts, my kids, the example hunts, and "Bake a new hunt"."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.hello, 1)
        self.kids_panel.add_event_handler("x-kid-link", self._kid_link)
        self._load()

    def _load(self):
        d = state.call("get_hq")
        if d is None:
            return
        me = state.me() or {}
        first = (me.get("name") or "").split(" ")[0]
        live = [h for h in d["hunts"] if h["status"] == "live"]
        if live:
            self.sub.text = "%s is on right now. Open it to watch the kids." % live[0]["title"]
        elif d["hunts"]:
            self.sub.text = "Hi %s! %s ready to play." % (first or "there", state.plural(len(d["hunts"]), "hunt"))
        else:
            self.sub.text = "Hi %s! Let's bake a hunt." % (first or "there")
        self.hunts_panel.items = d["hunts"]
        self.hunts_panel.visible = bool(d["hunts"])
        self.empty.visible = not d["hunts"]
        self.kids_panel.items = [dict(k, _compact=True) for k in d["kids"]]
        self.no_kids.visible = not d["kids"]
        self.examples_panel.items = d["examples"]
        self.examples_box.visible = bool(d["examples"])

    def _new(self):
        from ...Dialogs.HuntSettings import HuntSettings
        h = alert(HuntSettings(hunt={}), large=True, buttons=[], role="app-dialog")
        if h:
            state.toast("Hunt baked! Now add the treasures.", "ok")
            router.go("hunt", h["id"])

    @handle("new_button", "click")
    def new_button_click(self, **event_args):
        self._new()

    @handle("empty_button", "click")
    def empty_button_click(self, **event_args):
        self._new()

    def _kid_link(self, kid, **event_args):
        from ...Dialogs.KidLink import KidLink
        alert(KidLink(kid=kid), large=True, buttons=[], role="app-dialog")
