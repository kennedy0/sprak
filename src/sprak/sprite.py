from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from . import aseprite


@dataclass
class Sprite:
    name: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    source_file: str = ""
    source_format: str = ""
    source_width: int = 0
    source_height: int = 0
    offset_x: int = 0
    offset_y: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    image: Image.Image | None = None

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        """Check if this sprite has an area of zero."""
        if self.area:
            return False

        return True

    def to_dict(self) -> dict:
        excluded_fields = {"image"}

        def _dict_factory(fields: list[tuple[str, Any]]) -> dict:
            return {k: v for (k, v) in fields if k not in excluded_fields}

        return asdict(self, dict_factory=_dict_factory)

    @classmethod
    def from_image(cls, file: Path, name: str) -> Sprite:
        sprite = cls(name)

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
                sprite.image = image.crop(bbox)
            else:
                sprite.image = image.copy()

            if image_format := image.format:
                sprite.source_format = image_format.lower()
            else:
                sprite.source_format = file.stem

        return sprite

    @classmethod
    def from_aseprite(cls, file: Path, name: str) -> list[Sprite]:
        sprites = []

        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data_json = tmp / f"{file.stem}.json"
            sprite_name = tmp / f"{file.stem}.0001.png"

            cmd = [aseprite.get_aseprite_exe()]
            cmd += ["--batch"]
            cmd += ["--noinapp"]
            cmd += ["--list-tags"]
            cmd += ["--list-slices"]
            cmd += ["--data", data_json.absolute().as_posix()]
            cmd += ["--format", "json-array"]
            cmd += [file.absolute().as_posix()]
            cmd += ["--save-as", sprite_name.as_posix()]
            subprocess.run(cmd, check=True)

            with data_json.open() as fp:
                file_data = json.load(fp)
                frames: list[dict] = file_data["frames"]
                tags: list[dict] = file_data["meta"]["frameTags"]
                print(tags)

            for i, frame_data in enumerate(frames, start=1):
                frame_name = f"{name}.{i:04d}"
                frame_path = tmp / f"{file.stem}.{i:04d}.png"
                sprite = cls.from_image(frame_path, frame_name)
                sprite.metadata.update({"source_format": "aseprite"})
                sprites.append(sprite)
                print(frame_data)

        return sprites
