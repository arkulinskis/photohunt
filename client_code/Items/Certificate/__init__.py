from anvil import *

from ._anvil_designer import CertificateTemplate


class Certificate(CertificateTemplate):
    """A printable certificate for one player (shown only when printing the album). item = result + _hunt, _date."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r = self.item
        self.topper.topper, self.topper.colour = r["topper"], r["colour"]
        self.what.text = "lit %d of %d candles%s" % (r.get("found", 0), r.get("total", 0), " and won the hunt!" if r.get("winner") else "!")
        self.hunt.text = "%s · %s" % (r.get("_hunt", ""), r.get("_date", ""))
        self.stickers_panel.items = [{"id": s, "size": 44} for s in (r.get("stickers") or [])]
