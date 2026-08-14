# Skill 清单与接口契约

## 1. 设计原则

- Skill 是可复用任务能力，不绑定某个 Agent 的自然语言提示词。
- 输入输出使用 JSON Schema；所有写操作包含幂等键。
- 工具凭据由网关或部署环境管理，Agent 不持有真实密钥。
- Skill 失败必须返回结构化错误，不以一段自然语言掩盖失败。
- 事实输出必须携带证据引用；高风险结果必须可阻断和升级。

## 2. 核心 Skill 清单

| Skill | 类型 | 使用场景 | 输入 | 输出 | 主要调用者 |
|---|---|---|---|---|---|
| `document-to-markdown@1` | 自定义 Skill＋文件工具 | 上传 PDF/DOCX 后生成可查看文本 | 文件引用、格式、OCR 策略 | Markdown、区块 ID、文件哈希、解析警告 | Profile |
| `resume-evidence-extraction@1` | 自定义 Skill | 从简历/课程/项目中提取能力证据 | Markdown、Schema、词典 | 画像字段、证据、置信度、未确认声明 | Profile |
| `jd-normalization@1` | 自定义 Skill | 将 JD 拆成统一要求 | JD 文本、来源、岗位模式 | 要求、职责、加分项、模糊字段 | Job |
| `jd-policy-scan@1` | 自定义 Skill＋政策规则 | 检测歧视、虚假或不当岗位条件 | 原 JD、规范化要求、规则版本 | 风险标记、排除项、人工审核项 | Job、Audit |
| `evidence-based-match@1` | 自定义 Skill | 逐条比较学生证据和岗位要求 | 画像、岗位、权重、策略 | 要求矩阵、维度分、匹配度、置信度 | Match |
| `score-explanation@1` | 自定义 Skill | 将数值与规则转成可理解原因 | 要求矩阵、分数、证据 | 解释文本、可视化数据、证据链接 | Match、Navigator |
| `grounded-resume-review@1` | 自定义 Skill | 生成不虚构的简历修改建议 | 简历证据、目标岗位、约束 | 建议、改写草稿、证据引用、风险 | Coach |
| `gap-to-action-plan@1` | 自定义 Skill | 将能力缺口转为学习和准备计划 | 缺口、时间、资源偏好 | 周/月计划、验收任务、优先级 | Coach |
| `mock-interview@1` | 自定义 Skill | 岗位模拟面试与查漏补缺 | 岗位、证据、轮次、回答 | 问题、反馈、缺口、候选新证据 | Coach |
| `pii-minimization@1` | 自定义 Skill | 识别和最小化个人信息 | 原文引用、处理目的 | 脱敏文本、敏感字段、保留理由 | Audit、Profile |
| `claim-grounding-audit@1` | 自定义 Skill | 检查事实是否有证据 | 产物、证据图、策略 | PASS/BLOCK、无证据声明、修复建议 | Audit |
| `content-safety-gate@1` | 自定义 Skill | 检测违法有害与危机信号 | 用户输入、生成内容、地区配置 | 风险等级、处置、升级要求 | Audit、Navigator |
| `report-export@1` | 自定义 Skill＋导出工具 | 生成求职报告 | 已审计产物、审批记录、模板 | PDF/Markdown、哈希、导出记录 | Navigator |
| `alibabacloud-sls-query` | 阿里云官方 Skill | 查询 Trace/Log 并生成评测统计 | SLS 项目、日志库、查询 | 结构化日志与统计 | Audit、管理员 |

## 3. 代表性接口契约

### 3.1 `document-to-markdown@1`

输入：

```json
{
  "artifact_ref": "artifact://resume/sha256-...",
  "content_type": "application/pdf",
  "ocr_mode": "auto",
  "retain_layout_blocks": true,
  "idempotency_key": "task-001-parse-resume"
}
```

输出：

```json
{
  "status": "SUCCESS",
  "markdown_ref": "artifact://resume/normalized.md",
  "source_hash": "sha256:...",
  "blocks": [{"id": "block-12", "line_start": 42, "line_end": 45}],
  "warnings": [],
  "parser_version": "1.0.0"
}
```

失败处理：格式不支持返回 `UNSUPPORTED_FORMAT`；OCR 置信度低返回 `NEEDS_INPUT`；同一幂等键不得重复创建文件。

安全边界：原始文件只读；默认不把正文写入普通日志；处理前检查用户授权。

复用价值：可用于合同、报告、申请材料等所有证据型 Agent 场景。

### 3.2 `evidence-based-match@1`

输入：

