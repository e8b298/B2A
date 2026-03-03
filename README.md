# B2A

让 AI Agent（Claude Code、Codex、Cursor、Antigravity、Windsurf 等）原生具备“观看”和“倾听”B站视频能力的多模态 MCP 插件。

B2A 不是一个爬虫工具——它赋予 AI 真正理解视频内容的能力。AI 会像人一样先"读"字幕，看不懂就"看"画面，听不到就"听"声音，最终用自己的理解回答你的问题。

## 它是怎么工作的

当你把一个 B 站链接丢给 AI 时，它会自主决定用哪种方式来理解视频：

- **读字幕**（毫秒级）：最快的方式，直接读取视频自带的 CC 字幕。
- **看画面**（1-3分钟）：如果没有字幕，AI 会征得你同意后去"观看"视频——以低分辨率快速浏览全片画面，像人一样先看全局再聚焦细节。
- **听声音**（30秒-几分钟）：AI 也可以去"听"视频里的人声并转成文字。它会提前告诉你：它的"听力"是语音识别，只能听懂人说的话，纯音乐和音效听不出来。
- **自动清理**：分析结束后，AI 会自动清除所有临时文件，不占用你的磁盘空间。

所有耗时操作都会先征得你的同意，并在开始前给你一句等待提示，不会突然静默几分钟。

## 安装

### 1. 安装 FFmpeg（前置依赖）

画面分析和音频处理需要 FFmpeg。如果忘记装，AI 会在聊天里提示你怎么装：

- **Windows**: `winget install Gyan.FFmpeg`（安装后需重启终端）
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt install ffmpeg`

### 2. 安装 B2A

```bash
pip install b2a777
```

## MCP 接入指南

安装完成后，根据你使用的客户端选择对应的配置方式：

### Claude Code / Codex / Antigravity

在对话框中输入：

```text
/mcp add b2a-vision b2a-mcp
```

### Cursor

1. 打开 **Cursor Settings** -> **Features** -> **MCP**
2. 点击 **+ Add New MCP Server**
3. **Type**: `command`
4. **Name**: `b2a-vision`
5. **Command**: `b2a-mcp`

### Windsurf

在 `mcp_config.json` 中添加：

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

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

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

## 使用示例

配置好 MCP 后，直接用自然语言和 AI 对话即可：

- `"帮我看看这个视频讲了什么：BV1xx411c7mD"` — AI 读取字幕后直接回答
- `"这个视频没字幕，帮我了解一下内容"` — AI 会问你："我可以看一下视频画面吗？" 或 "我可以试着听一下吗？"，等你同意后才开始
- `"帮我看看 5分钟到 5分30秒 那段 PPT 写了什么"` — AI 会下钻到指定时间段，以更高清晰度仔细查看
- `"你看看这个视频，我想跟你聊聊..."` — AI 会尝试分析视频的内容并产生理解
  
AI 会根据视频内容自主判断最合适的理解方式，整个过程像和一个助手对话一样自然。

## 语音识别配置（可选）

如果需要"听"视频里的人声内容，B2A 接入了火山引擎（豆包）语音识别。配置方式极其简单：

1. 前往[火山引擎控制台](https://console.volcengine.com/speech/app)申请 API Key
2. 当 AI 提示需要 Key 时，直接把 Key 粘贴进聊天框
3. AI 会自动将 Key 安全地存储到 `~/.b2a/.env`（你的用户主目录下）

API Key 存储位置：`~/.b2a/.env`（Windows: `C:\Users\<用户名>\.b2a\.env`）

## CLI 工具

B2A 也可以作为命令行工具独立使用：

```bash
# 获取视频信息与字幕
b2a BV1xx411c7mD

# 语音识别（需配置 API Key）
b2a BV1xx411c7mD --asr

# 视觉抽帧
b2a BV1xx411c7mD --visual

# 指定时间段
b2a BV1xx411c7mD --asr --start 01:30 --end 02:40

# JSON 结构化输出
b2a BV1xx411c7mD --format json

# 指定分P
b2a BV1xx411c7mD --page 2
```

## License

MIT
