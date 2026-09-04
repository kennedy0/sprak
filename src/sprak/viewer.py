import json
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import ttk

from sprak.utils import is_image_file


def view_atlas_zip(zip_file: str | Path) -> None:
    with zipfile.ZipFile(zip_file) as zf:
        json_str = zipfile.Path(zf, "json").read_text()
        png_bytes = zipfile.Path(zf, "png").read_bytes()

    title = Path(zip_file).name
    view_atlas(title, json_str, png_bytes)


def view_atlas_json_and_png(files: list[str | Path]) -> None:
    file_1 = Path(files[0])
    file_2 = Path(files[1])
    if file_1.suffix.lower() == ".json" or file_2.suffix.lower() == ".png" or is_image_file(file_2):
        json_file = file_1
        png_file = file_2
    else:
        json_file = file_2
        png_file = file_1

    with json_file.open() as fp:
        json_str = fp.read()

    with png_file.open("rb") as fp:
        png_bytes = fp.read()

    title = f"{file_1.name}, {file_2.name}"
    view_atlas(title, json_str, png_bytes)


def view_atlas(title: str, json_str: str, png_bytes: bytes) -> None:
    json_data = json.loads(json_str)
    window_width = 800
    window_height = 450

    root = tk.Tk()
    root.title(f"{title} - sprak viewer")
    root.geometry(f"{window_width}x{window_height}")

    panes = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    panes.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(panes)
    panes.add(canvas, weight=1)

    text = tk.Text(panes, font=("TkFixedFont", 12), wrap=tk.NONE)
    text.insert(tk.END, json_str)
    text.config(state=tk.DISABLED)
    panes.add(text, weight=0)

    root.update()
    panes.sashpos(0, window_width // 2)
    root.update()

    loading_text = canvas.create_text(window_width // 4, window_height // 2, text="Loading atlas image")
    root.update()

    image = tk.PhotoImage(data=png_bytes, format="PNG")
    canvas.create_image(0, 0, image=image, anchor=tk.NW)
    canvas.delete(loading_text)

    rect_id = None

    def _on_quit(event: tk.Event) -> None:
        root.destroy()

    def _on_click(event: tk.Event) -> None:
        nonlocal rect_id

        if rect_id:
            canvas.delete(rect_id)
            rect_id = None

        text.tag_remove("highlight", "1.0", tk.END)

        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        for frame_name, frame in json_data.get("frames").items():
            if frame["x"] <= x < frame["x"] + frame["width"] and frame["y"] <= y < frame["y"] + frame["height"]:
                search_term = f'"{frame_name}"'
                highlight_start = text.search(search_term, "1.0")
                line, char = highlight_start.split(".")
                highlight_end = f"{line}.{int(char) + len(search_term)}"
                text.see(tk.END)
                text.see(highlight_start)
                text.tag_add("highlight", highlight_start, highlight_end)
                text.tag_configure("highlight", background="cyan")
                rect_id = canvas.create_rectangle(
                    frame["x"],
                    frame["y"],
                    frame["x"] + frame["width"],
                    frame["y"] + frame["height"],
                    outline="red",
                    width=2,
                )

    def _on_drag_start(event: tk.Event) -> None:
        canvas.scan_mark(event.x, event.y)

    def _on_drag(event: tk.Event) -> None:
        canvas.scan_dragto(event.x, event.y, gain=1)

    root.bind("<Escape>", _on_quit)
    canvas.bind("<ButtonPress-1>", _on_click)
    canvas.bind("<ButtonPress-3>", _on_drag_start)
    canvas.bind("<ButtonPress-2>", _on_drag_start)
    canvas.bind("<B3-Motion>", _on_drag)
    canvas.bind("<B2-Motion>", _on_drag)

    root.mainloop()
