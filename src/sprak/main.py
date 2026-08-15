import logging
import sys

import sprak

logger = logging.getLogger("sprak")
logger.setLevel(logging.CRITICAL)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)


def main() -> int:
    logger.setLevel(logging.INFO)
    src = "test/sprites"
    dst_zip = "test/atlas.zip"
    dst_json = "test/atlas.json"
    dst_image = "test/atlas.png"

    sprak.pack(src, dst_json, dst_image)
    sprak.pack_and_zip(src, dst_zip)

    return 0


if __name__ == "__main__":
    sys.exit(main())
