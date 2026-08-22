import json
import os
import platform
import shutil
import struct
import subprocess
import warnings
from functools import cache
from pathlib import Path
from tempfile import NamedTemporaryFile

from sprak.rect import Rect

ASEPRITE_MAGIC_NUMBER = 0xA5E0


def is_aseprite_file(file: str | Path) -> bool:
    """Check if a file is an Aseprite file.
    Bytes 4-5 should be the 0xA5E0 magic number: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md#header
    """
    file = Path(file)
    with file.open("rb") as fp:
        try:
            fp.seek(4)
            magic_number = struct.unpack("<H", fp.read(2))[0]
            if magic_number == ASEPRITE_MAGIC_NUMBER:
                return True
        except (ValueError, struct.error):
            pass

    return False


def read_json_data(aseprite_file: str | Path) -> dict:
    """Read the JSON data from an Aseprite file."""
    aseprite_file = Path(aseprite_file)
    with NamedTemporaryFile() as tmp:
        cmd = [get_aseprite_exe()]
        cmd += ["--batch"]
        cmd += ["--noinapp"]
        cmd += ["--list-tags"]
        cmd += ["--list-slices"]
        cmd += ["--format", "json-array"]
        cmd += ["--data", tmp.name]
        cmd += [aseprite_file.absolute().as_posix()]
        subprocess.run(cmd, check=True)
        return json.load(tmp)


def export_frames(aseprite_file: str | Path, sequence_path: str | Path) -> None:
    """Export each frame in an Aseprite file as an image sequence.
    Sequence path should be formatted as a printf-style formatted frame, e.g.:
        path/to/frames.%04d.png
    """
    aseprite_file = Path(aseprite_file)
    sequence_path = Path(sequence_path)
    first_sequence_file = sequence_path.absolute().as_posix() % 1

    cmd = [get_aseprite_exe()]
    cmd += ["--batch"]
    cmd += ["--noinapp"]
    cmd += [aseprite_file.absolute().as_posix()]
    cmd += ["--save-as", first_sequence_file]
    subprocess.run(cmd, check=True)


@cache
def get_aseprite_exe() -> str:
    """Get the path to the Aseprite executable. Search is done in the following order:
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
