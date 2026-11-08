from anvil import *

from ._anvil_designer import TaskRowTemplate
from ... import state


class TaskRow(TaskRowTemplate):
    """A task from the library: text, category, timer, proof; "Hear it" plays its recorded voice. In pick mode a tick box
    picks it (x-pick to the page). item = task dict + _cat_label, _pick (show the box), _picked."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        self.cat.text = t.get("_cat_label", "")
        self.timer.text = ("%d s" % t["timer"]) if t["timer"] else ""
        self.timer.visible = bool(t["timer"])
        self.proof.text = "Snap a photo" if t["proof"] == "photo" else "Tap when done"
        self.speak.text = t["text"]
        self.speak.lib_id = t["id"]
        self.pick.visible = bool(t.get("_pick"))
        self.pick.checked = bool(t.get("_picked"))
        self.classes["on"] = bool(t.get("_picked"))
        state.set_control_attr(self.pick, "aria-label", "Pick: " + t["text"])

    @handle("pick", "change")
    def pick_change(self, **event_args):
        self.item["_picked"] = self.pick.checked
        self.classes["on"] = self.pick.checked
        self.parent.raise_event("x-pick", task=self.item, picked=self.pick.checked)
