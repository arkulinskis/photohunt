from anvil import *

from ._anvil_designer import AlbumPhotoTemplate


class AlbumPhoto(AlbumPhotoTemplate):
    """A kid's snap in the album, polaroid style (no photo = they tapped "I did it" for a task)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        f = self.item
        self.photo.photo_key, self.photo.art = f.get("photo_key") or "", f.get("art") or ""
        self.photo.alt = "%s's photo" % f["player"]
        self.topper.topper, self.topper.colour = f["topper"], f["colour"]
        self.classes["pending"] = f.get("status") == "review"
