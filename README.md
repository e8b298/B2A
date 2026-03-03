# B2A

让 AI Agent（Claude Code、Codex、Cursor、Antigravity、Windsurf 等）原生具备「观看」和「倾听」B站视频能力的多模态 MCP 插件。

## 🌟 核心能力（v0.5.0 全新架构）
在 v0.5.0 的“三刀重构”后，B2A 彻底摒弃了可能造成大模型死锁或 C盘爆满的无脑提取模式。我们为所有 AI Agent 注入了**最省流、防剧情断层的分层多模态阅读能力**：

- **CC 字幕与元数据（最快）**：以毫秒级速度直接拉取视频信息与自带字幕文本，是了解视频的最快轨道。
- **全景故事板雷达（防反转架构）**：AI 将以极低分辨率均匀抽取视频的缩略图，以上帝视角综观整片节奏走向，绝不错过片尾的惊天大反转！
- **局部下钻特写（精准截取）**：看完缩略图后，AI 能敏锐地锁定特定时间段（如 `05:00-05:30`）重新索取对应的高清切片，精准看清 PPT 甚至代码！
- **强制缓存回收（绝对干净）**：你的存储守护神！分析结束后，AI 助手将强制调用清理协议，瞬间抹除由于抽帧与视频提取产生的各种残骸碎屑。

## 📦 安装说明

### 1. 安装 FFmpeg (前置依赖)
视觉抽帧和长音频处理依赖网络串流和 FFmpeg。如果忘记装，AI 会在聊天里贴心提示你如何一键上车：
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
5. **Command**: `b2a-mcp`

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
配置好 MCP 后，你不需要写任何代码。得益于内置的 `[CRITICAL SAFETY LOCK]` 安全锁，Agent 会以极度省流和尊重你的方式展开工作：

- *"总结一下这个视频的核心观点：BV1xx411c7mD"* -> (Agent 瞬间抓取 CC 字幕并给你答复)
- *"帮我看看这个视频讲了什么？BV..."* -> (Agent 返回询问：“为了更准确，是否允许我为您消耗空间去提取故事板画面？”)
- *"这没字幕，帮我听一下这个视频的 1分30秒 到 3分钟 说了什么"* -> (Agent 自动调度 ASR 识别，并在结束后默默打扫卫生)

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

## 🔑 极致简单的 ASR 语音配置
如果需要无字幕视频的听力功能，B2A 接入了火山引擎（豆包）。你不需要自己配置复杂环境变量文件，**直接把 API Key 的文本发给 AI 即可自动挂载。**

1. 申请途径：[点击前往火山引擎控制台](https://console.volcengine.com/speech/app)获取豆包平台的 API Key。
2. 自动化存入：当遇到需要权限的视频时，你的专属 Agent 将温和地提示你，**只需将 Key 的字符串丢进聊天框**（不用特意背暗号口令），AI 会极聪明地在你的回话里将字符串抽离，直接为你后台隐式地保存。

## License
MIT
