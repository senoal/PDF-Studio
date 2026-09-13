from __future__ import annotations

from pathlib import Path


def get_filename(file_path: str) -> str:
    """Return filename from a path."""
    return Path(file_path).name


def get_file_size(file_path: str) -> int:
    """Return file size in bytes."""
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """Convert bytes into human-readable file size."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"

    if size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.1f} MB"

    return f"{size_bytes / 1024**3:.1f} GB"