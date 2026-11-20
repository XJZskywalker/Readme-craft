# Fact extraction

Every statement in the README must trace to a file. This sheet lists where the facts live per ecosystem, and how to handle what cannot be found.

## Where to look

| Ecosystem | Manifest | Commands | Entry point | Env vars |
|---|---|---|---|---|
| Node | `package.json` | `scripts` | `bin`, `main`, `exports` | `.env.example`, `process.env.*` |
| Python | `pyproject.toml`, `setup.py`, `setup.cfg` | `[project.scripts]`, `Makefile`, `tox.ini` | `__main__.py`, `console_scripts` | `.env.example`, `os.environ` |
| Go | `go.mod` | `Makefile`, `Taskfile.yml` | `main.go`, `cmd/*/main.go` | `os.Getenv` |
| Rust | `Cargo.toml` | `[[bin]]`, `Makefile` | `src/main.rs` | `.env`, `std::env` |
| PHP | `composer.json` | `scripts` | `bin/` | `.env.example` |
| Java/Kotlin | `pom.xml`, `build.gradle` | gradle tasks, `mvnw` | `Main` class | `application.yml` |
| Ruby | `Gemfile`, `*.gemspec` | `Rakefile`, `bin/` | `exe/`, `bin/` | `.env.example` |

Framework configs worth reading when present: `Dockerfile` (CMD, EXPOSE), `docker-compose.yml` (services, ports, env), `.github/workflows/*` (real build and test commands), `Makefile` (the canonical shortcuts).

## Command precedence

When several sources disagree, trust them in this order:

1. CI workflow — it is the only place where the command is proven to run.
2. `Makefile` / `Taskfile` — written for humans, usually correct.
3. Manifest script definitions.
4. `Dockerfile` CMD / ENTRYPOINT.
5. The README that already exists — assume stale until verified.
6. Nothing. Do not default to `npm install` from habit.

Record the source next to each command so the reader can be shown the trail when challenged.

## Environment variables

Extract from `.env.example` (or `.env.sample`, `.env.template`), then confirm each key is actually read in code:

```bash
grep -rn "process.env\." src | head -30        # Node
grep -rn "os.environ\|getenv" src | head -30    # Python
grep -rn "os.Getenv" . | head -30               # Go
```

Defaults come from the code, not from the example file — `.env.example` often carries a demo value that is not the default. Mark required vs optional by whether the code throws or falls back.

A variable in `.env.example` that no code reads is itself a fact worth reporting: it means either dead config or missing wiring, and the README should not document it.

## Licensing

Read the `LICENSE` file and identify the text. Do not infer from the ecosystem, the author, or a badge. Common markers:

| Marker in file | License |
|---|---|
| `Permission is hereby granted, free of charge` | MIT |
| `Apache License` + `Version 2.0` | Apache-2.0 |
| `GNU GENERAL PUBLIC LICENSE` + `Version 3` | GPL-3.0 |
| `GNU AFFERO` | AGPL-3.0 |
| `BSD 3-Clause` | BSD-3-Clause |
| `Mozilla Public License` | MPL-2.0 |
| `UNLICENSED` in manifest, no file | proprietary — say "internal use only" or omit |

No file → no license section. `package.json` claiming MIT without a `LICENSE` file means the repo is effectively unlicensed; report that instead of copying the claim.

## Fact sheet format

`project_scan.py` writes this shape. Keep it in a scratch file, not in the repo, unless the user wants it committed.

```markdown
# Facts

## Identity
name: fastparse
version: 2.1.0            (package.json:3)
license: MIT              (LICENSE:1-3)
archetype: library

## Commands
install:   npm install fastparse            (README of registry, verified: no)
build:     npm run build                    (package.json scripts.build)
test:      npm test                         (.github/workflows/ci.yml:22)
dev:       npm run dev                      (package.json scripts.dev)
dev server: http://localhost:5173           (vite.config.ts:8)

## Entry points
src/index.ts   exports parse, ParseError

## Environment
FASTPARSE_CACHE_DIR   optional   default: ~/.cache/fastparse   (src/cache.ts:11)
FASTPARSE_LOG_LEVEL   required   no default, throws            (src/log.ts:6)

## Structure
src/       source
test/      vitest specs
docs/      guides

## Existing docs
README.md (312 lines) — has TOC, 9 badges, no config section
CONTRIBUTING.md — present, covers PR flow

## Unknowns
- Whether Windows is supported (no CI matrix entry)
- Node version floor (engines field absent)
```

## Handling gaps

| Situation | Action |
|---|---|
| Command exists but untested | Document it, keep it, note nothing. A manifest script is a reasonable source. |
| Command inferred from convention only | Leave `<!-- TODO: verify install command -->`, list in delivery notes. |
| Feature described in issues but absent from code | Do not document it. |
| Feature present but undocumented anywhere | Read the code, describe what it does, not what it should do. |
| Version number unavailable | Omit version-specific text entirely. |
| Screenshot referenced but missing | Remove the image; do not hotlink a placeholder service. |

The README's value is that a reader can trust it. One invented command destroys that trust more than ten missing sections ever would.
