"""CLI entry point — installed as `vibescanner` command."""

from __future__ import annotations

from pathlib import Path

import click

from .report import render_json, render_report
from .scanner import run_scan


@click.command()
@click.argument("target", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--verbose", "-v", is_flag=True, help="Show all 42 signals, including undetected")
@click.option("--json", "as_json", is_flag=True, help="Machine-readable JSON output")
def main(target: str, verbose: bool, as_json: bool) -> None:
    """Scan a directory for vibecoded indicators.

    Analyzes a codebase for the telltale signs of AI-generated code:
    the dependency stack, Tailwind patterns, shadcn components, and
    cookie-cutter animations that every AI coding tool produces.
    """
    target_path = Path(target).resolve()
    signals = run_scan(target_path)

    if as_json:
        render_json(signals, target_path)
    else:
        render_report(signals, target_path, verbose=verbose)


if __name__ == "__main__":
    main()
