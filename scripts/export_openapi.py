#!/usr/bin/env python3
"""Export OpenAPI schema from FastAPI app to docs/api/openapi.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
BACKEND_SRC = REPO_ROOT / "backend" / "src"
OUTPUT_PATH = REPO_ROOT / "docs" / "api" / "openapi.json"

sys.path.insert(0, str(BACKEND_SRC))


def main() -> None:
    from document_processor.main import app  # noqa: PLC0415

    schema = app.openapi()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
    print(f"OpenAPI schema exported to {OUTPUT_PATH}")
    print(f"  Title:   {schema.get('info', {}).get('title', 'N/A')}")
    print(f"  Version: {schema.get('info', {}).get('version', 'N/A')}")
    paths = schema.get("paths", {})
    print(f"  Paths:   {len(paths)}")


if __name__ == "__main__":
    main()
