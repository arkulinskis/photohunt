from anvil import *

from ._anvil_designer import VoiceButtonTemplate
from ... import ph


class VoiceButton(VoiceButtonTemplate):
    """Plays the grown-up's recorded clue, a library task's recorded voice (lib_id), or reads the text aloud with the
    device's voice. Press again to stop."""

    def __init__(self, **properties):
        self._o: dict = {"voice_key": "", "text": "", "lib_id": "", "label": "Hear the clue", "big": False}
        self._ready = False
        self._playing = False
        super().__init__(**properties)
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        o = self._o
        btn = self.dom_nodes["btn"]
        btn.classList.toggle("big", bool(o["big"]))
        btn.classList.toggle("playing", self._playing)
        btn.setAttribute("aria-pressed", "true" if self._playing else "false")
        has = bool(o["voice_key"] or o["text"])
        btn.disabled = not has
        self.dom_nodes["lab"].textContent = ("Stop" if self._playing else o["label"]) if has else "No clue recorded"

    def btn_click(self, event):
        self.play(not self._playing)

    def play(self, on=True):
        if not on:
            ph.stop_sound()
            self._done(True)
            return
        self._playing = True
        self._draw()
        ph.say_clue(self._o["voice_key"], self._o["text"], self._done, self._o["lib_id"])

    def _done(self, ok=True):
        self._playing = False
        self._draw()

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self._playing:
            ph.stop_sound()

    def _set(self, key, value):
        self._o[key] = value
        self._draw()

    @property
    def voice_key(self):
        return self._o["voice_key"]

    @voice_key.setter
    def voice_key(self, value):
        self._set("voice_key", value or "")

    @property
    def text(self):
        return self._o["text"]

    @text.setter
    def text(self, value):
        self._set("text", value or "")

    @property
    def lib_id(self):
        return self._o["lib_id"]

    @lib_id.setter
    def lib_id(self, value):
        self._set("lib_id", value or "")

    @property
    def label(self):
        return self._o["label"]

    @label.setter
    def label(self, value):
        self._set("label", value or "Hear the clue")

    @property
    def big(self):
        return self._o["big"]

    @big.setter
    def big(self, value):
        self._set("big", bool(value))
