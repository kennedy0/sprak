`sprak` is a Python module for packing sprites into a texture atlas.

## Usage

```python
from pathlib import Path

from sprak import SpritePacker


src = Path("path/to/src_folder")
dst = Path("path/to/dst_folder")

packer = SpritePacker()
packer.add_source_folder(src)
packer.pack(dst)

```

## Development
Create a virtual environment:
```sh
uv venv
```

Install requirements:
```sh
uv sync
```

## A note from Andrew
This is a module that I created and maintain for my own personal projects.
Please keep the following in mind:
- Features are added as I need them.
- Issues are fixed as my time and interest allow.
- Version updates may introduce breaking changes.
