# Windows 本地 Conda 调试

本机已创建 `mgm` 环境，使用 DeepSeek API 模式。它可以调试 Python
配置、LLM 协议处理、Agent 逻辑、测试及绘图。完整 SWE-bench / Polyglot
任务执行仍需要 Linux + Apptainer。WSL 2.7.14 已安装，相关 Windows 功能
已启用且要求重启后生效；Ubuntu、Linux Conda 和 Apptainer 尚未安装。
完整评测尚未跑通。

| 项目 | 配置 |
|---|---|
| Conda 环境 | `mgm` |
| Python | `3.11.15` |
| 解释器 | `D:\Tools\Anaconda\envs\mgm\python.exe` |
| 项目目录 | `E:\Third-Projects\MGM` |
| 本地配置 | `config.local.yaml` |
| 模型角色 | 三个角色均为 `deepseek-v4-flash` |
| 并发 | `1` |
| 依赖锁定 | `requirements-local.lock.txt`，Windows 专用 |

## 激活与检查

在 Anaconda PowerShell Prompt，或已经初始化 Conda 的 PowerShell 中运行：

```powershell
conda activate mgm
Set-Location E:\Third-Projects\MGM
python scripts/check_local_env.py
python -m pytest -c pytest.local.ini
```

激活时已设置 `PYTHONUTF8=1`、`PYTHONNOUSERSITE=1`、
`PYTHONUNBUFFERED=1` 和 `HGM_LLM_MODEL_ID=deepseek-v4-flash`。
本机的 Hugging Face 与 Matplotlib 缓存分别位于项目 `.cache` 下。

若当前终端尚未识别 `conda`，可以直接使用解释器：

```powershell
& 'D:\Tools\Anaconda\envs\mgm\python.exe' -X utf8 -s scripts/check_local_env.py
```

## PyCharm 断点调试

已在 PyCharm 2026.1 的解释器表中注册 `Python 3.11 (mgm)`，并在
`.idea/runConfigurations/` 中创建三个显式使用本地解释器的配置：

- `MGM Local - Environment Check`：离线导入和配置检查。
- `MGM Local - Windows Tests`：运行 Windows 测试子集，可在测试或业务函数中打断点。
- `MGM Local - Evaluate Entry (help)`：运行 `evaluate_agent.py --help`，检查导入和参数解析。

选择对应配置后使用 Debug。推荐先在 `config.py` 的 `load_config()`，
或 `llm.py` 的 `extract_json_between_markers()` 打断点。
前者由环境检查调用，后者可通过测试配置进入。

PyCharm 当前已打开，如果配置或新解释器尚未出现，重新打开 IDE 后再选择。
如果希望项目代码索引也切换到本地环境，在 Python Interpreter 设置中选择
`Python 3.11 (mgm)`，或添加上述 `python.exe` 作为已有解释器。
本地运行配置单独指定解释器，已有远程运行配置未改动。

命令行也可以让 Debugpy 执行离线检查：

```powershell
python -X frozen_modules=off -m debugpy --listen 127.0.0.1:5678 scripts/check_local_env.py
```

## API 配置

本次安装和检查没有发送模型请求。新环境没有持久化 API 密钥；已有运行配置
中的密钥不会自动成为新终端的环境变量。

可在运行配置的环境变量中设置 `DEEPSEEK_API_KEY`。也可以把根目录的
`.env.local.example` 复制为 `.secrets/local.env` 后填写；该目录已被 Git 忽略。
环境检查脚本会读取它。现有项目入口不保证自动加载 dotenv 文件，使用文件时
应通过下面的方式显式加载：

```powershell
python -m dotenv -f .secrets/local.env run -- python evaluate_agent.py --help
```

代理设置在模板中默认注释，按本机实际代理端口启用。已安装 HTTPX 和 Requests
的 SOCKS 支持。API 模式不需要在这块 8GB 显卡上加载模型，因此没有安装
vLLM、PyTorch 或模型权重。

## 验证结果与平台边界

