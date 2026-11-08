from anvil import *

from ._anvil_designer import HuntCardTemplate
from ... import ph, router, state

STATUS = {"draft": ("Getting ready", "badge-warn"), "live": ("Hunt on!", "badge-good"), "finished": ("Finished", "badge")}


class HuntCard(HuntCardTemplate):
    """A hunt on Party HQ (mine or an example): its cake in the hunt's flavour, name, what kind, status and code."""

    def __init__(self, **properties):
        super().__init__(**properties)
        h = self.item
        c = h.get("counts") or {}
        n = c.get("treasures", 0)
        self.cake.flavour = h["flavour"]
        self.cake.total = n
        self.cake.lit = n if h["status"] == "finished" else c.get("finds", 0) if h["win_style"] == "together" else 0
        self.cake.label = "%s cake" % h["flavour"].capitalize()
        bits = [ph.KIND_LABEL.get(h["kind"], "Hunt"), state.plural(n, "treasure")]
        if c.get("players"):
            bits.append(state.plural(c["players"], "player"))
        if h.get("birthday_name"):
            bits.insert(0, "For %s%s" % (h["birthday_name"], (", %d" % h["birthday_age"]) if h.get("birthday_age") else ""))
        self.meta.text = " · ".join(bits)
        label, role = STATUS.get(h["status"], STATUS["draft"])
        if h.get("demo"):
            label, role = "Example", "badge-brand"
        self.status.text = label
        self.status.role = ["badge", role]
        self.code.text = "Code " + h["code"]
        self.code.visible = not h.get("demo") or h["code"] in ph.OPEN_DEMOS
        state.set_attr(self.link, "href", router.href("hunt", h["id"]))
        state.set_attr(self.link, "aria-label", "%s, %s" % (h["title"], label))
