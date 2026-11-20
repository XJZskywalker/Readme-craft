#!/usr/bin/env python3
"""Deterministic README checks.

Catches the failure modes that make a README read as generated: invented
placeholder text, marketing language, decorative emoji, bullet-only
structure, broken formatting, and claims the repository cannot back up.

Usage:
    python readme_lint.py README.md [--type library] [--repo .] [--json]
    python readme_lint.py --stdin [--repo .]     # lint staged or committed content

Checks come in three tiers. Correctness errors and six always-on warnings
decide the exit code. Taste rules (sentence length, bullet density, emoji
count, CJK spacing) are opt-in with --style; the git gate never blocks on
them.

Exit codes: 0 pass, 1 fail, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HYPE = [
    "seamless", "seamlessly", "robust", "powerful", "cutting-edge", "cutting edge",
    "state-of-the-art", "state of the art", "blazing", "lightning-fast", "lightning fast",
    "world-class", "world class", "next-generation", "next generation", "revolutionary",
    "game-changing", "game changing", "effortless", "effortlessly", "enterprise-grade",
    "best-in-class", "best in class", "battle-tested", "production-grade",
    "meticulously", "beautifully crafted", "delightful", "supercharge", "empower",
    "unlock the", "elevate your", "turbocharge", "10x faster",
]

CJK_HYPE = [
    "强大", "优雅", "一站式", "开箱即用", "极致", "赋能", "深度集成", "全新升级",
    "业界领先", "完美支持", "轻松搞定", "颠覆", "震撼", "丝滑", "无缝",
]

FILLER = [
    "it is worth noting", "it's worth noting", "it should be noted", "please note that",
    "in today's", "have you ever", "let's dive", "delve into", "in order to",
    "a wide range of", "simply put", "needless to say", "at the end of the day",
    "this document will", "this article will", "we will explore", "as we all know",
    "下面就让我们", "本文将", "众所周知", "总而言之",
]

PLACEHOLDER = [
    r"\bTBD\b", r"\bTODO\b", r"lorem ipsum", r"your-project-name", r"<your[- ]",
    r"\byour-name\b", r"coming soon", r"placeholder\.(png|jpg|jpeg|gif|svg)",
    r"example\.com/your", r"\bXXX\b", r"\bFIXME\b",
]

OPENERS = ["welcome to", "introducing ", "say hello to"]

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\u2B00-\u2BFF]"
)

BUDGET = {
    "script": 60, "cli": 160, "library": 220, "web-app": 250, "monorepo": 200, "generic": 200,
}

SECTION_INSTALL = re.compile(
    r"(quick\s*start|getting\s*started|install|installation|setup|build|run\b"
    r"|安装|快速开始|开始|入门|搭建|运行|构建)", re.I
)
SECTION_USAGE = re.compile(
    r"(usage|example|commands?|api|deploy|configuration|config"
    r"|使用|用法|示例|例子|命令|配置|部署|接口)", re.I
)
FEATURE_HEADS = re.compile(r"^(features?|highlights?|why\b|key features|功能|特性|亮点)", re.I)
TOC_HEADS = re.compile(r"(table of contents|contents|目录)", re.I)

MAX_SENTENCE_WORDS = 30


class Finding:
    __slots__ = ("line", "severity", "rule", "message")

    def __init__(self, line: int, severity: str, rule: str, message: str):
        self.line = line
        self.severity = severity
        self.rule = rule
        self.message = message

    def as_dict(self) -> dict:
        return {"line": self.line, "severity": self.severity, "rule": self.rule, "message": self.message}


def parse(text: str) -> dict:
    lines = text.splitlines()
    fences: list[dict] = []
    in_fence = False
    fence_start = 0
    fence_lang = ""
    prose: list[tuple[int, str]] = []
    code_lines: list[tuple[int, str]] = []
    headings: list[dict] = []

    for idx, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if not in_fence:
                in_fence = True
                fence_start = idx
                fence_lang = stripped.lstrip("`~").strip()
            else:
                in_fence = False
                fences.append({"start": fence_start, "end": idx, "lang": fence_lang})
            continue
        if in_fence:
            code_lines.append((idx, raw))
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            headings.append({"line": idx, "level": len(m.group(1)), "text": m.group(2).strip()})
            prose.append((idx, m.group(2)))
            continue
        prose.append((idx, raw))

    return {
        "lines": lines,
        "headings": headings,
        "prose": prose,
        "code": code_lines,
        "fences": fences,
    }


def strip_inline_code(line: str) -> str:
    """Remove inline code spans so quoted constants do not trip word checks."""
    return re.sub(r"`[^`]*`", "", line)


def check_placeholder(parsed: dict) -> list[Finding]:
    out = []
    for idx, line in parsed["prose"]:
        scan = strip_inline_code(line)
        for pattern in PLACEHOLDER:
            m = re.search(pattern, scan, re.I)
            if m:
                what = m.group(0).strip()
                if what.upper().startswith("TODO"):
                    out.append(Finding(idx, "warn", "todo", f"unresolved `{what}` — resolve it or remove the marker before publishing"))
                else:
                    out.append(Finding(idx, "error", "placeholder", f"placeholder text `{what}` — replace with a real value"))
                break
    return out


def check_hype(parsed: dict) -> list[Finding]:
    out = []
    lowered = [(idx, strip_inline_code(line).lower()) for idx, line in parsed["prose"]]
    for idx, line in parsed["prose"]:
        scan = strip_inline_code(line)
        low = scan.lower()
        for word in HYPE:
            if word in low:
                out.append(Finding(idx, "error", "hype", f"marketing word `{word}` — state the behaviour or the number instead"))
        for word in CJK_HYPE:
            if word in scan:
                out.append(Finding(idx, "error", "hype", f"营销词「{word}」— 改为可验证的事实或数字"))
        for phrase in FILLER:
            if phrase in low or phrase in scan:
                out.append(Finding(idx, "warn", "filler", f"filler phrase `{phrase}`"))
    for idx, line in lowered:
        for opener in OPENERS:
            if line.startswith(opener) or f"# {opener}" in line:
                out.append(Finding(idx, "error", "opener", "greeting opener — lead with what the project does"))
    return out


def check_structure(parsed: dict, total_lines: int) -> list[Finding]:
    out = []
    headings = parsed["headings"]
    h1 = [h for h in headings if h["level"] == 1]
    if not h1:
        out.append(Finding(1, "error", "no-h1", "missing a top-level title"))
    elif len(h1) > 1:
        for extra in h1[1:]:
            out.append(Finding(extra["line"], "error", "multi-h1", "more than one H1 — demote to H2"))

    for prev, nxt in zip(headings, headings[1:]):
        if nxt["level"] > prev["level"] + 1:
            out.append(Finding(nxt["line"], "warn", "heading-skip", f"heading level jumps from H{prev['level']} to H{nxt['level']}"))

    levels = [(h["line"], h["level"]) for h in headings]
    for i, (line, level) in enumerate(levels):
        next_line = levels[i + 1][0] if i + 1 < len(levels) else total_lines + 1
        if next_line - line <= 1:
            out.append(Finding(line, "error", "empty-section", "section heading with no content"))

    titles = [h["text"] for h in headings]
    if headings:
        has_install = any(SECTION_INSTALL.search(t) for t in titles)
        has_usage = any(SECTION_USAGE.search(t) for t in titles)
        if not has_install and not has_usage:
            out.append(Finding(1, "error", "no-start", "neither a quick-start/install section nor a usage section exists"))
        elif not has_install:
            out.append(Finding(1, "warn", "no-install", "no install or quick-start section"))

    for i, h in enumerate(headings):
        if TOC_HEADS.search(h["text"]) and total_lines < 100:
            out.append(Finding(h["line"], "warn", "toc", f"table of contents in a {total_lines}-line file adds nothing"))
        if FEATURE_HEADS.search(h["text"]):
            end = headings[i + 1]["line"] if i + 1 < len(headings) else total_lines + 1
            body = [(n, l) for n, l in parsed["prose"] if h["line"] < n < end and l.strip()]
            bullets = [b for b in body if re.match(r"^[-*+]\s", b[1].strip())]
            if body and len(bullets) == len(body) and len(bullets) >= 4:
                out.append(Finding(h["line"], "warn", "bare-features", "feature list with no explanation — each item needs a reason or a boundary"))
    return out


def check_formatting(parsed: dict) -> list[Finding]:
    out = []
    lines = parsed["lines"]

    for fence in parsed["fences"]:
        if not fence["lang"]:
            out.append(Finding(fence["start"], "warn", "fence-lang", "code fence without a language tag"))

    for h in parsed["headings"]:
        if EMOJI.search(h["text"]):
            out.append(Finding(h["line"], "error", "heading-emoji", "decorative emoji in a heading"))

    emoji_count = len(EMOJI.findall("\n".join(l for _, l in parsed["prose"])))
    if emoji_count > 3:
        out.append(Finding(1, "warn", "emoji", f"{emoji_count} emoji in prose — remove decorative ones"))

    run_start, run_len = 0, 0
    for idx, line in enumerate(lines, start=1):
        if re.match(r"^\s*[-*+]\s", line):
            if run_len == 0:
                run_start = idx
            run_len += 1
        else:
            if run_len > 5:
                out.append(Finding(run_start, "warn", "bullet-run", f"{run_len} consecutive bullets — groups above 5 need prose or a table"))
            run_len = 0
    if run_len > 5:
        out.append(Finding(run_start, "warn", "bullet-run", f"{run_len} consecutive bullets — groups above 5 need prose or a table"))

    bullets = sum(1 for _, l in parsed["prose"] if re.match(r"^\s*[-*+]\s", l) and l.strip())
    paragraphs = sum(1 for _, l in parsed["prose"] if l.strip() and not l.strip().startswith(("#", "-", "*", "+", "|", ">", "![")))
    if bullets + paragraphs >= 20 and bullets / max(bullets + paragraphs, 1) > 0.55:
        out.append(Finding(1, "warn", "bullet-ratio", f"{bullets} bullets vs {paragraphs} prose lines — the README reads as an outline"))

    badges = len(re.findall(r"!\[[^\]]*\]\([^)]*badge[^)]*\)|\[!\[", "\n".join(l for _, l in parsed["prose"]), re.I))
    if badges > 3:
        out.append(Finding(1, "warn", "badges", f"{badges} badges — keep at most 3 that report real state"))

    bangs = sum(l.count("!") for _, l in parsed["prose"] if not l.strip().startswith("!"))
    if bangs > 1:
        out.append(Finding(1, "warn", "exclamation", f"{bangs} exclamation marks"))

    bold = len(re.findall(r"\*\*[^*\n]+\*\*", "\n".join(l for _, l in parsed["prose"])))
    if bold > 10:
        out.append(Finding(1, "warn", "bold", f"{bold} bold spans — emphasis loses meaning past ~10"))

    dashes = sum(l.count("—") + l.count("——") for _, l in parsed["prose"])
    if dashes > 5:
        out.append(Finding(1, "warn", "emdash", f"{dashes} em dashes — restructure those sentences"))

    return out


def check_prose_limits(parsed: dict) -> list[Finding]:
    out = []
    offenders = []
    for idx, line in parsed["prose"]:
        text = re.sub(r"`[^`]*`", "", line)
        if not text.strip() or text.strip().startswith(("#", "-", "*", "|", ">", "!")):
            continue
        for sentence in re.split(r"(?<=[.!?。！？])\s*", text):
            sentence = sentence.strip()
            if not sentence:
                continue
            if re.search(r"[\u4e00-\u9fff]", sentence):
                length = len(re.findall(r"[\u4e00-\u9fff]", sentence))
                if length > 40:
                    offenders.append((idx, sentence[:40], length, "chars"))
            else:
                words = len(sentence.split())
                if words > MAX_SENTENCE_WORDS:
                    offenders.append((idx, sentence[:60], words, "words"))
    for idx, snippet, length, unit in offenders[:3]:
        out.append(Finding(idx, "warn", "long-sentence", f"{length} {unit}: \"{snippet}...\""))
    return out


def check_cjk_spacing(parsed: dict) -> list[Finding]:
    out = []
    for idx, line in parsed["prose"]:
        text = re.sub(r"`[^`]*`", "", line)
        if re.search(r"[\u4e00-\u9fff][A-Za-z0-9]|[A-Za-z0-9][\u4e00-\u9fff]", text):
            out.append(Finding(idx, "warn", "cjk-spacing", "missing space between Chinese and Latin text"))
            break
    return out


def check_license(parsed: dict, repo: Path | None) -> list[Finding]:
    if repo is None:
        return []
    has_file = any((repo / n).is_file() for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE"))
    if has_file:
        return []
    out = []
    titles = [h["text"].lower() for h in parsed["headings"]]
    claims_section = any("license" in t for t in titles)
    claims_text = any(re.search(r"licensed under|license:", l, re.I) for _, l in parsed["prose"])
    if claims_section or claims_text:
        out.append(Finding(1, "error", "license-claim", "README claims a license but no LICENSE file exists in the repository"))
    return out


def check_budget(total_lines: int, kind: str) -> list[Finding]:
    ceiling = BUDGET.get(kind, BUDGET["generic"])
    if total_lines > ceiling:
        return [Finding(1, "warn", "too-long", f"{total_lines} lines exceeds the {kind} budget of {ceiling} — cut a section, do not compress every one")]
    return []


def guess_type(text: str) -> str:
    low = text.lower()
    if "## packages" in low or "workspaces" in low:
        return "monorepo"
    if "## commands" in low or "--help" in low:
        return "cli"
    if "## api" in low or "```python" in low or "```ts" in low:
        return "library"
    if "## environment" in low or "**deploy" in low or "docker compose" in low:
        return "web-app"
    return "generic"


def run(path: Path, kind: str, repo: Path | None, style: bool = False,
        source: str | None = None) -> dict:
    # A hook passes the staged or committed blob through stdin. Linting that
    # rather than the working-tree copy is what makes the gate honest: what
    # is about to be published is what gets checked.
    if source is None:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        label = str(path)
    else:
        text = source
        label = "<stdin>"
    parsed = parse(text)
    total_lines = len(parsed["lines"])
    if kind == "auto":
        kind = guess_type(text)

    findings: list[Finding] = []
    findings += check_structure(parsed, total_lines)
    findings += check_placeholder(parsed)
    findings += check_hype(parsed)
    findings += check_formatting(parsed)
    findings += check_prose_limits(parsed)
    findings += check_cjk_spacing(parsed)
    findings += check_license(parsed, repo)
    findings += check_budget(total_lines, kind)

    disabled: set[str] = set()
    for match in re.finditer(r"<!--\s*readme-lint:\s*disable\s*([^>]*)-->", text, re.I):
        disabled.update(part for part in re.split(r"[,\s]+", match.group(1)) if part)
    if disabled:
        findings = [f for f in findings if f.rule not in disabled]
    if not style:
        findings = [f for f in findings if f.rule not in STYLE_RULES]

    findings.sort(key=lambda f: (f.line, f.severity))

    penalty = sum(12 if f.severity == "error" else 4 for f in findings)
    score = max(0, 100 - penalty)
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = len(findings) - errors
    # Only correctness errors decide the exit code. Warnings are advice; if
    # they blocked, the gate would punish a file a reader can still use.
    passed = errors == 0

    return {
        "file": label,
        "type": kind,
        "lines": total_lines,
        "budget": BUDGET.get(kind, BUDGET["generic"]),
        "score": score,
        "errors": errors,
        "warnings": warnings,
        "passed": passed,
        "style": style,
        "findings": [f.as_dict() for f in findings],
    }


def render(result: dict) -> str:
    out = [f"README lint: {result['file']}"]
    out.append(f"type: {result['type']} (budget {result['budget']})  lines: {result['lines']}")
    out.append("")
    if not result["findings"]:
        out.append("  no findings")
    for f in result["findings"]:
        out.append(f"  L{f['line']:<4} {f['severity']:<5} {f['rule']:<14} {f['message']}")
    out.append("")
    out.append(f"score: {result['score']}/100  ({result['errors']} errors, {result['warnings']} warnings)")
    out.append("result: " + ("PASS" if result["passed"] else "FAIL"))
    return "\n".join(out)


RULES = {
    # A reader cannot trust the file.
    "hype": ("error", "marketing language standing in for a fact"),
    "placeholder": ("error", "placeholder text that would ship as-is"),
    "opener": ("error", "greeting opener instead of stating what the project does"),
    "no-h1": ("error", "no top-level title"),
    "multi-h1": ("error", "more than one H1"),
    "empty-section": ("error", "section heading with no content"),
    "no-start": ("error", "no quick-start, install, or usage section"),
    "heading-emoji": ("error", "decorative emoji in a heading"),
    "license-claim": ("error", "claims a license while no LICENSE file exists"),
    # Always on: cheap to check, cheap to fix.
    "todo": ("warn", "unresolved TODO marker"),
    "heading-skip": ("warn", "heading level skipped"),
    "no-install": ("warn", "no install or quick-start section"),
    "bare-features": ("warn", "feature list with no explanation"),
    "fence-lang": ("warn", "code fence without a language tag"),
    "too-long": ("warn", "file exceeds the archetype budget"),
    # Taste, opt-in via --style.
    "filler": ("warn", "filler phrase that says nothing"),
    "toc": ("warn", "table of contents in a short file"),
    "emoji": ("warn", "emoji scattered through prose"),
    "bullet-run": ("warn", "long run of consecutive bullets"),
    "bullet-ratio": ("warn", "document reads as an outline"),
    "badges": ("warn", "more badges than report real state"),
    "exclamation": ("warn", "exclamation marks"),
    "bold": ("warn", "bold used too often to mean anything"),
    "emdash": ("warn", "em dashes carrying the content"),
    "long-sentence": ("warn", "sentence over the length limit"),
    "cjk-spacing": ("warn", "missing space between Chinese and Latin text"),
}

# Taste, not correctness. These fire on text a reader can still use, so they
# only run when explicitly asked for; the gate does not block on style.
STYLE_RULES = {
    "filler", "toc", "emoji", "bullet-run", "bullet-ratio", "badges",
    "exclamation", "bold", "emdash", "long-sentence", "cjk-spacing",
}


def list_rules() -> str:
    out = ["readme_lint — checks", ""]
    for label, predicate in (
        ("error (exit non-zero)", lambda r: RULES[r][0] == "error"),
        ("warn (always on)", lambda r: RULES[r][0] == "warn" and r not in STYLE_RULES),
        ("style (only with --style, off in the gate)", lambda r: r in STYLE_RULES),
    ):
        out.append(label)
        for rule, (_, desc) in RULES.items():
            if predicate(rule):
                out.append(f"  {rule:<16} {desc}")
        out.append("")
    out.append("word lists")
    out.append(f"  hype (en)   {', '.join(HYPE)}")
    out.append(f"  hype (zh)   {'、'.join(CJK_HYPE)}")
    out.append(f"  filler      {', '.join(FILLER)}")
    out.append(f"  placeholder {' | '.join(PLACEHOLDER)}")
    out.append("")
    out.append("budgets   " + ", ".join(f"{k} {v}" for k, v in BUDGET.items()))
    return "\n".join(out)


def check_rule_table() -> list[str]:
    """Invariants a dict literal hides: duplicate keys and dangling style ids.

    A duplicated key in RULES is silently overwritten by Python, so a bad
    edit that repeats an id looks fine at runtime. Parse our own source to
    catch it, and verify the opt-in set names only real rules.
    """
    import ast

    problems: list[str] = []
    source = Path(__file__).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "RULES" for t in node.targets):
            continue
        keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
        for key in sorted({k for k in keys if keys.count(k) > 1}):
            problems.append(f"duplicate rule id in RULES: {key}")
    for key in sorted(STYLE_RULES - set(RULES)):
        problems.append(f"STYLE_RULES names an undeclared rule: {key}")
    return problems


def self_test() -> int:
    """Run the linter against the bundled examples and check declared rules."""
    root = Path(__file__).resolve().parent.parent
    cases = [
        ("examples/cli-before.md", "cli", False),
        ("examples/cli-after.md", "cli", True),
        ("examples/library-before.md", "library", False),
        ("examples/library-after.md", "library", True),
        ("README.md", "generic", True),
    ]
    failures = 0
    for rel, kind, expect_pass in cases:
        path = root / rel
        if not path.is_file():
            print(f"MISSING  {rel}")
            failures += 1
            continue
        result = run(path, kind, root)
        ok = result["passed"] == expect_pass
        failures += 0 if ok else 1
        print(f"{'ok  ' if ok else 'FAIL'}  {rel:28} score={result['score']:>3} "
              f"errors={result['errors']} expected={'PASS' if expect_pass else 'FAIL'}")
        for finding in result["findings"]:
            if finding["rule"] not in RULES:
                print(f"FAIL  undeclared rule id: {finding['rule']}")
                failures += 1

    for problem in check_rule_table():
        print(f"FAIL  {problem}")
        failures += 1

    sample = root / "examples/cli-before.md"
    plain = run(sample, "cli", root, style=False)
    styled = run(sample, "cli", root, style=True)
    leaked = sorted({f["rule"] for f in plain["findings"] if f["rule"] in STYLE_RULES})
    if leaked:
        print(f"FAIL  style rules leaked into default run: {leaked}")
        failures += 1
    else:
        print("ok    default run excludes style rules")
    gained = sorted({f["rule"] for f in styled["findings"] if f["rule"] in STYLE_RULES})
    if not gained:
        print("FAIL  --style produced no style findings")
        failures += 1
    else:
        print(f"ok    --style adds {len(gained)} style rules: {', '.join(gained)}")

    print("self-test", "PASS" if failures == 0 else f"FAIL ({failures})")
    return 0 if failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a README for AI-generated patterns.")
    parser.add_argument("file", nargs="?", default="README.md", help="README path (default: README.md)")
    parser.add_argument("--type", default="auto",
                        choices=["auto", "cli", "library", "web-app", "monorepo", "script", "generic"],
                        help="archetype, for the length budget")
    parser.add_argument("--repo", help="repository root, enables the license-file check")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--list-rules", action="store_true", help="print every check and word list, then exit")
    parser.add_argument("--self-test", action="store_true", help="verify the bundled examples score as expected")
    parser.add_argument("--style", action="store_true",
                        help="also check taste rules (sentence length, bullet density, emoji count)")
    parser.add_argument("--stdin", action="store_true",
                        help="read README content from stdin instead of the working-tree file")
    args = parser.parse_args()

    if args.list_rules:
        print(list_rules())
        return 0

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve() if args.repo else None
    if args.stdin:
        result = run(Path(args.file), args.type, repo, style=args.style,
                     source=sys.stdin.read())
    else:
        path = Path(args.file)
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 2
        result = run(path, args.type, repo, style=args.style)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
