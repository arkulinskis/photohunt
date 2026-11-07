from anvil import *

from ._anvil_designer import TeamRowTemplate


class TeamRow(TeamRowTemplate):
    """A player on the kid's screen (who's here, the race, the results). item = team dict + _show_rank, _total."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r = self.item
        self.topper.topper, self.topper.colour = r["topper"], r["colour"]
        self.dom_nodes["rank"].textContent = str(r.get("rank", "")) if r.get("_show_rank") else ""
        self.dom_nodes["rank"].style.display = "grid" if r.get("_show_rank") else "none"
        self.found.text = ("%d" % r.get("found", 0)) + ((" / %d" % r["_total"]) if r.get("_total") else "")
        self.found.visible = r.get("_show_found", True)
        self.classes["me"] = bool(r.get("me"))
        self.classes["win"] = bool(r.get("winner")) and bool(r.get("_show_rank"))
