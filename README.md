# BookerAutoTool

BookerAutoTool 是一个基于 OpenAI 兼容 API 的命令行工具集，专注于**大模型驱动的桌面 / 安卓 / 网页自动化**，
从 [BookerGptTool](https://github.com/DracoUnion/BookerGptTool) 中迁移而来，目前包含三个游戏自动化子命令。

## 安装

推荐使用 Python 3.10 或更高版本：

```bash
pip install git+https://github.com/DracoUnion/BookerAutoTool.git
```

也可以在源码目录中安装：

```bash
pip install .
```

安装后提供两个等价的命令：`auto-tool` 和 `BookerAutoTool`。

## 配置 API

工具通过 OpenAI 兼容接口访问大模型。至少需要设置 API Key：

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_CHAT_MODEL="gpt-4o-mini"
```

Windows PowerShell：

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:OPENAI_CHAT_MODEL = "gpt-4o-mini"
```

`OPENAI_BASE_URL` 可替换为其他 OpenAI 兼容服务的地址。视觉任务可额外配置：

```bash
export OPENAI_VIS_MODEL="视觉模型名称"
```

不要把 API Key 提交到 Git 仓库或写入公开脚本中。

## 基本用法

查看帮助和版本：

```bash
auto-tool -h
auto-tool --version
auto-tool <子命令> -h
```

通用参数应放在子命令之前，例如：

```bash
auto-tool --model gpt-4o-mini --retry 3 play-game "Minesweeper"
```

常用全局参数：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `-m, --model` | 聊天模型名称 | `OPENAI_CHAT_MODEL`，未设置时为 `gpt-3.5-turbo` |
| `-k, --key` | OpenAI API Key | `OPENAI_API_KEY` |
| `-H, --host` | API 地址 | `OPENAI_BASE_URL` |
| `-vm, --vmodel` | 视觉模型名称 | `OPENAI_VIS_MODEL` |
| `-r, --retry` | 重试次数 | `1000000` |
| `-tm, --temp` | temperature | `1` |
| `-tp, --top-p` | top-p | 不限制 |
| `-mt, --max-tokens` | 最大输出 token 数 | 不限制 |
| `-st, --stream` | 启用流式输出 | 关闭 |
| `-eb, --extra-body` | 额外请求体 | 无 |
| `-ct, --conn-timeout` | 连接超时秒数 | `60` |
| `-rt, --read-timeout` | 读取超时秒数 | `120` |
| `-rr, --repetition-regex` | 重复检测正则 | 无 |
| `-nt, --no-think` | 关闭思考模式 | 关闭 |
| `--emb` | Embedding 模型路径 | `moka-ai/m3e-base` |

### 通用模块

所有子命令共享 `BookerAutoTool/openai.py`（OpenAI 兼容 API 客户端，封装对话 / 视觉 / 文生图 /
工具调用循环）与 `BookerAutoTool/util.py`（提示词渲染、文本 / YAML 读写、代码块解析等工具函数）。

## 子命令

### play-game：用 LLM 在 Windows 窗口里玩游戏

通过 Win32 API 定位窗口并截取客户区，视觉模型看到截图后返回 JSON 操作指令，
由 pywin32 模拟鼠标 / 键盘逐帧执行，直到模型判定结束。

```bash
# 列出可见窗口（PID\t标题）
auto-tool play-game --list-windows

# 以窗口标题（模糊匹配）或进程号指定窗口，让大模型游玩
auto-tool play-game "Minesweeper"
auto-tool play-game 12345 --goal "尽快通关并获得最高分"

# 可选参数：--interval 每步间隔（秒）、--save-png 保存截图、--max-steps 最大步数
```

`play-game` 依赖 Windows 平台与 `pywin32`（`pip install pywin32`），视觉模型用通用参数
`-vm` 指定，未设置时回退到 `-m`。

### play-android-game：用 LLM + adb 在安卓设备上玩游戏

循环：adb 截屏 -> 视觉模型 -> 解析 JSON 操作 -> adb 执行触摸 / 按键 / 滑动，直到判定结束。

```bash
# 列出已连接设备
auto-tool play-android-game --list-devices

# 指定设备或自动选择唯一已连接设备
auto-tool play-android-game emulator-5554 --goal "尽快通关并获得最高分"
```

依赖 `adb`（Android Debug Bridge），需提前安装并加入 `PATH`，或用环境变量 `ADB` 指定绝对路径。

### play-game-chrome：通过 Chrome MCP 在网页上玩游戏

通过 `mcp-chrome-bridge`（默认 `http://127.0.0.1:12306/mcp`）驱动真实 Chrome，
循环：页面截图 -> 视觉模型 -> 解析 JSON 操作 -> MCP 执行点击 / 按键 / 滚动 / 跳转，直到判定结束。

```bash
# 列出 MCP 暴露的工具 / 当前标签页
auto-tool play-game-chrome --list-tools
auto-tool play-game-chrome --list-tabs

# 跳到指定游戏页面并开始游玩
auto-tool play-game-chrome -u https://example.com/game --goal "尽快通关并获得最高分"
```

注意：mcp-chrome-bridge 后端使用单例 Server，同一时刻只允许一个 MCP 客户端会话，
若连接被占用，请先断开其他客户端（如 Claude Code 里的 MCP 配置）。

### wx-auto-reply：后台自动回复 PC 微信白名单好友

后台守护循环：离屏抓取微信窗口画面 -> OCR 识别会话列表与聊天气泡 -> 白名单精确匹配与红点判定
-> 汇总待回复消息 -> 大模型生成回复 -> 剪贴板粘贴回车静默发送，并做绿底增量闭环验收。

```bash
# 先用 --dry-run 联调：只识别并生成回复，不真正发送
auto-tool wx-auto-reply --config wechat_config.json --dry-run --once

# 正式运行：持续扫描并在后台自动回复
auto-tool wx-auto-reply --config wechat_config.json
```

依赖 Windows 平台、`numpy`，以及两个可选依赖（惰性导入，未安装不影响其他子命令）：

```bash
pip install rapidocr_onnxruntime pyperclip
```

配置文件（默认 `./wechat_config.json`）主要字段：

| 字段 | 说明 |
| --- | --- |
| `whitelist_mode` | `true` 仅回复白名单好友；`false` 回复所有非黑名单单聊 |
| `whitelist` | 允许自动回复的好友昵称列表 |
| `blacklist` | 永不回复的会话关键词（群聊另有防火墙，按 `群`/人数后缀识别） |
| `system_prompt` | 大模型的角色提示词 |
| `friend_personas` | 按好友昵称定制的专属人设 |
| `check_interval_seconds` | 扫描间隔秒数（可用 `--check-interval` 覆盖） |
| `reply_delay_seconds` | 生成回复后、发送前的额外延迟 |

配置文件的 `system_prompt`、大模型的 `-m/-k/-H/-tm` 等既可用命令行参数，也可用
`OPENAI_API_KEY` 等环境变量指定。`--once` 只扫描一轮，`--limit N` 限定扫描轮数。

## 开发

```bash
pip install -e .
python -m BookerAutoTool -h
python -m BookerAutoTool play-game -h
python -m BookerAutoTool wx-auto-reply -h
```