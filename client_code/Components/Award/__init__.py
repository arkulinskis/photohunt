from anvil import *

from ._anvil_designer import AwardTemplate

SIZES = ("sm", "lg", "xl")


class Award(AwardTemplate):
    """A kid's award (one of its own for every player, server_code/Game.give_awards): medal, title and why."""

    def __init__(self, **properties):
        self._o: dict = {"award": None, "size": "sm"}
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        a = self._o["award"] or {}
        self.visible = bool(a.get("title"))
        box = self.dom_nodes["box"]
        box.className = "aw aw-" + (self._o["size"] if self._o["size"] in SIZES else "sm")
        self.dom_nodes["icon"].className = "ic ic-" + str(a.get("icon") or "star")
        self.dom_nodes["title"].textContent = a.get("title") or ""
        self.dom_nodes["why"].textContent = a.get("why") or ""

    @property
    def award(self):
        return self._o["award"]

    @award.setter
    def award(self, value):
        self._o["award"] = value if isinstance(value, dict) else None
        self._draw()

    @property
    def size(self):
        return self._o["size"]

    @size.setter
    def size(self, value):
        self._o["size"] = value or "sm"
        self._draw()
