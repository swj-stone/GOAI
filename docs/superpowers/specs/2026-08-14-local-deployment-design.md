# CampusMatch 本地部署与 GitHub README 设计规格

## 1. 目标

把当前已经能够运行的 CampusMatch Demo 整理成可从 GitHub 下载后本地部署、直接访问和直接调用的项目。普通体验者只使用浏览器；部署者可选择 Windows PowerShell 或 Docker Compose；开发者和 HiClaw Worker 通过同一组 REST/MCP 接口调用服务。

验收后的固定入口为：

- 浏览器：`http://127.0.0.1:3100`
- OpenAPI：`http://127.0.0.1:3100/docs`
- 健康检查：`http://127.0.0.1:3100/api/health`

## 2. 部署策略

采用混合部署：

1. Windows PowerShell 是首选路径。根目录脚本完成环境检查、虚拟环境创建、依赖安装、服务启动和停止。
2. Docker Compose 是备用路径。它不要求宿主机安装 Python，并提供一致的容器运行环境。
3. 两种路径启动同一个 FastAPI 应用，不维护两套业务实现。
4. HiClaw 继续通过 `host.docker.internal:3100` 和 `mcp-campusmatch` 调用宿主机服务。

## 3. 运行架构

```text
浏览器用户 ───────────────┐
REST API 调用者 ──────────┼─> 127.0.0.1:3100 / FastAPI
HiClaw Worker / MCP ──────┘           │
                                      ├─ Profile
                                      ├─ Job
                                      ├─ Match
                                      ├─ Coach
                                      ├─ Audit
                                      └─ Markdown 报告
```

FastAPI 同时提供静态网页、业务 API、Worker 工具 API 和 OpenAPI 文档。所有业务规则继续复用 `demo/src/campusmatch`；部署脚本不得复制或改写业务逻辑。

## 4. 文件边界

### 新增文件

- `README.md`：GitHub 仓库首页式中文文档，是唯一主入口。
- `setup-local.ps1`：检查 Python 3.13、创建根目录 `venv`、安装 `requirements.txt`、执行依赖检查。
- `run-local.ps1`：必要时调用安装脚本，在指定端口启动服务，等待健康检查，可选择后台运行和打开浏览器。
- `stop-local.ps1`：只停止由本项目启动且占用指定端口的 CampusMatch 服务；身份不匹配时拒绝终止。
- `Dockerfile`：创建非 root 的 Python 3.13 运行镜像，只复制运行所需源码、固定依赖和合成 fixtures。
- `compose.yaml`：把容器端口 3100 绑定到宿主机 `127.0.0.1`，包含健康检查和可选 MCP 令牌。
- `.dockerignore`：排除 Git、虚拟环境、缓存、上传物、临时文件、真实凭据和参赛材料。
- `demo/tests/test_local_deployment_assets.py`：验证 README 命令、PowerShell 入口、Docker 安全边界和 Compose 健康检查。

### 修改文件

- `.gitignore`：忽略本地运行状态目录和根目录环境文件。
- `demo/README.md`：缩减为 Demo 技术细节，并明确根目录 `README.md` 是部署入口。
- `demo/scripts/start-demo.ps1`：保留为底层兼容入口；根目录脚本负责面向用户的完整生命周期。
- `show/05-Demo复现方案.md`：同步最终公开部署命令，避免答辩材料与仓库 README 不一致。
- `show/19-Demo实机验收记录.md`：追加 PowerShell 和 Docker 的实机结果。

## 5. PowerShell 行为

### `setup-local.ps1`

- 从脚本所在目录确定项目根目录，不依赖调用者当前目录。
- 优先使用 `py -3.13`，其次使用可验证为 Python 3.13 或更高版本的 `python`。
- 缺少合格 Python 时停止，给出清晰的安装提示，不自动申请管理员权限或静默安装系统软件。
- 根目录 `venv` 不存在时执行 `python -m venv venv`；存在时直接复用。
- 使用 `venv\Scripts\python.exe -m pip install -r requirements.txt` 安装依赖，再运行 `pip check`。
- 任一命令失败时以非零状态退出，不打印环境变量或令牌。

### `run-local.ps1`

- 参数：`-Port`，默认 `3100`；`-Foreground`；`-NoBrowser`；`-SkipSetup`。
- 未指定 `-SkipSetup` 时，如虚拟环境或核心依赖缺失，自动调用 `setup-local.ps1`。
- 端口已有健康的 CampusMatch 服务时幂等成功，不重复启动。
- 端口被其他程序占用时明确报错，不杀死未知进程。
- 默认后台启动，日志写入忽略的 `.campusmatch/run/`；最多等待 30 秒，只有 `/api/health` 返回 `status=ok` 后才报告成功。
- 默认打开浏览器；自动化和服务器环境可使用 `-NoBrowser`。
- `-Foreground` 使用当前终端运行，支持 `Ctrl+C` 停止。

