from anvil import *
import anvil.js

from ._anvil_designer import PhotoTemplate
from ... import ph


class Photo(PhotoTemplate):
    """A square picture: a stored photo, a demo drawing, a fresh snapshot, a "no picture yet" frame, or a mystery card.
    A picture that fails to load falls back to the empty frame."""

    def __init__(self, **properties):
        self._o: dict = {"photo_key": "", "art": "", "src": "", "alt": "", "mystery": False}
        self._ready = False
        super().__init__(**properties)
        self.dom_nodes["img"].addEventListener("error", anvil.js.report_exceptions(self._broken))
        self._ready = True
        self._draw()

    def _broken(self, event):
        self.dom_nodes["box"].classList.add("is-empty")

    def _draw(self):
        if not self._ready:
            return
        o = self._o
        url = o["src"] or ph.photo_url(o["photo_key"], o["art"])
        box, img = self.dom_nodes["box"], self.dom_nodes["img"]
        box.classList.toggle("is-mystery", bool(o["mystery"]))
        box.classList.toggle("is-empty", not url and not o["mystery"])
        box.classList.toggle("is-art", bool(o["art"]) and not o["photo_key"] and not o["src"])
        if url and not o["mystery"]:
            if img.getAttribute("src") != url:
                img.setAttribute("src", url)
            img.setAttribute("alt", o["alt"] or "")
        else:
            img.removeAttribute("src")
            img.setAttribute("alt", "")

    def _set(self, key, value):
        self._o[key] = value
        self._draw()

    @property
    def photo_key(self):
        return self._o["photo_key"]

    @photo_key.setter
    def photo_key(self, value):
        self._set("photo_key", value or "")

    @property
    def art(self):
        return self._o["art"]

    @art.setter
    def art(self, value):
        self._set("art", value or "")

    @property
    def src(self):
        return self._o["src"]

    @src.setter
    def src(self, value):
        self._set("src", value or "")

    @property
    def alt(self):
        return self._o["alt"]

    @alt.setter
    def alt(self, value):
        self._set("alt", value or "")

    @property
    def mystery(self):
        return self._o["mystery"]

    @mystery.setter
    def mystery(self, value):
        self._set("mystery", bool(value))
