import os
from pathlib import Path

import pytest

from simulation.evidence import EvidenceError, freeze_legacy, verify_legacy


ROOTS = (
    "results/heterogeneous_v3_mnist",
    "results/heterogeneous_v3_fashion_mnist",
    "results/heterogeneous_v3_har",
    "results/phase2b_report",
)


def _legacy_tree(base: Path):
    for number, root in enumerate(ROOTS):
        path = base / root / "artifact.json"
        path.parent.mkdir(parents=True)
        path.write_text(f'{{"value":{number}}}\n', encoding="utf-8")


def test_freeze_is_deterministic_and_does_not_touch_sources(tmp_path):
    _legacy_tree(tmp_path)
    sources = sorted((tmp_path / "results").rglob("*.*"))
    before = {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in sources}
    manifest = tmp_path / "evidence" / "manifest.json"
    index = tmp_path / "evidence" / "index.md"

    freeze_legacy(tmp_path, manifest, index, ROOTS)
    first = manifest.read_bytes()
    freeze_legacy(tmp_path, manifest, index, reversed(ROOTS))

    assert manifest.read_bytes() == first
    assert verify_legacy(tmp_path, manifest)["file_count"] == 4
    assert before == {
        path: (path.stat().st_mtime_ns, path.read_bytes()) for path in sources
    }


def test_verify_rejects_changed_or_missing_legacy_source(tmp_path):
    _legacy_tree(tmp_path)
    manifest = tmp_path / "manifest.json"
    freeze_legacy(tmp_path, manifest, tmp_path / "index.md", ROOTS)
    target = tmp_path / ROOTS[0] / "artifact.json"
    target.write_text("changed\n", encoding="utf-8")

    with pytest.raises(EvidenceError, match="verification failed"):
        verify_legacy(tmp_path, manifest)

    os.unlink(target)
    with pytest.raises(EvidenceError):
        verify_legacy(tmp_path, manifest)


def test_freeze_rejects_outputs_inside_legacy_tree_or_same_path(tmp_path):
    _legacy_tree(tmp_path)
    inside = tmp_path / ROOTS[0] / "manifest.json"
    with pytest.raises(EvidenceError, match="outside legacy"):
        freeze_legacy(tmp_path, inside, tmp_path / "index.md", ROOTS)
    same = tmp_path / "evidence.json"
    with pytest.raises(EvidenceError, match="must differ"):
        freeze_legacy(tmp_path, same, same, ROOTS)


def test_freeze_rejects_symlinked_legacy_files(tmp_path):
    _legacy_tree(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / ROOTS[0] / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(EvidenceError, match="symlink"):
        freeze_legacy(
            tmp_path,
            tmp_path / "evidence/manifest.json",
            tmp_path / "evidence/index.md",
            ROOTS,
        )
