# CampusMatch Demo 完整复现方案

## 1. 复现目标与边界

本 Demo 用一条 3–5 分钟的真实任务链证明：材料可追溯、岗位可解释、建议不虚构、风险条件被隔离、导出受人工审批控制，以及同一业务能力可由 HiClaw 多 Agent 调用。

它不是招聘网站，也不做自动录用、淘汰或候选人排名。匹配度只表示“当前材料对当前 JD 的证据覆盖”，`NO_EVIDENCE` 只表示材料中未找到证据。

## 2. 角色与运行位置

| 角色 | 需要做什么 | 是否需要 Python |
|---|---|---|
| 学生/评委 | 打开浏览器、上传材料、查看结果、人工确认、下载报告 | 否 |
| Demo 维护者 | 安装依赖、启动本机服务、运行测试 | 是，使用项目根目录 `venv` |
| HiClaw | 通过网关/MCP 调用本机 CampusMatch API | 否，无需在 Worker 内安装 Python |

Python 只用于搭建后端，不是最终用户的使用门槛。

## 3. 软件结构

```text
GOAI/
├─ requirements.txt
├─ venv/
├─ demo/
│  ├─ README.md
│  ├─ src/campusmatch/
│  │  ├─ main.py                 # FastAPI、静态页面和工具接口
│  │  ├─ contracts.py            # Pydantic 数据契约
│  │  ├─ workflow.py             # Profile→Job→Match→Coach→Audit
│  │  ├─ services/               # 确定性业务规则与报告导出
│  │  └─ static/                 # 无框架浏览器界面
│  ├─ tests/                     # 单元、契约、API、安全门禁测试
│  ├─ fixtures/                  # 合成学生与岗位样例
│  ├─ agentteams/                # MCP、Skills、Souls 和容器脚本
│  └─ scripts/                   # Windows 启动与 HiClaw 配置脚本
└─ show/                         # 初赛材料、PPT 和验收记录
```

## 4. 浏览器 Demo 复现

### 4.1 首次准备

在项目根目录执行：

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python -m pytest demo\tests -q
```

如果 PowerShell 阻止激活脚本，可直接使用虚拟环境解释器：

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pytest demo\tests -q
```

### 4.2 启动

```powershell
.\demo\scripts\start-demo.ps1
```

检查健康状态：

```powershell
Invoke-RestMethod http://127.0.0.1:3100/api/health
```

预期返回包含 `status: ok`。浏览器打开 `http://127.0.0.1:3100`。

### 4.3 最短演示路径

1. 点击“载入合成案例”。
2. 确认模式为“应届/实习求职”，授权框已勾选。
3. 点击“开始证据化分析”。
4. 展示两个环形指标：匹配度 77、证据覆盖度 85。
5. 展示每项要求的“符合／部分符合／缺少证据”，点击或口述证据行号。
6. 展示“女性优先”风险条件被标记为 `POLICY_EXCLUDED`，未进入分数。
7. 展示 Audit 为 `BLOCK`，导出按钮不可用。
8. 勾选“我已检查并批准本次导出”，点击“提交审计”。
9. Audit 变为 `PASS`，点击导出 Markdown 报告。

### 4.4 自有材料路径

- 支持 `.md`、`.txt`、`.docx`、可提取文本的 `.pdf`。
- 单文件最大 5 MiB。
- 上传后先显示 Markdown，用户可直接修正文本再分析。
- 扫描 PDF 暂无 OCR，返回 `PDF_TEXT_NOT_FOUND`，用户可改传 DOCX/TXT 或手动粘贴。
- 不支持的扩展名返回结构化错误，不进入分析链。

## 5. 确定性合成案例

样例文件：

- 学生材料：`demo/fixtures/student-materials.md`
- 岗位 JD：`demo/fixtures/job-general-operations.md`

合成人物“林晓雨”只有课程小组汇报、社团报名与志愿服务经历。系统可从原文提取沟通表达、文档写作、办公与信息处理、活动执行与协作四类能力，并保留逐条证据。

岗位为“综合运营实习生”，包含办公软件、沟通、活动支持等要求，并故意加入与职责无关的性别条件。固定预期为：

```json
{
  "match_score": 77,
  "evidence_coverage": 85,
  "policy_condition": "POLICY_EXCLUDED",
  "audit_before_approval": "BLOCK",
  "audit_after_approval": "PASS",
  "final_status": "READY"
}
```

固定结果用于回归与现场稳定演示，不代表录用概率。

## 6. 五个业务 Agent 与通用编排

| Agent | 输入 | 输出 | 不允许做的事 |
|---|---|---|---|
| Profile | 用户 Markdown | 能力、证据、行号 | 无证据推断能力 |
| Job | JD Markdown、使用模式 | 硬性/加分/职责/风险条件 | 把歧视条件当作正常要求 |
| Match | Profile + Job | 分数、覆盖度、逐项状态、五维值 | 只给黑盒分数 |
| Coach | 真实材料、匹配缺口 | 简历、学习、面试建议 | 虚构经历、数字或技能 |
| Audit | 全部阶段输出、人工批准状态 | PASS/BLOCK、风险项、导出门禁 | 绕过人工批准 |
| Career Navigator | 用户目标与阶段状态 | 共情说明、编排、重试、人工交接 | 作出招聘决定或诊断心理疾病 |

