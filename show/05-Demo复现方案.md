# CampusMatch 简单 Demo 复现方案

## 1. Demo 目标

用一条 3–5 分钟的任务链证明以下能力，而不是追求完整招聘平台：

1. 多 Agent 有明确分工和结构化交接。
2. 学生能力与岗位结论可以回到原文证据。
3. 匹配度与判断置信度分开展示。
4. Coach 不得虚构经历，Audit 能阻止无证据输出。
5. 高风险结果进入人工审批并留下 Trace。

## 2. 双模式复现

### 2.1 离线确定性模式（初赛优先）

不需要模型 API。文档解析、画像和岗位输出使用固定夹具，匹配算法和 Audit 使用确定性规则，保证评委可以稳定复现。

适合：初赛材料演示、没有云额度、网络不稳定、回归测试。

### 2.2 在线 Agent 模式（入围后）

使用 AgentTeams Manager–Workers 实际编排，模型负责抽取和建议，所有输出经过 JSON Schema、证据引用和 Audit 门禁。

适合：复赛代码包、现场 Agent 协同、Element 房间观察与人工介入。

## 3. 建议目录结构

```text
campusmatch/
├─ README.md
├─ LICENSE
├─ .env.example
├─ docker-compose.yml
├─ app/
│  ├─ ui/                    # Streamlit 或轻量 Web UI
│  ├─ orchestrator/          # 离线编排适配器 / AgentTeams bridge
│  ├─ schemas/               # JSON Schema
│  └─ observability/         # JSONL / OpenTelemetry
├─ agents/
│  ├─ career-navigator/
│  ├─ profile-agent/
│  ├─ job-agent/
│  ├─ match-agent/
│  ├─ coach-agent/
│  └─ audit-agent/
├─ skills/
│  ├─ document-to-markdown/
│  ├─ resume-evidence-extraction/
│  ├─ jd-normalization/
│  ├─ evidence-based-match/
│  ├─ grounded-resume-review/
│  └─ claim-grounding-audit/
├─ fixtures/
│  ├─ students/
│  ├─ jobs/
│  ├─ policies/
│  └─ expected/
├─ artifacts/                # 运行产物，不提交真实个人信息
├─ traces/
└─ tests/
```

## 4. 固定样例数据

### 4.1 学生 S001（合成）

```markdown
# 陈同学（合成人物）

## 教育经历
某高校信息管理专业，本科三年级。

## 课程
Python 程序设计、数据库原理、统计学、数据可视化。

## 项目
校园消费数据分析：使用 Python/pandas 清洗 8,000 条合成数据，使用 SQL 完成分组统计，并制作可视化报告。本人负责数据清洗与图表制作。

## 求职偏好
数据分析实习；上海或杭州；每周可实习四天。
```

### 4.2 岗位 J001（合成）

```json
{
  "title": "数据分析实习生",
  "city": "上海",
  "requirements": [
    "熟悉 SQL 和 Python",
    "能使用 Excel 完成数据整理",
    "具备清晰的数据表达能力",
    "有 BI 工具经验者优先"
  ]
}
```

### 4.3 风险岗位 J004（合成）

固定测试中加入一条与岗位职责无关的性别偏好。Job/Audit 必须将其标记为 `POLICY_EXCLUDED`，不展示为学生能力缺口，也不计入匹配分。

### 4.4 幻觉注入

测试用 Coach 草稿加入：

> 通过项目将数据处理效率提升 30%。

学生材料没有这个数字。Audit 必须返回 `UNGROUNDED_NUMERIC_CLAIM` 并阻止导出。

## 5. 预期任务链

```text
1. Career Navigator 创建 task-001，记录同意范围
2. Profile Agent 生成 Markdown 和 4 条能力证据
3. Job Agent 规范化 5 个岗位，隔离 1 条风险条件
4. Match Agent 输出前三岗位和逐项证据矩阵
5. Coach Agent 生成简历/学习/面试建议
6. Audit Agent 发现无证据“提升 30%”，任务进入 BLOCKED
7. 用户删除虚构数字，Coach 重新生成
8. Audit PASS，老师点击批准
9. 系统导出 Markdown/PDF 和完整 Trace
```

## 6. 界面最小实现

只需要四个页面：

### 页面 A：材料与目标

