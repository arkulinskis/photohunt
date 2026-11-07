from anvil import *
from anvil.js import window

from ._anvil_designer import SavedLinkTemplate
from ... import state


class SavedLink(SavedLinkTemplate):
    """A shortcut this tablet remembers: a Kids' corner or a game in progress. item = {href, title, sub, topper, colour}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s = self.item
        window.PH.topper(self.dom_nodes["art"], {"topper": s.get("topper") or "star", "colour": s.get("colour") or "pink"})
        self.dom_nodes["title"].textContent = s["title"]
        self.dom_nodes["sub"].textContent = s.get("sub", "")
        state.set_attr(self.link, "href", s["href"])
