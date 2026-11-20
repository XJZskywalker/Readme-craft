---
name: readme-craft
description: Writes and rewrites project READMEs so the file reads like a maintainer wrote it. Use when a repository has no README, when an existing one is long or sounds generated, or before publishing to open source. Covers CLI tools, libraries, web apps, monorepos, and single scripts.
agent_created: true
---

# readme-craft

A README's only real asset is that a reader can trust it. Trust comes from detail a reader can check: the install command CI actually runs, the config key that appears in the code, the version floor taken from the manifest. A short file that holds up beats a complete one that does not.

## Three ways in

| What exists | What you do |
|---|---|
| Nothing, or a stub under 10 lines | Write the file |
| A README that is long, templated, or sounds generated | Rewrite it |
| A request for review, or "don't change anything" | Report findings, write nothing |

Ask one question when the intent is genuinely unclear. Otherwise read the situation from the repository and start.

## The fact sheet comes first

```bash
python scripts/project_scan.py . --out facts.md
```

The scanner reports `unknown` where it cannot tell, and those are questions for the repository rather than gaps to fill from habit. Verify by hand the three facts that drift fastest: how it installs, how it runs, and which environment variables it reads. `references/fact-sheet.md` says where each of those lives per ecosystem, and what to do when a value cannot be established at all.

The fact sheet is the evidence. A claim without a line behind it stays out of the file, or goes in as a `TODO` that the delivery note repeats back to the user.

**Done when** each planned section has a fact behind it. No prose before that point.

## Shape follows use

`references/structure.md` holds five archetypes — CLI, library, web app, monorepo, single script — each with a skeleton and a length budget. Pick the archetype that matches how the project gets consumed, start from its skeleton, then cut.

The cut is the work. A section survives because removing it would change what the reader does next; a section compressed into one line is still a section the reader has to skip. Going over the budget means one section is competing with another for space, not that every paragraph needs tightening.

**Done when** every surviving section passes that removal test, and the file sits inside its budget.

## Writing the prose

Keep `references/style-rules.md` open while drafting. It carries the voice rules, twenty before/after rewrites, and the three review reads that catch what the linter cannot.

The habit that carries most of the quality: replace the adjective with the number. A parse of 10k rows in 1.8 seconds is a fact the reader can check; "fast" is a claim they have to take on faith.

## The gate

```bash
python scripts/readme_lint.py README.md --type <archetype> --repo .
```

The linter scores the file 0–100, names the line, and exits non-zero only on errors. Correctness errors and a few always-on warnings run by default; fix and rerun until it exits zero. `python scripts/readme_lint.py --list-rules` prints every check and the word lists behind them, which is also where `references/style-rules.md` points instead of restating them.

It catches what a model misses in its own output: marketing adjectives, invented placeholders, broken headings, a license claim with no `LICENSE` file behind it. Taste rules — sentence length, emoji density, CJK spacing — are opt-in with `--style` and never block a gate, because style is not an incident. Whether a section earns its space is not machine-checkable, so that judgement stays with you.

## Handing it back

```text
README.md  (rewrite, cli, 64 lines, lint 100/100)
Removed: table of contents, six-bullet feature list, placeholder screenshot
Unverified: minimum Node version, whether Windows is supported
```

Two lines on what you cut, because the cut is where the quality came from.
