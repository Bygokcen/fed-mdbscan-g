"""Freeze and verify immutable legacy experiment evidence.

The manifest deliberately records content identity only.  It excludes mtimes,
ownership, absolute paths, and the manifest itself so identical source trees
produce byte-identical manifests on different machines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable


MANIFEST_SCHEMA = "fed-mdbscan-legacy-manifest-v1"
DEFAULT_SOURCE_ROOTS = (
    "results/heterogeneous_v3_mnist",
    "results/heterogeneous_v3_fashion_mnist",
    "results/heterogeneous_v3_har",
    "results/phase2b_report",
)


class EvidenceError(RuntimeError):
    """Raised when legacy evidence cannot be frozen or verified."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise EvidenceError(f"cannot read legacy source: {path}: {exc}") from exc
    return digest.hexdigest()


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def build_legacy_manifest(base_dir: Path, source_roots: Iterable[str]) -> dict:
    """Return a deterministic content manifest without mutating source files."""
    base_dir = base_dir.resolve()
    roots = sorted(dict.fromkeys(str(Path(root).as_posix()) for root in source_roots))
    if not roots:
        raise EvidenceError("at least one legacy source root is required")

    files = []
    seen_paths = set()
    for root_name in roots:
        unresolved_root = base_dir / root_name
        if unresolved_root.is_symlink():
            raise EvidenceError(f"legacy source root cannot be a symlink: {root_name}")
        root = unresolved_root.resolve()
        try:
            root.relative_to(base_dir)
        except ValueError as exc:
            raise EvidenceError(f"source root escapes base directory: {root_name}") from exc
        if not root.is_dir():
            raise EvidenceError(f"legacy source root is missing: {root_name}")
        discovered = list(root.rglob("*"))
        symlinks = [path for path in discovered if path.is_symlink()]
        if symlinks:
            relative = symlinks[0].relative_to(base_dir).as_posix()
            raise EvidenceError(f"legacy source cannot contain symlinks: {relative}")
        candidates = sorted(
            (path for path in discovered if path.is_file()),
            key=lambda path: path.relative_to(base_dir).as_posix(),
        )
        if not candidates:
            raise EvidenceError(f"legacy source root is empty: {root_name}")
        for path in candidates:
            resolved_path = path.resolve()
            try:
                resolved_path.relative_to(root)
                relative = resolved_path.relative_to(base_dir).as_posix()
            except ValueError as exc:
                raise EvidenceError(f"legacy file escapes source root: {path}") from exc
            if relative in seen_paths:
                raise EvidenceError(f"legacy source roots overlap at: {relative}")
            seen_paths.add(relative)
            try:
                size = path.stat().st_size
            except OSError as exc:
                raise EvidenceError(f"cannot stat legacy source: {relative}: {exc}") from exc
            files.append({"path": relative, "sha256": _sha256(path), "size": size})

    aggregate = hashlib.sha256()
    for entry in files:
        aggregate.update(
            f"{entry['path']}\0{entry['size']}\0{entry['sha256']}\n".encode("utf-8")
        )
    return {
        "schema_version": MANIFEST_SCHEMA,
        "evidence_class": "legacy-not-validated",
        "source_roots": roots,
        "file_count": len(files),
        "aggregate_sha256": aggregate.hexdigest(),
        "files": files,
    }


def canonical_manifest_json(manifest: dict) -> str:
    return json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ) + "\n"


def render_legacy_index(manifest: dict, manifest_path: Path) -> str:
    roots = "\n".join(f"- `{root}`" for root in manifest["source_roots"])
    return (
        "# Legacy Phase 2B Evidence Index\n\n"
        "> Classification: immutable legacy evidence; not validated evidence.\n\n"
        f"- Manifest: `{manifest_path.name}`\n"
        f"- Schema: `{manifest['schema_version']}`\n"
        f"- Files: {manifest['file_count']}\n"
        f"- Aggregate SHA-256: `{manifest['aggregate_sha256']}`\n\n"
        "## Frozen source roots\n\n"
        f"{roots}\n"
    )


def freeze_legacy(base_dir: Path, manifest_path: Path, index_path: Path,
                  source_roots: Iterable[str] = DEFAULT_SOURCE_ROOTS) -> dict:
    base_dir = base_dir.resolve()
    manifest_path = manifest_path.resolve()
    index_path = index_path.resolve()
    if manifest_path == index_path:
        raise EvidenceError("manifest and index paths must differ")
    roots = tuple(source_roots)
    resolved_roots = [(base_dir / root).resolve() for root in roots]
    for output in (manifest_path, index_path):
        for root in resolved_roots:
            try:
                output.relative_to(root)
            except ValueError:
                continue
            raise EvidenceError("manifest and index must be outside legacy source roots")

    manifest = build_legacy_manifest(base_dir, roots)
    _atomic_write(manifest_path, canonical_manifest_json(manifest))
    _atomic_write(index_path, render_legacy_index(manifest, manifest_path))
    return manifest


def verify_legacy(base_dir: Path, manifest_path: Path) -> dict:
    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            expected = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read manifest: {manifest_path}: {exc}") from exc
    if expected.get("schema_version") != MANIFEST_SCHEMA:
        raise EvidenceError("unsupported legacy manifest schema")
    required = {
        "source_roots", "files", "file_count", "aggregate_sha256",
        "evidence_class",
    }
    if not required.issubset(expected):
        raise EvidenceError("legacy manifest is incomplete")
    if expected.get("evidence_class") != "legacy-not-validated":
        raise EvidenceError("legacy manifest has an invalid evidence class")
    paths = [item.get("path") for item in expected.get("files", []) if isinstance(item, dict)]
    if len(paths) != len(expected.get("files", [])) or len(set(paths)) != len(paths):
        raise EvidenceError("legacy manifest contains invalid or duplicate paths")
    actual = build_legacy_manifest(base_dir, expected["source_roots"])
    if canonical_manifest_json(actual) != canonical_manifest_json(expected):
        expected_map = {item.get("path"): item for item in expected.get("files", [])}
        actual_map = {item["path"]: item for item in actual["files"]}
        changed = sorted(
            path for path in set(expected_map) | set(actual_map)
            if expected_map.get(path) != actual_map.get(path)
        )
        detail = ", ".join(changed[:5]) or "manifest metadata"
        raise EvidenceError(f"legacy evidence verification failed: {detail}")
    return actual


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze-legacy")
    freeze.add_argument("--manifest", required=True, type=Path)
    freeze.add_argument("--index", type=Path)
    freeze.add_argument("--base-dir", type=Path, default=Path("."))
    freeze.add_argument("--source-root", action="append", dest="source_roots")
    verify = subparsers.add_parser("verify-legacy")
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--base-dir", type=Path, default=Path("."))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "freeze-legacy":
            index = args.index or args.manifest.with_name("legacy_phase2b_index_v1.md")
            manifest = freeze_legacy(
                args.base_dir, args.manifest, index,
                args.source_roots or DEFAULT_SOURCE_ROOTS,
            )
            print(
                f"frozen {manifest['file_count']} files: "
                f"{manifest['aggregate_sha256']}"
            )
        else:
            manifest = verify_legacy(args.base_dir, args.manifest)
            print(
                f"verified {manifest['file_count']} files: "
                f"{manifest['aggregate_sha256']}"
            )
    except EvidenceError as exc:
        print(f"evidence error: {exc}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
