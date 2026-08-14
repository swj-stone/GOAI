# CampusMatch Demo 实现计划（HiClaw 实机版）

> 执行说明：本计划面向当前电脑上的 HiClaw／AgentTeams 环境。后端采用 Python/FastAPI，但普通用户只使用网页，不接触 Python、命令行、提示词或 API Key。执行时按任务顺序推进，每个任务先写测试、再实现、最后提交。未经确认，不创建 Worker、Team，不修改网关配置。

## 1. 目标与完成定义

### 1.1 本轮目标

实现一个普通学生不需要编程、不需要写提示词即可操作的 CampusMatch Demo：

1. 用户在浏览器中上传或选择合成材料。
2. 系统把材料转换成可共同查看的 Markdown，并给每条能力附原文证据。
3. 系统把综合运营实习 JD 拆成硬性要求、加分项、模糊描述和风险条件。
4. 系统输出可解释的匹配结果：符合、部分符合、缺少证据、风险排除。
5. 系统给出不虚构经历的简历、学习和面试建议。
6. Audit 阻断无证据数字、敏感属性评分和未审批导出。
7. HiClaw 的真实 AgentTeam 能调用同一套工具，并在 Element 中展示协同过程。

### 1.2 完成定义

以下条件全部满足才算 Demo 完成：

- 双击启动脚本后，浏览器访问 `http://127.0.0.1:3100` 可完成四步流程；首次部署由开发者创建项目专属 `.venv`。
- 未配置模型 API 时，固定合成案例仍可稳定得到 77 分匹配度和 85% 材料覆盖度。
- 每个能力结论都有 `evidence_ref`、原文摘录和行号。
- “女性优先”被标记为 `POLICY_EXCLUDED`，不进入分子和分母。
- Coach 生成未经材料支持的“提升 30%”时，Audit 返回 `BLOCK`，导出按钮不可用。
- 用户确认、Audit `PASS`、人工审批三项齐全后，才能生成报告。
- `pytest` 全部通过，并生成 `report.md`、`audit.json`、`trace.jsonl`。
- Element 中能够看到 Career Navigator 和五个专业 Worker 的真实协作记录。

## 2. 已核验的本机条件

| 项目 | 当前状态 | 对实现的影响 |
|---|---|---|
| Docker Desktop | Running | 可以运行 HiClaw 和 Worker 容器 |
| HiClaw Controller | 正常 | Matrix 与 MinIO 健康检查通过 |
| Higress Console | `127.0.0.1:18001` | 管理网关，不作为学生入口 |
| Higress Gateway | `127.0.0.1:18080` | 模型与 MCP 工具统一入口 |
| Element Web | `127.0.0.1:18088` | 查看 Agent 协作和人工介入 |
| OpenClaw Control UI | `127.0.0.1:18888` | 查看 Manager 运行状态 |
| AgentTeams 资源 | 0 Worker / 0 Team | 需要创建 CampusMatch 专用团队 |
| 默认 Worker Runtime | `openclaw` | 与本机 Node.js 路线一致 |
| Node.js | v24.15.0 | 可用于前端辅助，但不是本轮后端的必需运行时 |
| Python | 当前终端未加入 PATH | 从用户已有解释器中选择 Python 3.11/3.12，并在 `demo/.venv` 隔离依赖 |
| 容器访问主机 | `host.docker.internal` 可解析 | Worker 可调用 Windows 上的 Demo API |

说明：学生用户只会接触 `3100` 端口的网页；`18001`、`18080`、`18088` 和 `18888` 属于管理员或答辩展示入口。Python 只运行在开发者电脑或服务器上，不要求学生安装。

## 3. 总体实现架构

采用“同一可信内核、双入口”的结构：

```text
普通用户浏览器
    │
    ▼
CampusMatch Web（Python/FastAPI，3100）
    │
    ├─ 离线确定性编排：比赛现场保底，可重复验证
    │
    └─ REST 工具接口：Profile / Job / Match / Coach / Audit
                         ▲
                         │ Higress 将 REST 映射成 MCP Tools
                         │
HiClaw / AgentTeams ─ Career Navigator ─ 五个专业 Workers
    │
    └─ Element 显示协作、失败重试、审计阻断和人工批准
```

