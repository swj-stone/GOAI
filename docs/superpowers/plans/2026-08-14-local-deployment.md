# CampusMatch Local Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让用户从 GitHub 获取项目后，通过 Windows PowerShell 或 Docker Compose 在本机启动 CampusMatch，并能从浏览器、REST API 和 HiClaw 直接调用。

**Architecture:** 根目录脚本是面向部署者的稳定入口，内部仍调用唯一的 FastAPI 应用 `demo/src/campusmatch`。PowerShell 路径使用根目录 `venv`，Docker 路径使用非 root Python 3.13 镜像；两条路径暴露同一健康检查、网页和 API，并保持 HiClaw 的 `host.docker.internal:3100` 契约。

**Tech Stack:** PowerShell 5.1、Python 3.13、FastAPI、Uvicorn、pytest、Dockerfile、Docker Compose、Markdown。

## Global Constraints

- 普通体验者只需浏览器，不要求理解 Python、API Key 或提示词。
- Windows PowerShell 是主部署路径，Docker Compose 是无宿主 Python 的备用路径。
- 默认地址为 `http://127.0.0.1:3100`，脚本允许用 `-Port` 选择测试端口。
- PowerShell 脚本必须兼容 Windows PowerShell 5.1，并保持 ASCII 文本。
- Docker 必须以非 root 用户运行，只绑定宿主机回环地址，不复制真实凭据、虚拟环境或参赛材料。
- 不改变业务结果：合成案例仍为 77 / 85、Audit `BLOCK → PASS`。
- 不把真实令牌、账号或个人信息写入 Git；本地环境文件和运行状态必须被忽略。
- CampusMatch 是求职准备辅助工具，不是自动录用或淘汰系统。

---

### Task 1: 建立部署资产契约测试

**Files:**
- Create: `demo/tests/test_local_deployment_assets.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: 仓库根目录和现有 pytest 配置。
- Produces: 六个静态契约测试，后续脚本、Docker 和 README 任务以此为验收基线。

- [ ] **Step 1: 写入六个失败测试**

```python
from pathlib import Path

ROOT = Path(__file__).parents[2]

def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def test_root_readme_exposes_both_local_deployment_paths() -> None:
    text = read("README.md")
    assert ".\\run-local.ps1" in text
    assert "docker compose up --build -d" in text
    assert "http://127.0.0.1:3100/docs" in text

def test_setup_script_uses_project_venv_and_pinned_requirements() -> None:
    text = read("setup-local.ps1")
    assert "venv\\Scripts\\python.exe" in text
    assert "requirements.txt" in text
    assert "pip check" in text

def test_run_and_stop_scripts_use_health_and_scoped_state() -> None:
    run_text = read("run-local.ps1")
    stop_text = read("stop-local.ps1")
    assert "/api/health" in run_text
    assert ".campusmatch\\run" in run_text
    assert ".campusmatch\\run" in stop_text
    assert "Stop-Process" in stop_text

def test_dockerfile_runs_as_non_root_user() -> None:
    text = read("Dockerfile")
    assert "FROM python:3.13-slim" in text
    assert "USER campusmatch" in text
    assert "demo/src" in text

def test_compose_binds_loopback_and_has_healthcheck() -> None:
    text = read("compose.yaml")
    assert "127.0.0.1:${CAMPUSMATCH_PORT:-3100}:3100" in text
    assert "healthcheck:" in text
    assert "/api/health" in text

def test_dockerignore_excludes_secrets_and_local_artifacts() -> None:
    text = read(".dockerignore")
    for required in [".git", "venv", "demo/.env.local", ".campusmatch", "show"]:
        assert required in text
```

- [ ] **Step 2: 运行测试并确认因文件缺失而失败**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py -q`

Expected: 6 个测试失败，原因是目标文件尚不存在，不能因测试语法错误失败。

- [ ] **Step 3: 扩充忽略规则**

在 `.gitignore` 追加：

```gitignore
/.campusmatch/
/.env
```

