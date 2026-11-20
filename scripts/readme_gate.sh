#!/bin/sh
# README gate, shared by the pre-commit and pre-push hooks.
# Blocks the operation when README.md fails its own linter.
# Fix path: apply the readme-craft skill, see AGENTS.md.

set -u

root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$root" || exit 0

[ -f README.md ] || exit 0
[ -f scripts/readme_lint.py ] || exit 0

py=$(command -v python3 2>/dev/null || command -v python 2>/dev/null)
if [ -z "$py" ]; then
    echo "readme-gate: no python on PATH, gate skipped" >&2
    exit 0
fi

if "$py" scripts/readme_lint.py README.md --repo . >&2; then
    exit 0
fi

cat >&2 <<'EOF'

readme-gate: README.md failed the linter above.

Apply the readme-craft skill (SKILL.md) to fix it, then retry:
  1. python scripts/project_scan.py . --out facts.md
  2. rewrite README.md and README.en.md from the fact sheet
  3. python scripts/readme_lint.py README.md --repo .   # until exit 0
  4. rm facts.md

--no-verify skips this gate. Reserve it for commits whose README failure
is deliberate, such as working on the linter itself.
EOF
exit 1
