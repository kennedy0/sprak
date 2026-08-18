from __future__ import annotations

from pathlib import Path

from PIL import Image


class Sprite:
    def __init__(self, name: str) -> None:
        self.name: str = name

        self.x: int = 0
        self.y: int = 0
        self.width: int = 0
        self.height: int = 0
        self.source_file: str = ""
        self.source_width: int = 0
        self.source_height: int = 0
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.frame: int = 0
        self.duration: int = 0

        self._image: Image.Image | None = None

    @property
    def image(self) -> Image.Image | None:
        return self._image

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        return self.area == 0

    def to_dict(self) -> dict:
        """Returns the sprite data as a dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "source_file": self.source_file,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "frame": self.frame,
            "duration": self.duration,
        }

    @classmethod
    def from_image(cls, file: Path, name: str) -> Sprite:
        sprite = cls(name)
        sprite.source_file = file.name

        with Image.open(file) as image:
            sprite.width = image.width
            sprite.height = image.height
            sprite.source_width = image.width
            sprite.source_height = image.height

            if bbox := image.getbbox():
                left, upper, right, lower = bbox
                sprite.width = right - left
                sprite.height = lower - upper
                sprite.offset_x = left
                sprite.offset_y = upper
                sprite._image = image.crop(bbox)
            else:
                sprite._image = image.copy()

        return sprite
