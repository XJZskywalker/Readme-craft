#!/bin/sh
# README gate, shared by the pre-commit and pre-push hooks.
#
# $1  revision spec for the README blob: ":README.md" for the index, or
#     "<sha>:README.md" for the commit about to be pushed. Defaults to the index.
# $2  revision range for the staleness check, e.g. origin/main..HEAD. Empty on
#     pre-commit (uses the index) and on a first push (staleness is skipped).
#
# The gate lints the blob that will actually be published. Reading the
# working-tree copy instead would let a clean file mask a broken staged one,
# or a broken file block a clean commit. Hooks cannot call a model, so this
# blocks and names the fix path; AGENTS.md is what makes an agent apply
# readme-craft when that happens.

set -u

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0

[ -f scripts/readme_lint.py ] || exit 0

py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
if [ -z "$py" ]; then
    echo "readme-gate: no python on PATH, gate skipped" >&2
    exit 0
fi

rev_spec=${1:-":README.md"}
range=${2:-}

# A commit that removes the README is not something a README linter can judge.
if ! blob=$(git rev-parse --verify -q "$rev_spec" 2>/dev/null) || [ -z "$blob" ]; then
    echo "readme-gate: no README blob in $rev_spec, skipping" >&2
    exit 0
fi

# Staleness warns without blocking, and runs first so its message is visible
# even when the linter below fails.
if [ -f scripts/readme_stale.py ]; then
    if [ -n "$range" ]; then
        "$py" scripts/readme_stale.py --repo . --range "$range" >&2 || true
    elif [ "$rev_spec" = ":README.md" ]; then
        "$py" scripts/readme_stale.py --repo . --staged >&2 || true
    fi
fi

if git cat-file blob "$blob" | "$py" scripts/readme_lint.py --stdin --repo . >&2; then
    exit 0
fi

cat >&2 <<'EOF'

readme-gate: the README in this commit failed its linter (see above).

Apply the readme-craft skill (SKILL.md) to fix it, then retry:
  1. python scripts/project_scan.py . --out facts.md
  2. rewrite README.md and mirror the change in README.en.md
  3. python scripts/readme_lint.py README.md --repo .   # until exit 0
  4. rm facts.md
  5. git add README.md README.en.md

--no-verify skips this gate. Reserve it for commits whose README failure
is deliberate, such as working on the linter itself.
EOF
exit 1
