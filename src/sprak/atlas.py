import io
import json
import logging
import math
import zipfile
from pathlib import Path

import pyseq
from PIL import Image

from sprak import aseprite
from sprak.rect import Rect
from sprak.sprite import Sprite

logger = logging.getLogger("sprak")


class Atlas:
    def __init__(self) -> None:
        self.sprites: list[Sprite] = []

        self._is_packed = False
        self._image = Image.new("RGBA", (0, 0))
        self._current_folder: Path | None = None

    def add_file(self, file: Path) -> None:
        """Add a file to the atlas."""
        name = self._get_sprite_name(file)
        if aseprite.is_aseprite_file(file):
            self._is_packed = False
            self.sprites += Sprite.from_aseprite(file, name)
        elif self._is_image_file(file):
            self._is_packed = False
            self.sprites.append(Sprite.from_image(file, name))

    def add_folder(self, folder: Path) -> None:
        """Add a folder to the atlas."""
        self._current_folder = folder

        for root, dirs, files in folder.walk():
            for f in files:
                # ToDO: Detect image sequences with pyseq
                file = root / f
                self.add_file(file)

        self._current_folder = None

    def write_json(self, file: str | Path) -> None:
        """Write the atlas data to a JSON file."""
        if not self._is_packed:
            self._pack()

        file = Path(file)
        logger.info(f"Writing {file.absolute().as_posix()}")
        with file.open("w") as fp:
            fp.write(self._get_json_str())

    def write_image(self, file: str | Path) -> None:
        """Write the atlas image to a file."""
        if not self._is_packed:
            self._pack()

        file = Path(file)
        logger.info(f"Writing {file.absolute().as_posix()}")
        self._image.save(file)

    def write_zip(self, file: str | Path) -> None:
        """Write the atlas to a zip file."""
        if not self._is_packed:
            self._pack()

        file = Path(file)
        logger.info(f"Writing {file.absolute().as_posix()}")
        with zipfile.ZipFile(file, mode="w", compression=zipfile.ZIP_STORED) as zf:
            zf.writestr("json", self._get_json_str())
            zf.writestr("png", self._get_image_bytes())

    # noinspection PyMethodMayBeStatic
    def _is_image_file(self, file: Path) -> bool:
        try:
            with Image.open(file) as im:
                im.verify()
            return True
        except Exception:
            return False

    def _get_sprite_name(self, file: Path) -> str:
        """Get a sprite name by using its file name relative to the source folder that it was added from."""
        if self._current_folder:
            file = file.relative_to(self._current_folder)

        return file.with_suffix("").as_posix().strip("/")

    def _pack(self) -> None:
        """Pack the sprites into the atlas."""
        size = self._calculate_starting_size()
        self.sprites.sort(key=lambda s: s.height, reverse=True)

        while True:
            logger.debug(f"Packing sprites on atlas size of {size}x{size}")
            regions = [Rect(0, 0, size, size)]
            overflow = False
            for sprite in self.sprites:
                # Skip completely transparent images
                if sprite.is_empty:
                    continue

                # Try to find a region that the sprite fits into
                if region := self._find_region(sprite, regions):
                    # Place sprite
                    sprite.x = region.x
                    sprite.y = region.y

                    # Split region
                    regions.remove(region)
                    split_x = sprite.x + sprite.width
                    split_y = sprite.y + sprite.height
                    regions += self._split_region(region, split_x, split_y)
                    regions.sort(key=lambda rect: rect.area)

                else:
                    logger.debug(f"{sprite.name} overflowed")
                    overflow = True
                    break

            # If the sprites overflowed on the atlas, try again with increased atlas size
            if overflow:
                size = next_pow2(size)
            else:
                break

        # Create image
        self._image = Image.new("RGBA", (size, size))
        for sprite in self.sprites:
            if sprite.image:
                self._image.paste(sprite.image, box=(sprite.x, sprite.y))

        self._is_packed = True

    def _calculate_starting_size(self) -> int:
        """Calculate the starting size of the atlas.
        We assume the algorithm will be 100% efficient, meaning that the area of the atlas will be exactly the sum of the areas of the sprites.
        Of course it won't, but rounding to the next power of 2 gives us some padding, which is a reasonable place to start.
        """
        area = math.sqrt(sum([s.area for s in self.sprites]))
        return round_pow2(area)

    # noinspection PyMethodMayBeStatic
    def _find_region(self, sprite: Sprite, regions: list[Rect]) -> Rect | None:
        """Find a region that the sprite fits into."""
        for region in regions:
            if sprite.width <= region.w and sprite.height <= region.h:
                return region

        return None

    # noinspection PyMethodMayBeStatic
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

    def _get_json_str(self) -> str:
        """Get the atlas data as a JSON string."""
        return json.dumps(sorted([s.to_dict() for s in self.sprites], key=lambda x: x.get("name")), indent=2)

    def _get_image_bytes(self) -> bytes:
        """Get the image data as bytes."""
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
