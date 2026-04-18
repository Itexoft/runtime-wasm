#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path


PACKAGE_BASE_RESOURCE_TYPE = "PackageBaseAddress/3.0.0"


def fail(message: str) -> "NoReturn":
    print(f"::error::{message}", file=sys.stderr)
    raise SystemExit(1)


def fetch_json(url: str) -> object:
    try:
        result = subprocess.run(
            ["curl", "-fsSL", url],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        fail(f"curl not found: {exc}")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        detail = f": {stderr}" if stderr else ""
        fail(f"Failed to fetch {url}{detail}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"Failed to parse JSON from {url}: {exc}")


def parse_package_id(project_path: Path) -> str:
    try:
        root = ET.parse(project_path).getroot()
    except ET.ParseError as exc:
        fail(f"Failed to parse project file {project_path}: {exc}")

    for elem in root.iter():
        if elem.tag.endswith("PackageId"):
            value = (elem.text or "").strip()
            if value:
                return value

    fail(f"PackageId not found in {project_path}")


def resolve_package_base_address(source_url: str) -> str:
    payload = fetch_json(source_url)
    if not isinstance(payload, dict):
        fail(f"Unexpected NuGet service index format: {source_url}")

    resources = payload.get("resources")
    if not isinstance(resources, list):
        fail(f"NuGet service index does not contain resources: {source_url}")

    for resource in resources:
        if not isinstance(resource, dict):
            continue
        resource_type = resource.get("@type")
        resource_id = resource.get("@id")

        if isinstance(resource_type, list):
            matches = PACKAGE_BASE_RESOURCE_TYPE in resource_type
        else:
            matches = resource_type == PACKAGE_BASE_RESOURCE_TYPE

        if matches and isinstance(resource_id, str) and resource_id:
            return resource_id.rstrip("/")

    fail(f"Resource {PACKAGE_BASE_RESOURCE_TYPE} not found in {source_url}")


def parse_numeric_version(version: str) -> tuple[int, ...] | None:
    parts = version.split(".")
    if len(parts) not in (3, 4):
        return None

    numeric_parts: list[int] = []
    for part in parts:
        if not part.isdigit():
            return None
        numeric_parts.append(int(part))

    return tuple(numeric_parts)


def resolve_effective_version(base_version: str, published_versions: list[str]) -> str:
    base_parts = parse_numeric_version(base_version)
    if base_parts is None or len(base_parts) != 3:
        fail(f"Base version must be a stable numeric three-part version: {base_version}")

    matching_revisions: list[int] = []
    for version in published_versions:
        parts = parse_numeric_version(version)
        if parts is None:
            continue
        if parts[:3] != base_parts:
            continue
        revision = 0 if len(parts) == 3 else parts[3]
        matching_revisions.append(revision)

    if not matching_revisions:
        return base_version

    return f"{base_version}.{max(matching_revisions) + 1}"


def load_published_versions(source_url: str, package_id: str) -> list[str]:
    package_base_address = resolve_package_base_address(source_url)
    normalized_id = urllib.parse.quote(package_id.lower(), safe="")
    versions_url = f"{package_base_address}/{normalized_id}/index.json"
    payload = fetch_json(versions_url)

    if not isinstance(payload, dict):
        fail(f"Unexpected package index format: {versions_url}")

    versions = payload.get("versions")
    if versions is None:
        return []
    if not isinstance(versions, list):
        fail(f"Unexpected versions payload format: {versions_url}")

    normalized_versions: list[str] = []
    for version in versions:
        if not isinstance(version, str):
            fail(f"Unexpected version value in {versions_url}: {version!r}")
        normalized_versions.append(version)

    return normalized_versions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--base-version", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()

    project_path = Path(args.project)
    if not project_path.is_file():
        fail(f"Project file not found: {project_path}")

    package_id = parse_package_id(project_path)
    published_versions = load_published_versions(args.source, package_id)
    effective_version = resolve_effective_version(args.base_version, published_versions)
    print(effective_version)


if __name__ == "__main__":
    main()
