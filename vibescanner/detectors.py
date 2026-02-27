"""Signal definitions and detection logic for vibecoded indicators.

42 signals across 7 categories: dependencies, typography, theme,
layout, components, animation, and code-level tells.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = frozenset({
    "node_modules", ".next", "dist", "build", ".git", "__pycache__",
    ".venv", "venv", ".turbo", ".cache", "coverage", ".output",
    "out", ".nuxt", ".svelte-kit", ".vercel", ".netlify", ".docusaurus",
})

SKIP_FILES = frozenset({
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
})

SCAN_EXTENSIONS = frozenset({
    ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".mjs", ".cjs", ".vue", ".svelte", ".astro",
})


@dataclass
class Signal:
    id: str
    name: str
    category: str
    detected: bool = False
    evidence: list[str] = field(default_factory=list)
    count: int = 0


# ---------------------------------------------------------------------------
# Dependency detection
# ---------------------------------------------------------------------------

VIBECODE_DEPS: list[tuple[str, str]] = [
    ("tailwindcss", "Tailwind CSS"),
    ("lucide-react", "Lucide React"),
    ("framer-motion", "Framer Motion"),
    ("recharts", "Recharts"),
    ("sonner", "Sonner toasts"),
    ("cmdk", "cmdk command palette"),
    ("class-variance-authority", "class-variance-authority"),
    ("next-themes", "next-themes"),
    ("vaul", "Vaul drawer"),
    ("embla-carousel-react", "Embla Carousel"),
    ("react-day-picker", "React Day Picker"),
    ("@tanstack/react-table", "TanStack React Table"),
    ("tw-animate-css", "tw-animate-css"),
]


def _dep_id(name: str) -> str:
    return "dep_" + re.sub(r"[^a-z0-9]", "_", name.lower().lstrip("@"))


def _find_package_jsons(root: Path) -> list[Path]:
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "package.json" in filenames:
            results.append(Path(dirpath) / "package.json")
    return results


def _merge_deps(pkg_files: list[Path]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for pf in pkg_files:
        try:
            pkg = json.loads(pf.read_text(encoding="utf-8"))
            merged.update(pkg.get("dependencies", {}))
            merged.update(pkg.get("devDependencies", {}))
        except (json.JSONDecodeError, OSError):
            continue
    return merged


def detect_dependencies(root: Path) -> list[Signal]:
    pkg_files = _find_package_jsons(root)
    all_deps = _merge_deps(pkg_files)
    signals: list[Signal] = []

    for dep_name, display in VIBECODE_DEPS:
        sig = Signal(id=_dep_id(dep_name), name=display, category="dependencies")
        if dep_name in all_deps:
            sig.detected = True
            sig.count = 1
            sig.evidence.append(f"package.json \u2192 {all_deps[dep_name]}")
        signals.append(sig)

    # shadcn/ui — config file or components/ui/ directory
    shadcn = Signal(id="dep_shadcn", name="shadcn/ui", category="dependencies")
    shadcn_paths = [
        root / "components.json",
        root / "components" / "ui",
        root / "src" / "components" / "ui",
        root / "app" / "components" / "ui",
    ]
    for p in shadcn_paths:
        if p.exists():
            shadcn.detected = True
            shadcn.evidence.append(str(p.relative_to(root)))
    for dep in all_deps:
        if "shadcn" in dep.lower():
            shadcn.detected = True
            shadcn.evidence.append(f"package.json \u2192 {dep}")
    if shadcn.detected:
        shadcn.count = 1
    signals.append(shadcn)

    # @radix-ui/* (prefix match)
    radix = Signal(id="dep_radix", name="Radix UI", category="dependencies")
    radix_pkgs = [k for k in all_deps if k.startswith("@radix-ui/")]
    if radix_pkgs:
        radix.detected = True
        radix.count = len(radix_pkgs)
        shown = radix_pkgs[:4]
        tail = f" + {len(radix_pkgs) - 4} more" if len(radix_pkgs) > 4 else ""
        radix.evidence.append(f"{', '.join(shown)}{tail}")
    signals.append(radix)

    return signals


# ---------------------------------------------------------------------------
# Content-pattern detection
# ---------------------------------------------------------------------------

@dataclass
class _Pattern:
    signal_id: str
    name: str
    category: str
    regex: str
    extensions: frozenset[str] | None = None  # None = all SCAN_EXTENSIONS
    threshold: int = 1


CONTENT_PATTERNS: list[_Pattern] = [
    # ── Typography (4) ────────────────────────────────────────────────
    _Pattern(
        "typo_inter", "Inter font", "typography",
        r'(?:font-family[^;]*\bInter\b|["\']Inter["\']|@fontsource[/-]inter|next/font.*\binter\b)',
    ),
    _Pattern(
        "typo_geist", "Geist / Geist Mono", "typography",
        r'(?:\bGeist\b|@fontsource[/-]geist|next/font.*geist)',
    ),
    _Pattern(
        "typo_muted_fg", "text-muted-foreground", "typography",
        r"text-muted-foreground",
    ),
    _Pattern(
        "typo_tracking", "tracking-tight / negative letter-spacing", "typography",
        r"(?:tracking-tight|letter-spacing:\s*-0\.\d+em)",
    ),

    # ── Theme & Color (5) ─────────────────────────────────────────────
    _Pattern(
        "theme_css_vars", "shadcn CSS variables", "theme",
        r"--(?:background|foreground|primary|muted|accent|card|popover|radius)\s*:",
        frozenset({".css", ".scss"}),
    ),
    _Pattern(
        "theme_destructive", "--destructive variable", "theme",
        r"--destructive\s*:",
        frozenset({".css", ".scss"}),
    ),
    _Pattern(
        "theme_zinc", "Zinc/Slate palette", "theme",
        r"(?:bg|text|border)-(?:zinc|slate)-\d{2,3}",
    ),
    _Pattern(
        "theme_gradient", "Purple/violet/blue gradient", "theme",
        r"(?:from-(?:purple|violet|blue|indigo)-|to-(?:purple|violet|blue|indigo)-)",
    ),
    _Pattern(
        "theme_amber_gold", "Warm/Amber premium palette", "theme",
        r"(?:bg|text|border|from|to)-(?:amber|gold|orange)-(?:400|500)",
    ),
    _Pattern(
        "theme_toggle", "Sun/Moon theme toggle", "theme",
        r"(?:\bsetTheme\b|\buseTheme\b|ThemeToggle|theme-toggle|<Moon|<Sun)",
        frozenset({".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"}),
    ),

    # ── Layout & Spacing (5) ──────────────────────────────────────────
    _Pattern(
        "layout_container", "Centered container", "layout",
        r"(?:max-w-(?:5xl|6xl|7xl)\s+mx-auto|mx-auto\s+max-w-(?:5xl|6xl|7xl)"
        r"|max-width:\s*\d+px[^}]{0,200}margin:\s*0\s+auto)",
    ),
    _Pattern(
        "layout_section_pad", "py-16 md:py-24 rhythm", "layout",
        r"py-16\s+(?:\S+\s+)?md:py-24",
    ),
    _Pattern(
        "layout_grid", "3-column feature grid", "layout",
        r"(?:grid-cols-1\s+(?:\S+\s+)?md:grid-cols-[23]\s+(?:\S+\s+)?lg:grid-cols-[34]"
        r"|grid[^\n\"']*md:grid-cols-2[^\n\"']*lg:grid-cols-3"
        r"|grid-template-columns:\s*repeat\(\s*3)",
    ),
    _Pattern(
        "layout_hero", "Hero text-4xl \u2192 6xl", "layout",
        r"text-(?:4xl|5xl)\s+(?:\S+\s+)*(?:md:text-[56]xl|lg:text-[56]xl)",
    ),
    _Pattern(
        "layout_p6", "p-6 padding dominance", "layout",
        r"\bp-6\b",
    ),
    _Pattern(
        "layout_bento", "Bento grid sizing (col-span-2 / row-span-2)", "layout",
        r"\b(?:col-span-[234]|row-span-[234])\b",
    ),

    # ── Components & UI (5) ───────────────────────────────────────────
    _Pattern(
        "comp_rounded", "Large border-radius on cards", "components",
        r"(?:rounded-(?:xl|2xl)|border-radius:\s*(?:[6-9]|1[0-9]|2[0-4])px)",
    ),
    _Pattern(
        "comp_shadow", "shadow-sm everywhere", "components",
        r"\bshadow-sm\b",
    ),
    _Pattern(
        "comp_variants", "Button variant taxonomy", "components",
        r'(?:variant\s*[=:]\s*["\'](?:outline|ghost|destructive|secondary)["\']'
        r'|\.btn-(?:outline|ghost|destructive|secondary)\b'
        r'|class\s*=\s*["\'][^"\']*\bbtn-(?:outline|ghost)\b)',
    ),
    _Pattern(
        "comp_card_bg", "bg-white dark:bg-zinc-900 card", "components",
        r"bg-white\s+dark:bg-(?:zinc|slate)-(?:900|950)",
    ),
    _Pattern(
        "comp_hover", "Shadow-on-hover transition", "components",
        r"(?:hover:shadow-(?:md|lg)\s+transition|:hover\s*\{[^}]*box-shadow)",
    ),

    # ── Animation (3) ─────────────────────────────────────────────────
    _Pattern(
        "anim_fade_in", "Fade-in entrance animation", "animation",
        r"(?:animate-in|fade-in\s+slide-in-from"
        r"|@keyframes\s+\w*(?:fade.?in|enter|appear)\w*"
        r"|from\s*\{[^}]*opacity:\s*0[^}]*transform[^}]*translateY)",
    ),
    _Pattern(
        "anim_while_hover", "Framer whileHover", "animation",
        r"whileHover\s*=",
        frozenset({".tsx", ".jsx", ".ts", ".js"}),
    ),
    _Pattern(
        "anim_transition", "Ubiquitous short transitions", "animation",
        r"(?:transition-all\s+duration-(?:200|300)|transition:\s*[^;\n]{0,60}(?:0\.2s|0\.25s|0\.3s|200ms|250ms|300ms))",
    ),
    _Pattern(
        "anim_transition_var", "--transition-speed CSS variable", "animation",
        r"--transition-(?:speed|duration|time)\s*:",
        frozenset({".css", ".scss"}),
    ),

    # ── Code-Level Tells (5) ──────────────────────────────────────────
    _Pattern(
        "code_data_slot", "data-slot attributes (shadcn v4)", "code_tells",
        r"data-slot\s*=",
    ),
    _Pattern(
        "code_data_state", "data-state (Radix)", "code_tells",
        r"data-state\s*=",
    ),
    _Pattern(
        "code_cmdk", "cmdk palette in DOM", "code_tells",
        r"(?:cmdk-|CommandDialog|CommandInput|CommandList|CommandGroup)",
        frozenset({".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"}),
    ),
    _Pattern(
        "code_blur_nav", "Blurred sticky navbar", "code_tells",
        r"(?:backdrop-blur|backdrop-filter\s*:\s*blur)",
    ),
    _Pattern(
        "code_ui_imports", "components/ui/ imports", "code_tells",
        r'from\s+["\'](?:@/|~/|\.\./|\./)\S*components/ui/',
        frozenset({".tsx", ".jsx", ".ts", ".js"}),
    ),

    # ── Page Patterns (3) ────────────────────────────────────────────
    _Pattern(
        "page_section_ids", "Vibecoded section naming", "page_patterns",
        r'(?:id|class)\s*=\s*["\'][^"\']*\b(?:hero|features|pricing|testimonials|contact|how-it-works|cta)\b',
        frozenset({".html", ".jsx", ".tsx", ".vue", ".svelte", ".astro"}),
    ),
    _Pattern(
        "page_3tier_pricing", "3-tier pricing layout", "page_patterns",
        r'(?:pricing-card|PricingCard|pricing_card|price-card|PriceCard|pricing-tier|PricingTier)',
    ),
    _Pattern(
        "page_centered_hero", "Centered hero section", "page_patterns",
        r'(?:\.hero[^{]*\{[^}]*text-align:\s*center'
        r'|class\s*=\s*["\'][^"\']*(?:hero[^"\']*text-center|text-center[^"\']*hero'
        r'|min-h-screen[^"\']*items-center[^"\']*justify-center[^"\']*text-center'
        r'|text-center[^"\']*min-h-screen))',
    ),

    # ── Misc Tells (2) ───────────────────────────────────────────────
    _Pattern(
        "misc_pricing_scale", "Pricing card scale(1.05) highlight", "components",
        r"(?:scale-105\b|scale\(1\.0?5\))",
    ),
    _Pattern(
        "misc_emoji", "Emoji in UI source", "code_tells",
        # Unicode emoji blocks + HTML entities + JS \uXXXX surrogate pairs
        r"(?:[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F02F"
        r"\U0001F0A0-\U0001F0FF\U0001F100-\U0001F1FF\U0001F200-\U0001F2FF"
        r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]"
        r"|&#(?:9[0-9]{3}|[1-9][0-9]{4,5});"
        r"|\\u[Dd][89aAbB][0-9a-fA-F]{2}\\u[dD][cCdDeEfF][0-9a-fA-F]{2}"
        r"|\\u(?:26[0-9a-fA-F]{2}|27[0-9a-fA-F]{2}))",
    ),
    _Pattern(
        "typo_uppercase_label", "Uppercase pill labels (letter-spacing)", "typography",
        r"text-transform:\s*uppercase[^}]{0,200}letter-spacing",
    ),
    _Pattern(
        "code_root_div", "#root / __next wrapper (Vite/Next.js)", "code_tells",
        r"(?:#root\s*\{|id\s*=\s*[\"']root[\"']|<div\s+id\s*=\s*[\"']__next[\"']|__next\s*\{)",
    ),

    # ── Visual Render Tells ──────────────────────────────────────────
    _Pattern(
        "vis_gradient_text", "Gradient text effect", "typography",
        r"(?:bg-clip-text\s+text-transparent|-webkit-background-clip:\s*text"
        r"|background-clip:\s*text[^}]*(?:transparent|-webkit-text-fill-color))",
    ),
    _Pattern(
        "vis_hover_transform", "Micro-hover transforms (scale / translateY)", "animation",
        r"(?:hover:scale-10[0-9]|hover:-?translate-y-|"
        r":hover\s*\{[^}]*transform[^}]*(?:scale|translateY))",
    ),
    _Pattern(
        "vis_staggered_delay", "Staggered entrance animation delays", "animation",
        r"(?:animationDelay|animation-delay|animate-.*delay-?\d"
        r"|style=\s*\{[^}]*delay[^}]*['\"]0\.\d+s['\"])",
    ),
    _Pattern(
        "vis_lucide_svg", "Inline SVGs with Lucide stroke style", "components",
        r"stroke-?[Ll]ine-?[Cc]ap\s*[=:]\s*[\"']?round[^>]*stroke-?[Ll]ine-?[Jj]oin\s*[=:]\s*[\"']?round",
    ),
    _Pattern(
        "vis_tracking_widest", "Uppercase tracking-widest section labels", "typography",
        r"(?:tracking-widest|tracking-\[0\.[1-3]e?m\]|letter-spacing:\s*0\.(?:05|1|2)\d*em)",
    ),
    _Pattern(
        "vis_serif_italic", "Serif + Italic mixed heading typography", "typography",
        r"(?:font-\[family-name:[^\]]+\]|font-serif)[^>]+italic",
    ),
    _Pattern(
        "vis_glow_blob", "Large blur glow blobs (background decoration)", "theme",
        r"(?:blur-\[\d{2,3}px\]|blur:\s*\d{2,3}px|blur-3xl|blur-\[1[0-9]{2}px\])",
    ),
    _Pattern(
        "vis_glass_card", "Glassmorphism cards", "components",
        r"(?:glass-card|card-glass|bg-white/\[0\.0[24]\][^\"'\n]{0,100}border-white/5"
        r"|backdrop-filter:\s*blur\(\d+px\)[^}]{0,140}border:\s*1px\s+solid\s+rgba\(\s*255,\s*255,\s*255)",
    ),
    _Pattern(
        "vis_pill_cta", "Rounded-full pill CTA buttons", "components",
        r"(?:rounded-full[^\"'\n]{0,140}(?:bg-gradient-to-|bg-white)[^\"'\n]{0,140}"
        r"(?:hover:scale-10[0-9]|transition-transform)|border-radius:\s*9999px)",
    ),
    _Pattern(
        "vis_dark_canvas", "Near-black canvas + subtle separators", "theme",
        r"(?:bg-\[#0[0-9a-f]{5}\]|background(?:-color)?:\s*#0[0-9a-f]{5}|border-white/5)",
    ),
    _Pattern(
        "vis_trusted_by", "Trusted-by logo strip pattern", "page_patterns",
        r"(?:Trusted by|trusted by)[^\n<]{0,120}(?:teams|companies|enterprises|firms|startups|developers|organizations|brands|professionals)",
    ),
    _Pattern(
        "page_step_numbers", "01, 02, 03 step numbers", "page_patterns",
        r"(?:>0[1234]<|['\"]0[1234]['\"])",
    ),
    _Pattern(
        "page_ai_guarantees", "AI boilerplate copy (No credit card required, etc)", "page_patterns",
        r"(?:No credit card required|14-day free trial|Cancel anytime|SOC 2 certified|SOC 2 Type II)",
    ),
    _Pattern(
        "page_waitlist_copy", "Waitlist / Early Access boilerplate", "page_patterns",
        r"(?:Join Waitlist|Join the waitlist|Get early access|Request early access|Now in early access)",
    ),
    _Pattern(
        "page_fake_social_proof", "Fake social proof numbers (10,000+ teams)", "page_patterns",
        r"(?:[1-9][0-9]{1,3},000\+|[1-9][0-9]*[kKmM]\+)\s+(?:people|users|teams|developers|professionals)",
    ),
    _Pattern(
        "vis_hero_badge", "Hero announcement badge (pill with pulsing dot)", "components",
        r"(?:inline-flex|flex)[^\"'\n]*items-center[^\"'\n]*rounded-full[^\"'\n]*border[^>]*>[\s\S]{0,150}<(?:span|div)[^>]*[wh]-[0-9](?:\.[0-9])?[^>]*[wh]-[0-9](?:\.[0-9])?[^>]*rounded-full",
    ),
    _Pattern(
        "vis_faint_grid", "Faint grid/dot background pattern", "theme",
        r"(?:background-image:\s*(?:linear|radial)-gradient\([^;]+1px,\s*transparent\s+1px\)|bg-grid-[a-z]+(?:/[0-9]+)?|bg-dot-[a-z]+(?:/[0-9]+)?)",
    ),
    _Pattern(
        "vis_radial_fade", "Radial gradient fade background", "theme",
        r"(?:radial-fade|bg-\[radial-gradient|background(?:-image)?:\s*radial-gradient\([^)]*(?:transparent|rgba\([^)]+,\s*0\)))",
    ),
    _Pattern(
        "vis_soft_icon", "Soft-tinted icon square", "components",
        r"(?:bg-(?:[a-z]+-[456]00|primary|accent|brand)/10[\s\S]{0,150}text-(?:[a-z]+-[456]00|primary|accent(?:-light)?|brand)|text-(?:[a-z]+-[456]00|primary|accent(?:-light)?|brand)[\s\S]{0,150}bg-(?:[a-z]+-[456]00|primary|accent|brand)/10)",
    ),
    _Pattern(
        "vis_sparkles_icon", "Sparkles icon (AI indicator)", "components",
        r"(?:<Sparkles\b|lucide-react[^>]*Sparkles|M9\.937 15\.5A2 2 0 0 0 8\.5 14\.063)",
    ),
    _Pattern(
        "vis_shimmer", "Shimmer effect animation", "animation",
        r"(?:animate-shimmer|animation:\s*shimmer|background-size:\s*200%\s*(?:auto|100%)|bg-\[length:200%_100%\])",
    ),
    _Pattern(
        "vis_scroll_reveal", "Scroll-triggered IntersectionObserver reveals", "animation",
        r"(?:IntersectionObserver|useInView|react-intersection-observer|isIntersecting)",
        frozenset({".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte"}),
    ),
    _Pattern(
        "vis_floating", "Floating/bobbing animation", "animation",
        r"(?:animate-float|@keyframes\s+float\s*\{[\s\S]{0,100}translateY\(-|animation:\s*float\s+[3-6]s\s+ease-in-out\s+infinite)",
    ),
    _Pattern(
        "vis_mock_window", "Mock macOS window dots (red/yellow/green)", "components",
        r"bg-(?:red|rose)-[456]00(?:/[0-9]+)?[\s\S]{0,100}bg-(?:yellow|amber)-[456]00(?:/[0-9]+)?[\s\S]{0,100}bg-(?:green|emerald)-[456]00(?:/[0-9]+)?",
    ),
    _Pattern(
        "vis_gradient_border", "Gradient border mask technique", "components",
        r"(?:mask-composite:\s*exclude|-webkit-mask-composite:\s*xor|mask:\s*linear-gradient\([^)]+\)\s*content-box)",
    ),
    _Pattern(
        "vis_fading_divider", "Fading horizontal divider line", "components",
        r"(?:h-px|height:\s*1px)[^>]+bg-gradient-to-r[^>]+(?:transparent|from-transparent)[^>]+via-[a-z]+-[456]00"
        r"|linear-gradient\(90deg,\s*transparent\s*0%,\s*rgba\([^,]+,[^,]+,[^,]+,\s*0\.[1-9]\)\s*50%,\s*transparent\s*100%\)",
    ),
    _Pattern(
        "vis_conic_gradient", "Conic gradient background (often for orbs)", "theme",
        r"(?:conic-gradient\([^)]+from\s+0deg[^)]+\)|bg-\[conic-gradient)",
    ),
    _Pattern(
        "vis_hue_rotate", "Hue-rotation animation", "animation",
        r"(?:filter:\s*hue-rotate|hue-rotate-\[?\d+deg\]?)",
    ),
    _Pattern(
        "vis_custom_scrollbar", "Custom webkit scrollbar styling", "theme",
        r"::-webkit-scrollbar(?:-thumb|-track)?\s*\{",
    ),
    _Pattern(
        "vis_top_card_accent", "Top-edge gradient accent line on cards", "components",
        r"(?:absolute\s+inset-x-0\s+top-0\s+h-[12]\s+bg-gradient-to-[r|l]|border-t-[234]\s+border-[a-z]+-[456]00)",
    ),
    _Pattern(
        "vis_dashboard_mockup", "Fake dashboard/browser window mockup", "components",
        r"(?:Mock Dashboard|Dashboard mockup|Browser mockup|Mock browser|app\.[a-z]+\.[a-z]+)",
    ),
    _Pattern(
        "vis_pulse_glow", "Pulsing glow animation", "animation",
        r"(?:@keyframes\s+[a-z-]*pulse[a-z-]*|animate-[a-z-]*pulse[a-z-]*)",
    ),
]


def collect_files(root: Path) -> list[Path]:
    """Walk the tree, skip junk dirs, return scannable source files."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname in SKIP_FILES:
                continue
            fpath = Path(dirpath) / fname
            if fpath.suffix in SCAN_EXTENSIONS:
                try:
                    if fpath.stat().st_size < 1_000_000:
                        files.append(fpath)
                except OSError:
                    continue
    return files