情绪支持采用分级策略：一般低落提供支持和可执行小步骤；疑似危机只提示寻求现实支持与本地紧急帮助，不进行医学诊断。紧急号码必须按用户所在地动态确认，不能把单一地区号码硬编码为全球适用。

## 7. HiClaw MCP 复现

前提：`agentteams-manager`、`agentteams-controller` 和六个 `agentteams-worker-*` 容器在线，本机 Demo 正在运行。

### 7.1 注册 MCP

```powershell
.\demo\scripts\register-hiclaw.ps1
```

脚本注册实际服务名 `mcp-campusmatch`，随机令牌只写入被 Git 忽略的 `demo/.env.local`。验证：

```powershell
docker exec agentteams-manager mcporter list mcp-campusmatch --schema
```

预期发现六个工具：`profile_materials`、`parse_job`、`match_evidence`、`generate_coaching`、`audit_export`、`get_task_status`。

### 7.2 配置 Worker 与 Skill

```powershell
.\demo\scripts\configure-worker-mcp.ps1
.\demo\scripts\sync-worker-skills.ps1
```

第一条命令使用每个 Worker 已有的网关身份生成本地 `mcporter` 配置；第二条命令运行官方 Skill 推送并做容器兼容同步，最后比较 SHA-256。预期六个 Worker 均显示 `MCP_HEALTHY` 和 `SYNCED`。

### 7.3 六阶段 MCP 烟雾测试

```powershell
.\demo\scripts\smoke-hiclaw.ps1 -TaskId smoke-campusmatch-001
```

预期输出：

```text
profile PASS
job PASS
match_score 77
evidence_coverage 85
audit_gate [BLOCK,PASS]
final_status READY
```

此测试不依赖模型推理，专门验证网关、MCP、Schema、幂等键和业务 API。

### 7.4 真实 Agent Team 委派

```powershell
.\demo\scripts\delegate-team-smoke.ps1 -TaskId team-live-001
```

编排顺序：

```text
Career Navigator
  ├─ Profile Agent ─┐
  └─ Job Agent ─────┴─> Match Agent -> Coach Agent -> Audit Agent
```

Profile 与 Job 可以并行；后续阶段必须读取同一 `task_id` 的已完成状态。Team Room 消息、Worker 日志、共享任务文件和 MCP 状态共同构成可回放 Trace。

查询业务状态：

```powershell
docker exec agentteams-manager bash -lc "source /opt/hiclaw/scripts/gateway-api.sh >/dev/null 2>&1; timeout 15s mcporter call mcp-campusmatch.get_task_status task_id:team-live-001 --output json"
```

## 8. 审计和失败处理

| 场景 | 预期行为 | 是否可导出 |
|---|---|---|
| 材料没有某技能证据 | 标记 `NO_EVIDENCE`，不写“用户不会” | 视其他审计项决定 |
| JD 含年龄/性别等无关条件 | `POLICY_EXCLUDED`，不计分 | 可继续，但保留风险记录 |
| Coach 写入无依据数字 | `UNGROUNDED_*`，Audit `BLOCK` | 否 |
| 未人工批准 | `APPROVAL_REQUIRED`，Audit `BLOCK` | 否 |
| 扫描 PDF 无文本层 | `PDF_TEXT_NOT_FOUND`，要求补充材料 | 否 |
| MCP/Worker 暂时失败 | 保留 task_id，使用幂等键重试 | 否，直到阶段完整 |
| 服务重启 | 内存任务状态清空，需重新运行 | 旧任务不可导出 |

## 9. 最低验收标准

必须同时满足：

1. `python -m pip check` 无依赖冲突。
2. 全部自动化测试通过。
3. `/api/health` 返回成功。
4. 合成案例稳定得到 77/85。
5. Profile 每项能力都能回到原文证据。
6. 风险条件不参与匹配。
7. 未审批不能导出，审批后能够导出。
8. 浏览器桌面端和 390px 移动端无横向溢出，控制台无错误。
9. Manager 和六个 Worker 都能发现 `mcp-campusmatch`。
10. MCP 烟雾测试通过；真实 Team 至少完成五个专业阶段并留下结果。

## 10. 生产化前必须补齐

- 数据库和对象存储持久化；
- 用户账号、最小权限和学校组织隔离；
- 数据加密、留存期限、撤回同意和删除；
- OCR、恶意文件检测和上传隔离；
- 模型输出 Schema 校验、超时、重试、熔断和成本限制；
- 公平性、证据一致性、不同专业覆盖率和人工复核评测；
- 根据部署地区复核就业、个人信息、反歧视和心理危机提示的法律合规性。

因此，当前 Demo 的正确表述是“可运行、可复现的本地 MVP 与 Agent Infra 证明”，不是“已上线的自动招聘系统”。
