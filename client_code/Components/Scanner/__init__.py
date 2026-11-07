from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ScannerTemplate
from ... import ph


class Scanner(ScannerTemplate):
    """Reads a QR code with the camera (BarcodeDetector where the browser has it, else jsQR). start() when shown."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._cb = anvil.js.report_exceptions(self._got)

    def start(self):
        self.status.text = "Point the camera at the hunt's QR code."
        try:
            window.PH.scanStart(self.dom_nodes["video"], self._cb)
        except Exception as e:
            self.status.text = ph.err_text(e) + " You can type the code instead."
            return False
        return True

    def stop(self):
        window.PH.scanStop()

    def _got(self, text):
        ph.sfx("pop")
        self.raise_event("scanned", text=str(text))

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.stop()
        self.raise_event("closed")

    @handle("", "hide")
    def form_hide(self, **event_args):
        self.stop()
