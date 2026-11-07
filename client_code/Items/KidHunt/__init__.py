from anvil import *

from ._anvil_designer import KidHuntTemplate
from ... import router, state


class KidHunt(KidHuntTemplate):
    """A hunt in the Kids' corner: the cake with this kid's candles, and Keep hunting / See my cake."""

    def __init__(self, **properties):
        super().__init__(**properties)
        h = self.item
        self.cake.flavour, self.cake.total, self.cake.lit = h["flavour"], h["total"], h["found"]
        self.meta.text = "%s · %d of %d candles" % (h["kind_label"], h["found"], h["total"])
        self.dom_nodes["go"].textContent = "See my cake" if h["done"] else "Keep hunting"
        state.set_attr(self.link, "href", router.href("play", h["token"]))
