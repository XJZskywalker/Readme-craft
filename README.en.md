# readme-craft

English | [中文](README.md)

A skill that writes, rewrites, and audits project READMEs. Every claim is checked against the repository, and every section has to earn its place.

Most AI-generated READMEs fail the same way: a welcome paragraph, a six-item feature list with no verbs, and install commands copied from a tutorial. This skill replaces that with a fixed procedure. Scan the repo for facts, choose a section set for the project type, draft, then run a linter.

## Modes

| Mode | When it runs | Output |
|---|---|---|
| Generate | No README, or a stub under 10 lines | New `README.md` |
| Rewrite | README is bloated, templated, or reads as generated | Rewritten file plus change notes |
| Audit | You want a review without edits | Findings and a score |

## Install

Copy the folder into your agent's skills directory:

```bash
git clone https://github.com/XJZskywalker/Readme-craft.git
mkdir -p ~/.workbuddy/skills
cp -r Readme-craft ~/.workbuddy/skills/readme-craft
```

For Claude Code and other agents that read `SKILL.md` from a skills folder, the same copy works — the directory layout is standard.

Requirements: Python 3.9 or newer. The three Python scripts use only the standard library; the gate is a POSIX sh script.

Working on this repository itself, enable the README gate once after cloning. Every commit and push then lints the README inside the commit:

```bash
git config core.hooksPath .githooks
```

## Use

Ask in the language you would normally use:

```text
Write a README for this project.
```

```text
This README reads like it was generated. Cut it down and make it accurate.
```

```text
Check the README against the code. Don't change anything, just report.
```

The agent runs `project_scan.py`, reads the fact sheet, drafts the README, then runs `readme_lint.py` until it exits clean. Delivery notes list what was removed and which values could not be verified.

## What the linter checks

`readme_lint.py` is deterministic. It reads the file, reports a 0–100 reference score, and lets errors alone decide the exit code. Checks come in three tiers:

| Tier | Default | What it covers |
|---|---|---|
| error | on, blocks | placeholder text and fake links, marketing words, missing or repeated H1, empty sections, no quick start, emoji in headings, a license claim with no `LICENSE` file |
| warn | on, advisory | skipped heading levels, no install section, unexplained feature lists, untagged code fences, length over budget |
| style | off | sentence length, bullet runs, emoji density, badge count, bold density, em dashes, CJK spacing, filler phrases, a TOC in a short file |

Taste rules are off by default because style is not an incident. Add `--style` to see them; the gate never blocks on them. The score is advisory, and any number of warnings still exits zero.

Sample output, default tiers:

```text
README lint: README.md
type: cli (budget 160)  lines: 68

  L1   error heading-emoji  decorative emoji in a heading
  L8   error hype           marketing word detected — state the behaviour instead
  L20  warn  fence-lang     code fence without a language tag

score: 72/100  (2 errors, 1 warning)
result: FAIL
```

`python scripts/readme_lint.py --list-rules` prints every check with the word lists behind it; `references/style-rules.md` explains why those words are a problem instead of restating them. To exempt a rule for one file, put `<!-- readme-lint: disable rule-name -->` anywhere in it.

## Bundled examples

`examples/` holds two before/after pairs. The "before" files are typical generated READMEs; the "after" files were written with this skill.

| File | Score |
|---|---|
| `cli-before.md` | 0/100, 23 errors |
| `cli-after.md` | 100/100 |
| `library-before.md` | 4/100, 7 errors |
| `library-after.md` | 100/100 |

A score only says whether the file hit the rules this skill lists; errors decide FAIL, not the number.

Reproduce the scores, assert no rule id is duplicated or dangling, and verify the tiering holds:

```bash
python scripts/readme_lint.py --self-test
python scripts/readme_stale.py --self-test
```

## The gate on commit and push

Hooks cannot call a model, so they block and point rather than rewrite.

- `pre-commit` lints the README in the index; `pre-push` lints the README in the commit about to be published. Both read git objects, not the working tree — fixing the file after `git add` cannot fool the gate
- Any error blocks the commit or push; warnings are printed only
- Contract files changed — manifest, `.env.example`, `Dockerfile`, `Makefile`, CI workflow — while the README stayed the same produces a warning, not a block. Variables in the env example that no README names are listed individually, matched as whole tokens so `SUPPORT` does not count as documenting `PORT`
- A first push has no baseline, so the staleness check is skipped; a push carrying several branches checks each one

GitHub Actions also runs both self-tests and lints both READMEs on every push and pull request, on Python 3.9 and 3.12, so a broken rule cannot slip in quietly.

`python scripts/readme_stale.py --staged --strict` turns the warning into a non-zero exit for your own CI. The bundled workflow does not use it — a dependency bump would turn the build red on every run.

Facts are outside the gate's reach: whether a command really exists or a port is right still comes from the fact sheet and a human read. The license-file check looks at the working tree, so deleting `LICENSE` without committing it leaves a brief mismatch.

## Layout

```text
SKILL.md                  procedure the agent follows
references/
  structure.md            archetypes, section matrix, length budgets
  style-rules.md          voice rules, why phrases fail, 20 rewrites
  fact-sheet.md           where commands, config, and license live per ecosystem
scripts/
  project_scan.py         repo to fact sheet
  readme_lint.py          file to findings and score
  readme_stale.py         contract changed, README untouched
  readme_gate.sh          the commit and push gate
AGENTS.md                 how an agent works with the gate
.githooks/                pre-commit and pre-push hooks
.github/workflows/        CI running the self-tests and README lints
examples/
  cli-before.md    cli-after.md
  library-before.md  library-after.md
```

## Design notes

**Facts before prose.** The agent is not allowed to draft until the fact sheet is settled. Commands come from CI, then Makefile, then manifest scripts — never from memory. Anything unresolved becomes an unverified marker in the output, listed in the delivery notes.

**Trimming over filling.** `references/structure.md` defines five archetypes and a matrix of which sections apply. Optional sections are removed, not shortened into one-line stubs.

**Deterministic checks.** The linter handles what a model misses and what can actually break a reader's trust: marketing adjectives, invented placeholders, broken structure, claims the repository cannot support. Sentence length and emoji density stay with the prompt by default and are only reported by `--style`.

**Chinese and English.** The banned-phrase list includes the marketing vocabulary of generated Chinese READMEs, and headings are recognised in both languages. CJK spacing sits in the style tier and is off by default.

## License

MIT. See [LICENSE](LICENSE).
