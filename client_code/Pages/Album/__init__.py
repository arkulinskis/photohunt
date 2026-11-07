import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import AlbumTemplate
from ... import router, state


class Album(AlbumTemplate):
    """#album/<id>, the party album: results with stickers, every treasure with each kid's snap of it, printable
    certificates (only shown when printing), and "Delete kids' photos"."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hid = args[0] if args else ""
        state.heading(self.title, 1)
        self._load()

    def _load(self):
        r: dict = {"ok": False}
        if self.hid:
            r = anvil.server.call("album", self.hid)
        self.gone.visible = not r.get("ok")
        self.main.visible = bool(r.get("ok"))
        if not r.get("ok"):
            return
        h, mine = r["hunt"], r["mine"]
        self.h = h
        self.title.text = "%s: the album" % h["title"]
        when = h.get("finished") or h.get("started") or h.get("created")
        self.sub.text = "%s · %s · %s" % (state.short_date(when) if when else "Not played yet", state.plural(len(r["players"]), "player"),
                                         state.plural(r["photos"], "photo"))
        self.results_panel.items = r["players"]
        self.no_players.visible = not r["players"]
        self.treasures_panel.items = r["treasures"]
        date = state.short_date(when) + " " + (when or "")[:4] if when else ""
        self.certs_panel.items = [dict(p, _hunt=h["title"], _date=date) for p in r["players"]]
        self.print_button.visible = bool(r["players"])
        self.wipe_button.visible = mine and r["photos"] > 0
        self.make_button.visible = not mine
        state.set_attr(self.back_link, "href", router.href("hunt", h["id"]))

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        root = window.document.documentElement
        if root is not None:
            root.classList.add("ph-print-certs")
        window.print()
        if root is not None:
            root.classList.remove("ph-print-certs")

    @handle("make_button", "click")
    def make_button_click(self, **event_args):
        r = state.call("copy_hunt", self.hid)
        if r:
            router.go("hunt", r["hunt"]["id"])

    @handle("wipe_button", "click")
    def wipe_button_click(self, **event_args):
        if confirm("Every photo the kids took in this hunt is deleted. The results and stickers stay.",
                   title="Delete the kids' photos?", buttons=[("Cancel", False), ("Delete photos", True)]):
            r = state.call("delete_kid_photos", self.hid)
            if r:
                state.toast("Deleted %s" % state.plural(r["deleted"], "photo"), "ok")
                self._load()
