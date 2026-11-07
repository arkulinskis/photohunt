from anvil import *
from anvil.js import window

from ._anvil_designer import CameraTemplate
from ... import ph, state


class Camera(CameraTemplate):
    """Live camera (back camera on phones and tablets) with a big Snap button. Raises "snapped" with the shrunk JPEG
    as Media, its fingerprint (for Magic match) and a blob URL to show it right away. "Choose a photo" takes a file
    instead (also the way in when there is no camera). The ghost shows the photo to match at low opacity."""

    def __init__(self, **properties):
        self._ghost, self._hint, self._on = "", "", False
        self._ghost_on = True
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        g = self.dom_nodes["ghost"]
        if self._ghost:
            g.setAttribute("src", self._ghost)
        else:
            g.removeAttribute("src")
        g.style.display = "block" if (self._ghost and self._ghost_on) else "none"
        self.ghost_button.visible = bool(self._ghost)
        state.set_control_attr(self.ghost_button, "aria-pressed", "true" if self._ghost_on else "false")
        self.hint_label.text = self._hint
        self.hint_label.visible = bool(self._hint)

    def start(self):
        """Turn the camera on. Returns True, or False with the reason shown (and "failed" raised)."""
        self.status.visible = False
        try:
            window.PH.camStart(self.dom_nodes["video"], "environment")
        except Exception as e:
            msg = ph.err_text(e)
            self.status.text, self.status.visible = msg, True
            self.dom_nodes["box"].classList.add("no-cam")
            self.shutter.enabled = False
            self.raise_event("failed", message=msg)
            return False
        self._on = True
        self.shutter.enabled = True
        self.dom_nodes["box"].classList.remove("no-cam")
        return True

    def stop(self):
        window.PH.camStop()
        self._on = False

    @handle("shutter", "click")
    def shutter_click(self, **event_args):
        if not self._on:
            return
        self.shutter.enabled = False
        try:
            res = window.PH.camSnap(self.dom_nodes["video"])
        finally:
            self.shutter.enabled = True
        self.dom_nodes["box"].classList.add("flash")
        window.setTimeout(lambda: self.dom_nodes["box"].classList.remove("flash"), 260)
        ph.sfx("pop")
        self._emit(res)

    def file_change(self, event):
        try:
            res = window.PH.fromInput(self.dom_nodes["file"])
        except Exception as e:
            self.status.text, self.status.visible = ph.err_text(e), True
            return
        finally:
            self.dom_nodes["file"].value = ""
        if res is not None:
            self._emit(res)

    def _emit(self, res):
        self.raise_event("snapped", media=ph.to_media(ph.jget(res, "blob")), sig=ph.sig_of(res), url=ph.jget(res, "url"))

    @handle("ghost_button", "click")
    def ghost_button_click(self, **event_args):
        self._ghost_on = not self._ghost_on
        self._draw()

    @handle("", "hide")
    def form_hide(self, **event_args):
        self.stop()

    @property
    def ghost_url(self):
        return self._ghost

    @ghost_url.setter
    def ghost_url(self, value):
        self._ghost = value or ""
        self._draw()

    @property
    def hint(self):
        return self._hint

    @hint.setter
    def hint(self, value):
        self._hint = value or ""
        self._draw()

    @property
    def shutter_text(self):
        return self.shutter.text

    @shutter_text.setter
    def shutter_text(self, value):
        self.shutter.text = value or "Snap!"
