from anvil import *
from anvil.js import window

from ._anvil_designer import TopperPickTemplate


class TopperPick(TopperPickTemplate):
    """A cake topper to pick as your avatar. item = {key, label, colour, on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        window.PH.topper(self.dom_nodes["art"], {"topper": c["key"], "colour": c.get("colour") or "pink"})
        self.dom_nodes["label"].textContent = c["label"]
        b = self.dom_nodes["btn"]
        b.classList.toggle("on", bool(c.get("on")))
        b.setAttribute("aria-pressed", "true" if c.get("on") else "false")
        b.setAttribute("data-key", c["key"])

    def btn_click(self, event):
        self.parent.raise_event("x-pick", key=self.item["key"])
