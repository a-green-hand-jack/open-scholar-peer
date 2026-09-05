# Open ScholarPeer

Open ScholarPeer（OSP）是一个基于 OpenCode 的论文评审工具。它按照固定的七阶段流程分析论文、检索相关文献、检查 baseline、生成证据问答，并输出结构化审稿意见。

## 直接安装

用户不需要 clone 仓库，也不需要准备本地源码目录。系统需要 Node.js 20+、OpenCode 1.18.25+、Git，以及处理 PDF 所需的 Poppler：

```bash
curl -fsSL https://raw.githubusercontent.com/a-green-hand-jack/open-scholar-peer/main/install_cli.sh | bash
export PATH="${XDG_BIN_HOME:-$HOME/.local/bin}:$PATH"
osp doctor
```

然后使用已经在 OpenCode 中配置好的模型：

```bash
osp review ./paper.pdf \
  --output ./osp-review \
  --headless \
  --mode autonomous \
  --model <provider/model>
```

支持 PDF、TeX 目录、ZIP/TAR 源码包和已有 OSP workspace。原始输入不会被修改，OSP 会在隔离目录中创建只读副本。

## Bohrium 文献检索

需要使用 Bohrium LKM 时，先安装并登录：

```bash
npm install -g @dptech-corp/bohr-cli
bohr auth login
bohr auth status
```

允许本次运行使用计费的 LKM 调用：

```bash
osp review ./paper.pdf \
  --output ./osp-review \
  --headless \
  --mode autonomous \
  --model <provider/model> \
  --allow-lkm-spend
```

不加 `--allow-lkm-spend` 时，OSP 不会使用计费的 LKM 调用，但会记录限制并尝试其他文献来源。

## 交互和恢复

默认模式会启动 OpenCode TUI。无人值守运行使用 `--headless`。需要人工检查每个阶段时使用 collaborative 模式：

```bash
osp review ./paper.pdf --output ./osp-review --mode collaborative
osp status <run-directory>
osp approve <run-directory>
osp resume <run-directory>
```

常用命令：

```bash
osp doctor
osp status <run-directory> --json
osp validate <run-directory> --json
osp checkpoint <run-directory>
osp resume <run-directory>
```

## 评审流程

OSP 固定执行：

```text
onboarding -> summary -> literature -> historian -> baseline_scout -> qa -> review
```

文献阶段固定执行三轮检索：子领域 anchor、方法 anchor、时间扩展。最终报告包含摘要、优点、缺点、criterion 评分、证据、限制、问题和 recommendation。所有阶段产物都包含 `Method`、`Output` 和 `Provenance`。

## 输出

完成后可以在输出目录找到：

```text
final_review.md
run-manifest.json
osp-<timestamp>-<random>/
```

最终报告位于 `final_review.md`。运行目录还保留阶段产物、运行状态、输入摘要、来源信息、检索记录和 Git checkpoint。

## 网络策略

默认 `scholarly` 只允许 OSP 的学术检索服务。需要通用网络工具时使用 `--network-policy online`；完全离线时使用 `--network-policy offline`。

## 文档

- 用户完整指南：[`docs/OSP_CLI.md`](docs/OSP_CLI.md)
- 开发者指南：[`DEV.md`](DEV.md)
- 阶段和验收标准：[`docs/PHASES.md`](docs/PHASES.md)
- 阶段输入输出契约：[`docs/ARTIFACT_CONTRACTS.md`](docs/ARTIFACT_CONTRACTS.md)
