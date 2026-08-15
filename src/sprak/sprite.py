from dataclasses import asdict, dataclass, field
from typing import Any

from PIL import Image


@dataclass
class Sprite:
    name: str
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    original_width: int = 0
    original_height: int = 0
    offset_x: int = 0
    offset_y: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    image: Image.Image | None = None

    @property
    def is_empty(self) -> bool:
        """Check if this sprite has an area of zero."""
        if self.width * self.height == 0:
            return True

        return False

    def to_dict(self) -> dict:
        excluded_fields = {"image"}

        def _dict_factory(fields: list[tuple[str, Any]]) -> dict:
            return {k: v for (k, v) in fields if k not in excluded_fields}

        return asdict(self, dict_factory=_dict_factory)
