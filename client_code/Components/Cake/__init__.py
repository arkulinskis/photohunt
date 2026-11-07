from anvil import *
from anvil.js import window

from ._anvil_designer import CakeTemplate


class Cake(CakeTemplate):
    """The birthday cake (custom component): every property setter redraws the SVG."""

    def __init__(self, **properties):
        self._o: dict = {"flavour": "strawberry", "total": 6, "lit": 0, "blown": False, "label": ""}
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if self._ready:
            window.PH.cake(self.dom_nodes["art"], self._o)
            self.dom_nodes["art"].classList.toggle("is-blown", bool(self._o["blown"]))

    def _set(self, key, value):
        self._o[key] = value
        self._draw()

    @property
    def flavour(self):
        return self._o["flavour"]

    @flavour.setter
    def flavour(self, value):
        self._set("flavour", value or "strawberry")

    @property
    def total(self):
        return self._o["total"]

    @total.setter
    def total(self, value):
        self._set("total", int(value or 0))

    @property
    def lit(self):
        return self._o["lit"]

    @lit.setter
    def lit(self, value):
        self._set("lit", int(value or 0))

    @property
    def blown(self):
        return self._o["blown"]

    @blown.setter
    def blown(self, value):
        self._set("blown", bool(value))

    @property
    def label(self):
        return self._o["label"]

    @label.setter
    def label(self, value):
        self._set("label", value or "")