def detect_content(root: Path, files: list[Path]) -> list[Signal]:
    counts: dict[str, int] = {p.signal_id: 0 for p in CONTENT_PATTERNS}
    file_hits: dict[str, list[str]] = {p.signal_id: [] for p in CONTENT_PATTERNS}

    for fpath in files:
        try:
            content = fpath.read_text(errors="ignore")
        except OSError:
            continue

        rel = str(fpath.relative_to(root))

        for pat in CONTENT_PATTERNS:
            if pat.extensions and fpath.suffix not in pat.extensions:
                continue
            found = re.findall(pat.regex, content, re.IGNORECASE)
            if found:
                counts[pat.signal_id] += len(found)
                file_hits[pat.signal_id].append(rel)

    signals: list[Signal] = []
    for pat in CONTENT_PATTERNS:
        sig = Signal(
            id=pat.signal_id,
            name=pat.name,
            category=pat.category,
            count=counts[pat.signal_id],
        )
        if counts[pat.signal_id] >= pat.threshold:
            sig.detected = True
            top = file_hits[pat.signal_id][:5]
            sig.evidence = list(top)
            n_files = len(file_hits[pat.signal_id])
            if n_files > 5:
                sig.evidence.append(f"... and {n_files - 5} more files")
        signals.append(sig)

    return signals