- [ ] **Step 4: 运行现有测试确认基线**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests -q`

Expected: 原有 50 项测试通过，新部署资产测试保持预期失败。

- [ ] **Step 5: 提交测试基线**

```powershell
git add .gitignore demo/tests/test_local_deployment_assets.py
git commit -m "test: define local deployment contracts"
```

---

### Task 2: 实现 PowerShell 安装入口

**Files:**
- Create: `setup-local.ps1`
- Test: `demo/tests/test_local_deployment_assets.py`

**Interfaces:**
- Consumes: `requirements.txt`，可用的 `py -3.13` 或 Python 3.13+。
- Produces: `venv/Scripts/python.exe`；`-CheckOnly` 无修改验证；非零退出码表示环境不可用。

- [ ] **Step 1: 确认安装契约测试为红色**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py::test_setup_script_uses_project_venv_and_pinned_requirements -q`

Expected: FAIL，`setup-local.ps1` 不存在。

- [ ] **Step 2: 创建最小安装脚本**

脚本入口：

```powershell
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
$VenvPython = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
$Requirements = Join-Path $ProjectRoot 'requirements.txt'
```

实现 `Resolve-Python313`：先尝试 `py -3.13`，再尝试验证 `sys.version_info >= (3, 13)` 的 `python`。缺少合格版本时停止，不自动安装系统软件。

正常模式仅在 `venv` 不存在时创建，然后执行：

```powershell
& $VenvPython -m pip install -r $Requirements
& $VenvPython -m pip check
```

`-CheckOnly` 只验证文件、虚拟环境 Python 版本和 `pip check`。每个外部命令后检查 `$LASTEXITCODE`，错误文本保持 ASCII，且不打印令牌。

- [ ] **Step 3: 验证契约测试转绿**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py::test_setup_script_uses_project_venv_and_pinned_requirements -q`

Expected: PASS。

- [ ] **Step 4: 运行实机检查**

Run: `.\setup-local.ps1 -CheckOnly`

Expected: 输出 Python 3.13.x、`pip check` 成功和 `CampusMatch local environment: READY`。

- [ ] **Step 5: 检查 PowerShell 5.1 解析与 ASCII**

```powershell
[void][scriptblock]::Create((Get-Content .\setup-local.ps1 -Raw))
$bad = [IO.File]::ReadAllBytes((Resolve-Path .\setup-local.ps1)) | Where-Object { $_ -gt 127 }
if ($bad) { throw 'setup-local.ps1 is not ASCII' }
```

Expected: 无输出、退出码 0。

- [ ] **Step 6: 提交安装入口**

```powershell
git add setup-local.ps1
git commit -m "feat: add local environment setup"
```

---

### Task 3: 实现安全的启动与停止入口

**Files:**
- Create: `run-local.ps1`
- Create: `stop-local.ps1`
- Test: `demo/tests/test_local_deployment_assets.py`

**Interfaces:**
- Consumes: `setup-local.ps1`、`venv/Scripts/python.exe`、`campusmatch.main:app`。
- Produces: `run-local.ps1 -Port 3110 [-Foreground] [-NoBrowser] [-SkipSetup]`、`stop-local.ps1 -Port 3110`；任意合法端口都使用同样接口，3110 的状态文件为 `.campusmatch/run/3110.json`。

- [ ] **Step 1: 确认启动/停止契约测试为红色**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py::test_run_and_stop_scripts_use_health_and_scoped_state -q`

Expected: FAIL，两个脚本不存在。

- [ ] **Step 2: 创建 `run-local.ps1`**

入口参数：

```powershell
param(
    [ValidateRange(1024, 65535)][int]$Port = 3100,
    [switch]$Foreground,
    [switch]$NoBrowser,
    [switch]$SkipSetup
)
```

实现：

- `Test-CampusMatchHealth($Port)` 调用 `/api/health`，仅当 `status -eq 'ok'` 返回真。
- `Get-ListeningPid($Port)` 解析 `netstat -ano` 中 `LISTENING` 且本地端口完全匹配的行。
- `Wait-CampusMatch($Port, 30)` 每 500 ms 检查一次健康状态。
- 如未指定 `-SkipSetup` 且虚拟环境或 `fastapi` 缺失，调用 `setup-local.ps1`。
- 端口已有健康 CampusMatch 时幂等成功；端口被其他程序占用时抛错且不得终止它。
- 默认用隐藏窗口后台启动 Uvicorn；例如 3110 的日志写入 `.campusmatch/run/3110.out.log` 和 `.campusmatch/run/3110.err.log`，其他端口替换文件名中的端口数字。
- 健康后通过 `Get-ListeningPid` 记录真实监听 PID，JSON 包含 `port`、`pid`、`started_at`。
- 健康超时只停止本次启动进程并报告日志路径；默认打开浏览器，`-NoBrowser` 禁止打开。
- `-Foreground` 在当前终端运行并支持 `Ctrl+C`。

