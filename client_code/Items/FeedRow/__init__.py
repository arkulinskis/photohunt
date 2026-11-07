from anvil import *

from ._anvil_designer import FeedRowTemplate
from ... import state

VERB = {"ok": "found", "review": "is waiting for a check on", "rejected": "will try again for"}


class FeedRow(FeedRowTemplate):
    """One line of the live board's activity: "Mia found the red teapot · 2 minutes ago"."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r = self.item
        self.topper.topper, self.topper.colour = r["topper"], r["colour"]
        verb = "did" if (r["kind"] == "task" and r["status"] == "ok") else VERB.get(r["status"], "found")
        self.text.text = "%s %s %s" % (r["player"], verb, r["treasure"])
        self.when.text = state.ago(r["created"])
