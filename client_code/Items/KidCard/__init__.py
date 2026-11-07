from anvil import *

from ._anvil_designer import KidCardTemplate
from ... import state


class KidCard(KidCardTemplate):
    """A kid profile: topper, name, hunts and stickers; Kids' corner link, edit, delete (events to the page)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        k = self.item
        self.topper.topper, self.topper.colour = k["topper"], k["colour"]
        self.meta.text = "%s · %s" % (state.plural(k.get("hunts", 0), "hunt"), state.plural(k.get("stickers", 0), "sticker"))
        compact = bool(k.get("_compact"))
        self.edit_button.visible = self.delete_button.visible = not compact
        state.set_control_attr(self.edit_button, "aria-label", "Edit %s" % k["name"])
        state.set_control_attr(self.delete_button, "aria-label", "Delete %s" % k["name"])
        state.set_control_attr(self.link_button, "aria-label", "%s's Kids' corner" % k["name"])

    @handle("link_button", "click")
    def link_button_click(self, **event_args):
        self.parent.raise_event("x-kid-link", kid=self.item)

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.parent.raise_event("x-kid-edit", kid=self.item)

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        self.parent.raise_event("x-kid-delete", kid=self.item)
