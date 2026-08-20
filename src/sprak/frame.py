from __future__ import annotations

import re
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from sprak import aseprite
from sprak.log import logger

SPRITE_ANIM_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<animation>\w+)\.(?P<frame>\d+)$", re.IGNORECASE)
SPRITE_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<frame>\d+)$", re.IGNORECASE)


class Frame:
    def __init__(self, name: str, file: str | Path) -> None:
        self.name = name
        self.file = Path(file)
        self.sprite: str = ""
        self.animations: list[str] = []

        with Image.open(file) as image:
            width = image.width
            height = image.height
            source_width = image.width
            source_height = image.height

            if bbox := image.getbbox():
                left, upper, right, lower = bbox
                width = right - left
                height = lower - upper
                offset_x = left
                offset_y = upper
                image = image.crop(bbox)
            else:
                offset_x = 0
                offset_y = 0
                image = image.copy()

        self.x: int = 0
        self.y: int = 0
        self.width: int = width
        self.height: int = height
        self.source_width: int = source_width
        self.source_height: int = source_height
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y
        self.frame_number: int = 0
        self.duration: int = 0
        self.image: Image.Image = image

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        return self.area == 0

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "frame_number": self.frame_number,
            "duration": self.duration,
        }

    @classmethod
    def from_image(cls, name: str, file: Path) -> Frame:
        """Get a frame from a single image file."""
        frame = cls(name, file)

        # Parse the file name to look for sprite / animation / frame
        if match := SPRITE_ANIM_FRAME_RE.match(name):
            frame.sprite = match.group("sprite")
            frame.animations.append(match.group("animation"))
            frame.frame_number = int(match.group("frame"))
        elif match := SPRITE_FRAME_RE.match(name):
            frame.sprite = match.group("sprite")
            frame.frame_number = int(match.group("frame"))

        return frame

    @classmethod
    def from_aseprite(cls, name: str, file: Path) -> list[Frame]:
        aseprite_data = aseprite.read_json_data(file)
        frame_data = aseprite_data["frames"]
        tags = aseprite.get_tag_frame_ranges(aseprite_data)
        slice_data = aseprite_data["meta"]["slices"]  # ToDo: Add slice data

        for tag in aseprite.get_duplicate_tags(aseprite_data):
            logger.warning(f"duplicate '{tag}' tags found in {file.as_posix()}")

        frames = []
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sequence_path = tmp / (file.stem + ".%04d.png")
            aseprite.export_frames(file, sequence_path)

            for i, data in enumerate(frame_data, start=1):
                frame_path = sequence_path.absolute().as_posix() % i
                frame_name = f"{name}.{i:04d}"

                frame = cls(frame_name, frame_path)
                frame.sprite = name
                for tag, frame_range in tags:
                    if i in frame_range:
                        frame.animations.append(tag)
                frame.frame_number = i
                frame.duration = data["duration"]
                frames.append(frame)

        return frames