- `pip check`：通过，无依赖冲突。
- 实际导入：配置、LLM、两个 Coding Agent、容器适配层及评测主入口通过。
- `hgm.py --help` 和 `evaluate_agent.py --help`：通过。
- Windows 测试配置：27 passed，3 deselected，并排除整个 Bash 测试文件。
- 原始全量测试首次运行：23 passed，12 failed。失败涉及 `os.setsid`、GNU
  `find`、POSIX 绝对路径及 Linux 环境路径处理；安装 Python 包不能补齐这些接口。

`pytest.local.ini` 只用于 Windows 调试，原 `pytest.ini` 和原测试文件均未修改。
完整验证应在 Linux 中运行原测试集。测试报告保存在
`.cache/local-debug/pytest-initial.xml` 和 `pytest-windows.xml`。
新增运行时检查的回归报告为 `.cache/local-debug/runtime-after.xml`，
覆盖缺少 Linux/Apptainer 时两个主入口在数据集读取和创建输出目录之前退出。

## WinError 2 与 WSL 安装状态

若构建基础镜像时在 `_run_apptainer()` 收到 `[WinError 2]`，缺少的是
Apptainer 可执行程序。该程序要求 Linux；Windows 的 `python.exe`
不能因为 WSL 中安装了 Apptainer 就直接调用它。
现在 `evaluate_agent.py` 和 `hgm.py` 会提前检查，并提示切换到 Linux Python。
`--help` 和离线导入保持可用。

2026-09-14 已完成：

- 启用 `Microsoft-Windows-Subsystem-Linux` 和 `VirtualMachinePlatform`，
  两项均返回 `RestartNeeded=True`。
- 验证 Microsoft 签名后安装官方 WSL 2.7.14，MSI 退出码 0。
- `wsl --version` 成功；当前尚无 Linux 发行版。

下一步是保存工作并重启 Windows，再检查 `wsl --status`。
重启后需要安装 Ubuntu、在 Ubuntu 内创建 Conda 环境并安装 Apptainer，
再把 PyCharm 真实评测配置切换到 WSL 内的 Linux 解释器。
Windows 环境的锁文件不适用于 Linux；Linux 可使用 `requirements-local.txt`
安装项目依赖，其中已固定 `swebench==4.1.0`。

安装日志位于 `.cache/wsl-setup/install.log`。
Microsoft 的 [WSL 安装说明](https://learn.microsoft.com/en-us/windows/wsl/install)
也要求启用组件后重启系统。

## 完整评测前的检查

项目代码依赖 `swebench.harness.test_spec`；安装时发现 `swebench 5.x`
已经移除这个模块，因此本地依赖固定为已通过入口检查的 `swebench==4.1.0`。
依赖中包含上游所需的 Docker Python SDK，它不代表已配置 Docker 容器运行时；
本项目的实际容器运行时是 Apptainer。

完整评测前需在 WSL2/Linux 内另建 Linux Conda 环境、安装 Apptainer，
并配置模型凭据、评测数据和容器镜像。可以用下面的检查识别运行时是否具备：

```powershell
python scripts/check_local_env.py --full
```

这条命令在 Windows 上预期返回非零，明确报告需要 Linux。
即使在 Linux 上检查通过，也只验证导入和 Apptainer 版本，不代表基准任务已跑通。

`config.local.yaml` 保留 MGM 的 A/B/C 策略，设为单并发、5 次进化任务评测预算，
输出目录为 `output_local_debug`。注意：首次运行 `hgm.py` 仍会先评测
60 个初始任务，这一步不受 `max_task_evals` 限制。完整环境搭好后应先使用
`evaluate_agent.py` 的 `--n_tasks 1 --num_workers 1` 验证单任务，再启动进化。

## 重建环境

在另一台 Windows 机器的项目根目录、且尚未创建 `mgm` 环境时：

```powershell
conda env create -f environment.local.yml
conda activate mgm
python scripts/check_local_env.py
```

`requirements-local.txt` 记录直接依赖和兼容版本要求；
`requirements-local.lock.txt` 记录此次安装的全部 Python 包版本。
锁文件包含 Windows 专用依赖，不应直接用于 Linux 环境。
PyCharm 本地配置中的解释器路径需要按新机器的 Conda 安装位置调整。
