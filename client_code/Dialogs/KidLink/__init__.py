import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import KidLinkTemplate
from ... import ph, router, state


class KidLink(KidLinkTemplate):
    """A kid's private Kids' corner link as a QR code. "Make a new link" stops the old one. Closes with the kid."""

    def __init__(self, kid, **properties):
        super().__init__(**properties)
        self.k = kid
        state.set_control_attr(self.link_box, "readonly", "readonly")
        state.set_control_attr(self.link_box, "aria-label", "Kids' corner link")
        self._draw()

    def _draw(self):
        url = ph.kid_url(self.k["token"])
        self.dom_nodes["heading"].textContent = "%s's corner" % self.k["name"]
        self.dom_nodes["intro"].textContent = "Open %s's Kids' corner on the tablet the kids use. Keep this link in the family: anyone with it can play as %s." % (self.k["name"], self.k["name"])
        self.qr.text = url
        self.link_box.text = url
        self.open_link.url = router.href("kid", self.k["token"])
        node = state.control(self.open_link)
        node.removeAttribute("target")
        node.removeAttribute("rel")

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        try:
            window.navigator.clipboard.writeText(self.link_box.text)
            state.toast("Link copied", "ok")
        except Exception:
            state.toast("Select the link and copy it.")

    @handle("open_link", "click")
    def open_link_click(self, **event_args):
        self.raise_event("x-close-alert", value=self.k)

    @handle("new_button", "click")
    def new_button_click(self, **event_args):
        if not confirm("The old link and QR code stop working. A tablet that already has the corner needs the new one.",
                       title="Make a new link?", buttons=[("Cancel", False), ("Make a new link", True)]):
            return
        r = state.call("new_kid_link", self.k["id"])
        if r:
            self.k = r["kid"]
            self._draw()
            state.toast("New link made", "ok")

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=self.k)
