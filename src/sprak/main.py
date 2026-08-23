import sys

import sprak


def main() -> int:
    src = "test/sprites"
    dst_zip = "test/atlas.zip"
    dst_json = "test/atlas.json"
    dst_image = "test/atlas.png"
    dst_animation = "test/animation/test.%04d.png"
    dst_debug_animation = "test/debug_animation/test.%04d.png"

    sprak.pack(
        src,
        dst_zip=dst_zip,
        dst_json=dst_json,
        dst_image=dst_image,
        dst_animation=dst_animation,
        dst_debug_animation=dst_debug_animation,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
