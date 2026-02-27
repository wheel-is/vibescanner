# vibescanner

Forensic CLI scanner that analyzes any directory for the telltale signs of a vibecoded (AI-generated) web project. Detects the exact dependency stack, Tailwind patterns, shadcn components, and animation defaults that every AI coding tool produces by default.

## Install

```bash
pip install -e .
```

## Usage

```bash
vibescanner /path/to/project        # scan a project
vibescanner .                        # scan current directory
vibescanner /path/to/project -v      # verbose — show all 42 signals
vibescanner /path/to/project --json  # machine-readable JSON output
```

## What It Detects

42 signals across 7 categories:

| Category | Signals | What it catches |
|---|---|---|
| **Dependency Stack** | 15 | shadcn/ui, Tailwind, Lucide, Framer Motion, Radix, Recharts, Sonner, cmdk, CVA, next-themes, Vaul, Embla, React Day Picker, TanStack Table, tw-animate-css |
| **Typography** | 4 | Inter font, Geist, `tracking-tight`, `text-muted-foreground` |
| **Theme & Color** | 5 | shadcn CSS variables, `--destructive`, zinc/slate palette, purple gradients, sun/moon toggle |
| **Layout & Spacing** | 5 | `max-w-7xl mx-auto`, `py-16 md:py-24`, responsive 1→2→3 grids, hero text scaling, `p-6` everywhere |
| **Components & UI** | 5 | `rounded-xl` cards, `shadow-sm`, variant taxonomy, dark-mode card backgrounds, hover transitions |
| **Animation** | 3 | `animate-in fade-in`, Framer `whileHover`, `transition-all duration-200/300` |
| **Code-Level Tells** | 5 | `data-slot`, `data-state`, cmdk DOM, blurred navbar, `components/ui/` imports |

## Scoring

| Hits | Verdict |
|------|---------|
| 0–4 | Probably human-built |
| 5–9 | AI-assisted, developer cleaned up |
| 10–17 | Almost certainly vibecoded |
| 18–25 | Pure vibecode |
| 26+ | Terminal vibecode |
