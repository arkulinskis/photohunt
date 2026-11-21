from anvil import *

from ._anvil_designer import PacksTemplate
from ... import router, state

AGE_KEY = "ph_pack_age"


class Packs(PacksTemplate):
    """Ready in a minute: age chips + the ready-made packs. One tap makes a task hunt (create_pack_hunt) and opens its
    QR code in the hunt kitchen. Signed-out visitors are sent to sign up first (and come back to Party HQ)."""

    def __init__(self, **properties):
        self._heading = "Ready in a minute"
        self._ready = False
        super().__init__(**properties)
        self.ages_panel.add_event_handler("x-cat", self._pick_age)
        self.packs_panel.add_event_handler("x-pack", self._make)
        self.data: dict = {"ages": [], "packs": []}
        try:
            from ...Dialogs.TaskPicker import library
            self.data = library().get("packs") or self.data
        except Exception:
            self.error.text = "The packs didn't load. Check the connection and reload the page."
            self.error.visible = True
        keys = [a["key"] for a in self.data["ages"]]
        saved = state.store_get(AGE_KEY, "middle")
        self.age = saved if saved in keys else (keys[1] if len(keys) > 1 else (keys[0] if keys else ""))
        self._ready = True
        self._draw()

    def _draw(self):
        if not self._ready:
            return
        self.dom_nodes["heading"].textContent = self._heading
        ages = self.data["ages"]
        self.ages_panel.items = [{"key": a["key"], "label": a["label"], "on": a["key"] == self.age} for a in ages]
        cur = next((a for a in ages if a["key"] == self.age), None)
        self.age_note.text = ("For %s: %s." % (cur["label"].lower(), cur["note"])) if cur else ""
        signed_in = bool(state.me())
        self.packs_panel.items = [dict(p, _age=self.age, _age_label=cur["label"] if cur else "", _signed_in=signed_in)
                                  for p in self.data["packs"]]

    def _pick_age(self, key, **event_args):
        self.age = key
        state.store_set(AGE_KEY, key)
        self._draw()
        state.refocus(self.ages_panel, key)

    def _make(self, pack, button=None, **event_args):
        if not state.me():
            router.remember_after("#home")
            router.go("auth", "signup")
            return
        if button is not None:
            button.enabled = False
        try:
            r = state.call("create_pack_hunt", pack["key"], self.age)
        finally:
            if button is not None:
                button.enabled = True
        if r:
            state.toast("Your hunt is ready! Show the kids the QR code.", "ok")
            router.go("hunt", r["hunt"]["id"], "share")

    @property
    def heading(self):
        return self._heading

    @heading.setter
    def heading(self, value):
        self._heading = value or "Ready in a minute"
        self._draw()