- [ ] **Step 3: 创建 `stop-local.ps1`**

读取端口对应的状态 JSON，核对记录端口、当前监听 PID 和健康响应。任一不匹配时拒绝终止；全部匹配时执行：

```powershell
Stop-Process -Id $state.pid -Force
Remove-Item -LiteralPath $StateFile -Force
```

状态文件不存在且端口未监听时输出实际端口，例如 `CampusMatch is not running on port 3110.`，并以 0 退出。

- [ ] **Step 4: 验证契约测试转绿**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py::test_run_and_stop_scripts_use_health_and_scoped_state -q`

Expected: PASS。

- [ ] **Step 5: 实机验证测试端口生命周期**

```powershell
.\run-local.ps1 -Port 3110 -NoBrowser -SkipSetup
Invoke-RestMethod http://127.0.0.1:3110/api/health
.\stop-local.ps1 -Port 3110
```

Expected: 启动 READY、健康 `status=ok`，停止后 3110 不再 LISTENING。

- [ ] **Step 6: 验证未知端口占用不会被终止**

在 3111 启动一个明确记录 PID 的临时非 CampusMatch HTTP 服务，再运行 `.\run-local.ps1 -Port 3111 -NoBrowser -SkipSetup`。

Expected: 非零退出并提示端口冲突，临时服务仍在运行；测试后只停止该明确 PID。

- [ ] **Step 7: 检查两个脚本的解析与 ASCII**

```powershell
foreach ($file in @('.\run-local.ps1', '.\stop-local.ps1')) {
    [void][scriptblock]::Create((Get-Content $file -Raw))
    if ([IO.File]::ReadAllBytes((Resolve-Path $file)) | Where-Object { $_ -gt 127 }) {
        throw "$file is not ASCII"
    }
}
```

Expected: 无输出、退出码 0。

- [ ] **Step 8: 提交生命周期脚本**

```powershell
git add run-local.ps1 stop-local.ps1
git commit -m "feat: add safe local service lifecycle"
```

---

### Task 4: 实现 Docker Compose 部署

**Files:**
- Create: `Dockerfile`
- Create: `compose.yaml`
- Create: `.dockerignore`
- Test: `demo/tests/test_local_deployment_assets.py`

**Interfaces:**
- Consumes: `requirements.txt`、`demo/src`、`demo/fixtures`。
- Produces: Compose 服务 `campusmatch`，容器端口 3100，宿主机端口 `${CAMPUSMATCH_PORT:-3100}`。

- [ ] **Step 1: 确认 Docker 契约测试为红色**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py -q`

Expected: PowerShell 两项测试通过；Dockerfile、Compose、dockerignore 三项失败；根目录 README 测试仍因 Task 5 尚未执行而失败。

- [ ] **Step 2: 创建 `.dockerignore`**

```dockerignore
.git
.gitignore
venv
.venv
**/__pycache__
**/.pytest_cache
.campusmatch
.env
demo/.env
demo/.env.local
demo/uploads
demo/artifacts
show
docs
*.pptx
*.png
```

- [ ] **Step 3: 创建非 root `Dockerfile`**

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/demo/src

WORKDIR /app
RUN groupadd --system campusmatch && useradd --system --gid campusmatch campusmatch
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt
COPY demo/src /app/demo/src
COPY demo/fixtures /app/demo/fixtures
RUN chown -R campusmatch:campusmatch /app
USER campusmatch
EXPOSE 3100
CMD ["python", "-m", "uvicorn", "campusmatch.main:app", "--host", "0.0.0.0", "--port", "3100"]
```

- [ ] **Step 4: 创建 `compose.yaml`**

```yaml
services:
  campusmatch:
    build:
      context: .
      dockerfile: Dockerfile
    image: campusmatch-demo:local
    ports:
      - "127.0.0.1:${CAMPUSMATCH_PORT:-3100}:3100"
    environment:
      CAMPUSMATCH_MCP_TOKEN: "${CAMPUSMATCH_MCP_TOKEN:-}"
    healthcheck:
      test: ["CMD", "python", "-c", "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:3100/api/health', timeout=2))['status']=='ok'"]
      interval: 5s
      timeout: 2s
      retries: 12
      start_period: 5s
    restart: unless-stopped
