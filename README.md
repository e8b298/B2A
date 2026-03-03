# B2A (Bilibili to Agents) - 哔哩哔哩 MCP 插件

让 AI Agent（Claude Code、Codex、Cursor、Antigravity、Windsurf 等）原生具备「观看」和「倾听」B站视频能力的多模态 MCP 插件。

## 🌟 核心能力
B2A 为各种 Agent 提供了三条信息获取轨道：
- **CC 字幕（最快）**：直接拉取视频自带的字幕文本及精准时间戳。
- **ASR 语音识别（听觉）**：通过火山引擎大模型将音频转为文字，解决无字幕视频痛点。
- **视觉抽帧（视觉）**：自动下载视频片段并按间隔抽帧，让多模态大模型能够使用内置 Vision 能力“看到”画面。

## 📦 安装说明

### 1. 安装 FFmpeg (前置依赖)
视觉抽帧和长音频处理依赖网络串流和 FFmpeg。
- **Windows**: `winget install Gyan.FFmpeg` (安装后需重启终端)
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt install ffmpeg`

### 2. 安装 B2A 插件
```bash
pip install b2a777
```

## 🔌 MCP 接入指南 (核心用法)

安装完成后，你可以将它原生挂载到各种大模型 IDE 的上下文中。**请根据你使用的客户端选择对应的配置方式：**

### 1. Claude Code
在 Claude Code 的聊天对话框中输入以下斜杠命令：
```text
/mcp add b2a-vision b2a-mcp
```
*(开发者本地测试模式：如果你正在修改源码，可直接指向源码挂载：`/mcp add b2a-vision python "绝对路径/src/mcp_server.py"`，这样保存代码即生效)*

### 2. Codex
由于 Codex 同样深度集成了指令模式，可以直接在其命令行终端中添加挂载命令：
```text
/mcp add b2a-vision b2a-mcp
```

### 3. Cursor
1. 打开 **Cursor Settings** -> **Features** -> **MCP**
2. 点击 **+ Add New MCP Server**
3. **Type**: 选择 `command`
4. **Name**: `b2a-vision`
5. **Command**: `b2a-mcp` *(注意：如果是使用源码测试，Command 填 `python`，Args 填 `绝对路径/src/mcp_server.py`)*

### 4. Antigravity
作为直接的衍生环境，与 Claude Code 保持一致，在对话框内执行即可：
```text
/mcp add b2a-vision b2a-mcp
```

### 5. Windsurf
在配置目录下的 `mcp_config.json` 中添加：
```json
{
  "mcpServers": {
    "b2a-vision": {
      "command": "b2a-mcp",
      "args": []
    }
  }
}
```

### 6. Claude Desktop
在配置目录下的 `claude_desktop_config.json` 中添加：
```json
{
  "mcpServers": {
    "b2a-vision": {
      "command": "b2a-mcp",
      "args": []
    }
  }
}
```

## 💬 与 Agent 互动的提示词示例
配置好 MCP 后，你不需要写任何代码，直接用自然语言向 Agent 发送包含 B站链接的任务：

- *"总结一下这个视频的核心观点：BV1xx411c7mD"* (Agent 会自调度获取 CC 字幕)
- *"这没字幕，帮我听一下这个视频的 1分30秒 到 3分钟 说了什么：https://b23.tv/xxxx"* (Agent 会自动调度 ASR 识别)
- *"看看这个 BV1xx411c7mD 视频的画面，前两分钟里展示了哪些代码？"* (Agent 会提取关键帧并使用自己的视觉能力识图)

---

## 🛠️ 进阶：作为 CLI 工具独立使用

B2A 同时也可以作为极简的命令行工具在未接入 MCP 的环境中独立运行。

### 基础用法
```bash
# 获取视频信息与字幕
b2a BV1xx411c7mD

# 结构化 JSON 输出
b2a BV1xx411c7mD --format json
```
### 更多参数
```text
  --asr              启用语音识别（提取音频轨并转文字）
  --visual           启用视觉提取（抽取视频关键帧截图）
  --start TIME       截取开始时间（如 01:30）
  --end TIME         截取结束时间（如 02:40）
  --page N           指定分P编号（从1开始）
```

## 🔑 ASR 语音识别配置 (可选)
ASR 功能依赖火山引擎（豆包）API Key。不配置时不影响获取 CC 字幕和抽取关键帧。
在工程运行目录或用户目录创建 `.env` 文件：
```env
VOLC_ENV=production
VOLC_PROD_API_KEY=你的火山引擎API_Key
```

## License
MIT
