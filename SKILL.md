---
name: readme-craft
description: Writes, rewrites, and audits project READMEs so they read like a maintainer's work instead of generated text. Use when creating a README from scratch, cleaning up a bloated or template-heavy README, preparing a repository for open source, or checking that README commands and configuration match the actual code. Covers CLI tools, libraries, web apps, and monorepos.
agent_created: true
---

# README Craft

Produce README files a maintainer would sign their name to: every claim traceable to a file in the repository, every section earning its space, prose written in flat declarative sentences.

## Modes

| Mode | Condition | Output |
|---|---|---|
| generate | No README, or a stub under 10 lines | New `README.md` |
| rewrite | README exists but is bloated, templated, or AI-flavored | Rewritten `README.md` + change notes |
| audit | User asks for review only, or says "don't change anything" | Findings and score, no file writes |

Infer the mode from the request. If the intent is genuinely unclear, ask one question instead of guessing.

## Non-negotiables

1. **No invented facts.** Every command, flag, environment variable, port, and badge must trace to a file in the repository. When a value cannot be determined, leave `<!-- TODO: verify <thing> -->` and list it in the delivery notes. Never fill a gap with a plausible guess.
2. **No marketing register.** `seamless`, `robust`, `powerful`, `blazing fast`, `cutting-edge`, `effortlessly` are defects, not style choices.
3. **No decorative emoji** in headings or bullets.
4. **Trim, do not fill.** A missing section beats an empty one. A 60-line README for a 300-line script is correct.
5. **Verify before delivering.** Run `scripts/readme_lint.py` until it exits zero.

## Workflow

### Phase 1 — Scope the repository

Identify the project root (the directory holding the manifest). Check:

- what kind of project this is (see `references/structure.md` → archetype table)
- whether `LICENSE` exists, and which license it actually is
- whether a README already exists and how long it is
- whether `docs/`, `CONTRIBUTING.md`, or `CHANGELOG.md` already cover ground the README should link to instead of duplicate

### Phase 2 — Collect facts

Run the scanner, then verify anything that will be quoted:

```bash
python scripts/project_scan.py . --out facts.md
```

Read `facts.md`. Confirm by opening the source files — install commands, run commands, and environment variables are the three things that most often drift from reality. When the scanner reports `unknown`, resolve it by reading code, or leave a `TODO`.

Do not write prose until the fact sheet is settled.

### Phase 3 — Choose archetype and trim

Load `references/structure.md`. Pick the archetype, start from its skeleton, then delete every section that does not apply. Sections are removed, never compressed into a one-line stub.

### Phase 4 — Draft

Write in this order; earlier sections constrain later ones.

1. Title and one-sentence positioning: what it does, for whom, no adjectives.
2. Quick start: fewest steps to a working state, ending with one command whose output proves it worked.
3. Installation, when it differs from quick start (extras, system dependencies, Docker).
4. Usage and examples: copy-pasteable, each with expected output.
5. Remaining sections from the skeleton.

### Phase 5 — Lint and self-review

```bash
python scripts/readme_lint.py README.md --type <archetype> --repo .
```

Fix errors, rerun until clean. Then read once more and cut any sentence that would survive unchanged in a different project's README — that sentence carries no information about this project.

### Phase 6 — Deliver

Write the file, then report:

```text
README: <path>  (<mode>, <archetype>, <n> lines, lint <score>/100)
Removed: <what and why, one bullet per item>
TODOs: <unverified items, or "none">
```

## Writing rules of thumb

| Rule | Detail |
|---|---|
| Numbers over adjectives | `parses 10k rows in ~1.8s` beats `blazing fast` |
| One idea per sentence | Under 25 words; paragraphs under 4 sentences |
| Lists stay short | At most 5 items, introduced by a sentence; two lists never touch |
| No TOC under 100 lines | Anchor lists cost more than they save in short files |
| At most 3 badges | Each one points at state that actually exists |
| Tag every code fence | `bash`, `ts`, `text` — never a bare fence |
| Never skip heading levels | H1 → H2 → H3 |

Detailed voice rules, the banned-phrase list, and 20 before/after rewrites live in `references/style-rules.md`. Load it before drafting any prose.

## References

| File | Load when |
|---|---|
| `references/structure.md` | Choosing archetype, section set, length budget |
| `references/style-rules.md` | Writing or reviewing prose |
| `references/fact-sheet.md` | Extracting commands/config from a specific ecosystem |
| `examples/` | Needing a concrete before/after reference |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/project_scan.py` | Emit a fact sheet: manifests, commands, env vars, entry points, license, tree |
| `scripts/readme_lint.py` | Deterministic checks for invented facts, AI tells, formatting; scores 0–100 |

Both use the standard library only. Run them from the repository being documented so relative paths resolve.
