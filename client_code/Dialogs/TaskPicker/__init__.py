import anvil.server
from anvil import *

from ._anvil_designer import TaskPickerTemplate
from ... import state

_lib: dict = {}


def library():
    """The task library (100 tasks), fetched once per visit."""
    if "v" not in _lib:
        _lib["v"] = anvil.server.call("task_library")
    return _lib["v"]


class TaskPicker(TaskPickerTemplate):
    """Pick tasks from the library and add them to the hunt. Closes with how many were added (or None)."""

    def __init__(self, hunt, **properties):
        super().__init__(**properties)
        self.h = hunt
        lib = library()
        self.cats = lib["categories"]
        self.labels = {c["key"]: c["label"] for c in self.cats}
        self.tasks: list = [dict(t, _cat_label=self.labels.get(t["cat"], ""), _pick=True, _picked=False) for t in lib["tasks"]]
        self.cat = "all"
        self.cats_panel.add_event_handler("x-cat", self._cat)
        self.tasks_panel.add_event_handler("x-pick", self._picked)
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
        self.count.text = state.plural(n, "task") + " picked"
        self.add_button.enabled = n > 0
        self.add_button.text = "Add %s" % state.plural(n, "task") if n else "Add tasks"

    def _cat(self, key, **event_args):
        self.cat = key
        self._draw()
        state.refocus(self.cats_panel, key)

    def _picked(self, task, picked, **event_args):
        self._count()

    @handle("search_box", "change")
    def search_box_change(self, **event_args):
        self._draw()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        ids = [t["id"] for t in self.tasks if t["_picked"]]
        r = anvil.server.call("add_library_tasks", self.h["id"], ids)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.raise_event("x-close-alert", value=r["added"])
