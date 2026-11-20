# Structure

Section sets, skeletons, and length budgets per archetype. Start from the skeleton, then delete — never add a section "for completeness".

## Archetype detection

| Signal in repo | Archetype |
|---|---|
| `bin` field, `bin/` dir, `console_scripts` entry point, `cmd/` + `main.go`, argparse/click at entry | `cli` |
| `main`/`exports`/`types` with no runnable server, `[project]` + `src/` layout, published to a registry | `library` |
| framework dependency (next, nuxt, django, fastapi, rails, spring), `docker-compose.yml`, `Dockerfile` exposing a port | `web-app` |
| `workspaces`, `packages/*`, `apps/*`, multiple manifests | `monorepo` |
| A single script under 500 lines, no packaging | `script` |

When two apply, choose the one that matches how a reader will consume it: a library that ships a CLI is a `library` if most readers import it.

## Section matrix

`●` required · `○` only if it carries real information · `—` omit

| Section | cli | library | web-app | monorepo | script |
|---|---|---|---|---|---|
| Title + one-line positioning | ● | ● | ● | ● | ● |
| Status note (experimental / deprecated / replaces X) | ○ | ○ | ○ | ○ | ○ |
| Quick start | ● | ● | ● | ● | ● |
| Installation | ● | ● | ● | ○ | — |
| Usage / examples | ● | ● | ● | ● | ● |
| API surface or command reference | ○ | ● | — | — | — |
| Configuration table | ○ | ○ | ● | ○ | ○ |
| Architecture / how it works | ○ | ○ | ○ | ● | — |
| Package map | — | — | — | ● | — |
| Deployment | — | — | ● | ○ | — |
| Troubleshooting | ○ | ○ | ○ | ○ | — |
| Contributing | ○ | ○ | ○ | ○ | — |
| License | ○ | ○ | ○ | ○ | ○ |

"Optional" means: include it only when the content is specific and non-obvious. `## Configuration` followed by "Configure as needed" is worse than no section.

## Length budgets

Measured in rendered lines, excluding code blocks longer than 10 lines.

| Archetype | Target | Hard ceiling |
|---|---|---|
| script | 20–40 | 60 |
| cli | 60–120 | 160 |
| library | 80–150 | 220 |
| web-app | 100–180 | 250 |
| monorepo | 60–120 (plus links) | 200 |

Over budget means sections are competing. Cut the weakest one rather than shortening every section by a line.

## Skeletons

### cli

```
# name

One sentence: what it does, for whom.

## Install
## Quick start        (shortest path to a first successful command)
## Commands           (table or one subsection per command, with output)
## Configuration      (flags + env vars in one table)
## License
```

CLI notes: show real output, not just the invocation. Document exit codes only when they matter to scripts. Put flags in a table with `Default` and `Description` columns; long-form flag prose belongs in `--help`, which the README should not duplicate.

### library

```
# name

One sentence: what problem it solves.

## Install
## Quick start        (10–20 lines, imports included)
## API                (the 3–6 things people actually call)
## Configuration      (options with defaults)
## Compatibility      (runtime versions, only if constrained)
## License
```

Library notes: the install line must match the registry name, which sometimes differs from the repo name. Show the import, not only the call. Skip a full API dump — link to generated docs if they exist.

### web-app

```
# name

One sentence: what it does and where it runs.

## Quick start        (clone → env → run, in numbered steps)
## Environment        (table: variable, required, default, purpose)
## Deploy             (only the targets actually supported)
## Project layout     (only if the tree is non-obvious)
## License
```

Web-app notes: the environment table is the highest-value section; a missing variable is the most common reason a new contributor fails. State the port. If the app needs a database, include the exact setup command.

### monorepo

```
# name

One sentence: what the repo contains as a whole.

## Quick start        (install + build the whole workspace)
## Packages           (table: package, path, purpose, published?)
## Common tasks       (table: task, command)
## License
```

Monorepo notes: the package table replaces per-package prose. Per-package READMEs carry their own detail; link them.

### script

```
# name

One sentence: what it does, one input, one output.

## Usage              (invocation + a real example with output)
```

Script notes: no installation section, no contributing section, no badges.

## Positioning line

The sentence under the title decides whether a reader continues. It answers: what is this, who is it for.

| Weak | Why | Better |
|---|---|---|
| A powerful, modern tool for working with data | adjectives, no object | Converts CSV exports into SQLite databases with one command. |
| Welcome to foo! | greeting, no information | `foo` runs your test suite against every Node version in `.nvmrc`. |
| foo is a library. | tautology | Parses and validates ISO 8601 durations in TypeScript, with no dependencies. |
| Next-generation AI-powered platform | marketing, unfalsifiable | Serves a local web UI for browsing Parquet files without loading them into memory. |

Rules: one sentence, no comma-spliced feature lists, no "that helps you", no target-market language.

## Badges

At most three, and only when they report something true: CI status on the primary branch, registry version, license. Badges point at real endpoints; a badge for a workflow that does not exist is an invented fact.

Skip entirely for internal or private repos — they add visual noise without information.

## Trimming test

For each section, ask: *does removing it change what a reader does next?*

- If no → delete.
- If the section restates the code ("the `parse()` function parses") → delete.
- If it exists only because a template had it (Roadmap, Acknowledgements, Star History) → delete unless it holds real content.
- If it duplicates `CONTRIBUTING.md` or `docs/` → replace with one link.

Typical casualties in AI-generated READMEs: Table of Contents on a 60-line file, "Features" lists that repeat the positioning line, "Contributing" paragraphs with no steps, empty "Roadmap", placeholder screenshots.
