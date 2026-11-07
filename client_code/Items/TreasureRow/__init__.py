from anvil import *

from ._anvil_designer import TreasureRowTemplate
from ... import ph, state


class TreasureRow(TreasureRowTemplate):
    """One treasure in the hunt kitchen: its photo (or a task star), name, clue and what kids get; edit tools if mine.
    item = treasure dict + _mine, _first, _last."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        task = t["kind"] == "task"
        self.dom_nodes["num"].textContent = str(t["position"])
        self.pic_box.visible, self.task_box.visible = not task, task
        self.photo.photo_key, self.photo.art, self.photo.alt = t.get("photo_key") or "", t.get("art") or "", t["name"]
        self.name.text = t["name"] or "(no name)"
        self.clue.text = t["clue"] if (t["clue"] and t["clue"] != t["name"]) else ""
        self.clue.visible = bool(self.clue.text)
        self.voice_chip.text = ("Voice clue %s" % ph.clock(t["voice_seconds"])) if t.get("voice_key") else ""
        self.voice_chip.visible = bool(t.get("voice_key"))
        self.timer_chip.text = ("%d s timer" % t["timer"]) if t.get("timer") else ""
        self.timer_chip.visible = bool(t.get("timer"))
        self.proof_chip.text = ("Snap to show it" if t["proof"] == "photo" else "Tap when done") if task else ("" if t.get("has_photo") else "No photo: a grown-up checks")
        self.proof_chip.visible = bool(self.proof_chip.text)
        self.match_chip.visible = (not task) and bool(t.get("has_target"))
        mine = bool(t.get("_mine"))
        self.actions.visible = mine
        self.up_button.enabled = not t.get("_first")
        self.down_button.enabled = not t.get("_last")
        for b, what in ((self.up_button, "Move up"), (self.down_button, "Move down"), (self.edit_button, "Edit"), (self.delete_button, "Delete")):
            state.set_control_attr(b, "aria-label", "%s: %s" % (what, t["name"]))

    @handle("up_button", "click")
    def up_button_click(self, **event_args):
        self.parent.raise_event("x-move", treasure=self.item, step=-1)

    @handle("down_button", "click")
    def down_button_click(self, **event_args):
        self.parent.raise_event("x-move", treasure=self.item, step=1)

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.parent.raise_event("x-edit", treasure=self.item)

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        self.parent.raise_event("x-delete", treasure=self.item)