```

- [ ] **Step 5: 验证静态契约与 Compose 解析**

```powershell
.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py -k "not root_readme" -q
docker compose config --quiet
```

Expected: 5 passed、1 deselected；Compose 配置退出码 0。README 契约将在 Task 5 转绿。

- [ ] **Step 6: 构建并实机启动容器**

先停止占用 3100 的本地 CampusMatch，再运行：

```powershell
docker compose build
docker compose up -d
docker compose ps
Invoke-RestMethod http://127.0.0.1:3100/api/health
```

Expected: 服务最终 healthy，健康响应为 `status=ok`。

- [ ] **Step 7: 验证业务与容器身份**

```powershell
$body = @{task_id='docker-demo'; human_approved=$false} | ConvertTo-Json
$result = Invoke-RestMethod http://127.0.0.1:3100/api/v1/demo/run -Method Post -ContentType 'application/json' -Body $body
$result.match.match_score
$result.match.evidence_coverage
docker compose exec campusmatch id
```

Expected: 77、85；`id` 中用户不是 root。

- [ ] **Step 8: 停止容器并恢复本地服务**

```powershell
docker compose down
.\run-local.ps1 -NoBrowser -SkipSetup
```

Expected: Compose 资源移除，本地服务重新在 3100 返回 `status=ok`。

- [ ] **Step 9: 提交 Docker 部署**

```powershell
git add Dockerfile compose.yaml .dockerignore
git commit -m "feat: add Docker Compose deployment"
```

---

### Task 5: 编写 GitHub 风格中文 README 与同步材料

**Files:**
- Create: `README.md`
- Modify: `demo/README.md`
- Modify: `show/05-Demo复现方案.md`
- Modify: `show/10-交付验收记录.md`
- Modify: `show/19-Demo实机验收记录.md`
- Modify: `show/06-初赛PPT逐页大纲与讲稿.md`
- Modify: `show/09-PPT生成脚本.mjs`
- Modify: `show/CampusMatch-初赛方案.pptx`
- Modify: `show/PPT-总览.png`
- Test: `demo/tests/test_local_deployment_assets.py`

**Interfaces:**
- Consumes: 已实测的 PowerShell、Docker 和 HiClaw 命令。
- Produces: 根目录唯一部署入口；参赛材料使用相同命令和最新测试计数 56。

- [ ] **Step 1: 确认 README 契约测试为红色**

Run: `.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py::test_root_readme_exposes_both_local_deployment_paths -q`

Expected: FAIL，根目录 `README.md` 不存在。

- [ ] **Step 2: 创建根目录 `README.md`**

严格按设计规格第 7 节的 12 个部分编写。快速开始必须包含：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run-local.ps1
```

Docker 路径必须包含：

```powershell
docker compose up --build -d
docker compose ps
```

REST 最短示例必须调用真实接口：

```powershell
$body = @{ task_id = 'readme-demo'; human_approved = $false } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:3100/api/v1/demo/run -Method Post -ContentType 'application/json' -Body $body
```

README 还必须包含当前 HiClaw 五条命令、项目目录树、测试与停止命令、Docker 日志命令、Python/执行策略/端口/MCP 401 排障、扫描 PDF 限制、进程内存限制、隐私和非招聘决策声明。不得包含虚构徽章、真实令牌、占位仓库 URL 或不存在的许可证。

- [ ] **Step 3: 同步技术 README 与参赛材料**

- `demo/README.md` 首段链接根目录 README，并保留 API/HiClaw 深入说明。
- `show/05-Demo复现方案.md` 将首选命令改为 `run-local.ps1`，增加 Docker 备用命令。
- `show/10-交付验收记录.md` 增加 PowerShell 与 Docker 实机项目。
- `show/19-Demo实机验收记录.md` 记录 3110 生命周期、Compose healthy、非 root 和 56 passed。
- `show/06-初赛PPT逐页大纲与讲稿.md`、`show/09-PPT生成脚本.mjs` 和正式 PPT 将测试计数从 50 改为 56；77 / 85 和其他业务结果保持不变。

