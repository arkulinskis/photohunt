import anvil.server
from anvil import *

from ._anvil_designer import TasksTemplate
from ... import router, state
from ...Dialogs.TaskPicker import library


class Tasks(TasksTemplate):
    """#tasks, the public library of 100 party tasks. Signed-in grown-ups tick tasks and add them to one of their
    task or mix hunts."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.title, 1)
        lib = library()
        self.cats = lib["categories"]
        labels = {c["key"]: c["label"] for c in self.cats}
        me = state.me()
        self.tasks: list = [dict(t, _cat_label=labels.get(t["cat"], ""), _pick=bool(me), _picked=False) for t in lib["tasks"]]
        self.cat = args[0] if args and args[0] in labels else "all"
        self.cats_panel.add_event_handler("x-cat", self._cat)
        self.tasks_panel.add_event_handler("x-pick", self._picked)
        self.add_bar.visible = bool(me)
        self.guest_bar.visible = not me
        self.hunts: list = []
        if me:
            d = anvil.server.call("get_hq")
            self.hunts = [h for h in d["hunts"] if h["kind"] in ("task", "mix")]
            self.hunt_drop.items = [(h["title"], h["id"]) for h in self.hunts] or [("Make a task party first", None)]
            state.set_control_attr(self.hunt_drop, "aria-label", "Hunt to add them to")
        self._draw()

    def _draw(self):
        self.cats_panel.items = [{"key": "all", "label": "All", "count": len(self.tasks), "on": self.cat == "all"}] + [
            {"key": c["key"], "label": c["label"], "count": c["count"], "on": self.cat == c["key"]} for c in self.cats]
        q = (self.search_box.text or "").strip().lower()
        shown = [t for t in self.tasks if (self.cat == "all" or t["cat"] == self.cat) and (not q or q in str(t["text"]).lower())]
        self.tasks_panel.items = shown
        self.empty.visible = not shown
        self._count()

    def _count(self):
        n = len([t for t in self.tasks if t["_picked"]])
        self.picked.text = state.plural(n, "task") + " picked"
        self.add_button.enabled = n > 0 and bool(self.hunts)

    def _cat(self, key, **event_args):
        self.cat = key
        self._draw()
        state.refocus(self.cats_panel, key)

    def _picked(self, task, picked, **event_args):
        self._count()

    @handle("search_box", "change")
    def search_box_change(self, **event_args):
        self._draw()

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        hid = self.hunt_drop.selected_value
        ids = [t["id"] for t in self.tasks if t["_picked"]]
        if not hid or not ids:
            return
        r = state.call("add_library_tasks", hid, ids)
        if r:
            state.toast("Added %s" % state.plural(r["added"], "task"), "ok")
            router.go("hunt", hid)
