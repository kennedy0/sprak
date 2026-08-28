from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NotRequired, TypedDict

from sprak import aseprite
from sprak.frame import Frame
from sprak.log import logger
from sprak.parse import parse_filename
from sprak.rect import Rect, RectJSON


class SpriteJSON(TypedDict):
    frames: list[str]
    animations: NotRequired[dict[str, list[str]]]
    slice9: NotRequired[list[RectJSON]]


class Sprite:
    def __init__(self, name: str) -> None:
        self.name = name
        self.frames: list[Frame] = []
        self.animations: dict[str, list[Frame]] = {}
        self.slice9: list[Rect] = []

    def add_frame(self, frame: Frame) -> None:
        self.frames.append(frame)

    def to_json(self) -> SpriteJSON:
        sprite_json: SpriteJSON = {"frames": [f.name for f in self.frames]}

        if self.animations:
            sprite_json["animations"] = {
                animation: [f.name for f in frames] for (animation, frames) in self.animations.items()
            }

        if self.slice9:
            sprite_json["slice9"] = [rect.to_json() for rect in self.slice9]

        return sprite_json

    @classmethod
    def from_image(cls, name: str, file: Path) -> Sprite:
        sprite = cls(name)
        frame = Frame(name, file)
        sprite.frames.append(frame)
        return sprite

    @classmethod
    def from_sequence(cls, rel_path: str, files: list[Path]) -> Sprite:
        sprite_name = parse_filename(files[0]).sprite_name
        if rel_path:
            sprite_name = f"{rel_path}/{sprite_name}"

        sprite = cls(sprite_name)
        animations: dict[str, list[Frame]] = defaultdict(list)

        for file in sorted(files):
            frame_name = file.stem
            if rel_path:
                frame_name = f"{rel_path}/{frame_name}"

            frame = Frame(frame_name, file)
            _, animation_name, frame_number = parse_filename(file)
            if animation_name:
                animations[animation_name].append(frame)
            if frame_number is not None:
                frame.frame_number = frame_number
            sprite.frames.append(frame)

        if animations:
            sprite.animations = animations

        return sprite

    @classmethod
    def from_aseprite(cls, name: str, file: Path) -> Sprite:
        sprite = cls(name)

        # Get data from file
        aseprite_data = aseprite.read_json_data(file)
        frame_data = aseprite_data["frames"]
        tags = aseprite_data["meta"]["frameTags"]
        tag_frame_ranges = {tag["name"]: range(tag["from"] + 1, tag["to"] + 2) for tag in tags}
        slices = aseprite_data["meta"]["slices"]

        # Warn about duplicate tags
        duplicate_tags = {tag for tag in tags if tags.count(tag) > 1}
        for tag in duplicate_tags:
            logger.warning(f"duplicate '{tag}' tags found in {file.as_posix()}")

        # Add animations from tags
        for tag in tags:
            sprite.animations[tag["name"]] = []

        # Add 9-slice data
        # There must be only a single frame and a single slice in the Aseprite file
        if len(frame_data) == 1 and len(slices) == 1 and len(slices[0]["keys"]) == 1:
            bounds = slices[0]["keys"][0].get("bounds")
            center = slices[0]["keys"][0].get("center")
            if bounds and center:
                bounds = Rect(**bounds)
                center = Rect(**center)

                left_x = bounds.x
                center_x = bounds.x + center.x
                right_x = bounds.x + center.x + center.w

                top_y = bounds.y
                center_y = bounds.y + center.y
                bottom_y = bounds.y + center.y + center.h

                left_width = center_x - left_x
                center_width = center.w
                right_width = bounds.w - left_width - center_width

                top_height = center_y - top_y
                center_height = center.h
                bottom_height = bounds.h - top_height - center_height

                sprite.slice9 = [
                    Rect(left_x, top_y, left_width, top_height),  # top-left
                    Rect(center_x, top_y, center_width, top_height),  # top-center
                    Rect(right_x, top_y, right_width, top_height),  # top-right
                    Rect(left_x, center_y, left_width, center_height),  # center-left
                    Rect(center_x, center_y, center_width, center_height),  # center
                    Rect(right_x, center_y, right_width, center_height),  # center-right
                    Rect(left_x, bottom_y, left_width, bottom_height),  # bottom-left
                    Rect(center_x, bottom_y, center_width, bottom_height),  # bottom-center
                    Rect(right_x, bottom_y, right_width, bottom_height),  # bottom-right
                ]

        # Create a Frame from each frame in the Aseprite file
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
                for tag, frame_range in tag_frame_ranges.items():
                    if i in frame_range:
                        sprite.animations[tag].append(frame)
                sprite.frames.append(frame)

        return sprite
