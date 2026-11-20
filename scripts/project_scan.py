#!/usr/bin/env python3
"""Collect the facts a README is allowed to state.

Scans a repository for manifests, commands, entry points, environment
variables, license, and layout, then prints a Markdown fact sheet.
Anything it cannot determine is reported as unknown rather than guessed.

Usage:
    python project_scan.py [repo] [--out facts.md] [--depth 2]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "target",
    "out", ".next", ".nuxt", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".idea", ".vscode", "coverage", ".turbo", ".cache",
    ".gradle", ".tox", ".dart_tool", "Pods", "bin", "obj",
}

ENV_GLOBS = (".env.example", ".env.sample", ".env.template", "env.example", ".env.dist")

LICENSE_MARKERS = [
    ("MIT", ["permission is hereby granted, free of charge"]),
    ("Apache-2.0", ["apache license", "version 2.0"]),
    ("AGPL-3.0", ["gnu affero general public license"]),
    ("GPL-3.0", ["gnu general public license", "version 3"]),
    ("GPL-2.0", ["gnu general public license", "version 2"]),
    ("BSD-3-Clause", ["redistribution and use in source and binary forms", "neither the name"]),
    ("BSD-2-Clause", ["redistribution and use in source and binary forms"]),
    ("MPL-2.0", ["mozilla public license"]),
    ("ISC", ["isc license"]),
    ("Unlicense", ["this is free and unencumbered software"]),
]


def read(path: Path, limit: int = 400_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def find_manifests(root: Path) -> dict:
    names = {
        "node": ["package.json"],
        "python": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
        "php": ["composer.json"],
        "ruby": ["Gemfile", "Rakefile"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    }
    found = {}
    for eco, files in names.items():
        hits = [root / f for f in files if (root / f).is_file()]
        if hits:
            found[eco] = hits
    return found


def parse_node(root: Path) -> dict:
    path = root / "package.json"
    data = json.loads(read(path) or "{}")
    scripts = data.get("scripts") or {}
    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "description": data.get("description"),
        "license_field": data.get("license"),
        "scripts": scripts,
        "bin": data.get("bin"),
        "main": data.get("main") or data.get("module") or data.get("exports"),
        "engines": data.get("engines"),
        "workspaces": data.get("workspaces"),
        "deps": sorted(list((data.get("dependencies") or {}).keys()))[:20],
        "dev_deps": sorted(list((data.get("devDependencies") or {}).keys()))[:20],
        "source": "package.json",
    }


def parse_python(root: Path) -> dict:
    info: dict = {"source": None, "scripts": {}, "name": None}
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        info["source"] = "pyproject.toml"
        text = read(pyproject)
        try:
            import tomllib  # Python 3.11+

            data = tomllib.loads(text)
            project = data.get("project", {})
            info["name"] = project.get("name")
            info["version"] = project.get("version")
            info["description"] = project.get("description")
            info["engines"] = {"python": project.get("requires-python")}
            info["scripts"] = {
                k: v for k, v in (project.get("scripts") or {}).items()
            }
            info["deps"] = list(project.get("dependencies") or [])[:20]
        except Exception:
            for key in ("name", "version", "description", "requires-python"):
                m = re.search(rf'^\s*{re.escape(key)}\s*=\s*"([^"]+)"', text, re.M)
                if m:
                    field = "engines" if key == "requires-python" else key
                    if field == "engines":
                        info["engines"] = {"python": m.group(1)}
                    else:
                        info[field] = m.group(1)
            for m in re.finditer(r'^([\w.-]+)\s*=\s*"([\w.\[\]-]+:[\w_.-]+)"', text, re.M):
                info["scripts"][m.group(1)] = m.group(2)
    setup_py = root / "setup.py"
    if setup_py.is_file():
        text = read(setup_py)
        m = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", text)
        if m:
            info.setdefault("name", m.group(1))
        if not info["source"]:
            info["source"] = "setup.py"
    return info


def parse_go(root: Path) -> dict:
    text = read(root / "go.mod")
    info = {"source": "go.mod"}
    m = re.search(r"^module\s+(\S+)", text, re.M)
    if m:
        info["name"] = m.group(1).rstrip("/").split("/")[-1]
        info["module_path"] = m.group(1)
    m = re.search(r"^go\s+(\S+)", text, re.M)
    if m:
        info["engines"] = {"go": m.group(1)}
    return info


def parse_rust(root: Path) -> dict:
    text = read(root / "Cargo.toml")
    info = {"source": "Cargo.toml"}
    for key in ("name", "version", "description", "edition"):
        m = re.search(rf'^{key}\s*=\s*"([^"]+)"', text, re.M)
        if m:
            info[key if key != "edition" else "engines"] = m.group(1)
    bins = re.findall(r"\[\[bin\]\]\s*\nname\s*=\s*\"([^\"]+)\"", text)
    if bins:
        info["bin"] = bins
    return info


def parse_composer(root: Path) -> dict:
    try:
        data = json.loads(read(root / "composer.json") or "{}")
    except json.JSONDecodeError:
        return {"source": "composer.json"}
    return {
        "source": "composer.json",
        "name": data.get("name"),
        "description": data.get("description"),
        "license_field": data.get("license"),
        "scripts": data.get("scripts") or {},
        "engines": data.get("require", {}).get("php") and {"php": data["require"]["php"]},
    }


def parse_makefile(root: Path) -> dict:
    targets = []
    for name in ("Makefile", "makefile", "GNUmakefile"):
        path = root / name
        if path.is_file():
            text = read(path)
            targets = [
                t for t in re.findall(r"^([A-Za-z0-9_.-]+):(?!=)", text, re.M)
                if not t.startswith(".")
            ][:25]
            return {"source": name, "targets": targets}
    return {}


def parse_docker(root: Path) -> dict:
    out: dict = {}
    for name in ("Dockerfile", "dockerfile"):
        path = root / name
        if path.is_file():
            text = read(path)
            ports = re.findall(r"^EXPOSE\s+(.+)$", text, re.M)
            cmd = re.findall(r"^(?:CMD|ENTRYPOINT)\s+(.+)$", text, re.M)
            out["dockerfile"] = {
                "ports": [p.strip() for p in ports],
                "cmd": [c.strip() for c in cmd[-2:]],
            }
            break
    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        path = root / name
        if path.is_file():
            text = read(path)
            services = re.findall(r"^  ([A-Za-z0-9_.-]+):\s*$", text, re.M)
            ports = re.findall(r"^\s*-\s*[\"']?(\d+:\d+)", text, re.M)
            out["compose"] = {"file": name, "services": services[:10], "ports": ports[:10]}
            break
    return out


def parse_env(root: Path) -> list:
    for name in ENV_GLOBS:
        path = root / name
        if path.is_file():
            keys = []
            for line in read(path).splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                keys.append({
                    "key": key.strip().removeprefix("export ").strip(),
                    "example": value.strip().strip("'\""),
                    "source": name,
                })
            return keys
    return []


def parse_env_usage(root: Path) -> list:
    patterns = {
        ".js,.ts,.jsx,.tsx,.mjs,.cjs": r"process\.env\.([A-Z0-9_]+)",
        ".py": r"os\.(?:environ(?:\.get)?|getenv)\(?\[?[\"']([A-Z0-9_]+)",
        ".go": r"os\.Getenv\(\"([A-Z0-9_]+)\"",
        ".rs": r"env::var\(\"([A-Z0-9_]+)\"",
        ".php": r"(?:env|getenv)\(\s*['\"]([A-Z0-9_]+)",
    }
    found = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1]
            for exts, pattern in patterns.items():
                if ext in exts.split(","):
                    text = read(Path(dirpath) / fname, limit=200_000)
                    for name in re.findall(pattern, text):
                        if 2 < len(name) < 60:
                            found.add(name)
    return sorted(found)


def parse_workflows(root: Path) -> list:
    wf_dir = root / ".github" / "workflows"
    if not wf_dir.is_dir():
        return []
    out = []
    for path in sorted(wf_dir.glob("*.y*ml")):
        text = read(path)
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        runs = re.findall(r"^\s*run:\s*\|?\s*(.+)$", text, re.M)
        runs += re.findall(r"^\s*-\s*run:\s*(.+)$", text, re.M)
        runs = [r.strip() for r in runs if r.strip()][:8]
        nodes = re.findall(r"node-version:\s*\[?([\d.,\s\"]+)\]?", text)
        pythons = re.findall(r"python-version:\s*\[?([\d.,\s\"]+)\]?", text)
        out.append({
            "file": rel(root, path),
            "name": name.group(1).strip() if name else path.stem,
            "runs": runs,
            "node_versions": [n.strip(' "\'') for n in nodes],
            "python_versions": [p.strip(' "\'') for p in pythons],
        })
    return out


def parse_license(root: Path) -> dict:
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE"):
        path = root / name
        if path.is_file():
            head = read(path, 4000).lower()
            for label, markers in LICENSE_MARKERS:
                if all(m in head for m in markers):
                    return {"file": name, "spdx": label}
            return {"file": name, "spdx": "unknown (unrecognized text)"}
    return {}


def tree(root: Path, depth: int = 2) -> list:
    lines = []

    def walk(path: Path, prefix: str, level: int):
        if level > depth:
            return
        try:
            entries = sorted(
                (e for e in path.iterdir() if e.name not in IGNORE_DIRS and not e.name.startswith(".git")),
                key=lambda e: (e.is_file(), e.name.lower()),
            )
        except OSError:
            return
        for entry in entries[:20]:
            marker = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{entry.name}{marker}")
            if entry.is_dir():
                walk(entry, prefix + "  ", level + 1)

    walk(root, "", 1)
    return lines


WEB_FRAMEWORKS = {
    "next", "nuxt", "@angular/core", "svelte", "@sveltejs/kit", "vue", "react", "react-dom",
    "gatsby", "@remix-run/react", "astro", "express", "fastify", "koa", "hono",
    "@nestjs/core", "solid-js", "vite",
}


def guess_archetype(root: Path, manifests: dict, node: dict, py: dict) -> tuple:
    reasons = []
    if (root / "package.json").is_file():
        pkg = json.loads(read(root / "package.json") or "{}")
        if pkg.get("workspaces") or list(root.glob("packages/*/package.json")):
            reasons.append("workspaces / packages/")
            return "monorepo", reasons
    deps = set(node.get("deps") or []) | set(node.get("dev_deps") or [])
    frameworks = sorted(deps & WEB_FRAMEWORKS)
    if frameworks:
        reasons.append(f"framework dependency: {', '.join(frameworks[:3])}")
        return "web-app", reasons
    for marker in ("next.config.js", "next.config.mjs", "nuxt.config.ts", "manage.py", "index.html"):
        if (root / marker).is_file():
            reasons.append(marker)
            return "web-app", reasons
    if (root / "compose.yml").is_file() or (root / "compose.yaml").is_file():
        reasons.append("compose file")
        return "web-app", reasons
    if (root / "bin").is_dir() or node.get("bin") or py.get("scripts"):
        reasons.append("bin field or console entry point")
        return "cli", reasons
    if node.get("main") or (root / "src" / "index.ts").is_file() or (root / "src" / "lib.rs").is_file():
        reasons.append("library entry point")
        return "library", reasons
    py_src = root / "src"
    if py_src.is_dir() and any(py_src.glob("*/__init__.py")):
        reasons.append("src layout package")
        return "library", reasons
    if (root / "Dockerfile").is_file() or (root / "docker-compose.yml").is_file():
        reasons.append("Dockerfile / compose present")
        return "web-app", reasons
    py_files = list(root.glob("*.py"))
    if len(py_files) <= 2 and not manifests.get("python"):
        reasons.append("loose scripts only")
        return "script", reasons
    return "unknown", reasons


def build(root: Path, depth: int) -> str:
    manifests = find_manifests(root)
    node = parse_node(root) if (root / "package.json").is_file() else {}
    py = parse_python(root) if "python" in manifests else {}
    go = parse_go(root) if (root / "go.mod").is_file() else {}
    rust = parse_rust(root) if (root / "Cargo.toml").is_file() else {}
    php = parse_composer(root) if (root / "composer.json").is_file() else {}
    make = parse_makefile(root)
    docker = parse_docker(root)
    env_example = parse_env(root)
    env_used = parse_env_usage(root)
    workflows = parse_workflows(root)
    license_info = parse_license(root)
    archetype, reasons = guess_archetype(root, manifests, node, py)

    out = []
    add = out.append
    add("# Facts")
    add("")
    add(f"Repository: `{root.name}`  ")
    add(f"Path: `{root}`")
    add("")

    add("## Identity")
    add("")
    name = node.get("name") or py.get("name") or go.get("name") or rust.get("name") or php.get("name")
    add(f"name: {name or 'unknown'}")
    version = node.get("version") or py.get("version") or rust.get("version")
    add(f"version: {version or 'unknown'}")
    desc = node.get("description") or py.get("description") or rust.get("description") or php.get("description")
    add(f"manifest description: {desc or 'none'}")
    if license_info:
        add(f"license: {license_info['spdx']}  ({license_info['file']})")
    else:
        declared = node.get("license_field") or php.get("license_field")
        if declared:
            add(f"license: NO LICENSE FILE, manifest declares {declared} -> report, do not copy")
        else:
            add("license: none (no LICENSE file)")
    add(f"archetype guess: {archetype}" + (f"  ({'; '.join(reasons)})" if reasons else ""))
    if node.get("engines") or py.get("engines") or go.get("engines"):
        engines = node.get("engines") or py.get("engines") or go.get("engines")
        if isinstance(engines, dict):
            engines = ", ".join(f"{k} {v}" for k, v in engines.items())
        add(f"runtime: {engines}")
    add("")

    add("## Commands")
    add("")
    commands = []
    for key in ("dev", "start", "build", "test", "lint", "format"):
        if node.get("scripts", {}).get(key):
            commands.append((key, node["scripts"][key], "package.json scripts"))
    if make.get("targets"):
        for t in make["targets"][:10]:
            commands.append((f"make {t}", f"make {t}", make["source"]))
    for wf in workflows:
        for run in wf["runs"][:3]:
            commands.append((f"ci [{wf['name']}]", run, wf["file"]))
    if py.get("scripts"):
        for k, v in py["scripts"].items():
            commands.append((k, v, "pyproject [project.scripts]"))
    if docker.get("dockerfile", {}).get("cmd"):
        commands.append(("docker run", docker["dockerfile"]["cmd"][-1], "Dockerfile CMD"))
    if not commands:
        add("unknown — no scripts, Makefile targets, or CI commands found")
    for label, cmd, src in commands:
        add(f"- {label}: `{cmd}`  ({src})")
    add("")

    if docker:
        add("## Runtime")
        add("")
        if "dockerfile" in docker:
            if docker["dockerfile"]["ports"]:
                add(f"exposed ports: {', '.join(docker['dockerfile']['ports'])}")
            for c in docker["dockerfile"]["cmd"]:
                add(f"container command: `{c}`")
        if "compose" in docker:
            add(f"compose services: {', '.join(docker['compose']['services']) or 'unknown'}")
            if docker["compose"]["ports"]:
                add(f"compose ports: {', '.join(docker['compose']['ports'])}")
        add("")

    add("## Entry points")
    add("")
    entries = []
    if node.get("bin"):
        entries.append(f"bin: {node['bin']}")
    if node.get("main"):
        entries.append(f"main: {node['main']}")
    if rust.get("bin"):
        entries.append(f"bin: {rust['bin']}")
    for candidate in ("src/index.ts", "src/index.js", "index.js", "src/main.rs", "main.go",
                      "src/__main__.py", "__main__.py", "src/main.py"):
        if (root / candidate).is_file():
            entries.append(candidate)
    cmd_dir = root / "cmd"
    if cmd_dir.is_dir():
        entries.extend(f"cmd/{p.name}/" for p in cmd_dir.iterdir() if p.is_dir())
    add("\n".join(f"- {e}" for e in entries) if entries else "unknown")
    add("")

    add("## Environment")
    add("")
    if env_example:
        add("From example file (verify each key is read in code):")
        add("")
        for item in env_example:
            used = "used" if item["key"] in env_used else "NOT READ IN CODE — do not document"
            add(f"- `{item['key']}` example=`{item['example']}` ({item['source']}, {used})")
    elif env_used:
        add("No example file. Keys read in code:")
        add("")
        for key in env_used[:20]:
            add(f"- `{key}` (default unknown — check the call site)")
    else:
        add("none found")
    add("")

    if workflows:
        add("## CI")
        add("")
        for wf in workflows:
            versions = wf["node_versions"] or wf["python_versions"]
            add(f"- {wf['name']} ({wf['file']})" + (f" versions={versions}" if versions else ""))
        add("")

    add("## Layout")
    add("")
    add("```text")
    lines = tree(root, depth)
    out.extend(lines[:60])
    add("```")
    add("")

    add("## Existing docs")
    add("")
    docs = []
    for candidate in ("README.md", "README.rst", "CONTRIBUTING.md", "CHANGELOG.md", "docs"):
        path = root / candidate
        if path.is_file():
            count = len(read(path).splitlines())
            docs.append(f"- {candidate} ({count} lines)")
        elif path.is_dir():
            docs.append(f"- {candidate}/ ({len(list(path.glob('*')))} entries)")
    add("\n".join(docs) if docs else "none")
    add("")

    add("## Unknowns")
    add("")
    unknowns = []
    if not license_info:
        unknowns.append("license text")
    if not (node.get("engines") or py.get("engines") or go.get("engines")):
        unknowns.append("minimum runtime version")
    if not env_example and env_used:
        unknowns.append("environment variable defaults")
    if archetype == "unknown":
        unknowns.append("project archetype")
    if not workflows:
        unknowns.append("whether CI exists at all")
    add("\n".join(f"- {u}" for u in unknowns) if unknowns else "- none")
    add("")
    add("> Anything not listed above is unknown. Leave a TODO in the README rather than guessing.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a README fact sheet for a repository.")
    parser.add_argument("repo", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--out", help="write to file instead of stdout")
    parser.add_argument("--depth", type=int, default=2, help="directory tree depth (default: 2)")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    text = build(root, args.depth)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(text.splitlines())} lines)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
