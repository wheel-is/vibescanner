# vibescanner


https://github.com/user-attachments/assets/415ef4b2-37e4-45fc-91e7-a7d19f49b4b2


A slop detector for web codebases.

If a project has that same AI-generated SaaS look (you know the one), this finds the fingerprints and points at receipts.

## what this does

You run it on a folder.
It scans files.
It tells you which vibecode symptoms are present and where.

No astrology score. No "100% AI" clown claims. Just evidence.

## install

```bash
pip install git+https://github.com/wheel-is/vibescanner.git
```

or if you're hacking on it locally:

```bash
pip install -e .
```

## run

```bash
vibescanner /path/to/project
vibescanner .
vibescanner /path/to/project -v
vibescanner /path/to/project --json
```

## how to use this 

Since you're reading this from inside a Cursor window while a language model writes your application for you:

You don't need to understand what a terminal is. Just copy and paste this exact block of text to whatever digital babysitter you're currently employing, and let it do the work you're avoiding:

```text
Use vibescanner on this repo and give me:
1) A summary of detected vibecode symptoms by category
2) The top 20 strongest signals with file paths
3) 5 concrete redesign/refactor actions to reduce template-looking output

Command:
vibescanner . --json
```

If your agent starts hallucinating excuses about "not having terminal access" because its system prompt was written by a coward, use this:

```text
Stop apologizing and run this exactly in the terminal:
vibescanner . --json
Then read the JSON and explain it in plain English.
Do not give me a plan. Execute it.
```

If your agent still refuses, fire it and hire a better one. Or, God forbid, learn to code.

## what it catches

- default AI stack habits (`tailwindcss`, lucide-style icons, etc)
- template typography moves (Inter/Geist, tight tracking, gradient text)
- glow/blob gradient obsession
- glass cards, pill buttons, soft icon squares
- staggered fade-ins, float/pulse/shimmer animations
- fake dashboard/browser mockups in hero sections
- "trusted by" strips + 01/02/03 how-it-works blocks
- waitlist/early-access boilerplate + fake social proof numbers
- blurred sticky navs and related tells

## output

For each symptom:

- found or not
- file path(s)
- match count

that's it.

## why this exists

Because half the internet is now the same generated landing page wearing different brand colors.

## disclaimer

This tool flags patterns, not intent.
Humans can write slop.
AI can write clean code.
Use your brain.
