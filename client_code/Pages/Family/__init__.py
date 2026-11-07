from anvil import *

from ._anvil_designer import FamilyTemplate
from ... import state


class Family(FamilyTemplate):
    """#family: kid profiles (name, topper, colour) and each one's Kids' corner link."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.title, 1)
        self.kids_panel.add_event_handler("x-kid-link", self._link)
        self.kids_panel.add_event_handler("x-kid-edit", self._edit)
        self.kids_panel.add_event_handler("x-kid-delete", self._delete)
        self._load()

    def _load(self):
        d = state.call("get_hq")
        if d is None:
            return
        self.kids_panel.items = d["kids"]
        self.empty.visible = not d["kids"]

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        from ...Dialogs.KidEdit import KidEdit
        kid = alert(KidEdit(kid={}), large=True, buttons=[], role="app-dialog")
        if kid:
            self._load()
            self._link(kid)

    def _link(self, kid, **event_args):
        from ...Dialogs.KidLink import KidLink
        alert(KidLink(kid=kid), large=True, buttons=[], role="app-dialog")
        self._load()

    def _edit(self, kid, **event_args):
        from ...Dialogs.KidEdit import KidEdit
        if alert(KidEdit(kid=kid), large=True, buttons=[], role="app-dialog"):
            self._load()

    def _delete(self, kid, **event_args):
        if confirm("Their Kids' corner link stops working. Hunts they played keep their results.",
                   title="Delete %s?" % kid["name"], buttons=[("Cancel", False), ("Delete", True)]):
            if state.call("delete_kid", kid["id"]) is not None:
                self._load()
