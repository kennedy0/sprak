from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from sprak import aseprite
from sprak.frame import Frame
from sprak.log import logger
from sprak.rect import Rect


class Sprite:
    def __init__(self, name: str) -> None:
        self.name = name
        self.frames: list[Frame] = []
        self.animations: dict[str, list[Frame]] = {}
        self.slice: dict[str, Rect] | None = None

    def add_frame(self, frame: Frame) -> None:
        self.frames.append(frame)

    def to_json(self) -> dict:
        d = {"frames": [f.name for f in self.frames]}

        if self.animations:
            d["animations"] = {animation: [f.name for f in frames] for (animation, frames) in self.animations.items()}

        if self.slice:
            d["slice"] = self.slice
            d.update({"slice": self.slice})

        return d

    @classmethod
    def from_image(cls, name: str, file: Path) -> Sprite:
        sprite = cls(name)
        frame = Frame(name, file)
        sprite.frames.append(frame)
        return sprite

    @classmethod
    def from_images(cls, name: str, files: list[Path]) -> Sprite:
        sprite = cls(name)
        # Parse the file name to look for sprite / animation / frame
        # SPRITE_ANIM_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<animation>\w+)\.(?P<frame>\d+)$", re.IGNORECASE)
        # SPRITE_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<frame>\d+)$", re.IGNORECASE)
        # if match := SPRITE_ANIM_FRAME_RE.match(name):
        #     frame.sprite = match.group("sprite")
        #     frame.animations.append(match.group("animation"))
        #     frame.frame_number = int(match.group("frame"))
        # elif match := SPRITE_FRAME_RE.match(name):
        #     frame.sprite = match.group("sprite")
        #     frame.frame_number = int(match.group("frame"))

        return sprite

    @classmethod
    def from_aseprite(cls, name: str, file: Path) -> Sprite:
        sprite = cls(name)

        aseprite_data = aseprite.read_json_data(file)
        frame_data = aseprite_data["frames"]
        tags = aseprite.get_tag_frame_ranges(aseprite_data)
        slice_data = aseprite_data["meta"]["slices"]

        if slice_data:
            print("ToDo: add slice data")

        for tag in aseprite.get_duplicate_tags(aseprite_data):
            logger.warning(f"duplicate '{tag}' tags found in {file.as_posix()}")

        for tag, _ in tags:
            sprite.animations[tag] = []

        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            sequence_path = tmp / (file.stem + ".%04d.png")
            aseprite.export_frames(file, sequence_path)
            for i, data in enumerate(frame_data, start=1):
                frame_name = f"{name}.{i:04d}"
                frame_path = sequence_path.absolute().as_posix() % i
                frame = Frame(frame_name, frame_path)
                frame.frame_number = i
                frame.duration = data["duration"]
                for tag, frame_range in tags:
                    if i in frame_range:
                        sprite.animations[tag].append(frame)
                sprite.frames.append(frame)

        return sprite
