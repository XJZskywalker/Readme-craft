# AGENTS.md

## README is gated

`.githooks/pre-commit` and `.githooks/pre-push` run `scripts/readme_lint.py` against `README.md` and block the commit or push on any error. Enable them once per clone:

```bash
git config core.hooksPath .githooks
```

## When to apply the skill

Before committing a change to a manifest, a dependency, a command, an environment variable, or anything the README describes: apply the `readme-craft` skill. This repository is that skill, so `SKILL.md` is the procedure and the gate's failure message is the entry point.

The short form, when the file is close enough that a full pass would be ceremony:

```bash
python scripts/project_scan.py . --out facts.md    # facts first
# update README.md, then mirror the change in README.en.md
python scripts/readme_lint.py README.md --repo .    # until it exits 0
rm facts.md
```

Both READMEs carry the same sections and the same facts; only the language differs. A change that lands in one and not the other is a bug the linter cannot see.

## What the gate cannot check

Facts. It catches placeholder text and license claims the repository cannot support, but it has no way to know whether `npm run start` is the real command or whether the port in the table matches the code. That verification comes from the fact sheet, and it is the part worth doing carefully.

## Working on the linter

`python scripts/readme_lint.py --self-test` asserts that the bundled examples score as expected and that no check emits an undeclared rule id. Run it after touching a rule. A commit that deliberately leaves `README.md` failing, such as one mid-refactor of the linter itself, may use `--no-verify`.
