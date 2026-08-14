# CampusMatch Demo 实机验收记录

验收日期：2026-08-14
环境：Windows 本机 Python 虚拟环境 + Docker HiClaw 分离部署
数据：完全合成的“林晓雨 / 综合运营实习生”案例

## 验收原则

本文只记录实际执行过的项目，不把设计目标写成实测结果。涉及令牌、管理员账号和真实个人信息的内容不进入记录。

## 本地服务

| 检查项 | 方法 | 结果 |
|---|---|---|
| Python 环境 | 根目录 `venv\Scripts\python.exe --version` | PASS |
| 依赖一致性 | `python -m pip check` | PASS |
| 自动化测试 | `python -m pytest demo\tests -q` | PASS，50 passed |
| HTTP 健康 | `GET /api/health` | PASS |
| 任务编号输入约束 | 含换行符的任务编号 | PASS，HTTP 422 |
| 浏览器桌面端 | 载入案例、分析、审批、导出 | PASS |
| 浏览器移动端 | 390×844 视口，无横向溢出 | PASS |
| 浏览器控制台 | errors/warnings | 0/0 |

## 业务结果

| 项目 | 实测值 | 解释 |
|---|---:|---|
| 岗位匹配度 | 77 | 固定规则下的证据匹配结果 |
| 证据覆盖度 | 85 | 当前材料对 JD 判断的证据充分度 |
| 风险条件 | `POLICY_EXCLUDED` | 不计入匹配分 |
| 审批前 Audit | `BLOCK` | 缺少人工批准 |
| 审批后 Audit | `PASS` | 可导出 Markdown |
| 源材料隐私门 | `PRIVACY_IN_SOURCE` | 检出手机号、身份证号或邮箱时阻止导出 |
| 风险计分回归门 | `POLICY_RISK_SCORED` | 风险条件一旦被误计分即阻止导出 |

## HiClaw / MCP

| 检查项 | 实测结果 |
|---|---|
| `mcp-campusmatch` 注册 | PASS，Manager 发现 6 个工具 |
| 六个 Worker MCP | PASS，全部状态 `ok` |
| 六个 Worker Skill | PASS，全部 SHA-256 一致 |
| Manager 六阶段烟雾测试 | PASS，77 / 85 / BLOCK→PASS / READY |
| Profile + Job 并行 Team 阶段 | PASS |
| Match Team 阶段 | PASS |
| Coach Team 阶段 | PASS，建议锚定真实证据，无虚构经历 |
| Audit Team 阶段 | PASS，返回预期 `BLOCK + APPROVAL_REQUIRED`，未绕过人工门 |
| 最终共享结果 | PASS，`STATUS=SUCCESS`，业务状态 `READY`，五阶段完整 |

真实 Team 任务 `team-live-001` 于 2026-08-14T09:05Z 完成，最终共享结果复核到：匹配分 77、证据覆盖率 85、`R-GENDER` 为 `POLICY_EXCLUDED`、`export_allowed=false`。任务 `meta.json` 已按 HiClaw finite task 流程更新为 `completed` 并同步到共享对象存储；Manager 当前无残留 active task。

最终发布烟雾任务 `smoke-release-20260814174133` 在最新审计实现上再次通过，结果为 77 / 85、Audit `BLOCK → PASS`、最终状态 `READY`。

## PPT 与提交材料

| 检查项 | 实测结果 |
|---|---|
| 页数与比例 | PASS，14 页、16:9 |
| 模板忠实度 | PASS，逐页沿用原模板布局并记录定点修改 |
| 文本溢出 | PASS，自动布局检查未发现越界 |
| 逐页视觉检查 | PASS，14 页逐页渲染核对 |
| 实机数据一致性 | PASS，PPT 与合成 JSON 均为 77 / 85；文档写作为“部分符合”，Excel 为“符合” |

## 已知限制

- 任务状态目前保存在 FastAPI 进程内存，服务重启后清空。
- 扫描 PDF 尚无 OCR。
- 当前业务抽取和评分为确定性 MVP 规则，不代表真实招聘效果。
- HiClaw Team 的模型执行速度受本地网关和模型服务影响；MCP 业务接口本身已有独立确定性烟雾测试。
- 生产环境仍需补充账号、权限、持久化、加密、数据删除和地区法律合规评审。

本文 HiClaw 项和测试数量均来自本次实机结果，不是预期值；如后续修改代码，应重新运行完整回归并更新数量。
