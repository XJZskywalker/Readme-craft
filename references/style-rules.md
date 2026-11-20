# Style rules

Rules are checkable. A sentence either obeys them or gets rewritten; "sounds fine" is not a criterion.

## Voice

1. **Verb first, subject implied.** "Installs as a single binary" not "The installation of this tool can be performed".
2. **One idea per sentence.** Split at the second "and" or "which".
3. **Concrete over abstract.** Numbers, file names, command names, type names. `Supports Node 18+` beats `modern runtimes`.
4. **No hedging stacks.** Cut `basically`, `essentially`, `simply`, `just`, `easily`, `of course`.
5. **State limitations plainly.** `Does not support Windows.` is a feature, not a weakness — it tells the reader whether to keep reading.
6. **Second person only in steps.** "Run the command" is fine in Quick start; elsewhere prefer "the command".

## Sentence and paragraph limits

| Unit | Limit |
|---|---|
| Sentence | 25 words / 40 CJK characters |
| Paragraph | 4 sentences |
| List | 5 items |
| Heading depth | 3 levels, no skipped levels |
| Code block | 20 lines; longer goes to a file or a collapsible block |

## Banned phrases

The word lists live in the linter, in one place:

```bash
python scripts/readme_lint.py --list-rules
```

Read them as a taxonomy rather than a spell-check, because each group is a different failure. Hype names a quality where a behaviour belongs: "blazing fast" tells the reader nothing they can act on, while "1.8s for 10k rows" tells them whether to keep reading. Filler postpones the sentence ("It is worth noting that X" means "X"). Openers greet instead of stating.

A phrase on those lists is the linter's problem. The paragraphs below are yours: rhythm, symmetry, and the shape of the document. They share a signature — text written to sound complete rather than to say something.

**The parallel-triple.** "Fast, simple, and reliable." Three items, same grammar, no verb carrying an object. Sounds decisive, commits to nothing. Rewrite as one concrete claim, or cut.

**Uniform weight.** Every section the same length, every bullet four to eight words. Real projects are lopsided: the config table has nine rows, the architecture note has two sentences. Even distribution is the tell of a template.

**Restatement.** A closing paragraph that rewords the opening one, an intro that repeats the title. The reader already read it.

**Rhythm over meaning.** Em-dash chains that carry the actual content ("It's fast — really fast — faster than anything else"), bold on every key noun, "not only ... but also" holding two clauses that did not need joining.

## Formatting

- **Headings**: sentence case, no emoji, no trailing punctuation. `## Quick start`, not `## 🚀 Quick Start!`
- **Bold**: at most one or two per section, for warnings or defaults. Not for emphasis in ordinary sentences.
- **Code fences**: always tagged. `bash`, `ts`, `python`, `json`, `text`.
- **Commands**: no `$` prompt prefix unless the block mixes commands with output.
- **Tables**: for parallel data (options, env vars, packages). Never for two-row comparisons.
- **Inline code**: for identifiers, file names, flags, values. Not for emphasis.
- **Links**: descriptive text. `See [configuration](docs/config.md)`, not `[click here]`.
- **Emoji**: none. If the project itself is emoji-forward, at most one, in the title only.

## Chinese-specific

- 中英文之间加空格：`使用 Node 18 运行`，不是 `使用Node18运行`。
- 不在正式文档里用「我们」「让我们」；步骤用祈使句。
- 全角标点，代码与命令保持半角。
- 避免「本文将」「下面让我们来看看」这类过渡句，直接进入内容。

## Before / after

| # | Before | After | Fault |
|---|---|---|---|
| 1 | Welcome to **fastparse**! A powerful and elegant parsing library. | `fastparse` turns TypeScript interfaces into runtime validators. | greeting + hype |
| 2 | 🚀 **Blazing fast** — up to 10x faster! | Parses a 1 MB JSON payload in about 12 ms on a 2020 MacBook Air. | hype + unverifiable claim |
| 3 | ## ✨ Features<br>• **Simple** — easy to use<br>• **Fast** — high performance<br>• **Flexible** — highly configurable | Handles nested schemas and reports the exact path of the first failure. | empty parallelism |
| 4 | Simply run `npm install` to get started! | ```bash<br>npm install fastparse<br>``` | filler + exclamation |
| 5 | This project is licensed under the MIT License. (no LICENSE file) | Add `LICENSE` with the MIT text before claiming it. | invented fact |
| 6 | It is worth noting that the config file is optional. | The config file is optional; defaults are in `src/defaults.ts`. | filler + vague |
| 7 | ## Table of Contents<br>1. [Install](#install)<br>2. [Usage](#usage) | (delete — the file is 48 lines) | ceremony |
| 8 | Our tool provides a wide range of options to customize your experience. | Three options: `--port`, `--host`, `--no-color`. | vague + hype |
| 9 | ## Contributing<br>We welcome contributions of all kinds! | ## Contributing<br>Open an issue before sending a PR. Run `npm test` first. | no actionable content |
| 10 | The `parse()` function is used for parsing the input. | `parse(input)` returns a `Node` tree or throws `ParseError` with `line` and `column`. | restates the name |
| 11 | Built with ❤️ using React, TypeScript, Vite, Tailwind, ESLint, Prettier, ... | Built with React and Vite. | badge soup |
| 12 | Getting started is easy! First, make sure you have Node installed. Then... | Needs Node 18+. `npm install && npm run dev`, then open `http://localhost:5173`. | padding |
| 13 | Whether you're a beginner or an expert, this tool has something for you. | (delete) | marketing to everyone |
| 14 | ## Roadmap<br>- [ ] More features<br>- [ ] Better docs | (delete, or link the actual issue tracker) | placeholder |
| 15 | ![screenshot](placeholder.png) | ![](docs/screenshot.png) — with the file committed | broken asset |
| 16 | Our mission is to revolutionize how developers handle configuration. | Reads `app.toml` and exports typed values. | mission statement |
| 17 | 本工具是一个强大、优雅、开箱即用的配置管理方案。 | 读取 `app.toml`，按 schema 校验后导出带类型的配置对象。 | 中文营销词 |
| 18 | Simply put, it just works. | (delete) | says nothing |
| 19 | Install via npm, yarn, pnpm, bun, or your favorite package manager. | ```bash<br>npm install fastparse<br>``` | option flood |
| 20 | ## FAQ<br>**Q: Is it fast?**<br>A: Yes, very fast! | Move the real numbers into the positioning line; delete the FAQ. | self-interview |

## Review pass

After drafting, run these three reads:

1. **Delete test** — cover the intro. Does the README still make sense? If yes, the intro was decoration.
2. **Substitution test** — swap the project name for a competitor's. Any sentence that still reads true is filler.
3. **Skeptic test** — for each claim, point at the file or command that proves it. No proof, no claim.
