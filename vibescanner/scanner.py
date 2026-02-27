"""Scan orchestration — walks a target directory and runs all detectors."""

from __future__ import annotations

from pathlib import Path

from .detectors import (
    Signal,
    collect_files,
    detect_content,
    detect_dependencies,
)


def run_scan(target: Path) -> list[Signal]:
    """Run every detector against *target* and return the combined signal list."""
    signals: list[Signal] = []
    signals.extend(detect_dependencies(target))
    files = collect_files(target)
    signals.extend(detect_content(target, files))
    return signals
