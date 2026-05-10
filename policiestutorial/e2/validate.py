"""
Validate an MPEG-21 REL policy (policy.xml) against the three REL schemas:
    - rel-r.xsd   (Core schema,        urn:mpeg:mpeg21:2003:01-REL-R-NS)
    - rel-sx.xsd  (Standard Extension, urn:mpeg:mpeg21:2003:01-REL-SX-NS)
    - rel-mx.xsd  (Multimedia Ext.,    urn:mpeg:mpeg21:2003:01-REL-MX-NS)

The three schemas live in different namespaces, so we cannot load them
directly into a single XMLSchema. Instead we build a tiny in-memory wrapper
schema that <xs:import>s all three, then validate against that.

Requirements:
    pip install lxml
"""

from __future__ import annotations

import sys
from pathlib import Path

from lxml import etree


# --- Configuration ---------------------------------------------------------

SCHEMAS = {
    "urn:mpeg:mpeg21:2003:01-REL-R-NS":  "rel-r.xsd",
    "urn:mpeg:mpeg21:2003:01-REL-SX-NS": "rel-sx.xsd",
    "urn:mpeg:mpeg21:2003:01-REL-MX-NS": "rel-mx.xsd",
}

POLICY_FILE = "policy.xml"


# --- Validation ------------------------------------------------------------

def build_composite_schema(schema_dir: Path) -> etree.XMLSchema:
    """Build a wrapper schema that imports whichever REL schemas are present.

    Missing files are skipped with a warning rather than treated as fatal,
    since a given policy may not exercise every REL namespace.
    """
    available: dict[str, Path] = {}
    for ns, fn in SCHEMAS.items():
        path = (schema_dir / fn).resolve()  # absolute, required by as_uri()
        if path.is_file():
            available[ns] = path
        else:
            print(f"[warn] {fn} not found in {schema_dir} — skipping {ns}")

    if not available:
        raise FileNotFoundError(
            f"None of the REL schema files were found in {schema_dir}"
        )

    imports = "\n".join(
        f'  <xs:import namespace="{ns}" schemaLocation="{path.as_uri()}"/>'
        for ns, path in available.items()
    )
    wrapper = f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
{imports}
</xs:schema>
"""
    return etree.XMLSchema(etree.fromstring(wrapper.encode("utf-8")))


def validate(policy_path: Path, schema_dir: Path) -> bool:
    schema = build_composite_schema(schema_dir)

    try:
        doc = etree.parse(str(policy_path))
    except etree.XMLSyntaxError as exc:
        print(f"[FAIL] {policy_path} is not well-formed XML:\n  {exc}")
        return False

    if schema.validate(doc):
        print(f"[OK]   {policy_path} is valid against the MPEG-21 REL schemas.")
        return True

    print(f"[FAIL] {policy_path} failed schema validation:")
    for err in schema.error_log:
        print(f"  line {err.line}, col {err.column}: {err.message}")
    return False


# --- Entry point -----------------------------------------------------------

def main() -> int:
    # Allow overriding paths from the command line:
    #   python validate_policy.py [policy.xml] [schema_dir]
    policy_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(POLICY_FILE)
    schema_dir  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    return 0 if validate(policy_path, schema_dir) else 1


if __name__ == "__main__":
    sys.exit(main())