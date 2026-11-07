from anvil import *

from ._anvil_designer import LandingTemplate
from ... import ph, router, state


class Landing(LandingTemplate):
    """#landing, the front page: the promise (polaroids drop in around the cake and light its candles), how it works,
    the three kinds of hunt, features, FAQ. Static copy lives in the template; only the variations are set here:
    signed in or not, and the shortcuts this tablet remembers (Kids' corners, games in progress)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = not me
        self.member_cta.visible = bool(me)
        if me:
            state.set_attr(self.band_link, "href", "#home")
        saved = [{"href": router.href("kid", k["token"]), "title": "%s's corner" % k["name"], "sub": "Kids' corner",
                  "topper": k.get("topper"), "colour": k.get("colour")} for k in ph.kid_corners()]
        saved += [{"href": router.href("play", g["token"]), "title": g.get("title") or ("Hunt " + c),
                   "sub": "Keep playing as %s" % g.get("name", ""), "topper": "star", "colour": "lemon"} for c, g in ph.games().items()]
        self.saved_panel.items = saved[:6]
        self.saved_box.visible = bool(saved)