关键原则：

- 网页入口不要求用户理解 Agent、MCP、模型或 API Key。
- 离线模式与在线 Agent 模式共用数据契约、匹配公式和 Audit 规则，不能产生两套口径。
- LLM 只负责“提取候选项和自然语言建议”；合法性、计分、证据校验和导出门禁由确定性代码执行。
- 在线模型故障时明确降级为离线演示，不伪装为在线成功。

## 4. 代码和数据目录

执行后新增以下目录；不改动用户现有的 `requirements.txt`：

```text
demo/
├─ README.md
├─ pyproject.toml
├─ requirements.lock
├─ .env.example
├─ config/
│  ├─ competency-catalog.json
│  ├─ policy-rules.json
│  └─ emergency-contacts.example.json
├─ fixtures/
│  ├─ student-materials.md
│  ├─ job-general-operations.md
│  ├─ expected-profile.json
│  ├─ expected-job.json
│  ├─ expected-match.json
│  ├─ expected-audit-block.json
│  └─ expected-policy-exclusion.json
├─ src/campusmatch/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ contracts.py
│  ├─ workflow.py
│  ├─ lib/
│  │  ├─ errors.py
│  │  ├─ ids.py
│  │  ├─ line_index.py
│  │  └─ trace_store.py
│  ├─ services/
│  │  ├─ document_service.py
│  │  ├─ profile_service.py
│  │  ├─ job_service.py
│  │  ├─ match_service.py
│  │  ├─ coach_service.py
│  │  ├─ audit_service.py
│  │  └─ export_service.py
│  └─ static/
│     ├─ index.html
│     ├─ app.css
│     └─ app.js
├─ tests/
│  ├─ test_contracts.py
│  ├─ test_profile.py
│  ├─ test_job.py
│  ├─ test_match.py
│  ├─ test_coach_audit.py
│  ├─ test_workflow.py
│  └─ test_api.py
├─ artifacts/
│  └─ .gitkeep
├─ scripts/
│  ├─ preflight.ps1
│  ├─ start-demo.ps1
│  ├─ verify-demo.ps1
│  └─ register-hiclaw.ps1
└─ agentteams/
   ├─ mcp-campusmatch.yaml
   ├─ souls/
   │  ├─ career-navigator.md
   │  ├─ profile-agent.md
   │  ├─ job-agent.md
   │  ├─ match-agent.md
   │  ├─ coach-agent.md
   │  └─ audit-agent.md
   └─ skills/
      ├─ campusmatch-orchestrate/SKILL.md
      ├─ campusmatch-profile/SKILL.md
      ├─ campusmatch-job/SKILL.md
      ├─ campusmatch-match/SKILL.md
      ├─ campusmatch-coach/SKILL.md
      └─ campusmatch-audit/SKILL.md
```

运行时生成的上传文件、真实材料、访问令牌和报告全部加入 `.gitignore`，只提交合成夹具。

## 5. 数据契约冻结

### 5.1 核心状态

```python
from enum import StrEnum

class MatchState(StrEnum):
    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    NO_EVIDENCE = "NO_EVIDENCE"
    GAP = "GAP"
    CONFLICT = "CONFLICT"
    POLICY_EXCLUDED = "POLICY_EXCLUDED"

class WorkflowState(StrEnum):
    CREATED = "CREATED"
    MATERIAL_READY = "MATERIAL_READY"
    PROFILE_CONFIRMED = "PROFILE_CONFIRMED"
    JOB_PARSED = "JOB_PARSED"
    MATCHED = "MATCHED"
    COACHED = "COACHED"
    BLOCKED = "BLOCKED"
    AUDIT_PASS = "AUDIT_PASS"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    NEEDS_INPUT = "NEEDS_INPUT"
    FAILED = "FAILED"
```

### 5.2 证据对象

