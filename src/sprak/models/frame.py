from pathlib import Path
from typing import Any

from PIL import Image


class Frame:
    def __init__(self, name: str, source_image: Path) -> None:
        self._image = None

        # The name of the frame - referencing this is how we'll retrieve it from the atlas
        self.name: str = name

        # Original sprite size
        self.sprite_width: int = 0
        self.sprite_height: int = 0

        # The sprite's top-left pixel offset in the original canvas
        self.offset_x: int = 0
        self.offset_y: int = 0

        # Frame width after trimming transparent edges
        self.frame_width: int = 0
        self.frame_height: int = 0

        # Frame position on the atlas
        self.x: int = 0
        self.y: int = 0

        # Extra metadata that will be included in the framedata file
        self.metadata: dict[str, Any] = {}

        self.load_source_image(source_image)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        return str(self)

    @property
    def image(self) -> Image.Image:
        """The cropped image that will be placed onto the atlas."""
        return self._image

    def load_source_image(self, source_image: Path) -> None:
        """Load source image data."""
        image = Image.open(source_image)

        self.sprite_width = image.width
        self.sprite_height = image.height
        self.frame_width = image.width
        self.frame_height = image.height

        self._image = image

    def trim_edges(self) -> None:
        """ Trim transparent edges on the sprite. """
        if bbox := self._image.getbbox():
            left, upper, right, lower = bbox
            self.offset_x = left
            self.offset_y = upper
            self.frame_width = right - left
            self.frame_height = lower - upper
            self._image = self._image.crop(bbox)

    def to_dict(self) -> dict:
        """Return the frame as a dictionary that can be JSON serialized."""
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "frame_width": self.frame_width,
            "frame_height": self.frame_height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "sprite_width": self.sprite_width,
            "sprite_height": self.sprite_height,
            "metadata": self.metadata,
        }
