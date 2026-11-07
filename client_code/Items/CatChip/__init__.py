from anvil import *

from ._anvil_designer import CatChipTemplate
from ... import state


class CatChip(CatChipTemplate):
    """A category filter chip (Tasks page, task picker). item = {key, label, count, on}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c = self.item
        self.chip.text = "%s (%d)" % (c["label"], c["count"]) if c.get("count") is not None else c["label"]
        self.chip.role = ["btn", "btn-sm", "ph-chip"] + (["on"] if c.get("on") else [])
        state.set_control_attr(self.chip, "aria-pressed", "true" if c.get("on") else "false")
        state.set_control_attr(self.chip, "data-key", c["key"])

    @handle("chip", "click")
    def chip_click(self, **event_args):
        self.parent.raise_event("x-cat", key=self.item["key"])