```json
{
  "profile_ref": "artifact://profiles/s001.json",
  "job_ref": "artifact://jobs/j001.json",
  "mode": "campus_job_search",
  "weights": {
    "professional": 0.30,
    "projects": 0.20,
    "tools": 0.15,
    "communication": 0.15,
    "preference": 0.20
  },
  "policy_version": "cn-recruitment-policy-2026.1"
}
```

输出：

```json
{
  "status": "SUCCESS",
  "fit_score": 76,
  "confidence": 0.82,
  "dimension_scores": {
    "professional": 80,
    "projects": 70,
    "tools": 85,
    "communication": 65,
    "preference": 78
  },
  "requirements": [
    {
      "requirement_id": "j001-r03",
      "state": "MATCH",
      "evidence_refs": ["resume:block-12"],
      "reason": "项目中使用 Python 完成数据处理"
    }
  ],
  "excluded_policy_items": []
}
```

失败处理：画像或岗位未通过 Schema 校验时拒绝计算；证据引用不存在时返回 `EVIDENCE_NOT_FOUND`；权重不等于 1 时返回 `INVALID_WEIGHTS`。

安全边界：输入中出现敏感属性时丢弃并记录；`POLICY_EXCLUDED` 要求不得计分。

复用价值：可用于校招、职业培训、人才发展，但不能直接用于自动淘汰。

### 3.3 `claim-grounding-audit@1`

输入：

```json
{
  "artifact_refs": ["artifact://reports/draft.json"],
  "evidence_graph_ref": "artifact://evidence/task-001.json",
  "required_coverage": 1.0,
  "block_numeric_claim_without_evidence": true
}
```

输出：

```json
{
  "decision": "BLOCK",
  "issues": [
    {
      "code": "UNGROUNDED_NUMERIC_CLAIM",
      "text": "将处理效率提升 30%",
      "evidence_refs": [],
      "severity": "high",
      "remediation": "删除该数字或补充经用户确认的原始证据"
    }
  ],
  "trace_complete": true,
  "next_action": "RETURN_TO_COACH"
}
```

失败处理：证据图不可用时默认 `BLOCK`，不以“审计失败”视为“审计通过”。

安全边界：Audit 只能阻断和建议修复，不能自行创造证据或修改原始材料。

## 4. 通用错误结构

```json
{
  "status": "ERROR",
  "error": {
    "code": "EVIDENCE_NOT_FOUND",
    "message": "引用的证据不存在",
    "retryable": false,
    "safe_to_show": true
  },
  "trace_id": "trace-001",
  "next_action": "NEEDS_INPUT"
}
```

错误码至少包括：

- `UNAUTHORIZED_SCOPE`
- `UNSUPPORTED_FORMAT`
- `OCR_LOW_CONFIDENCE`
- `SCHEMA_INVALID`
- `EVIDENCE_NOT_FOUND`
- `POLICY_RISK`
- `TOOL_TIMEOUT`
- `MODEL_OUTPUT_INVALID`
- `APPROVAL_REQUIRED`
- `EXPORT_BLOCKED`

## 5. 工具与 MCP/等价契约

| 工具能力 | Demo 实现 | 生产规划 | 鉴权 | 审计与降级 |
|---|---|---|---|---|
| 文件解析/OCR | 本地库或固定 Markdown | 私有文档服务/MCP | 本地目录最小权限 | 哈希、解析版本；失败人工上传文本 |
| 岗位数据 | 本地 JSON | 学校岗位库适配器/MCP | 只读 Token | 来源、抓取时间；失败使用缓存 |
| 政策与能力词典 | 本地版本化 YAML | RAG＋管理后台 | 只读 | 记录规则版本；不确定升级人工 |
| 共享文件 | 本地目录 | AgentTeams MinIO/PDS | 短期凭据 | 对象哈希；失败只读降级 |
| 模型调用 | OpenAI-compatible 可选 | 经 Higress 多模型路由 | 网关持有密钥 | 记录模型/耗时/Token；失败离线模板 |
| Trace/Log | JSONL | OpenTelemetry＋AgentLoop/SLS | 服务身份 | 脱敏；SLS 不可用时保留本地日志 |
| 报告导出 | 本地 Markdown/PDF | 报告服务/MCP | 审批后短期授权 | 产物哈希、审批人；失败保留草稿 |

## 6. Skill 质量与发布

- 每个 Skill 附 `SKILL.md`、Schema、示例、失败用例和安全说明。
- 版本发布前必须运行固定数据集和安全注入测试。
- Registry 保存 Skill 版本、依赖、兼容的 Agent Identity 与质量结果。
- 新版本先灰度给测试 Worker；失败可回滚到上一个通过评测的版本。
- 开源 Skill 不包含真实个人数据、学校内部规则或商业接口凭据。
