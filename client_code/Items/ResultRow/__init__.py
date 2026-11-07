from anvil import *

from ._anvil_designer import ResultRowTemplate


class ResultRow(ResultRowTemplate):
    """A player's result in the album: place, topper, name, candles lit, stickers won."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r = self.item
        self.dom_nodes["rank"].textContent = str(r.get("rank", ""))
        self.topper.topper, self.topper.colour = r["topper"], r["colour"]
        self.meta.text = "%d of %d candles" % (r.get("found", 0), r.get("total", 0)) + ("  ·  Winner!" if r.get("winner") else "")
        self.classes["win"] = bool(r.get("winner"))
        self.stickers_panel.items = [{"id": s, "size": 40} for s in (r.get("stickers") or [])]
