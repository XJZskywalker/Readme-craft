# readme-craft

[English](README.en.md) | 中文

一个用于生成、重写、审查项目 README 的 skill。所有结论都要能在仓库里找到出处，每个章节都要有存在的理由。

多数 AI 生成的 README 有相同的毛病：一句欢迎语、六条没有动词的功能列表、从教程里抄来的安装命令。这个 skill 用固定流程替代它们：取事实、裁章节、起草、跑 linter。

## 三种模式

| 模式 | 触发条件 | 产出 |
|---|---|---|
| generate | 没有 README，或只有不到 10 行的占位 | 新 `README.md` |
| rewrite | README 冗长、模板化、有明显生成痕迹 | 重写后的文件 + 修改说明 |
| audit | 只要审查意见，不改文件 | 问题清单与评分 |

## 安装

把目录复制到 agent 的 skills 目录即可：

```bash
git clone https://github.com/XJZskywalker/Readme-craft.git
mkdir -p ~/.workbuddy/skills
cp -r Readme-craft ~/.workbuddy/skills/readme-craft
```

Claude Code 及其他从 skills 目录读取 `SKILL.md` 的 agent 使用方法相同，目录结构是通用的。

依赖：Python 3.9 以上。三个 Python 脚本只用标准库，闸门是一个 POSIX sh 脚本。

改这个仓库本身的话，clone 后先启用 README 闸门，之后每次 commit 和 push 都会检查提交里的 README：

```bash
git config core.hooksPath .githooks
```

## 使用

直接说需求即可：

```text
给这个项目写一个 README
```

```text
这个 README 太像 AI 写的了，删掉废话，把不准确的地方改对
```

```text
对照代码检查这份 README，不要改文件，只给报告
```

agent 会先跑 `project_scan.py` 拿到事实清单，读完再起草，然后反复跑 `readme_lint.py` 直到退出码为 0。交付时会列出删掉了什么，以及哪些值没能核实。

## linter 检查什么

`readme_lint.py` 是确定性检查：读文件、给出 0–100 的参考分，退出码只由 error 决定。规则分三层：

| 层 | 默认 | 检查内容 |
|---|---|---|
| error | 开，阻断 | 占位文本与假链接、营销词、缺标题、多个 H1、空章节、没有快速开始、标题带 emoji、声称有协议但仓库没有 `LICENSE` |
| warn | 开，只提示 | 标题跳级、缺安装段、功能列表只列不解释、代码块没语言标记、超出长度预算 |
| style | 关 | 句长、连续列表、emoji 密度、badge 数量、加粗密度、em dash、中英空格、填充短语、短文件加目录 |

审美类规则默认关闭，因为文风不是事故。要单独看文风问题就加 `--style`；闸门从不因它们拦人。分数只是参考，warning 再多也不会让退出码变成非零。

输出示例（默认层）：

```text
README lint: README.md
type: cli (budget 160)  lines: 68

  L1   error heading-emoji  decorative emoji in a heading
  L8   error hype           marketing word detected — state the behaviour instead
  L20  warn  fence-lang     code fence without a language tag

score: 72/100  (2 errors, 1 warning)
result: FAIL
```

全部检查项与背后的词表用 `python scripts/readme_lint.py --list-rules` 打印，`references/style-rules.md` 只解释这些词为什么是病，不再抄一遍词表。如需豁免某条规则，在文件任意位置写 `<!-- readme-lint: disable rule-name -->`。

## 自带样例

`examples/` 里有两组 before/after。before 是典型的生成式 README，after 是用本 skill 写的版本。

| 文件 | 得分 |
|---|---|
| `cli-before.md` | 0/100，23 个 error |
| `cli-after.md` | 100/100 |
| `library-before.md` | 4/100，7 个 error |
| `library-after.md` | 100/100 |

分数只表示是否踩中本 skill 列出的规则，判定 FAIL 的是 error 数，不是分数高低。

复现（校验样例得分、规则表没有重复或悬空的 id、分层没有被绕过）：

```bash
python scripts/readme_lint.py --self-test
python scripts/readme_stale.py --self-test
```

## 提交时的闸门

钩子不调模型，它做两件事：拦下，指路。

- `pre-commit` 检查 index 里的 README，`pre-push` 检查即将推送的提交里的 README。读的是 git 对象而不是工作树文件——`git add` 之后再把工作区改好，骗不过闸门
- 有 error 就拦住这次提交或推送，warning 只打印
- 契约文件（manifest、`.env.example`、Dockerfile、Makefile、CI workflow）变了但 README 没动 → 打印警告，不阻断。`.env.example` 里出现 README 没写的变量 → 逐个列出来，变量名按整词匹配，`PORT` 不会被 `SUPPORT` 糊弄过去
- 首次推送没有基线，跳过过期检测；一次推多个分支会逐个检查

push 和 PR 还会由 GitHub Actions 跑一遍两个 self-test 与两份 README 的 lint，Python 3.9 和 3.12 各一次，改坏规则不会静默混进去。

`python scripts/readme_stale.py --staged --strict` 会把警告变成非零退出码，可以接进自己的 CI；仓库自带的 CI 不使用它，因为改个依赖版本就红一次太吵。

事实准确性闸门查不了：命令是不是真的、端口对不对，只能靠事实清单和人工核对。协议文件是否存在按工作树判断，删掉 `LICENSE` 却还没提交时，工作树与提交内容会有短暂不一致。

## 目录结构

```text
SKILL.md                  agent 执行的主流程
references/
  structure.md            项目类型、章节矩阵、长度预算
  style-rules.md          语感规则、禁用词成因、20 组改写对照
  fact-sheet.md           各生态里命令、配置、许可证的出处
scripts/
  project_scan.py         仓库 → 事实清单
  readme_lint.py          文件 → 问题清单与评分
  readme_stale.py         契约变了 README 没动 → 警告
  readme_gate.sh          commit / push 前的闸门
AGENTS.md                 agent 在这个仓库里如何配合闸门
.githooks/                pre-commit / pre-push 钩子
.github/workflows/        CI 跑自检与两份 README 的 lint
examples/                 before/after 样例
```

## 设计取舍

**先事实后文字。** 事实清单没定下来之前不许起草。命令的取值顺序是 CI → Makefile → manifest scripts，不靠记忆。核不实的项写成未核实标记，并在交付说明里列出。

**裁剪优先于填充。** `references/structure.md` 定义了五种项目类型和章节矩阵。可选章节是删掉，而不是压缩成一句话。

**确定性的检查交给代码。** linter 只管模型容易漏掉、且能防事故的东西：营销形容词、编造的占位内容、坏掉的结构、仓库支撑不了的声明。句长和 emoji 密度这类审美判断默认交给提示词，需要时才由 `--style` 单独报告。

**中英文都管。** 禁用词表包含中文 README 常见的营销词，标题与章节名同时识别中英文。中英空格属于 style 层，默认不报。

## License

MIT，见 [LICENSE](LICENSE)。
