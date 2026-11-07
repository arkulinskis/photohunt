from anvil import *
from anvil.js import window

from ._anvil_designer import QrCodeTemplate


class QrCode(QrCodeTemplate):
    """A QR code drawn as SVG (theme/assets/ph-qrgen.js, MIT)."""

    def __init__(self, **properties):
        self._text, self._label, self._ready = "", "QR code", False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if self._ready:
            node = self.dom_nodes["art"]
            window.PH.qr(node, self._text)
            svg = node.querySelector("svg")
            if svg:
                svg.setAttribute("aria-label", self._label)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value or ""
        self._draw()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value or "QR code"
        self._draw()
