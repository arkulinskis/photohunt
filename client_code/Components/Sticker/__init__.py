from anvil import *
from anvil.js import window

from ._anvil_designer import StickerTemplate
from ... import ph


class Sticker(StickerTemplate):
    """A sticker a kid won (scalloped round badge), optionally named and counted."""

    def __init__(self, **properties):
        self._o: dict = {"sticker": "party", "size": 56, "show_label": False, "count": 0}
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        o = self._o
        art = self.dom_nodes["art"]
        window.PH.sticker(art, {"id": o["sticker"]})
        art.style.width = art.style.height = "%dpx" % int(o["size"] or 56)
        name, about = ph.STICKERS.get(o["sticker"], ("Sticker", ""))
        self.dom_nodes["box"].setAttribute("title", "%s: %s" % (name, about))
        self.dom_nodes["box"].setAttribute("aria-label", "%s sticker%s" % (name, (" x%d" % o["count"]) if o["count"] > 1 else ""))
        self.dom_nodes["cap"].textContent = name if o["show_label"] else ""
        self.dom_nodes["cap"].style.display = "block" if o["show_label"] else "none"
        self.dom_nodes["n"].textContent = ("x%d" % o["count"]) if o["count"] > 1 else ""

    def _set(self, key, value):
        self._o[key] = value
        self._draw()

    @property
    def sticker(self):
        return self._o["sticker"]

    @sticker.setter
    def sticker(self, value):
        self._set("sticker", value or "party")

    @property
    def size(self):
        return self._o["size"]

    @size.setter
    def size(self, value):
        self._set("size", int(value or 56))

    @property
    def show_label(self):
        return self._o["show_label"]

    @show_label.setter
    def show_label(self, value):
        self._set("show_label", bool(value))

    @property
    def count(self):
        return self._o["count"]

    @count.setter
    def count(self, value):
        self._set("count", int(value or 0))
