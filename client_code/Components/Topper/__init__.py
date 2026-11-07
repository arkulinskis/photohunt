from anvil import *
from anvil.js import window

from ._anvil_designer import TopperTemplate


class Topper(TopperTemplate):
    """A kid's avatar: a cake topper in their colour."""

    def __init__(self, **properties):
        self._o: dict = {"topper": "star", "colour": "pink", "size": 44}
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if self._ready:
            node = self.dom_nodes["art"]
            window.PH.topper(node, self._o)
            node.style.width = node.style.height = "%dpx" % int(self._o["size"] or 44)

    @property
    def topper(self):
        return self._o["topper"]

    @topper.setter
    def topper(self, value):
        self._o["topper"] = value or "star"
        self._draw()

    @property
    def colour(self):
        return self._o["colour"]

    @colour.setter
    def colour(self, value):
        self._o["colour"] = value or "pink"
        self._draw()

    @property
    def size(self):
        return self._o["size"]

    @size.setter
    def size(self, value):
        self._o["size"] = int(value or 44)
        self._draw()
