from anvil import *
from anvil.js import window

from ._anvil_designer import SwatchPickTemplate


class SwatchPick(SwatchPickTemplate):
    """A colour or cake-flavour choice. item = {key, label, kind ("flavour" or "colour"), on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        dot = self.dom_nodes["dot"]
        if c.get("kind") == "flavour":
            f = window.PH.FLAVOURS[c["key"]]
            dot.style.background = "linear-gradient(180deg, %s 0 48%%, %s 48%% 100%%)" % (f.frost, f.sponge)
        else:
            dot.style.background = window.PH.COLOURS[c["key"]]
        self.dom_nodes["label"].textContent = c["label"]
        b = self.dom_nodes["btn"]
        b.classList.toggle("on", bool(c.get("on")))
        b.setAttribute("aria-pressed", "true" if c.get("on") else "false")
        b.setAttribute("data-key", c["key"])

    def btn_click(self, event):
        self.parent.raise_event("x-pick", key=self.item["key"])