### `stop-local.ps1`

- 参数：`-Port`，默认 `3100`。
- 从端口对应的运行记录读取进程信息，例如 3100 端口使用 `.campusmatch/run/3100.json`。
- 同时核对健康响应、监听端口和记录的进程身份；无法确认是 CampusMatch 时拒绝终止。
- 停止成功后删除对应运行记录；服务本来就未运行时幂等成功。

## 6. Docker 行为

- 构建基于 `python:3.13-slim`。
- 安装根目录固定版本依赖后，以非 root 用户运行 Uvicorn。
- 容器内监听 `0.0.0.0:3100`，Compose 仅发布到宿主机 `127.0.0.1`。
- `compose.yaml` 使用 `/api/health` 做健康检查：5 秒间隔、2 秒超时、最多 12 次、5 秒启动宽限期。
- 默认不挂载真实简历、不持久化任务状态，也不把本地环境文件复制进镜像。
- 浏览器演示可直接运行 `docker compose up --build -d`。
- HiClaw 模式通过 `CAMPUSMATCH_MCP_TOKEN` 注入令牌；令牌只来自本地环境或被 Git 忽略的文件。

## 7. README 信息架构

根目录 `README.md` 使用中文 GitHub 项目首页风格，按以下顺序组织：

1. 项目名称、一句话定位、当前可运行状态和安全边界。
2. 功能亮点与 77 / 85 合成案例说明。
3. 三分钟快速开始：PowerShell 主路径。
4. Docker Compose 路径。
5. 浏览器操作步骤。
6. REST API 直接调用示例，分别提供 PowerShell 和通用 `curl`。
7. HiClaw 六 Worker / MCP 接入步骤。
8. 项目目录结构和关键源码索引。
9. 测试、健康检查和停止服务命令。
10. 常见错误：Python 版本、执行策略、端口冲突、Docker 未启动、扫描 PDF、HiClaw MCP 401。
11. 隐私、公平、人工审批和非招聘决策声明。
12. 已知限制与生产化路线。

README 不声称真实招聘效果，不包含真实令牌、账号、个人信息、虚构徽章或不存在的许可证。

## 8. 调用与数据流

### 浏览器

用户上传文件或粘贴 Markdown，网页调用 `/api/v1/documents/convert` 和 `/api/v1/analyze`。Audit 未通过时导出接口保持 409；人工确认后重新分析并导出报告。

### REST API

README 的最短调用使用 `/api/v1/demo/run`，确保复制命令即可得到结构化 JSON。完整自有材料调用指向 `/docs` 和 `/api/v1/analyze` 示例。

### HiClaw

Manager 注册 `mcp-campusmatch`，六个 Worker 使用各自网关身份调用同一 FastAPI 服务。Profile 与 Job 可并行，Match、Coach、Audit 按依赖推进；Audit 后才查询最终 `READY`。

## 9. 错误处理

- 安装失败：保留 pip 原始退出码，并打印可执行的重试命令。
- 健康检查超时：停止本次新启动的进程，输出日志文件路径。
- 端口冲突：只报告监听端口和处理建议，不自动终止未知程序。
- Docker 构建或健康检查失败：README 给出 `docker compose logs campusmatch`。
- MCP 401：检查服务与 Manager 是否使用同一令牌，但任何脚本都不得回显令牌。
- 文档错误继续返回现有结构化代码，例如 `DOCUMENT_TOO_LARGE` 和 `PDF_TEXT_NOT_FOUND`。

## 10. 测试与验收

### 自动化

- 现有 Python 测试必须全部通过。
- 新增部署资产测试，验证所有 README 命令指向真实文件和真实接口。
- PowerShell 文件必须可以被 Windows PowerShell 5.1 解析，并保持 ASCII，避免编码问题。
- `docker compose config` 必须成功。
- Dockerfile 必须声明非 root 用户，Compose 必须绑定 `127.0.0.1` 并包含健康检查。

### 实机

1. 在现有仓库执行 `setup-local.ps1`。
2. 使用测试端口后台执行 `run-local.ps1 -Port 3110 -NoBrowser`。
3. 验证健康检查、合成案例 77 / 85、审批前 409 和审批后 200。
4. 执行 `stop-local.ps1 -Port 3110`，确认端口释放。
5. 执行 `docker compose build` 和 `docker compose up -d`。
6. 在容器路径重复健康和合成案例验证，然后执行 `docker compose down`。
7. 在最终本地服务上重复 HiClaw MCP 六阶段烟雾测试。

## 11. 非目标

本轮不实现生产数据库、账号体系、扫描 PDF OCR、云端部署、自动录用决策、真实高校数据接入或大模型在线抽取。这些能力不得写成当前已完成功能。
