from anvil import *
from anvil.js import window

from ._anvil_designer import ShareTemplate
from ... import ph, state


class Share(ShareTemplate):
    """The hunt's QR code, code and link, ready to show, copy or print as a party card."""

    def __init__(self, hunt, **properties):
        super().__init__(**properties)
        url = ph.join_url(hunt["code"])
        self.qr.text = url
        self.code.text = hunt["code"]
        self.link_box.text = url
        self.dom_nodes["site"].textContent = str(window.location.host)
        self.dom_nodes["title"].textContent = "Scan to join %s!" % hunt["title"]
        state.set_control_attr(self.link_box, "readonly", "readonly")
        state.set_control_attr(self.link_box, "aria-label", "Link to join the hunt")

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        try:
            window.navigator.clipboard.writeText(self.link_box.text)
            state.toast("Link copied", "ok")
        except Exception:
            state.control(self.link_box).select()
            state.toast("Select the link and copy it.")

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        root = window.document.documentElement
        if root is not None:
            root.classList.add("ph-printing")
        window.print()
        if root is not None:
            root.classList.remove("ph-printing")

    @handle("close_button", "click")
    def close_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)
