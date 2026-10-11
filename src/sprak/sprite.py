from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from sprak import aseprite
from sprak.frame import Frame
from sprak.json_types import SpriteJSON
from sprak.log import logger
from sprak.parse import parse_filename
from sprak.rect import Rect


class Sprite:
    def __init__(self, name: str) -> None:
        self.name = name
        self.frames: list[Frame] = []
        self.animations: dict[str, list[Frame]] = {}
        self.nine_slice: list[Rect] = []

    def to_json(self) -> SpriteJSON:
        sprite_json: SpriteJSON = {"frames": [f.name for f in self.frames]}

        if self.animations:
            animations = {animation: [f.name for f in frames] for (animation, frames) in self.animations.items()}
            sprite_json["animations"] = animations

        if self.nine_slice:
            sprite_json["nine_slice"] = [rect.to_json() for rect in self.nine_slice]

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
    def from_aseprite(cls, batch: list[tuple[str, Path]]) -> list[Sprite]:
        sprites = []
        # ToDo: slices, animations

        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data = aseprite.batch_export_frames(batch, export_dir=tmp)
            for name, _ in batch:
                sprite = cls(name)
                sprite_data = data[name]

                if frames := sprite_data["frames"]:
                    for frame_name, frame_data in frames.items():
                        frame_number = frame_data["frame_number"]
                        frame_duration = frame_data["duration"]
                        frame_filepath = frame_data["filepath"]

                        frame = Frame(frame_name, frame_filepath)
                        frame.frame_number = frame_number
                        frame.duration = frame_duration
                        sprite.frames.append(frame)

                if tags := sprite_data["tags"]:
                    for tag_name, tag_data in tags.items():
                        sprite.animations[tag_name] = []
                        tag_range = range(tag_data["from"], tag_data["to"] + 1)
                        for frame in sprite.frames:
                            if frame.frame_number in tag_range:
                                sprite.animations[tag_name].append(frame)

                if (slices := sprite_data["slices"]) and len(slices) == 1:
                    bounds = slices[0].get("bounds")
                    center = slices[0].get("center")
                    if bounds and center:
                        bounds = Rect(bounds["x"], bounds["y"], bounds["w"], bounds["h"])
                        center = Rect(center["x"], center["y"], center["w"], center["h"])

                        left_x = bounds.x
                        center_x = bounds.x + center.x
                        right_x = bounds.x + center.x + center.width

                        top_y = bounds.y
                        center_y = bounds.y + center.y
                        bottom_y = bounds.y + center.y + center.height

                        left_width = center_x - left_x
                        center_width = center.width
                        right_width = bounds.width - left_width - center_width

                        top_height = center_y - top_y
                        center_height = center.height
                        bottom_height = bounds.height - top_height - center_height

                        sprite.nine_slice = [
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

                sprites.append(sprite)

        return sprites
