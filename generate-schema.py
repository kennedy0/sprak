from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from sprak.json_types import Atlas

SCHEMA_FILE = Path(__file__).parent / "sprak.schema.json"


atlas_schema = TypeAdapter(Atlas).json_schema(mode="serialization")
atlas_schema = {
    "$id": "https://raw.githubusercontent.com/kennedy0/sprak/refs/heads/main/sprak.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **atlas_schema,
}

with SCHEMA_FILE.open("w") as fp:
    json.dump(atlas_schema, fp, indent=2)
