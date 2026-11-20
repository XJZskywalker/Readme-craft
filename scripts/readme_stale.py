#!/usr/bin/env python3
"""Warn when a project's contract changed but its README did not.

The linter reads one file and judges it. This reads the *other* half of the
failure: the commit changes a command or a variable while the README still
describes last month's project.

Two modes:
    --staged        the index against HEAD, for pre-commit
    --range A..B    two revisions, for pre-push

Findings are warnings. Exit 0 unless --strict, which makes them exit 1.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

CONTRACT_FILES = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "Cargo.toml", "go.mod", "composer.json", "Gemfile", "pom.xml", "build.gradle",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml", "Makefile", "Taskfile.yml", "justfile",
    ".env.example", ".env.sample", ".env.template", ".env.dist",
}
CONTRACT_PREFIXES = (".github/workflows/",)
README_NAMES = {"README.md", "README.en.md", "README.rst", "README"}
ENV_FILES = {".env.example", ".env.sample", ".env.template", ".env.dist"}


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git failed")
    return proc.stdout


def changed_paths(root: Path, staged: bool, rev_range: str | None) -> list[str]:
    try:
        if staged:
            out = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")
        elif rev_range:
            out = git(root, "diff", "--name-only", "--diff-filter=ACMR", rev_range)
        else:
            return []
    except RuntimeError:
        # A range whose base is gone locally (force push, rewritten remote)
        # cannot be diffed. Skip the warning instead of crashing a hook.
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def is_contract(path: str) -> bool:
    if path.startswith(CONTRACT_PREFIXES):
        return True
    return Path(path).name in CONTRACT_FILES


def read_at(root: Path, name: str, at: str | None) -> str | None:
    """Read from the working tree (None), the index ("index") or a revision.

    A pre-push hook must judge the commit that is about to be published,
    not whatever happens to be in the working tree at that moment.
    """
    if at is None:
        path = root / name
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
    spec = f":{name}" if at == "index" else f"{at}:{name}"
    try:
        return git(root, "show", spec)
    except RuntimeError:
        return None


def env_keys(root: Path, at: str | None) -> list[str]:
    keys = []
    for name in sorted(ENV_FILES):
        content = read_at(root, name, at)
        if content is None:
            continue
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key = line.partition("=")[0].strip().removeprefix("export ").strip()
            if key:
                keys.append(key)
    return keys


def mentioned(key: str, text: str) -> bool:
    # Whole token. "PORT" is not documented by SUPPORT or PORTAL, and a
    # substring match would silently hide a variable that was never written
    # down.
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(key) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, text) is not None


def undocumented_env(root: Path, at: str | None) -> list[str]:
    parts = [read_at(root, name, at) for name in ("README.md", "README.en.md")]
    text = "\n".join(part for part in parts if part)
    if not text:
        return []
    return [key for key in env_keys(root, at) if not mentioned(key, text)]


def evaluate(root: Path, staged: bool, rev_range: str | None,
             at: str | None = None) -> dict:
    paths = changed_paths(root, staged, rev_range)
    contract = [p for p in paths if is_contract(p)]
    readme_touched = any(Path(p).name in README_NAMES for p in paths)
    env_changed = any(Path(p).name in ENV_FILES for p in contract)
    missing_env = undocumented_env(root, at) if env_changed else []
    stale_contract = bool(contract) and not readme_touched
    return {
        "changed": paths,
        "contract": contract,
        "readme_touched": readme_touched,
        "missing_env": missing_env,
        "warned": stale_contract or bool(missing_env),
    }


def render(result: dict) -> str:
    out = []
    if result["contract"] and not result["readme_touched"]:
        out.append("readme-stale: contract files changed, README untouched")
        for path in result["contract"]:
            out.append(f"  {path}")
        out.append("These files define the commands and variables the README promises.")
        out.append("If the change left them alone, ignore this. If not, apply readme-craft:")
        out.append("  python scripts/project_scan.py . --out facts.md")
    if result["missing_env"]:
        out.append("readme-stale: variables in the env example that no README names:")
        for key in result["missing_env"]:
            out.append(f"  {key}")
        out.append("Document them in the config table, or ignore if deliberately internal.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Warn when the contract changed but the README did not.")
    parser.add_argument("--repo", default=".", help="repository root")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true", help="compare the index against HEAD")
    group.add_argument("--range", dest="rev_range", help="revision range, e.g. origin/main..HEAD")
    parser.add_argument("--strict", action="store_true", help="exit 1 on findings instead of warning only")
    parser.add_argument("--self-test", action="store_true", help="verify against a synthetic repository")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.repo).resolve()
    # pre-push reads the blob about to be published; pre-commit reads the
    # index; a manual run reads the working tree.
    if args.rev_range:
        at: str | None = args.rev_range.rsplit("..", 1)[-1]
    elif args.staged:
        at = "index"
    else:
        at = None
    result = evaluate(root, args.staged, args.rev_range, at=at)
    text = render(result)
    if text:
        print(text)
    return 1 if (args.strict and result["warned"]) else 0


def self_test() -> int:
    import os
    import shutil
    import tempfile

    root = Path(tempfile.mkdtemp(prefix="readme-stale-"))
    failures = 0

    def stage(name: str, content: str):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", name], cwd=root, check=True, capture_output=True)

    def case(label: str, expect_warn: bool) -> None:
        nonlocal failures
        result = evaluate(root, True, None, at="index")
        ok = result["warned"] == expect_warn
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'}  {label}  (contract={result['contract']}, readme_touched={result['readme_touched']})")

    def commit(label: str) -> None:
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
             "commit", "-q", "-m", label],
            cwd=root, check=True, capture_output=True,
        )

    try:
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
        subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True, env=env)
        stage("README.md", "# demo\n\n## Install\n\n```bash\nnpm install demo\n```\n\n## Usage\n\n`demo run`\n")
        stage("src.js", "console.log(1)\n")
        case("code change only -> silent", False)
        commit("base")

        stage("package.json", '{"name":"demo","scripts":{"start":"node src.js"}}\n')
        case("package.json changed, README untouched -> warn", True)
        commit("manifest")

        stage("README.md", "# demo\n\n## Install\n\n```bash\nnpm install demo\n```\n\n## Usage\n\n`npm start`\n")
        case("package.json and README both changed -> silent", False)
        commit("readme")

        stage(".env.example", "PORT=3000\nSECRET_TOKEN=abc\n")
        stage("package.json", '{"name":"demo","scripts":{"start":"node src.js","dev":"node src.js"}}\n')
        result = evaluate(root, True, None, at="index")
        found = set(result["missing_env"]) == {"PORT", "SECRET_TOKEN"}
        failures += 0 if found else 1
        print(f"{'ok  ' if found else 'FAIL'}  undocumented env keys listed -> {result['missing_env']}")

        stage("README.md", "# demo\n\nSUPPORT and PORTAL are ordinary words here.\n")
        result = evaluate(root, True, None, at="index")
        found = "PORT" in result["missing_env"]
        failures += 0 if found else 1
        print(f"{'ok  ' if found else 'FAIL'}  substring does not count as documentation -> {result['missing_env']}")

        stage("README.md", "# demo\n\n## Config\n\n| PORT | 3000 |\n")
        result = evaluate(root, True, None, at="index")
        found = "PORT" not in result["missing_env"]
        failures += 0 if found else 1
        print(f"{'ok  ' if found else 'FAIL'}  exact token is accepted as documentation -> {result['missing_env']}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("self-test", "PASS" if failures == 0 else f"FAIL ({failures})")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
