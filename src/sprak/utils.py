from pathlib import Path

from PIL import Image, UnidentifiedImageError

from sprak.log import logger


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
