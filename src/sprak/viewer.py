import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import ttk

from sprak.utils import is_image_file


def view_atlas_zip(zip_file: str | Path) -> None:
    with zipfile.ZipFile(zip_file) as zf:
        json_str = zipfile.Path(zf, "json").read_text()
        png_bytes = zipfile.Path(zf, "png").read_bytes()

    view_atlas(json_str, png_bytes)


def view_atlas_json_and_png(files: list[str | Path]) -> None:
    if Path(files[0]).suffix.lower() == ".json" or Path(files[1]).suffix.lower() == ".png" or is_image_file(files[1]):
        json_file = Path(files[0])
        png_file = Path(files[1])
    else:
        json_file = Path(files[1])
        png_file = Path(files[2])

    with json_file.open() as fp:
        json_str = fp.read()

    with png_file.open("rb") as fp:
        png_bytes = fp.read()

    view_atlas(json_str, png_bytes)


def view_atlas(json_str: str, png_bytes: bytes) -> None:
    root = tk.Tk()
    root.title("sprak viewer")

    panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)

    text = tk.Text(panes)
    text.insert(tk.END, json_str)

    photo_image = tk.PhotoImage(data=png_bytes, format="PNG")
    image = ttk.Label(panes, image=photo_image)

    panes.add(image)
    panes.add(text)
    panes.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