- 选择“应届求职”模式。
- 上传/选择固定简历。
- 勾选授权范围。
- 输入城市、岗位方向和时间约束。

### 页面 B：证据化画像

- 左侧显示带行号 Markdown。
- 右侧显示能力列表。
- 点击能力跳转到对应原文。
- 允许用户确认、纠正或标记缺失。

### 页面 C：匹配报告

- 总体环形图和独立置信度。
- 五维雷达图。
- 岗位要求证据矩阵。
- Coach 的行动计划和一个模拟面试入口。

### 页面 D：审计与 Trace

- 展示虚构、隐私、歧视和证据覆盖检查。
- 展示 BLOCK → 修复 → PASS 的状态变化。
- 人工批准后出现导出按钮。

## 7. 可视化样例数据

```json
{
  "fit_score": 76,
  "confidence": 82,
  "radar": {
    "专业技能": 80,
    "项目经历": 70,
    "工具能力": 85,
    "协作表达": 65,
    "岗位偏好": 78
  },
  "requirements": [
    {"name": "Python", "state": "MATCH", "evidence": "resume:L10-L11"},
    {"name": "SQL", "state": "MATCH", "evidence": "resume:L10-L11"},
    {"name": "Excel", "state": "PARTIAL", "evidence": "course:L6"},
    {"name": "BI 工具", "state": "NO_EVIDENCE", "evidence": null}
  ]
}
```

上述数字是合成演示数据，不是模型实测准确率，也不是录用概率。

## 8. AgentTeams 实现映射

AgentTeams 官方项目当前提供 Manager–Workers、Matrix 协作、共享文件、Higress 网关和人工介入能力。建议复赛锁定明确版本并在 README 中记录镜像与安装方式。[AgentTeams 官方仓库](https://github.com/agentscope-ai/AgentTeams)

| CampusMatch 组件 | AgentTeams 映射 |
|---|---|
| Career Navigator | Manager |
| Profile/Job/Match/Coach/Audit | Workers |
| 任务链 | Manager 任务拆解＋Team Rooms |
| 文档和 JSON | Shared File System / MinIO |
| 人工观察与纠正 | Element/Matrix 房间 |
| 模型与 MCP 凭据 | Higress Gateway |
| Skill 分发 | Worker Skills / Nacos Registry 规划 |
| Trace | Matrix 事件＋应用 Trace＋AgentLoop/SLS 规划 |

## 9. 离线验收用例

| 编号 | 输入 | 预期 |
|---|---|---|
| T01 | 正常简历＋正常 JD | 生成带证据匹配报告 |
| T02 | 扫描 PDF 解析失败 | 状态 `NEEDS_INPUT`，不生成假画像 |
| T03 | 简历未提 BI | 标记 `NO_EVIDENCE`，不写“不会 BI” |
| T04 | JD 含风险性别条件 | 标记 `POLICY_EXCLUDED`，不计分 |
| T05 | Coach 注入“提升 30%” | Audit `BLOCK`，不能导出 |
| T06 | 用户补充新经历但未确认 | 进入候选证据，不写回正式画像 |
| T07 | 导出前无人工审批 | 返回 `APPROVAL_REQUIRED` |
| T08 | 同一导出请求重复发送 | 幂等，只产生一个产物 |

## 10. Demo 讲解脚本

1. “这不是替学生编简历的聊天机器人，而是高校可审计的求职任务闭环。”
2. 上传合成简历，展示原文件、Markdown 和证据对象。
3. 展示推荐岗位，但强调匹配度不是录用概率。
4. 点击 Python 能力，回到项目原文。
5. 展示风险 JD 条件被隔离。
6. 展示 Coach 的无证据数字被 Audit 拦截。
7. 人工确认修复版本，导出报告与 Trace。
8. 打开 AgentTeams/Element，说明 Manager–Workers 协作和人工介入映射。

## 11. 复现验收标准

- README 中一条命令启动离线 Demo。
- 不配置 API Key 也能完成固定任务链。
- 运行后生成 `report.md`、`audit.json`、`trace.jsonl`。
- 所有重要结论可找到有效 `evidence_ref`。
- 安全用例 T04/T05/T07 必须稳定通过。
- 若在线模型失败，系统明确降级，不把失败结果当作成功。
