import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from sprak import aseprite
from sprak.frame import Frame
from sprak.log import logger
from sprak.rect import Rect


class Atlas:
    def __init__(self) -> None:
        self._frames: list[Frame] = []
        self._frame_names: set[str] = set()
        self._is_packed = False
        self._image = Image.new("RGBA", (0, 0))
        self._current_folder: Path | None = None

    def add_frame(self, frame: Frame) -> None:
        if frame.name in self._frame_names:
            logger.error(f"a frame named {frame.name} is already in the atlas")
            return

        logger.debug(f"adding frame {frame.name}")
        self._is_packed = False
        self._frames.append(frame)
        self._frame_names.add(frame.name)

    def add_file(self, file: Path) -> None:
        name = self._get_frame_name(file)
        if aseprite.is_aseprite_file(file):
            for frame in Frame.from_aseprite(name, file):
                self.add_frame(frame)
        elif self._is_image_file(file):
            self.add_frame(Frame.from_image(name, file))
        else:
            logger.debug(f"skipping unsupported file {file.as_posix()}")

    def add_folder(self, folder: Path) -> None:
        self._current_folder = folder

        for root, dirs, files in folder.walk():
            for f in files:
                file = root / f
                self.add_file(file)

        self._current_folder = None

    def write_zip(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        with zipfile.ZipFile(file, mode="w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("json", self._get_json_str())
            zf.writestr("png", self._get_image_bytes())

    def write_json(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        with open(file, "w") as fp:
            fp.write(self._get_json_str())

    def write_image(self, file: str | Path) -> None:
        if not self._is_packed:
            self._pack()

        self._image.save(file)

    def to_dict(self) -> dict:
        return {
            "frames": self._get_frames_dict(),
            "sprites": self._get_sprites_dict(),
        }

    def _is_image_file(self, file: Path) -> bool:
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

    def _get_frame_name(self, file: Path) -> str:
        """Get a frame name by using its file name relative to the source folder that it was added from."""
        if self._current_folder:
            file = file.relative_to(self._current_folder)

        return file.with_suffix("").as_posix().strip("/")

    def _pack(self) -> None:
        size = self._calculate_starting_size()
        self._frames.sort(key=lambda f: f.height, reverse=True)

        # Place frames
        while True:
            regions = [Rect(0, 0, size, size)]
            overflow = False
            for frame in self._frames:
                # Skip completely transparent images
                if frame.is_empty:
                    continue

                # Try to find a region that the frame fits into
                if region := self._find_region(frame, regions):
                    # Place frame
                    frame.x = region.x
                    frame.y = region.y

                    # Split region
                    regions.remove(region)
                    split_x = frame.x + frame.width
                    split_y = frame.y + frame.height
                    regions += self._split_region(region, split_x, split_y)
                    regions.sort(key=lambda rect: rect.area)

                else:
                    overflow = True
                    break

            # If the frames overflowed on the atlas, try again with increased atlas size
            if overflow:
                size = next_pow2(size)
            else:
                break

        # Create image
        self._image = Image.new("RGBA", (size, size))
        for frame in self._frames:
            if frame.image:
                self._image.paste(frame.image, box=(frame.x, frame.y))

        self._is_packed = True

    def _calculate_starting_size(self) -> int:
        """Calculate the starting size of the atlas.
        We assume the algorithm will be 100% efficient, meaning that the area of the atlas will be exactly the sum of the areas of the frames.
        Of course it won't, but rounding to the next power of 2 gives us some padding, which is a reasonable place to start.
        """
        area = math.sqrt(sum([f.area for f in self._frames]))
        return round_pow2(area)

    def _find_region(self, frame: Frame, regions: list[Rect]) -> Rect | None:
        """Find a region that the frame fits into."""
        for region in regions:
            if frame.width <= region.w and frame.height <= region.h:
                return region

        return None

    def _split_region(self, region: Rect, x: int, y: int) -> list[Rect]:
        """Horizontally split a region into top and bottom sub-regions.
               X
        ┌──────┬────────┐
        │░░░░░░│  top   │
        │░░░░░░│        │
        ├──────┴────────┤ Y
        │    bottom     │
        │               │
        └───────────────┘
        """
        sub_regions = []

        top_w = region.right - x + 1
        top_h = y - region.top
        top = Rect(x, region.y, top_w, top_h)

        bottom_w = region.w
        bottom_h = region.bottom - y + 1
        bottom = Rect(region.x, y, bottom_w, bottom_h)

        # Add non-empty regions back to region list
        if not top.is_empty:
            sub_regions.append(top)
        if not bottom.is_empty:
            sub_regions.append(bottom)

        return sub_regions

    def _get_frames_dict(self) -> dict:
        return {f.name: f.to_dict() for f in self._frames}

    def _get_sprites_dict(self) -> dict:
        def _default_factory() -> dict:
            return {
                "frames": [],
                "animations": defaultdict(list),
            }

        sprites = defaultdict(_default_factory)

        for frame in self._frames:
            if sprite_name := frame.sprite:
                sprites[sprite_name]["frames"].append(frame.name)
                for animation in frame.animations:
                    sprites[sprite_name]["animations"][animation].append(frame.name)

        for sprite in sprites.values():
            sprite["frames"].sort()
            for animation in sprite["animations"].values():
                animation.sort()

        return sprites

    def _get_json_str(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def _get_image_bytes(self) -> bytes:
        image_buffer = io.BytesIO()
        self._image.save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()
        return image_bytes


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
