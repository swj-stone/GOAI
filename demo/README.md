# CampusMatch Demo

CampusMatch 是面向学生的“证据化求职助手”Demo。学生只需使用浏览器：上传材料或粘贴 Markdown、选择求职目标、查看匹配解释，最后由本人确认后导出报告。学生不需要安装 Python、配置模型、编写提示词或接触 API Key。

项目实现了两条可独立演示的链路：

- 浏览器链路：FastAPI + 原生 HTML/CSS/JavaScript，适合评委和普通用户直接操作。
- HiClaw AgentTeams 链路：1 个 Career Navigator + 5 个专业 Worker，通过 MCP 调用同一套确定性业务接口，适合展示真实多 Agent 编排。

## 1. 三分钟运行浏览器 Demo

开发者只需在项目根目录执行：

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
.\demo\scripts\start-demo.ps1
```

然后用浏览器打开：

```text
http://127.0.0.1:3100
```

普通体验者从这一步开始即可，不需要打开终端。点击“载入合成案例”，再点击“开始证据化分析”。系统会稳定得到：

- 岗位匹配度：77；
- 证据覆盖度：85；
- 与岗位职责无关的性别条件：`POLICY_EXCLUDED`，不参与匹配；
- 未人工确认时 Audit：`BLOCK`，报告不可导出；
- 勾选人工确认并重新审计后：`PASS`，Markdown 报告可导出。

这些数字仅用于确定性复现，不代表录用概率或真实模型准确率。

## 2. 用户操作流程

1. 选择“求职”“跳槽”或“了解岗位”。
2. 上传 `.md`、`.txt`、`.docx` 或可提取文本的 `.pdf`，也可以直接粘贴 Markdown。
3. 系统把文档转为 Markdown；用户和 Agent 查看同一份文本。
4. Profile Agent 从原文提取能力，每条能力保留原文、来源和行号。
5. Job Agent 将 JD 拆成硬性要求、加分项、岗位职责和风险条件。
6. Match Agent 输出匹配度、证据覆盖度、五维图及“符合／部分符合／缺少证据”。
7. Coach Agent 只依据已有经历给出简历、学习和面试建议，不补写不存在的经历。
8. Audit Agent 检查证据缺失、无依据陈述、隐私、歧视性条件和人工审批。
9. 用户确认结果后重新审计；只有 `PASS` 才能导出报告。

单文件上限为 5 MiB。扫描版 PDF 暂不做 OCR，系统会明确返回 `PDF_TEXT_NOT_FOUND`，不会凭空生成画像。

## 3. 本地开发与测试

项目使用根目录虚拟环境，不需要在 HiClaw 容器中安装 Python：Python 服务运行在本机，HiClaw Worker 通过网关/MCP 调用它。

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python -m pytest demo\tests -q
```

主要目录：

```text
demo/
├─ src/campusmatch/        # API、规则服务与网页
├─ tests/                  # 单元、契约、API 和安全门禁测试
├─ fixtures/               # 完全合成、可公开的固定案例
├─ agentteams/             # MCP 配置、Worker Skills 与容器内脚本
└─ scripts/                # Windows 一键启动、注册、同步与烟雾测试
```

常用接口：

| 接口 | 作用 |
|---|---|
| `GET /api/health` | 服务健康检查 |
| `POST /api/v1/documents/convert` | 文档转 Markdown |
| `POST /api/v1/analyze` | 一次执行完整分析流程 |
| `POST /api/v1/profile` | Profile Worker 工具接口 |
| `POST /api/v1/job` | Job Worker 工具接口 |
| `POST /api/v1/match` | Match Worker 工具接口 |
| `POST /api/v1/coach` | Coach Worker 工具接口 |
| `POST /api/v1/audit` | Audit Worker 与人工审批接口 |
| `GET /api/v1/tasks/{task_id}` | 查询阶段状态 |
| `GET /api/v1/reports/{task_id}.md` | 审计通过后导出 Markdown |

OpenAPI 调试页位于 `http://127.0.0.1:3100/docs`。

## 4. 接入本地 HiClaw

前提：HiClaw 的 Manager、Controller 和六个 Worker 容器已经运行，本机 Demo 也正在监听 `3100` 端口。

首次或配置变化后，按顺序执行：

```powershell
# 1. 注册 MCP，并为 Manager 生成/保存本地随机令牌
.\demo\scripts\register-hiclaw.ps1

# 2. 让六个 Worker 使用各自已有的网关身份访问 MCP
.\demo\scripts\configure-worker-mcp.ps1

# 3. 同步并校验六个 CampusMatch Skill
.\demo\scripts\sync-worker-skills.ps1

# 4. 不依赖模型的六阶段 MCP 烟雾测试
.\demo\scripts\smoke-hiclaw.ps1 -TaskId smoke-campusmatch-001

# 5. 真实 Team Room 委派测试
.\demo\scripts\delegate-team-smoke.ps1 -TaskId team-live-001
```

第 4 步直接验证 Profile → Job → Match → Coach → Audit → 状态查询。第 5 步会把同一案例交给 Team Leader，由五个 Worker 分阶段处理，并在 Matrix Team Room 中留下真实消息和执行记录。

`demo/.env.local` 仅保存本地 MCP 令牌，已被 Git 忽略。脚本不会在控制台打印令牌；请勿把该文件加入截图、PPT 或公开仓库。

## 5. 可信边界

- 这是求职准备辅助工具，不是自动录用、淘汰或排名系统。
- 匹配度是“当前材料对当前 JD 的证据覆盖”，不是个人价值判断。
- `NO_EVIDENCE` 表示材料中没有证据，不等于用户不会该能力。
- 年龄、性别等与岗位职责无关的条件被隔离，不计入匹配。
- Coach 的建议不得改写成已经发生的经历或量化成果。
- 当前 MVP 使用确定性规则保证可复现；接入大模型后仍需保留 Schema、证据引用、审计和人工批准门禁。
- 当前报告状态保存在进程内存中；服务重启后任务状态会清空。生产环境需要数据库、对象存储、访问控制、保留期限和删除机制。

完整方案、PPT、复现步骤和实机验收证据位于项目根目录的 `show` 文件夹。
