import json
from pathlib import Path

from pydantic import TypeAdapter

from sprak.json_types import AtlasJSON

SCHEMA_FILE = Path(__file__).parent / "sprak.schema.json"

Atlas = AtlasJSON
atlas_adapter = TypeAdapter(Atlas)
schema = atlas_adapter.json_schema(mode="serialization")

import pprint

pprint.pprint(schema)


with SCHEMA_FILE.open("w") as fp:
    json.dump(schema, fp, indent=2)
