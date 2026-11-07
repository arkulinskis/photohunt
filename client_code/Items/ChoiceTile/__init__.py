from anvil import *

from ._anvil_designer import ChoiceTileTemplate


class ChoiceTile(ChoiceTileTemplate):
    """A big choice (the kind of hunt). item = {key, title, text, icon, on}; a click raises x-pick on the panel."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        self.dom_nodes["title"].textContent = c["title"]
        self.dom_nodes["text"].textContent = c.get("text", "")
        self.dom_nodes["icon"].className = "ic ic-" + c.get("icon", "star")
        b = self.dom_nodes["btn"]
        b.classList.toggle("on", bool(c.get("on")))
        b.setAttribute("aria-pressed", "true" if c.get("on") else "false")
        b.setAttribute("data-key", c["key"])

    def btn_click(self, event):
        self.parent.raise_event("x-pick", key=self.item["key"])
