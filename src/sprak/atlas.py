import io
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageText, UnidentifiedImageError

from sprak import aseprite
from sprak.frame import Frame
from sprak.log import logger
from sprak.parse import parse_filename
from sprak.rect import Rect
from sprak.sprite import Sprite

SPRITE_ANIM_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<animation>\w+)\.(?P<frame>\d+)$", re.IGNORECASE)
SPRITE_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<frame>\d+)$", re.IGNORECASE)

FONT_M5X7 = Path(__file__).parent / "fonts" / "m5x7.ttf"
FONT_SIZE = 16


class Atlas:
    def __init__(self) -> None:
        self.sprites: dict[str, Sprite] = {}
        self.frames: dict[str, Frame] = {}
        self._is_packed = False
        self._image = Image.new("RGBA", (0, 0))
        self._current_folder: Path | None = None
        self._history: list[tuple[Frame, list[Rect]]] = []  # (frame_added, current_regions)

    def add_sprite(self, sprite: Sprite) -> None:
        if sprite.name in self.sprites:
            logger.error(f"a sprite named {sprite.name} is already in the atlas")
            return

        logger.debug(f"adding sprite {sprite.name}")
        self._is_packed = False
        self.sprites[sprite.name] = sprite
        for frame in sprite.frames:
            if frame.name in self.frames:
                logger.error(f"a frame named {frame.name} is already in the atlas")
                continue
            self.frames[frame.name] = frame

    def add_file(self, file: Path) -> None:
        name = self._get_sprite_name(file)
        if aseprite.is_aseprite_file(file):
            self.add_sprite(Sprite.from_aseprite(name, file))
        elif is_image_file(file):
            self.add_sprite(Sprite.from_image(name, file))
        else:
            logger.debug(f"skipping unsupported file {file.as_posix()}")

    def add_folder(self, folder: Path) -> None:
        self._current_folder = folder

        for root, dirs, files in folder.walk():
            for seq in group_sequences([(root / f) for f in files]):
                if len(seq) == 1:
                    self.add_file(seq[0])
                else:
                    if root.samefile(folder):
                        rel_path = ""
                    else:
                        rel_path = root.relative_to(folder).as_posix()
                    self.add_sprite(Sprite.from_sequence(rel_path, seq))

        self._current_folder = None

    def to_json(self) -> dict:
        return {
            "frames": {k: v.to_json() for k, v in self.frames.items()},
            "sprites": {k: v.to_json() for k, v in self.sprites.items()},
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json(), indent=2, sort_keys=True)

    def write_zip(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        image_buffer = io.BytesIO()
        self._image.save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()

        with zipfile.ZipFile(file, mode="w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("json", self.to_json_str())
            zf.writestr("png", image_bytes)

    def write_json(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        with open(file, "w") as fp:
            fp.write(self.to_json_str())

    def write_png(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        self._image.save(file, format="PNG")

    def write_gif(self, file: str | Path, fps: float = 10) -> None:
        if fps <= 0:
            logger.error("fps must be greater than 0")
            return

        if not self._is_packed:
            self._pack()

        atlas_image = Image.new(self._image.mode, self._image.size)
        images: list[Image.Image] = []

        for frame, _ in self._history:
            atlas_image.paste(frame.image, box=(frame.x, frame.y))
            images.append(atlas_image.copy())

        images[0].save(file, format="GIF", save_all=True, disposal=2, append_images=images[1:], duration=1000 / fps)

    def write_debug_gif(self, file: str | Path, fps: float = 10) -> None:
        if fps <= 0:
            logger.error("fps must be greater than 0")
            return

        if not self._is_packed:
            self._pack()

        font = ImageFont.truetype(FONT_M5X7, FONT_SIZE)

        # Get max size of text
        max_text_w = 0
        max_text_h = 0
        for frame_name, frame in self.frames.items():
            frame_json = json.dumps(frame.to_json(), indent=2, sort_keys=True)
            _, _, name_w, _ = ImageText.Text(frame_name, font).get_bbox()
            _, _, json_w, json_h = ImageText.Text(frame_json, font).get_bbox()
            text_w = math.ceil(max(name_w, json_w))
            text_h = math.ceil(FONT_SIZE + json_h)
            max_text_w = max(text_w, max_text_w)
            max_text_h = max(text_h, max_text_h)

        text_spacing = 4
        image_width = self._image.width + text_spacing + max_text_w
        image_height = max(self._image.height, max_text_h)

        text_rect = (self._image.width, 0, image_width, image_height)
        name_text_position = (text_rect[0] + text_spacing, text_rect[1])
        json_text_position = (text_rect[0] + text_spacing, text_rect[1] + FONT_SIZE)

        color_red = (255, 0, 0)
        color_black = (0, 0, 0)
        color_white = (200, 200, 200)

        atlas_image = Image.new(self._image.mode, (image_width, image_height))
        images: list[Image.Image] = []

        for frame, regions in self._history:
            atlas_image.paste(frame.image, box=(frame.x, frame.y))
            image = atlas_image.copy()

            draw = ImageDraw.Draw(image)
            for rect in regions:
                draw.rectangle(rect.pil_rect, fill=color_black, outline=color_red)

            draw.rectangle(text_rect, fill=color_black)
            draw.text(name_text_position, frame.name, font=font, fill=color_white)
            draw.text(
                json_text_position,
                json.dumps(frame.to_json(), indent=2, sort_keys=True),
                font=font,
                fill=color_white,
            )

            images.append(image)

        images[0].save(file, format="GIF", save_all=True, disposal=2, append_images=images[1:], duration=1000 / fps)

    def _get_sprite_name(self, file: Path) -> str:
        """Get a sprite name by using its file name relative to the source folder that it was added from."""
        if self._current_folder:
            file = file.relative_to(self._current_folder)

        return file.with_suffix("").as_posix().strip("/")

    def _pack(self) -> None:
        size = self._calculate_starting_size()
        frames = list(self.frames.values())
        frames.sort(key=lambda f: f.area, reverse=True)

        # Place frames
        while True:
            logger.debug(f"packing frames on atlas size {size}x{size}")
            self._history.clear()
            regions = [Rect(0, 0, size, size)]
            overflow = False
            for frame in frames:
                # Skip completely transparent images
                if frame.is_empty:
                    continue

                # Try to find a region that the frame fits into
                if region := self._find_region(frame, regions):
                    # Place frame
                    frame.x = region.x
                    frame.y = region.y

                    # Split region and merge the results
                    regions.remove(region)
                    split_x = frame.x + frame.width
                    split_y = frame.y + frame.height
                    new_regions = self._split_region(region, split_x, split_y)
                    self._merge_regions(regions, new_regions)
                    regions.sort(key=lambda rect: rect.area)
                    self._history.append((frame, regions.copy()))
                else:
                    overflow = True
                    logger.debug("packing overflowed")
                    break

            # If the frames overflowed on the atlas, try again with increased atlas size
            if overflow:
                size = next_pow2(size)
            else:
                break

        # Create image
        self._image = Image.new("RGBA", (size, size))
        for frame in frames:
            if not frame.is_empty:
                self._image.paste(frame.image, box=(frame.x, frame.y))

        self._is_packed = True

    def _calculate_starting_size(self) -> int:
        """Calculate the starting size of the atlas.
        We assume the algorithm will be 100% efficient, meaning that the area of the atlas will be exactly the sum of the areas of the frames.
        Of course it won't, but rounding to the next power of 2 gives us some padding, which is a reasonable place to start.
        """
        area = math.sqrt(sum([f.area for f in self.frames.values()]))
        return round_pow2(area)

    def _find_region(self, frame: Frame, regions: list[Rect]) -> Rect | None:
        """Find a region that the frame fits into."""
        for region in regions:
            if frame.width <= region.w and frame.height <= region.h:
                return region

        return None

    def _split_region(self, region: Rect, x: int, y: int) -> list[Rect]:
        """Split a region using guillotine cutting.
        Both horizontal and vertical cutting are attempted.

        Horizontal:            Vertical:
               X                      X
        ┌──────┬────────┐      ┌──────┬────────┐
        │░░░░░░│  top   │      │░░░░░░│ right  │
        │░░░░░░│        │      │░░░░░░│        │
        ├──────┴────────┤ Y    ├──────┤        │ Y
        │    bottom     │      │ left │        │
        │               │      │      │        │
        └───────────────┘      └──────┴────────┘

        The aspect ratios of the resulting regions are compared against each other.
        The cutting direction that produces the "most square-ish" results (i.e. the least-extreme aspect ratio) wins.
        """
        left_w = x - region.left
        right_w = region.right - x + 1

        top_h = y - region.top
        bottom_h = region.bottom - y + 1

        top = Rect(x, region.y, right_w, top_h)
        bottom = Rect(region.x, y, region.w, bottom_h)
        left = Rect(region.x, y, left_w, bottom_h)
        right = Rect(x, region.y, right_w, region.h)

        horizontal = []
        if not top.is_empty:
            horizontal.append(top)
        if not bottom.is_empty:
            horizontal.append(bottom)

        vertical = []
        if not left.is_empty:
            vertical.append(left)
        if not right.is_empty:
            vertical.append(right)

        if not horizontal and not vertical:
            return []
        elif not horizontal:
            return vertical
        elif not vertical:
            return horizontal

        least_squarish_horizontal = min([rect.squareness for rect in horizontal])
        least_squarish_vertical = min([rect.squareness for rect in vertical])

        if least_squarish_horizontal < least_squarish_vertical:
            return vertical
        else:
            return horizontal

    def _merge_regions(self, regions: list[Rect], new_regions: list[Rect]) -> None:
        """Add new regions from a split to the list of existing regions.
        The new regions will make attempts to merge with the old regions.
        """
        merged_regions = []
        for new in new_regions[:]:
            for old in regions[:]:
                if rect := Rect.merge(new, old):
                    new_regions.remove(new)
                    regions.remove(old)
                    merged_regions.append(rect)
                    break

        regions += new_regions
        regions += merged_regions


def round_pow2(value: float) -> int:
    """Round a value up to its closest power of 2."""
    result = 2
    while value > result:
        result *= 2

    return result


def next_pow2(value: float) -> int:
    """Given a value, get the next power of 2 that is greater than the value."""
    result = 2
    while value >= result:
        result *= 2

    return result


def group_sequences(files: list[Path]) -> list[list[Path]]:
    """Group files into sequences."""
    sequences: dict[str, list[Path]] = defaultdict(list)

    for file in files:
        if aseprite.is_aseprite_file(file):
            sequences[file.name].append(file)
        else:
            seq_name = parse_filename(file).sprite_name
            sequences[seq_name].append(file)

    return list(sequences.values())


def is_image_file(file: str | Path) -> bool:
    """Check if the file can be opened by PIL."""
    try:
        with Image.open(file) as im:
            im.verify()
        return True
    except UnidentifiedImageError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.error(e)

    return False
