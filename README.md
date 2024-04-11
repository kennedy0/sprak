# sprak

`sprak` is a Python module for packing sprites into a texture atlas.

## Usage

```python
from pathlib import Path

from sprak import SpritePacker


src = Path("/path/to/src/folder")
dst = Path("/path/to/dst/folder")

packer = SpritePacker()
packer.add_source_folder(src)
packer.pack(dst)

```
