import anvil.server
from anvil import *

from ._anvil_designer import HuntTemplate
from ... import ph, router, state

STATUS = {"draft": ("Getting ready", "badge-warn"), "live": ("Hunt on!", "badge-good"), "finished": ("Finished", "badge")}
EMPTY = {
    "photo": "Press Snap a treasure and take pictures of 5 to 10 things around the house: a teapot, a teddy, a red sock...",
    "voice": "Snap a treasure, then record a clue in your voice. Kids hear the clue, not the photo.",
    "task": "Add fun tasks from the library of 100, or write your own and record yourself saying it.",
    "mix": "Snap things to find and add a few tasks: a little of everything.",
}


class Hunt(HuntTemplate):
    """#hunt/<id>, the hunt kitchen: settings, welcome message, treasures (add, edit, order, delete), share, live board.
    Example hunts open read-only with "Make one like this"."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hid = args[0] if args else ""
        self.h: dict = {}
        self.mine = False
        state.heading(self.title, 1)
        self.treasures_panel.add_event_handler("x-edit", self._edit)
        self.treasures_panel.add_event_handler("x-move", self._move)
        self.treasures_panel.add_event_handler("x-delete", self._delete)
        self._load()

    def _load(self):
        r: dict = {"ok": False}
        if self.hid:
            r = anvil.server.call("get_hunt", self.hid)
        self.gone.visible = not r.get("ok")
        self.main.visible = bool(r.get("ok"))
        if not r.get("ok"):
            return
        self.h, self.mine = r["hunt"], r["mine"]
        h, ts = self.h, r["treasures"]
        self.cake.flavour, self.cake.total, self.cake.lit = h["flavour"], len(ts), 0
        self.title.text = h["title"]
        bits = [ph.KIND_LABEL.get(h["kind"], "Hunt")]
        if h["birthday_name"]:
            bits.append("for %s%s" % (h["birthday_name"], (", turning %d" % h["birthday_age"]) if h["birthday_age"] else ""))
        bits.append(("%d minutes" % h["time_limit"]) if h["time_limit"] else "no time limit")
        bits.append("race" if h["win_style"] == "race" else "one cake for everyone")
        self.meta.text = " · ".join(bits)
        label, role = STATUS.get(h["status"], STATUS["draft"])
        self.status.text, self.status.role = label, ["badge", role]
        self.code.text = "Code " + h["code"]
        self.actions.visible = self.welcome_box.visible = self.add_row.visible = self.mine
        self.example_box.visible = not self.mine
        for link in (self.live_link, self.live2_link):
            state.set_attr(link, "href", router.href("live", h["id"]))
        state.set_attr(self.album_link, "href", router.href("album", h["id"]))
        state.set_attr(self.example_album, "href", router.href("album", h["id"]))
        state.set_attr(self.example_play, "href", router.href("join", h["code"]))
        self.example_play.visible = h["code"] == "CAKE42"
        self.intro_rec.voice_key = h.get("intro_key") or ""
        k = h["kind"]
        self.add_find_button.visible = k in ("photo", "voice", "mix")
        self.add_lib_button.visible = self.add_task_button.visible = k in ("task", "mix")
        self.add_find_button.text = "Add a voice clue" if k == "voice" else "Snap a treasure"
        n = len(ts)
        self.count.text = "Treasures (%d)" % n if k != "task" else "Tasks (%d)" % n
        self.treasures_panel.items = [dict(t, _mine=self.mine, _first=i == 0, _last=i == n - 1) for i, t in enumerate(ts)]
        self.empty.visible = not ts
        self.empty_text.text = EMPTY.get(k, EMPTY["photo"]) if self.mine else "This example has no treasures."
        self.ready_box.visible = self.mine and n > 0

    # ---- hunt tools
    @handle("share_button", "click")
    def share_button_click(self, **event_args):
        from ...Dialogs.Share import Share
        alert(Share(hunt=self.h), large=True, buttons=[], role="app-dialog")

    @handle("share2_button", "click")
    def share2_button_click(self, **event_args):
        self.share_button_click()

    @handle("settings_button", "click")
    def settings_button_click(self, **event_args):
        from ...Dialogs.HuntSettings import HuntSettings
        if alert(HuntSettings(hunt=self.h), large=True, buttons=[], role="app-dialog"):
            state.toast("Saved", "ok")
            self._load()

    def _copy(self):
        r = state.call("copy_hunt", self.h["id"])
        if r:
            state.toast("Copied! This one is yours to change.", "ok")
            router.go("hunt", r["hunt"]["id"])

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        self._copy()

    @handle("make_button", "click")
    def make_button_click(self, **event_args):
        self._copy()

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("Its treasures, players and the kids' photos are deleted too. This can't be undone.",
                   title="Delete %s?" % self.h["title"], buttons=[("Cancel", False), ("Delete the hunt", True)]):
            if state.call("delete_hunt", self.h["id"]) is not None:
                state.toast("Hunt deleted")
                router.go("home")

    @handle("intro_rec", "recorded")
    def intro_rec_recorded(self, media, seconds, **event_args):
        if state.call("set_intro", self.h["id"], media, seconds):
            state.toast("Welcome message saved", "ok")

    @handle("intro_rec", "removed")
    def intro_rec_removed(self, **event_args):
        state.call("set_intro", self.h["id"], None, 0)

    # ---- treasures
    def _open_editor(self, treasure, kind):
        from ...Dialogs.TreasureEdit import TreasureEdit
        if alert(TreasureEdit(hunt=self.h, treasure=treasure, kind=kind), large=True, buttons=[], role="app-dialog"):
            state.toast("Saved", "ok")
            self._load()

    @handle("add_find_button", "click")
    def add_find_button_click(self, **event_args):
        self._open_editor({}, "find")

    @handle("add_task_button", "click")
    def add_task_button_click(self, **event_args):
        self._open_editor({}, "task")

    @handle("add_lib_button", "click")
    def add_lib_button_click(self, **event_args):
        from ...Dialogs.TaskPicker import TaskPicker
        n = alert(TaskPicker(hunt=self.h), large=True, buttons=[], role="app-dialog")
        if n:
            state.toast("Added %s" % state.plural(n, "task"), "ok")
            self._load()

    def _edit(self, treasure, **event_args):
        self._open_editor(treasure, treasure["kind"])

    def _move(self, treasure, step, **event_args):
        if state.call("move_treasure", treasure["id"], step) is not None:
            self._load()

    def _delete(self, treasure, **event_args):
        if confirm("Kids' finds for it are removed too.", title="Delete %s?" % treasure["name"],
                   buttons=[("Cancel", False), ("Delete", True)]):
            if state.call("delete_treasure", treasure["id"]) is not None:
                self._load()
