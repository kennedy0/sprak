import sys

import sprak


def main() -> int:
    src = "test/sprites"
    dst_zip = "test/atlas.zip"
    dst_json = "test/atlas.json"
    dst_png = "test/atlas.png"
    dst_gif = "test/atlas.gif"
    dst_debug_gif = "test/atlas_debug.gif"

    sprak.pack(
        src,
        dst_zip=dst_zip,
        dst_json=dst_json,
        dst_png=dst_png,
        dst_gif=dst_gif,
        dst_debug_gif=dst_debug_gif,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
