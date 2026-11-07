import anvil.server
from anvil import *

from ._anvil_designer import HuntSettingsTemplate
from ... import ph, state


class HuntSettings(HuntSettingsTemplate):
    """Make a hunt or change its settings. hunt = the hunt dict ({} for a new one). Closes with the saved hunt, or None."""

    def __init__(self, hunt, **properties):
        super().__init__(**properties)
        self.h = hunt or {}
        new = not self.h.get("id")
        self.dom_nodes["heading"].textContent = "Bake a new hunt" if new else "Hunt settings"
        self.save_button.text = "Bake it" if new else "Save"
        self.kind = self.h.get("kind", "photo")
        self.flavour = self.h.get("flavour", "strawberry")
        self.title_box.text = self.h.get("title", "")
        self.bday_box.text = self.h.get("birthday_name", "")
        self.age_drop.items = [("Not saying", 0)] + [(str(i), i) for i in range(1, 13)]
        self.age_drop.selected_value = self.h.get("birthday_age", 0) or 0
        self.time_drop.items = [(label, v) for v, label in ph.TIME_LIMITS]
        self.time_drop.selected_value = self.h.get("time_limit", 15)
        self.win_drop.items = [("Race: everyone fills their own cake", "race"), ("Together: one cake for everybody", "together")]
        self.win_drop.selected_value = self.h.get("win_style", "race")
        self.start_drop.items = [("Kids wait until I press Start", "together"), ("Each kid starts when they're ready", "self")]
        self.start_drop.selected_value = self.h.get("start_mode", "together")
        self.match_drop.items = [("Magic match: the app compares photos", "magic"), ("I check every photo", "judge"),
                                 ("Every photo counts (little ones)", "honour")]
        self.match_drop.selected_value = self.h.get("match_mode", "magic")
        self.strict_drop.items = [("Easy (for little ones)", "easy"), ("Just right", "normal"), ("Tricky (big kids)", "tricky")]
        self.strict_drop.selected_value = self.h.get("strictness", "normal")
        self.message_box.text = self.h.get("message", "")
        self.kinds_panel.add_event_handler("x-pick", self._pick_kind)
        self.flavours_panel.add_event_handler("x-pick", self._pick_flavour)
        self._draw()
        for box, what in ((self.age_drop, "Turning"), (self.time_drop, "Time limit"), (self.win_drop, "How to win"),
                          (self.start_drop, "How it starts"), (self.match_drop, "Checking photos"), (self.strict_drop, "Strictness")):
            state.set_control_attr(box, "aria-label", what)

    def _draw(self):
        self.kinds_panel.items = [{"key": k, "title": t, "text": d, "icon": i, "on": k == self.kind} for k, t, d, i in ph.KINDS]
        self.flavours_panel.items = [{"key": k, "label": label, "kind": "flavour", "on": k == self.flavour} for k, label in ph.FLAVOURS]
        self.strict_field.visible = self.match_drop.selected_value == "magic"

    @handle("match_drop", "change")
    def match_drop_change(self, **event_args):
        self._draw()

    def _pick_kind(self, key, **event_args):
        self.kind = key
        self._draw()
        state.refocus(self.kinds_panel, key)

    def _pick_flavour(self, key, **event_args):
        self.flavour = key
        self._draw()
        state.refocus(self.flavours_panel, key)

    @handle("", "show")
    def form_show(self, **event_args):
        self.title_box.focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        d = {"title": self.title_box.text or "", "birthday_name": self.bday_box.text or "",
             "birthday_age": self.age_drop.selected_value, "kind": self.kind, "flavour": self.flavour,
             "time_limit": self.time_drop.selected_value, "win_style": self.win_drop.selected_value,
             "start_mode": self.start_drop.selected_value, "match_mode": self.match_drop.selected_value,
             "strictness": self.strict_drop.selected_value, "message": self.message_box.text or ""}
        if len(d["title"].strip()) < 2:
            self.message.text, self.message.visible = "Give the hunt a name (at least 2 letters).", True
            self.title_box.focus()
            return
        self.save_button.enabled = False
        try:
            if self.h.get("id"):
                r = anvil.server.call("update_hunt", self.h["id"], d)
            else:
                r = anvil.server.call("create_hunt", d)
        finally:
            self.save_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.raise_event("x-close-alert", value=r["hunt"])