```json
{
  "evidence_id": "E-S001-003",
  "source_id": "student-materials",
  "source_type": "course|club|volunteer|self_confirmed",
  "line_start": 8,
  "line_end": 9,
  "quote": "维护 Excel 报名名单，并通知参与者签到安排。",
  "confirmed_by_user": true
}
```

约束：

- `quote` 必须是规范化 Markdown 中的连续原文，不能由模型改写。
- `line_start` 和 `line_end` 必须能定位原文。
- `confirmed_by_user=false` 的证据只能作为候选项，不能写入最终简历。
- `self_confirmed` 必须显示“本人确认，未上传附件”。

### 5.3 匹配对象

```json
{
  "requirement_id": "R-COMMUNICATION",
  "label": "沟通表达",
  "category": "MUST",
  "weight": 25,
  "state": "MATCH",
  "coefficient": 1,
  "evidence_refs": ["E-S001-001", "E-S001-004"],
  "reason": "课堂展示和志愿服务答疑提供了直接证据"
}
```

匹配度和覆盖度必须由代码计算：

```text
match_score = Σ(合法要求权重 × 状态系数)
coverage = Σ(存在有效证据的合法要求权重)
```

系数固定为：`MATCH=1`、`PARTIAL=0.6`、其余可计分状态为 `0`；`POLICY_EXCLUDED` 完全移出计算。

## 6. 分任务实施步骤

### 任务 0：保护现场与冻结基线

**涉及文件**

- 修改：`.gitignore`
- 新增：`demo/README.md`
- 新增：`demo/.env.example`

**步骤**

1. 记录但不修改当前工作树中的用户文件：`requirements.txt` 和 PowerPoint 临时锁文件状态。
2. 在 `.gitignore` 中加入：

```gitignore
demo/.venv/
demo/.pytest_cache/
demo/**/__pycache__/
demo/.env
demo/.env.local
demo/uploads/
demo/artifacts/*
!demo/artifacts/.gitkeep
*.tmp
~$*.pptx
```

3. `demo/.env.example` 只放字段名和安全默认值，不放真实密钥：

```dotenv
PORT=3100
HOST=0.0.0.0
DEMO_MODE=offline
CAMPUSMATCH_MCP_TOKEN=
DATA_RETENTION_HOURS=24
```

4. 运行：

```powershell
git status --short
git diff --check
```

5. 只提交本任务相关文件：

```powershell
git add .gitignore demo/README.md demo/.env.example demo/artifacts/.gitkeep
git commit -m "chore: scaffold CampusMatch demo"
```

**验收**：没有凭据、真实简历、上传文件或无关用户修改进入暂存区。

### 任务 1：建立 Python/FastAPI 项目和健康检查

**涉及文件**

- 新增：`demo/pyproject.toml`
- 新增：`demo/src/campusmatch/__init__.py`
- 新增：`demo/src/campusmatch/main.py`
- 新增：`demo/tests/test_api.py`
- 新增：`demo/scripts/preflight.ps1`

**步骤**

1. 从用户已有解释器中选择 Python 3.11 或 3.12 的 64 位版本。不要依赖全局 `PATH`，将解释器绝对路径保存在当前 PowerShell 变量中：

```powershell
$CampusPython = '用户确认的 python.exe 绝对路径'
& $CampusPython --version
& $CampusPython -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

`pyproject.toml` 声明 FastAPI、Uvicorn、Pydantic、python-multipart、python-docx、pypdf 等运行依赖，以及 pytest、httpx 等开发依赖。安装验证通过后生成 `requirements.lock`，用于冻结实际版本。

2. 先写失败测试，要求 `GET /api/health` 返回：

```json
{"status":"ok","mode":"offline","version":"0.1.0"}
```

3. 运行并确认失败：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_api.py -k health -q
```

