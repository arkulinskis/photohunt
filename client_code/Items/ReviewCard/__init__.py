from anvil import *

from ._anvil_designer import ReviewCardTemplate


class ReviewCard(ReviewCardTemplate):
    """A photo waiting for a grown-up: your photo next to the kid's, yes or try again (x-review to the page)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r = self.item
        self.target.photo_key, self.target.art, self.target.alt = r.get("treasure_photo_key") or "", r.get("treasure_art") or "", r["treasure"]
        self.snap.photo_key, self.snap.art, self.snap.alt = r.get("photo_key") or "", r.get("art") or "", "%s's photo" % r["player"]
        self.dom_nodes["who"].textContent = "%s's snap" % r["player"]
        score = (" (match %d%%)" % int(100 * r["score"])) if r.get("score") else ""
        self.what.text = ("%s did: %s" if r["kind"] == "task" else "%s says this is: %s") % (r["player"], r["treasure"]) + score

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        self.parent.raise_event("x-review", find=self.item, approve=True)

    @handle("no_button", "click")
    def no_button_click(self, **event_args):
        self.parent.raise_event("x-review", find=self.item, approve=False)
