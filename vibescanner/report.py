"""CLI report rendering — Rich terminal output and JSON export."""

from __future__ import annotations

import json as json_lib
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel

from .detectors import Signal

CATEGORIES: list[tuple[str, str]] = [
    ("dependencies", "Dependency Stack"),
    ("typography", "Typography"),
    ("theme", "Theme & Color"),
    ("layout", "Layout & Spacing"),
    ("components", "Components & UI"),
    ("animation", "Animation"),
    ("page_patterns", "Page Patterns"),
    ("code_tells", "Code-Level Tells"),
]


def render_report(
    signals: list[Signal],
    target: Path,
    *,
    verbose: bool = False,
) -> None:
    console = Console()
    hits = sum(1 for s in signals if s.detected)
    total = len(signals)

    # ── Header ────────────────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            "[bold magenta]VIBECODE FORENSIC SCANNER[/bold magenta]\n"
            "[dim]v0.1.0 \u2014 detecting mass-produced AI aesthetics since 2025[/dim]",
            box=box.HEAVY,
            border_style="magenta",
            padding=(1, 2),
        )
    )
    console.print(f"\n  [dim]Target:[/dim]  [bold]{target}[/bold]")
    hit_color = "green" if hits == 0 else "red" if hits > total * 0.4 else "yellow"
    console.print(
        f"  [dim]Found:[/dim]   [{hit_color}][bold]{hits}[/bold][/{hit_color}]"
        f" [dim]of {total} indicators present[/dim]\n"
    )

    # ── Category breakdown ────────────────────────────────────────────
    for cat_id, cat_name in CATEGORIES:
        cat_sigs = [s for s in signals if s.category == cat_id]
        if not cat_sigs:
            continue

        cat_hits = sum(1 for s in cat_sigs if s.detected)
        if cat_hits == 0 and not verbose:
            continue

        hdr = "green" if cat_hits == 0 else "red" if cat_hits / len(cat_sigs) > 0.6 else "yellow"
        rule_pad = max(1, 52 - len(cat_name))
        rule_tail = "\u2501" * rule_pad
        console.print(
            f"  [bold {hdr}]\u2501\u2501\u2501 {cat_name} "
            f"({cat_hits}/{len(cat_sigs)}) "
            f"{rule_tail}[/bold {hdr}]"
        )

        for sig in cat_sigs:
            if sig.detected:
                marker = "[red]\u25a0[/red]"
                name = f"[bold]{sig.name}[/bold]"
                ev = sig.evidence[0] if sig.evidence else ""
                if sig.count > 1:
                    ev = f"{sig.count}x \u2014 {ev}" if ev else f"{sig.count} matches"
                detail = f"  [dim]{ev}[/dim]"
            elif verbose:
                marker = "[dim]\u25a1[/dim]"
                name = f"[dim]{sig.name}[/dim]"
                detail = ""
            else:
                continue
            console.print(f"    {marker} {name}{detail}")

        console.print()


def render_json(signals: list[Signal], target: Path) -> None:
    categories: dict[str, dict] = {}
    for sig in signals:
        cat = sig.category
        if cat not in categories:
            categories[cat] = {"hits": 0, "total": 0, "signals": []}
        categories[cat]["total"] += 1
        if sig.detected:
            categories[cat]["hits"] += 1
        categories[cat]["signals"].append(
            {
                "id": sig.id,
                "name": sig.name,
                "detected": sig.detected,
                "count": sig.count,
                "evidence": sig.evidence,
            }
        )

    output = {
        "target": str(target),
        "indicators_present": sum(1 for s in signals if s.detected),
        "indicators_total": len(signals),
        "categories": categories,
    }
    print(json_lib.dumps(output, indent=2))
