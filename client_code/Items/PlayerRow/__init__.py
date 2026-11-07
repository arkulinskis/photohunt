from anvil import *

from ._anvil_designer import PlayerRowTemplate
from ... import ph, state


class PlayerRow(PlayerRowTemplate):
    """A player on the live board: rank, topper, name, candles lit as a bar, here/finished, time left."""

    def __init__(self, **properties):
        super().__init__(**properties)
        p = self.item
        total = p.get("total") or 0
        found = p.get("team_found") if p.get("_together") else p.get("found", 0)
        self.dom_nodes["rank"].textContent = "" if p.get("_together") else str(p.get("rank", ""))
        self.topper.topper, self.topper.colour = p["topper"], p["colour"]
        self.here.visible = bool(p.get("online"))
        over = p.get("_status") == "finished"
        if p.get("winner") and not p.get("_together"):
            self.done.text = "Winner" if over else "In the lead"
        else:
            self.done.text = "Done"
        self.done.visible = bool(p.get("finished")) or bool(p.get("winner"))
        pct = int(100 * (p.get("found", 0)) / total) if total else 0
        self.dom_nodes["fill"].style.transform = "scaleX(%.2f)" % (pct / 100.0)
        self.dom_nodes["bar"].setAttribute("aria-label", "%d of %d candles" % (p.get("found", 0), total))
        bits = ["%d of %d found" % (p.get("found", 0), total)] if not p.get("_together") else ["found %d for the team" % p.get("found", 0)]
        if p.get("seconds_left") is not None and not p.get("finished"):
            bits.append(ph.clock(p["seconds_left"]) + " left")
        self.meta.text = " · ".join(bits)
        self.remove_button.visible = bool(p.get("_mine"))
        state.set_control_attr(self.remove_button, "aria-label", "Remove " + p["name"])

    @handle("remove_button", "click")
    def remove_button_click(self, **event_args):
        self.parent.raise_event("x-remove", player=self.item)
