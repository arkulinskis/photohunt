from anvil import *

from ._anvil_designer import PackCardTemplate
from ... import state


class PackCard(PackCardTemplate):
    """A ready-made pack ("Ready in a minute"): icon in its cake flavour, name, what it is, the 8 tasks for the chosen
    ages, and one button that makes the hunt. item = pack + _age (key), _age_label, _signed_in, _busy."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p = self.item
        self.dom_nodes["icon"].className = "ic ic-" + str(p.get("icon") or "star")
        self.dom_nodes["tile"].setAttribute("data-flavour", str(p.get("flavour") or "strawberry"))
        tasks = (p.get("tasks") or {}).get(p.get("_age") or "middle") or []
        self.inside.text = "\n".join("%d. %s" % (i + 1, t) for i, t in enumerate(tasks))
        self.dom_nodes["summary"].textContent = "The %d tasks for %s" % (len(tasks), str(p.get("_age_label") or "").lower())
        if p.get("_signed_in"):
            self.make_button.text = "Make this hunt"
        else:
            self.make_button.text = "Sign up to use it"
            self.make_button.role = ["btn", "btn-block", "ic-user"]
        state.set_control_attr(self.make_button, "aria-label", "%s: %s" % (self.make_button.text, p.get("title", "")))

    @handle("make_button", "click")
    def make_button_click(self, **event_args):
        self.parent.raise_event("x-pack", pack=self.item, button=self.make_button)
