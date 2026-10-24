"""Contained paths for reading externally supplied artifact references."""

from pathlib import Path


def contained_path(root: Path, relative: str | Path) -> Path:
    """Reject absolute paths, parent traversal and resolved symlink escapes."""
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError("Artifact path must be a contained relative path")
    resolved_root = root.resolve()
    resolved_path = (resolved_root / path).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise ValueError("Artifact path escapes its root through a symlink")
    return resolved_path