- [ ] **Step 4: 验证 README 契约和占位内容**

```powershell
.\venv\Scripts\python.exe -m pytest demo\tests\test_local_deployment_assets.py -q
rg -n "your-account|repo-name|待补充|尚未实测" README.md demo/README.md show/05-Demo复现方案.md show/19-Demo实机验收记录.md
```

Expected: 6 项部署测试通过；`rg` 无输出。

- [ ] **Step 5: 按 presentations 技能更新并验证 PPT**

以现有 14 页 PPT 为模板，只修改第 12、13 页的测试计数和这两页的演讲者备注，重新生成 `show/PPT-总览.png`。运行模板忠实度检查、`slides_test.py` 并逐页查看第 12、13 页。

Expected: 模板检查 0 个问题、无文本溢出、页面显示 56，业务值仍为 77 / 85。

- [ ] **Step 6: 提交 README、材料和 PPT**

```powershell
git add README.md demo/README.md show
git commit -m "docs: add Chinese local deployment guide"
```

---

### Task 6: 全链路发布验证与收口

**Files:**
- Modify: `show/19-Demo实机验收记录.md`（只有最终实测值与记录不一致时修改）

**Interfaces:**
- Consumes: 两条部署路径、REST API、HiClaw MCP、56 项 pytest 和 PPT。
- Produces: 干净 Git 分支和正在运行的 3100 本地服务。

- [ ] **Step 1: 运行完整 Python 与依赖检查**

```powershell
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m pytest demo\tests -q
```

Expected: `No broken requirements found.`；`56 passed`。

- [ ] **Step 2: 运行预检和脚本解析**

```powershell
.\demo\scripts\preflight.ps1
foreach ($file in @('.\setup-local.ps1', '.\run-local.ps1', '.\stop-local.ps1')) {
    [void][scriptblock]::Create((Get-Content $file -Raw))
}
```

Expected: preflight PASS；三个脚本无解析错误且 ASCII 检查通过。

- [ ] **Step 3: 验证本地 REST 审批门**

使用合成 fixtures 调用 `/api/v1/analyze`：审批前报告 GET 返回 409；审批后返回 200；匹配度 77、覆盖度 85；含邮箱的原始证据返回 `PRIVACY_IN_SOURCE`。

- [ ] **Step 4: 验证 Docker 发布路径**

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose down
```

Expected: build 成功、服务 healthy、down 成功且不残留容器。

- [ ] **Step 5: 运行最新 HiClaw 六阶段烟雾测试**

恢复 PowerShell 服务后运行：

```powershell
$task = 'smoke-deploy-' + (Get-Date -Format 'yyyyMMddHHmmss')
.\demo\scripts\smoke-hiclaw.ps1 -TaskId $task
```

Expected: Profile PASS、Job PASS、77 / 85、Audit `BLOCK → PASS`、最终 `READY`。

- [ ] **Step 6: 运行最终静态和 Git 检查**

```powershell
git diff --check
git status --short
git check-ignore demo/.env.local .campusmatch
```

Expected: 无空白错误；只存在本计划范围内修改；凭据和运行状态均被忽略。

- [ ] **Step 7: 提交最终实测差异（如有）**

```powershell
$changes = git status --porcelain
if (-not [string]::IsNullOrWhiteSpace(($changes | Out-String))) {
    git add README.md setup-local.ps1 run-local.ps1 stop-local.ps1 Dockerfile compose.yaml .dockerignore .gitignore demo show docs/superpowers/plans/2026-08-14-local-deployment.md
    git commit -m "feat: make CampusMatch locally deployable"
}
```

Expected: 若最终实测改变了验收记录，则产生一个收口提交；若工作区已被前序提交清空，则不创建空提交。

- [ ] **Step 8: 确认交付状态**

```powershell
git status --porcelain
git log -1 --oneline
Invoke-RestMethod http://127.0.0.1:3100/api/health
```

Expected: Git 工作区干净；HEAD 为本地部署最终提交；健康状态为 `ok`。
