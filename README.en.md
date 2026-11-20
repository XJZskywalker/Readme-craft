# readme-craft

English | [中文](README.md)

A skill that writes, rewrites, and audits project READMEs. Every claim is checked against the repository, and every section has to earn its place.

Most AI-generated READMEs fail the same way: a welcome paragraph, a six-item feature list with no verbs, and install commands copied from a tutorial. This skill replaces that with a fixed procedure. Scan the repo for facts, choose a section set for the project type, draft, then run a linter that fails on marketing language, invented values, and decorative emoji.

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

Requirements: Python 3.9 or newer for the two scripts. Neither imports anything outside the standard library.

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

`readme_lint.py` is deterministic. It reads the file, scores it 0–100, and exits non-zero on any error.

| Group | Examples |
|---|---|
| Invented content | `TODO`, `TBD`, placeholder images, `example.com/your-*` links |
| Marketing register | `seamless`, `robust`, `blazing`, `cutting-edge`, `强大`, `一站式`, `开箱即用` |
| Structure | missing title, multiple H1, empty section, no quick start or usage |
| Formatting | untagged code fence, emoji headings, more than 3 badges |
| Density | bullet-only documents, six-bullet runs, over-long sentences, length over budget |
| License | claims a license while no `LICENSE` file exists |

`python scripts/readme_lint.py --list-rules` prints every check with the word lists behind it. To exempt a rule for one file, put `<!-- readme-lint: disable rule-name -->` anywhere in it.

Sample output:

```text
README lint: README.md
type: cli (budget 160)  lines: 68

  L1   error heading-emoji  decorative emoji in a heading
  L8   error hype           marketing word `seamless` — state the behaviour instead
  L20  warn  bullet-run     6 consecutive bullets — use prose or a table

score: 64/100  (2 errors, 1 warning)
result: FAIL
```

## Bundled examples

`examples/` holds two before/after pairs. The "before" files are typical generated READMEs; the "after" files were written with this skill.

| File | Score |
|---|---|
| `cli-before.md` | 0/100, 23 errors |
| `cli-after.md` | 100/100 |
| `library-before.md` | 0/100, 7 errors |
| `library-after.md` | 100/100 |

Reproduce all of it, and check the rule table has no undeclared ids, with one command:

```bash
python scripts/readme_lint.py --self-test
```

## Layout

```text
SKILL.md                  procedure the agent follows
references/
  structure.md            archetypes, section matrix, length budgets
  style-rules.md          voice rules, banned phrases, 20 rewrites
  fact-sheet.md           where commands, config, and license live per ecosystem
scripts/
  project_scan.py         repo to fact sheet
  readme_lint.py          fact sheet and prose to score
examples/
  cli-before.md    cli-after.md
  library-before.md  library-after.md
```

## Design notes

**Facts before prose.** The agent is not allowed to draft until the fact sheet is settled. Commands come from CI, then Makefile, then manifest scripts — never from memory. Anything unresolved becomes a `TODO` in the output, listed in the delivery notes.

**Trimming over filling.** `references/structure.md` defines five archetypes and a matrix of which sections apply. Optional sections are removed, not shortened into one-line stubs.

**Deterministic checks.** The linter catches what a model tends to miss in its own output: marketing adjectives, decorative emoji, bullet-only structure, claims that the repository cannot support. Style judgement stays with the prompt; measurable defects go to code.

**Chinese and English.** Rules cover both. The linter flags missing spacing between Chinese and Latin text, and the banned-phrase list includes the Chinese marketing vocabulary that generated READMEs tend to use.

## License

MIT. See [LICENSE](LICENSE).
