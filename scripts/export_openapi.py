#!/usr/bin/env python3
"""Export the OpenAPI specification to JSON and generate an API documentation
Markdown file that can easily be converted to PDF.

Usage:
    python scripts/export_openapi.py          # writes docs/openapi.json + docs/api_documentation.md
    python scripts/export_openapi.py --json   # only openapi.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import create_app  # noqa: E402


def export_openapi_json(out_dir: Path) -> dict:
    """Write openapi.json and return the parsed spec."""
    app = create_app()
    spec = app.openapi()
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "openapi.json"
    json_path.write_text(json.dumps(spec, indent=2))
    print(f"✓ OpenAPI spec written to {json_path}")
    return spec


def _md_type(schema: dict) -> str:
    """Return a human-readable type string from a JSON-Schema snippet."""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "allOf" in schema:
        refs = [s["$ref"].rsplit("/", 1)[-1] for s in schema["allOf"] if "$ref" in s]
        return ", ".join(refs) if refs else "object"
    return schema.get("type", "any")


def generate_markdown(spec: dict, out_dir: Path) -> None:
    """Generate a Markdown API documentation file from the OpenAPI spec."""
    lines: list[str] = []

    lines.append(f"# {spec['info']['title']}")
    lines.append(f"\n**Version:** {spec['info']['version']}\n")
    lines.append(spec["info"].get("description", ""))
    lines.append("")

    # Authentication
    security_schemes = spec.get("components", {}).get("securitySchemes", {})
    if security_schemes:
        lines.append("## Authentication\n")
        for name, scheme in security_schemes.items():
            lines.append(f"- **{name}**: {scheme.get('type', '')} — {scheme.get('description', scheme.get('scheme', ''))}")
        lines.append("")

    # Group endpoints by tag
    tag_groups: dict[str, list] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method in ("get", "post", "put", "patch", "delete"):
                tags = details.get("tags", ["Other"])
                for tag in tags:
                    tag_groups.setdefault(tag, []).append((method.upper(), path, details))

    for tag in sorted(tag_groups):
        lines.append(f"## {tag}\n")
        for method, path, details in tag_groups[tag]:
            summary = details.get("summary", details.get("operationId", ""))
            lines.append(f"### `{method} {path}`\n")
            if summary:
                lines.append(f"**{summary}**\n")
            desc = details.get("description", "")
            if desc:
                lines.append(f"{desc}\n")

            # Parameters
            params = details.get("parameters", [])
            if params:
                lines.append("**Parameters:**\n")
                lines.append("| Name | In | Type | Required | Description |")
                lines.append("|------|----|------|----------|-------------|")
                for p in params:
                    ptype = _md_type(p.get("schema", {}))
                    required = "Yes" if p.get("required") else "No"
                    lines.append(f"| `{p['name']}` | {p['in']} | {ptype} | {required} | {p.get('description', '')} |")
                lines.append("")

            # Request body
            body = details.get("requestBody", {})
            if body:
                content = body.get("content", {})
                for ct, ct_details in content.items():
                    ref = _md_type(ct_details.get("schema", {}))
                    lines.append(f"**Request Body** (`{ct}`): `{ref}`\n")

            # Responses
            responses = details.get("responses", {})
            if responses:
                lines.append("**Responses:**\n")
                lines.append("| Status | Description |")
                lines.append("|--------|-------------|")
                for status_code, resp in sorted(responses.items()):
                    lines.append(f"| {status_code} | {resp.get('description', '')} |")
                lines.append("")

            lines.append("---\n")

    # Schemas
    schemas = spec.get("components", {}).get("schemas", {})
    if schemas:
        lines.append("## Data Models\n")
        for name, schema in sorted(schemas.items()):
            lines.append(f"### {name}\n")
            props = schema.get("properties", {})
            required_fields = set(schema.get("required", []))
            if props:
                lines.append("| Field | Type | Required |")
                lines.append("|-------|------|----------|")
                for field, field_schema in props.items():
                    ftype = _md_type(field_schema)
                    req = "Yes" if field in required_fields else "No"
                    lines.append(f"| `{field}` | {ftype} | {req} |")
                lines.append("")

    md_path = out_dir / "api_documentation.md"
    md_path.write_text("\n".join(lines))
    print(f"✓ API documentation written to {md_path}")
    print(f"  → Convert to PDF: pandoc {md_path} -o docs/api_documentation.pdf")


def main():
    parser = argparse.ArgumentParser(description="Export OpenAPI spec and API docs")
    parser.add_argument("--json", action="store_true", help="Export only openapi.json")
    args = parser.parse_args()

    out_dir = Path("docs")
    spec = export_openapi_json(out_dir)
    if not args.json:
        generate_markdown(spec, out_dir)


if __name__ == "__main__":
    main()
