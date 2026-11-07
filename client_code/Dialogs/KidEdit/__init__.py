import anvil.server
from anvil import *

from ._anvil_designer import KidEditTemplate
from ... import ph, state


class KidEdit(KidEditTemplate):
    """Add or change a kid profile (name, topper, colour). kid = the kid dict ({} = new). Closes with the kid, or None."""

    def __init__(self, kid, **properties):
        super().__init__(**properties)
        self.k = kid or {}
        self.dom_nodes["heading"].textContent = "Edit %s" % self.k["name"] if self.k.get("id") else "Add a kid"
        self.name_box.text = self.k.get("name", "")
        self.topper = self.k.get("topper", "star")
        self.colour = self.k.get("colour", "pink")
        self.toppers_panel.add_event_handler("x-pick", self._pick_topper)
        self.colours_panel.add_event_handler("x-pick", self._pick_colour)
        self._draw()

    def _draw(self):
        self.toppers_panel.items = [{"key": k, "label": label, "colour": self.colour, "on": k == self.topper} for k, label in ph.TOPPERS]
        self.colours_panel.items = [{"key": k, "label": label, "kind": "colour", "on": k == self.colour} for k, label in ph.COLOURS]
        self.preview.topper, self.preview.colour = self.topper, self.colour

    def _pick_topper(self, key, **event_args):
        self.topper = key
        self._draw()
        state.refocus(self.toppers_panel, key)

    def _pick_colour(self, key, **event_args):
        self.colour = key
        self._draw()
        state.refocus(self.colours_panel, key)

    @handle("", "show")
    def form_show(self, **event_args):
        self.name_box.focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if not name:
            self.message.text, self.message.visible = "Type a first name or nickname.", True
            return
        if self.k.get("id"):
            r = anvil.server.call("update_kid", self.k["id"], name, self.topper, self.colour)
        else:
            r = anvil.server.call("add_kid", name, self.topper, self.colour)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.raise_event("x-close-alert", value=r["kid"])
