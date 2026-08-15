import os
import platform
import shutil
import struct
import warnings
from pathlib import Path

_ASEPRITE_MAGIC_NUMBER = 0xA5E0


def is_aseprite_file(file: Path) -> bool:
    """Check if a file is an Aseprite file.
    Bytes 4-5 should be the 0xA5E0 magic number: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md#header
    """
    with file.open("rb") as fp:
        try:
            fp.seek(4)
            magic_number = struct.unpack("<H", fp.read(2))[0]
            if magic_number == _ASEPRITE_MAGIC_NUMBER:
                return True
        except Exception:
            pass

    return False


def get_aseprite_exe() -> str:
    """Get the path to the aseprite executable. Search is done in the following order:
    1. If the SPRAK_ASEPRITE_EXE_PATH environment variable is set, that path is used.
    2. The 'aseprite' command/alias is used, if it exists.
    3. Known install paths (first vanilla, then Steam) are searched.
    4. If nothing was found, fall back to 'aseprite' which will probably fail.
    """
    if exe_from_env := os.getenv("SPRAK_ASEPRITE_EXE_PATH"):
        return exe_from_env
    elif exe_from_which := shutil.which("aseprite"):
        return exe_from_which
    elif exe_from_install_path := search_aseprite_install_paths():
        return exe_from_install_path

    warnings.warn(
        "An Aseprite installation could not be found. Make sure it is installed, and/or set the SPRAK_ASEPRITE_EXE_PATH.",
        UserWarning,
    )

    return "aseprite"


def search_aseprite_install_paths() -> str | None:
    """Search known install paths for the Aseprite executable."""

    if platform.system() == "Darwin":
        paths = [
            "/Applications/Aseprite.app/Contents/MacOS/aseprite",
            "~/Library/Application Support/Steam/steamapps/common/Aseprite/Aseprite.app/Contents/MacOS/aseprite",
        ]
    elif platform.system() == "Linux":
        paths = [
            "/usr/bin/aseprite",
            "~/.steam/debian-installation/steamapps/common/Aseprite/aseprite",
            "~/.local/share/Steam/steamapps/common/Aseprite/aseprite",
        ]
    elif platform.system() == "Windows":
        paths = [
            "C:\\Program Files\\Aseprite\\Aseprite.exe",
            "C:\\Program Files (x86)\\Aseprite\\Aseprite.exe",
            "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Aseprite\\Aseprite.exe",
        ]
    else:
        paths = []

    for path in paths:
        path = os.path.expanduser(path)
        if os.path.exists(path):
            return path

    return None
