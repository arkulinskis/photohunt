from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import RecorderTemplate
from ... import ph


class Recorder(RecorderTemplate):
    """Record a voice clip: Record -> Stop (with a level meter and a timer) -> Play / Record again / Remove.
    Raises "recorded" (media, seconds) with the new clip; the page saves it. voice_key = a clip saved before."""

    def __init__(self, **properties):
        self._key, self._max, self._prompt = "", 45, "Record a clue"
        self._url = None
        self._ready = False
        super().__init__(**properties)
        self._ready = True
        self._level = anvil.js.report_exceptions(self._on_level)
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        has = bool(self._url or self._key)
        self.rec_button.text = "Record again" if has else self._prompt
        self.play_button.visible = has
        self.remove_button.visible = has
        if not self.stop_button.visible:
            self.time_label.text = "Recorded" if has else ""
        self.dom_nodes["meter"].style.display = "inline-block" if self.stop_button.visible else "none"

    def _on_level(self, level, secs):
        self.dom_nodes["bar"].style.transform = "scaleX(%.2f)" % max(0.04, float(level))
        self.time_label.text = "%s / %s" % (ph.clock(secs), ph.clock(self._max))

    @handle("rec_button", "click")
    def rec_button_click(self, **event_args):
        self.message.visible = False
        ph.stop_sound()
        try:
            window.PH.recStart(self._level, self._max)
        except Exception as e:
            self.message.text, self.message.visible = ph.err_text(e), True
            return
        self.rec_button.visible, self.stop_button.visible = False, True
        self.play_button.visible = self.remove_button.visible = False
        self.dom_nodes["box"].classList.add("is-recording")
        self._draw()

    @handle("stop_button", "click")
    def stop_button_click(self, **event_args):
        res = window.PH.recStop()
        self.rec_button.visible, self.stop_button.visible = True, False
        self.dom_nodes["box"].classList.remove("is-recording")
        if res is None:
            self._draw()
            return
        secs = float(ph.jget(res, "seconds", 0) or 0)
        if secs < 0.6:
            self.message.text, self.message.visible = "That was very short. Hold on a moment longer and try again.", True
            self._draw()
            return
        self._url = ph.jget(res, "url")
        self._draw()
        self.time_label.text = "New recording, %s" % ph.clock(secs)
        self.raise_event("recorded", media=ph.to_media(ph.jget(res, "blob")), seconds=secs)

    @handle("play_button", "click")
    def play_button_click(self, **event_args):
        url = self._url or ph.voice_url(self._key)
        if url:
            window.PH.playUrl(url, None)

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        ph.stop_sound()
        self._url, self._key = None, ""
        self._draw()
        self.raise_event("removed")

    @handle("", "hide")
    def form_hide(self, **event_args):
        if self.stop_button.visible:
            window.PH.recCancel()
            self.rec_button.visible, self.stop_button.visible = True, False

    @property
    def voice_key(self):
        return self._key

    @voice_key.setter
    def voice_key(self, value):
        self._key = value or ""
        self._url = None
        self._draw()

    @property
    def max_seconds(self):
        return self._max

    @max_seconds.setter
    def max_seconds(self, value):
        self._max = int(value or 45)

    @property
    def prompt(self):
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        self._prompt = value or "Record a clue"
        self._draw()
