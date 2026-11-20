# dirsnap

Hashes every file under a directory so you can tell whether the tree changed since a snapshot was taken.

## Install

```bash
npm install -g dirsnap
```

Needs Node 18 or newer.

## Quick start

```bash
cd ~/projects/site
dirsnap take     # records the current tree in .dirsnap/meta.json
dirsnap check    # exit 0 if nothing changed, exit 1 otherwise
```

`check` names the first path that differs:

```text
changed: src/index.html
```

## Commands

| Command | Does |
|---|---|
| `dirsnap take` | Writes a snapshot of the current tree |
| `dirsnap check` | Compares the tree against the last snapshot; exits 1 on any difference |
| `dirsnap diff` | Lists every changed, added, and removed path |

Each command accepts `--root <path>` to work outside the current directory and `--ignore <glob>` (repeatable) to skip paths. Ignore rules are stored in the snapshot, so `check` compares against the rules that were active at capture time.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DIRSNAP_DIR` | `.dirsnap` | Where snapshots are written |
| `DIRSNAP_IGNORE` | empty | Extra globs, comma separated; merges with `--ignore` |
| `NO_COLOR` | unset | Disables ANSI output in `diff` |

## When to use this instead of git

`git status` answers the same question for tracked files. dirsnap exists for trees that are not repositories: build outputs, generated assets, vendored dependencies, and directories on a machine where git is not installed.

The snapshot is a plain JSON map of relative path to SHA-256, plus the resolved ignore rules. It contains no file contents, so it stays small for large trees, and it cannot restore anything. For restoring, use git or a real backup tool.

Snapshots are not portable across machines when absolute paths appear in the ignore rules; `--root` is recorded for that reason.

## Limits

- Skips symlinks rather than following them, to avoid cycles.
- Hashes files sequentially. A 40k-file tree takes about 12 seconds on an SSD.
- Does not watch for changes; run `check` from a hook or a timer.

## Contributing

Open an issue before sending a pull request for anything beyond a bug fix. Run `npm test` before pushing.

## License

MIT. See [LICENSE](LICENSE).
