# AGENTS.md

## README is gated

`.githooks/pre-commit` and `.githooks/pre-push` run `scripts/readme_lint.py` on the README blob inside the index or the commit being pushed. An error blocks the operation; warnings only print. Enable once per clone:

```bash
git config core.hooksPath .githooks
```

The gate reads git objects, not the working-tree file. Editing `README.md` without `git add` cannot change what gets checked. To see exactly what the gate saw:

```bash
git show :README.md | python scripts/readme_lint.py --stdin --repo .
```

`scripts/readme_stale.py` runs alongside it. It warns without blocking when a manifest, `.env.example`, `Dockerfile`, `Makefile`, or a command/env line of a CI workflow changed while the README stayed the same, and it names any env-example variable that no README documents. Workflow edits that change only the runner, matrix, or triggers stay silent. Treat that warning as the real trigger: an untouched README after a contract change is how documentation goes stale. A first push has no diff base, so this check is skipped there.

## When to apply the skill

Before committing a change to a manifest, a dependency, a command, an environment variable, or anything the README describes: apply the `readme-craft` skill. This repository is that skill, so `SKILL.md` is the procedure and the gate's failure message is the entry point.

The short form, when the file is close enough that a full pass would be ceremony:

```bash
python scripts/project_scan.py . --out facts.md    # facts first
# update README.md, then mirror the change in README.en.md
python scripts/readme_lint.py README.md --repo .    # until it exits 0
rm facts.md
git add README.md README.en.md
```

Both READMEs carry the same sections and the same facts; only the language differs. A change that lands in one and not the other is a bug the linter cannot see.

## What the gate cannot check

Facts. It catches placeholder text and license claims the repository cannot support, but it has no way to know whether `npm run start` is the real command or whether the port in the table matches the code. That verification comes from the fact sheet, and it is the part worth doing carefully.

The license-file check looks at the working tree, so deleting `LICENSE` without committing it leaves a short window where that one check judges the working tree rather than the commit. Everything else the gate reads comes from the commit.

Taste rules (sentence length, emoji density, CJK spacing) are off by default. `--style` turns them on for a manual pass; the gate never blocks on them.

## Working on the linter

Run both self-tests after touching a rule:

```bash
python scripts/readme_lint.py --self-test
python scripts/readme_stale.py --self-test
```

The first asserts the bundled examples score as expected, that no rule id is duplicated or dangling, and that style rules stay out of the default run. The second builds a throwaway repository to exercise the staleness cases and whole-token env matching.

A commit that deliberately leaves `README.md` failing, such as one mid-refactor of the linter itself, may use `--no-verify`.