4. 实现最小 FastAPI 应用。`main.py` 导出 `app`，由 Uvicorn 启动，也供测试通过 `TestClient` 直接调用。
5. `preflight.ps1` 检查 Node 版本、3100 端口、夹具、HiClaw 四个端口；HiClaw 不可用时只把在线模式标红，不阻止离线模式启动。
6. 再运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts/preflight.ps1
```

7. 提交：

```powershell
git add demo/pyproject.toml demo/requirements.lock demo/src demo/tests/test_api.py demo/scripts/preflight.ps1
git commit -m "feat: add CampusMatch web service baseline"
```

**验收**：依赖只安装在 `demo/.venv`；学生页面无需 Python 操作；健康检查在 1 秒内返回；HiClaw 关闭时仍能启动离线 Demo。

### 任务 2：建立合成数据与可验证契约

**涉及文件**

- 新增：`demo/src/campusmatch/contracts.py`
- 新增：`demo/config/*.json`
- 新增：`demo/fixtures/*`
- 新增：`demo/tests/test_contracts.py`

**步骤**

1. 从 `show/改版设计规格-大众低门槛版.md` 生成林晓雨和综合运营岗位夹具。
2. 先写契约失败测试，至少检查：

- 每条能力至少有一个有效证据引用。
- 合法要求权重之和为 100。
- 风险条件的权重为 0，状态为 `POLICY_EXCLUDED`。
- 匹配分为 77，材料覆盖度为 85。
- 合成材料不得出现真实手机号、身份证号、邮箱或学校姓名。

3. 运行并确认失败：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_contracts.py -q
```

4. 使用 Pydantic 实现输入、输出和状态枚举校验；所有 API 返回 `schema_version: "1.0"`。
5. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

6. 提交：

```powershell
git add demo/src/campusmatch/contracts.py demo/config demo/fixtures demo/tests/test_contracts.py
git commit -m "feat: define evidence-first data contracts"
```

**验收**：修改任一证据 ID、状态或权重后，测试会明确指出字段路径。

### 任务 3：文档转 Markdown 与 Profile Agent 内核

**涉及文件**

- 新增：`demo/src/campusmatch/services/document_service.py`
- 新增：`demo/src/campusmatch/services/profile_service.py`
- 新增：`demo/src/campusmatch/lib/line_index.py`
- 新增：`demo/tests/test_profile.py`

**步骤**

1. 先写测试覆盖：Markdown/TXT、DOCX、文本型 PDF、空文件、超限文件和扫描 PDF 无文本层。
2. 上传限制固定为：一次 1 个文件、最大 5 MB、仅 `.md/.txt/.docx/.pdf`。
3. DOCX 用 `python-docx` 提取段落和表格纯文本，不执行宏、不加载外部资源，也不把文档 HTML 注入页面。
4. PDF 用 `pypdf` 提取文本；没有文本层时返回 `DOCUMENT_OCR_REQUIRED`，提供“粘贴文字”替代入口，不自动编造内容。
5. 规范化换行并生成不可变的带行号 Markdown；原文件只读，后续修订生成新版本。
6. Profile 先采用“词典＋证据模式”的确定性提取：课程展示→沟通表达，Excel 名单→办公与信息处理，通知/签到→活动执行，访客答疑→服务沟通。
7. 每张经历卡显示：系统理解、原文、来源、确认开关、修改入口。
8. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_profile.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

9. 提交：

```powershell
git add demo/src/campusmatch/services/document_service.py demo/src/campusmatch/services/profile_service.py demo/src/campusmatch/lib/line_index.py demo/tests/test_profile.py
git commit -m "feat: extract grounded student profile"
```

**验收**：点击能力可回到正确行；未确认经历不进入后续匹配；解析失败可继续粘贴文本。

### 任务 4：Job Agent 内核和公平风险隔离

**涉及文件**

- 新增：`demo/src/campusmatch/services/job_service.py`
- 新增：`demo/tests/test_job.py`
- 修改：`demo/config/policy-rules.json`

**步骤**

1. 先写测试覆盖四类要求：`MUST`、`BONUS`、`AMBIGUOUS`、`POLICY_RISK`。
2. 模糊描述转为行为问题，例如“抗压能力强”转为“请举例说明计划临时变化时你如何调整任务”。
3. 性别、民族、宗教、婚育、与工作无关的健康条件只做风险提示；不得据此推断违法结论，也不得参与匹配。
4. 区分三个用户模式；MVP 对 `job_search` 完整处理，`career_change` 和 `explore` 返回清晰的范围提示。
5. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_job.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

6. 提交：

```powershell
git add demo/src/campusmatch/services/job_service.py demo/config/policy-rules.json demo/tests/test_job.py
git commit -m "feat: classify job requirements and policy risks"
```

**验收**：“女性优先”只能出现在风险区；合法要求重新归一化为 100；界面不把它显示为学生缺口。

### 任务 5：Match Agent 的可解释计分

**涉及文件**

- 新增：`demo/src/campusmatch/services/match_service.py`
- 新增：`demo/tests/test_match.py`

**步骤**

1. 先写失败测试，固定断言：

```python
assert result.match_score == 77
assert result.evidence_coverage == 85
assert next(x for x in result.items if x.label == "内容发布").state == "NO_EVIDENCE"
assert not any(x.state == "POLICY_EXCLUDED" and x.counted for x in result.items)
```

2. 实现纯函数 `calculateMatch(profile, job)`；函数不得调用模型。
3. 明确区分：

- `NO_EVIDENCE`：当前材料没写，不能说用户不会。
- `GAP`：用户明确说不会、测验未通过或证据与要求相反。
- `CONFLICT`：材料相互冲突，转人工。

4. 输出五维图数据和逐项证据矩阵；环形图表示匹配度，材料覆盖度单独显示。
5. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_match.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

6. 提交：

```powershell
git add demo/src/campusmatch/services/match_service.py demo/tests/test_match.py
git commit -m "feat: calculate explainable evidence match"
```

**验收**：评委可手算复核 77/85；页面明确写“不是录用概率”。

### 任务 6：Coach 建议、模拟面试与 Audit 门禁

**涉及文件**

- 新增：`demo/src/campusmatch/services/coach_service.py`
- 新增：`demo/src/campusmatch/services/audit_service.py`
- 新增：`demo/tests/test_coach_audit.py`
- 修改：`demo/config/emergency-contacts.example.json`

**步骤**

1. 先写失败测试：正常建议通过；注入“提升 30%”被阻断；新增“独立策划大型活动”被阻断；敏感信息输出被脱敏；未配置地区时不得生成紧急号码。
2. Coach 每条简历建议必须包含：原句、建议句、使用的证据 ID、是否需要用户确认。
3. 学习计划只针对 `NO_EVIDENCE/GAP`，并区分“补证据”和“补能力”。
4. 模拟面试首版使用固定题库＋证据追问，保存回答但不进行人格或心理诊断。
5. Audit 按顺序检查：

```text
授权 → Schema → 证据引用 → 新数字/新事实 → 隐私 → 公平 → 运行记录 → 人工审批
```

6. 危机信号只触发简短支持和地区配置，不输出“你患有抑郁症”等诊断；电话号码只能来自部署配置。
7. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_coach_audit.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

8. 提交：

```powershell
git add demo/src/campusmatch/services/coach_service.py demo/src/campusmatch/services/audit_service.py demo/config/emergency-contacts.example.json demo/tests/test_coach_audit.py
git commit -m "feat: add grounded coaching and audit gate"
```

**验收**：任何无证据事实都使 `export_allowed=false`；Audit 说明阻断原因和修复动作。

### 任务 7：四步网页与可视化

**涉及文件**

- 新增：`demo/src/campusmatch/static/index.html`
- 新增：`demo/src/campusmatch/static/app.css`
- 新增：`demo/src/campusmatch/static/app.js`
- 新增：`demo/src/campusmatch/workflow.py`
- 修改：`demo/src/campusmatch/main.py`
- 新增：`demo/tests/test_workflow.py`

**步骤**

1. 先写状态机测试：未确认画像不能匹配；Audit 阻断不能导出；修复后必须重新审计；重复导出只产生一个产物。
2. 实现单页四步向导：

```text
① 提交材料 → ② 选择目标 → ③ 确认经历 → ④ 获取报告
```

3. 首屏提供两个大按钮：“使用演示案例”和“上传我的材料”；技术详情折叠。
4. 报告页实现：CSS 环形图、五维雷达图、状态图标、证据抽屉。图表必须同时有文字和表格替代，不能只靠颜色表达。
5. 错误提示采用“双层信息”：自然语言说明＋可展开错误码。
6. 使用浏览器 `textContent` 渲染用户材料；不得直接把 DOCX 转换出的 HTML 注入 DOM。
7. 运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_workflow.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn campusmatch.main:app --app-dir src --host 0.0.0.0 --port 3100
```

8. 手动验收：键盘可完成流程；125% 缩放无横向溢出；1366×768 能看清主操作；风险不只靠红色表示。
9. 提交：

```powershell
git add demo/src/campusmatch/static demo/src/campusmatch/workflow.py demo/src/campusmatch/main.py demo/tests/test_workflow.py
git commit -m "feat: build accessible four-step demo UI"
```

**验收**：非技术用户不接触代码、提示词、模型选择和 API Key。

### 任务 8：报告、Trace 与一键复现

**涉及文件**

- 新增：`demo/src/campusmatch/services/export_service.py`
- 新增：`demo/src/campusmatch/lib/trace_store.py`
- 新增：`demo/scripts/start-demo.ps1`
- 新增：`demo/scripts/verify-demo.ps1`
- 修改：`demo/README.md`

**步骤**

1. Trace 采用追加式 JSONL，每条记录至少含：`trace_id`、`task_id`、`actor`、`input_refs`、`output_ref`、`state_before`、`state_after`、`timestamp`、`retry_count`。
2. 导出产生 `report.md`、`audit.json`、`trace.jsonl`；浏览器打印作为 PDF 演示方式，首版不再安装 PDF 生成器。
3. `start-demo.ps1` 自动定位 `demo/.venv/Scripts/python.exe`、检查依赖、启动 Uvicorn 并打开浏览器；脚本不得自动读取或上传真实简历。
4. `verify-demo.ps1` 执行预检、全部测试、固定案例 API 和产物校验，失败时返回非零退出码。
5. 运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-demo.ps1
```

6. 提交：

```powershell
git add demo/src/campusmatch/services/export_service.py demo/src/campusmatch/lib/trace_store.py demo/scripts demo/README.md
git commit -m "feat: add auditable export and one-click reproduction"
```

**验收**：一条命令复现；报告中的每个关键结论都能追溯；同一幂等键不产生重复报告。

### 任务 9：把 REST 内核注册为 HiClaw MCP 工具

**涉及文件**

- 新增：`demo/agentteams/mcp-campusmatch.yaml`
- 新增：`demo/scripts/register-hiclaw.ps1`
- 修改：`demo/src/campusmatch/main.py`

**暴露工具**

| MCP Tool | REST Endpoint | 责任 |
|---|---|---|
| `profile_materials` | `POST /api/v1/profile` | 生成证据化画像 |
| `parse_job` | `POST /api/v1/job` | 拆分岗位要求和风险 |
| `match_evidence` | `POST /api/v1/match` | 计算 77/85 和逐项理由 |
| `generate_coaching` | `POST /api/v1/coach` | 生成有证据的建议与面试题 |
| `audit_export` | `POST /api/v1/audit` | 审计并控制导出 |
| `get_task_status` | `GET /api/v1/tasks/{task_id}` | 支持重试和恢复 |

**步骤**

1. 所有工具要求 `task_id` 和 `schema_version`，写操作要求 `idempotency_key`。
2. API 使用随机本地访问令牌；令牌只保存在 `demo/.env.local` 和 Higress 配置中，不进入 Git、日志、PPT或聊天消息。
3. `mcp-campusmatch.yaml` 的 API 地址使用：

```text
http://host.docker.internal:3100/api/v1/...
```

4. 启动 Demo 后，在 HiClaw Manager 容器中通过官方脚本注册自定义 MCP 服务；脚本内部完成授权，不能直接调用 Controller REST API。
5. 等待网关配置生效后，在 Manager 容器内验证：

```bash
mcporter list
mcporter list campusmatch --schema
mcporter call campusmatch.get_task_status task_id=demo-s001
```

6. 至少真实调用一个工具并验证响应；失败时不得继续推送给 Worker。
7. 提交：

```powershell
git add demo/agentteams/mcp-campusmatch.yaml demo/scripts/register-hiclaw.ps1 demo/src/campusmatch/main.py
git commit -m "feat: expose CampusMatch tools through HiClaw gateway"
```

**验收**：Manager 能通过 `mcporter` 发现六个工具；无令牌调用被拒绝；工具响应通过同一 Pydantic 契约。

### 任务 10：创建六个角色与 AgentTeam

此任务会创建容器、Matrix 账号、房间和网关消费者，执行前必须由用户确认以下四项：名称、运行时、SOUL 角色、Skills。

**推荐配置**

| 名称 | 类型 | Runtime | 自定义 Skill |
|---|---|---|---|
| `career-navigator` | Team Leader / 通用 Agent | `openclaw` | `campusmatch-orchestrate` |
| `profile-agent` | Worker | `openclaw` | `campusmatch-profile` |
| `job-agent` | Worker | `openclaw` | `campusmatch-job` |
| `match-agent` | Worker | `openclaw` | `campusmatch-match` |
| `coach-agent` | Worker | `openclaw` | `campusmatch-coach` |
| `audit-agent` | Worker | `openclaw` | `campusmatch-audit` |

所有 Worker 自动包含 `file-sync`、`task-progress` 和 `project-participation`。默认不启用 Worker 之间随意互相 @mention，避免消息循环；团队交流由 Leader 组织。

**SOUL 共同约束**

- 明确“你是 AI Agent，不是人类”。
- 不泄露密钥、密码、令牌和个人信息。
- 不访问角色任务之外的文件与工具。
- 不虚构经历，不把缺证据写成缺能力。
- Audit 的阻断结论不能被其他 Agent 覆盖。
- 紧急风险不诊断，联系方式只读地区配置。

**步骤**

1. 编写六个 SOUL 和六个 `SKILL.md`；每个 Skill 写明 `name`、`description`、`assign_when`、输入、步骤、工具、失败处理和完成条件。
2. 将自定义 Skill 同步到 Manager 的 `~/worker-skills/`。
3. 通过 `agt create worker --no-wait ... -o json` 创建六个 Worker；不得直接调用 Controller REST API。
4. 每 5–10 秒使用以下命令查看状态，不重复创建：

```bash
agt get workers -o json
```

5. 全部进入 `Running` 后，推送对应 Skill 和 MCP 授权。
6. 创建团队：

```bash
agt create team \
  --name campusmatch-demo \
  --leader-name career-navigator \
  --workers profile-agent,job-agent,match-agent,coach-agent,audit-agent \
  --description "Evidence-grounded campus career support demo"
```

7. 验证：

```bash
agt get workers -o json
agt get teams campusmatch-demo -o json
```

8. 在 Element 中给 Career Navigator 发送固定案例任务，并要求五个 Worker 按角色调用对应工具。
9. 提交角色与 Skill 定义：

```powershell
git add demo/agentteams
git commit -m "feat: define CampusMatch HiClaw agent team"
```

**验收**：六个 Worker 为 `Running`；团队状态正常；每个 Worker 只调用授权工具；Leader 能处理失败和人工确认。

### 任务 11：端到端演练和证据包

**涉及文件**

- 新增：`demo/tests/test_e2e_offline.py`
- 新增：`demo/docs/演示脚本.md`
- 新增：`demo/docs/验收记录.md`
- 生成但不提交真实数据：`demo/artifacts/*`

**步骤**

1. 离线正常路径：选择演示案例→确认经历→解析 JD→77/85→Audit PASS→人工批准→导出。
2. 离线异常路径：注入“提升 30%”→Audit BLOCK→删除虚构数字→重新审计→PASS。
3. 在线路径：在 Element @Career Navigator→查看五个 Worker 调用→收到审计结果→人工批准。
4. 故障路径：停止或模拟 MCP 不可用→状态为 `NEEDS_INPUT/FAILED`→网页保留草稿→明确切换离线模式。
5. 运行最终验证：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File scripts/verify-demo.ps1
git diff --check
git status --short
```

6. 将实测结果写入验收记录；未测项目标记“未验证”，不能写成已实现。
7. 提交：

```powershell
git add demo/tests/test_e2e_offline.py demo/docs
git commit -m "test: verify CampusMatch end-to-end demo"
```

**验收**：3–5 分钟可讲完；正常、阻断、修复三段完整；所有展示数据明确为合成数据。

## 7. 第一天的最小行动顺序

如果今天只投入 2–3 小时，按下面顺序做，不要先做全部 Agent：

1. 完成任务 0–2，用已选 Python 创建 `demo/.venv`，搭好 FastAPI、健康检查、合成数据和契约。
2. 完成任务 5 的纯函数，让 `77/85` 自动测试先通过。
3. 做任务 7 的最小页面，先实现“使用演示案例→查看匹配报告”。
4. 运行 `.\.venv\Scripts\python.exe -m pytest -q` 并在浏览器完整走一遍。
5. 保存截图。此时已经有一个不会因模型失败而中断的演示骨架。

第二天再做文档解析、Coach、Audit；第三天接 HiClaw 和 Element。不要先创建六个空 Worker 再临时决定它们做什么。

## 8. 风险与降级

| 风险 | 识别方式 | 降级动作 |
|---|---|---|
| 模型不可用 | 网关请求失败或超时 | 保留草稿，切离线规则，显示降级标识 |
| DOCX 含危险链接 | 转换器输出链接/HTML | 只提取纯文本，禁用外部文件访问 |
| 扫描 PDF 无文本 | 文本长度低于阈值 | 返回 OCR 提示，允许粘贴文字 |
| Agent 输出不符合 Schema | Pydantic 校验失败 | 最多重试两次，再转人工 |
| Worker 创建长期 Pending | 超过 90 秒 | 查看 `message`，不重复创建 |
| Audit 被绕过 | 导出请求没有有效审计 ID | 返回 `APPROVAL_REQUIRED` |
| 敏感条件影响评分 | 条件类别为风险且 `counted=true` | 测试失败并阻断报告 |
| 真实数据误提交 | Git 预检检测上传目录或 PII | 阻止提交，删除或改用合成数据 |

## 9. 演示时的操作顺序

1. 双击 `start-demo.ps1`，打开学生网页。
2. 点击“使用演示案例”，说明无需准备标准简历。
3. 展示课程、社团、志愿服务如何变成带原文的能力卡。
4. 展示 JD 四类拆分及风险条件隔离。
5. 展示 77 分环形图、85% 材料覆盖度和逐项证据。
6. 注入无证据的“提升 30%”，展示 Audit 阻断导出。
7. 修复后人工批准并导出报告。
8. 打开 Element，展示同一工具内核被真实 AgentTeam 调用。
9. 最后说明：匹配度不是录用概率，系统服务学生决策而不替企业筛人。

## 10. 执行前需要的一次确认

代码任务 0–9 可以在当前项目内实施。Python 只安装到 `demo/.venv`；HiClaw 保持自身 Runtime，不在其容器内手工安装 Python。任务 10 会改变 HiClaw 运行状态，因此创建资源前确认以下推荐配置：

- Worker 名称：`career-navigator`、`profile-agent`、`job-agent`、`match-agent`、`coach-agent`、`audit-agent`。
- Runtime：全部使用当前默认 `openclaw`。
- SOUL：采用本计划中的角色边界和安全共同约束，由实现时补齐完整文本。
- Skills：每个 Worker 一个 CampusMatch 专属 Skill，并保留系统自动技能。
- Team：`campusmatch-demo`，Career Navigator 为 Leader。

确认后先实现离线网页和测试；到任务 10 时再执行 AgentTeams 的实际创建命令。
