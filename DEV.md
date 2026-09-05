# OSP 开发者指南

开发者不再使用单元测试验证 OSP。验证方式是构建 Docker 镜像，在隔离环境中使用真实的 OSP、OpenCode、Codex、Bohrium 和 Hugging Face CLI，模拟用户完成一次端到端评审。

## 文件与行为

| 修改位置 | 影响的行为 |
|---|---|
| `src/cli.ts` | CLI 命令、参数、doctor、运行准备、认证检测和交付行为 |
| `src/controller.ts` | 阶段调度、headless/TUI、超时、暂停、恢复和审批 gate |
| `src/phases.ts` | 七阶段注册和执行顺序 |
| `src/input.ts` | PDF/TeX/压缩包/workspace 导入、文件过滤、只读 source 和输入摘要 |
| `src/validation.ts` | 阶段产物、最终报告和 contract 的通过条件 |
| `src/config.ts` | 每次运行的 OpenCode、MCP 和权限配置 |
| `src/network.ts` | `scholarly`、`online`、`offline` 网络权限 |
| `src/delivery.ts` | `final_review.md`、manifest、submission 和 trail 输出 |
| `src/state.ts` | 运行状态、phase 状态、scope 和 resume 数据结构 |
| `src/mcp/` | 学术检索服务、Bohrium LKM、arXiv、Semantic Scholar 等行为 |
| `extensions/_shared/commands/` | 每个阶段的用户可见工作流程和提示词 |
| `extensions/_shared/skills/` | 各个评审 persona 的职责和分析方式 |
| `extensions/_shared/rules/osp-rules.md` | 所有 OSP 阶段共同遵守的规则 |
| `extensions/_shared/defaults/` | 评审标准、领域指导、Q&A 模板、推荐词汇和报告结构 |
| `.brain-template/session.json` | 新运行的初始状态和默认 Q&A 配置 |
| `Dockerfile` | 隔离开发环境中的系统工具和 CLI 版本 |
| `docker/acceptance.sh` | 开发者实际执行的端到端验收流程 |
| `docs/ARTIFACT_CONTRACTS.md` | 阶段 reads/writes、artifact 结构和兼容版本 |

调整七阶段协议时，必须同步修改 `src/phases.ts`、契约、validator、canonical assets 和 Docker 验收流程。

## 构建镜像

```bash
docker build -t open-scholar-peer:dev .
```

镜像包含 Node.js、OSP、OpenCode、Codex、Bohrium CLI、Hugging Face CLI、Git、Poppler 和联网所需组件。

## 挂载开发者配置

容器使用宿主机配置，但认证文件和目录只读挂载。Bohrium access key 通过环境变量传入：

```bash
BOHR_ACCESS_KEY="$(bohr auth token)" docker run --rm \
  -e OSP_MODEL=provider/model \
  -e BOHR_ACCESS_KEY \
  -v "$HOME/.config/opencode/opencode.jsonc:/root/.config/opencode/opencode.jsonc:ro" \
  -v "$HOME/.local/share/opencode/auth.json:/root/.local/share/opencode/auth.json:ro" \
  -v "$HOME/.codex:/root/.codex:ro" \
  -v "$HOME/.bohr:/root/.bohr:ro" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro" \
  --entrypoint bash open-scholar-peer:dev \
  -lc 'opencode --version && codex --version && bohr auth status && hf auth whoami'
```

不要把配置或 access key 写入 Dockerfile、镜像层或 Git。

## 端到端评审

默认入口需要论文和模型，执行完整七阶段评审：

```bash
BOHR_ACCESS_KEY="$(bohr auth token)" docker run --rm \
  -e OSP_MODEL=provider/model \
  -e OSP_ALLOW_LKM_SPEND=true \
  -e BOHR_ACCESS_KEY \
  -v "$HOME/.config/opencode/opencode.jsonc:/root/.config/opencode/opencode.jsonc:ro" \
  -v "$HOME/.local/share/opencode/auth.json:/root/.local/share/opencode/auth.json:ro" \
  -v "$HOME/.codex:/root/.codex:ro" \
  -v "$HOME/.bohr:/root/.bohr:ro" \
  -v "$HOME/.cache/huggingface:/root/.cache/huggingface:ro" \
  -v "$PWD/osp-docker-output:/tmp/osp-docker-output" \
  open-scholar-peer:dev
```

默认联网策略是 `scholarly`。设置 `OSP_NETWORK_POLICY=online` 可以启用通用 web 工具。设置 `OSP_DOCKER_SOURCE` 可以指定容器内挂载的其他稿件路径。

## 验收标准

成功运行必须满足：

- `osp doctor` 的必需依赖全部通过
- Bohrium 返回 `logged_in: true`
- Hugging Face `hf auth whoami` 成功
- OSP 完成七个阶段
- 三轮 literature artifact 全部生成
- Q&A artifact 数量正确
- 最终报告生成
- `osp validate` 返回 `valid: true`
- 输出目录包含 `final_review.md` 和 `run-manifest.json`
- 容器输出 `OSP Docker acceptance passed`

需要注意：真实端到端测试会消耗模型额度，启用 `--allow-lkm-spend` 时也可能产生 Bohrium 费用。
