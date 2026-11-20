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

依赖：Python 3.9 以上，两个脚本都只用标准库。

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

`readme_lint.py` 是确定性检查：读文件、算分 0–100、有 error 就退出非零。

| 类别 | 例子 |
|---|---|
| 编造内容 | `TODO`、`TBD`、占位图、`example.com/your-*` 链接 |
| 营销腔 | `seamless`、`robust`、`blazing`、`cutting-edge`、`强大`、`一站式`、`开箱即用` |
| 结构 | 缺标题、多个 H1、空章节、没有快速开始或用法 |
| 格式 | 代码块没有语言标记、标题带 emoji、badge 超过 3 个 |
| 信息密度 | 通篇 bullet、连续 6 条以上列表、句子过长、超出长度预算 |
| 许可证 | 声称有协议但仓库里没有 `LICENSE` |

输出示例：

```text
README lint: README.md
type: cli (budget 160)  lines: 68

  L1   error heading-emoji  decorative emoji in a heading
  L8   error hype           marketing word `seamless` — state the behaviour instead
  L20  warn  bullet-run     6 consecutive bullets — use prose or a table

score: 64/100  (2 errors, 1 warning)
result: FAIL
```

如需豁免某条规则，在文件任意位置写 `<!-- readme-lint: disable rule-name -->`。

## 自带样例

`examples/` 里有两组 before/after。before 是典型的生成式 README，after 是用本 skill 写的版本。

| 文件 | 得分 |
|---|---|
| `cli-before.md` | 0/100，23 个 error |
| `cli-after.md` | 100/100 |
| `library-before.md` | 0/100，7 个 error |
| `library-after.md` | 100/100 |

复现：

```bash
python scripts/readme_lint.py examples/cli-before.md --type cli
python scripts/readme_lint.py examples/cli-after.md --type cli
```

## 目录结构

```text
SKILL.md                  agent 执行的主流程
references/
  structure.md            项目类型、章节矩阵、长度预算
  style-rules.md          语感规则、禁用词、20 组改写对照
  fact-sheet.md           各生态里命令、配置、许可证的出处
scripts/
  project_scan.py         仓库 → 事实清单
  readme_lint.py          文件 → 问题清单与评分
examples/                 before/after 样例
```

## 设计取舍

**先事实后文字。** 事实清单没定下来之前不许起草。命令的取值顺序是 CI → Makefile → manifest scripts，不靠记忆。核不实的项写成 `TODO`，并在交付说明里列出。

**裁剪优先于填充。** `references/structure.md` 定义了五种项目类型和章节矩阵。可选章节是删掉，而不是压缩成一句话。

**确定性的检查交给代码。** linter 负责模型自己容易漏掉的东西：营销形容词、装饰 emoji、通篇 bullet、仓库支撑不了的声明。语感判断留在提示词里，可量化的缺陷交给脚本。

**中英文都管。** 规则覆盖两种语言：linter 会报中英文之间缺空格，禁用词表里包含中文 README 常见的营销词。

## License

MIT，见 [LICENSE](LICENSE)。
