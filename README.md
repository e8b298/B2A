# B2A (Bilibili to Agents)

让 AI Agent 能「观看」B站视频的多模态内容提取工具。

## 解决什么问题

AI Agent（如 Claude Code、Cursor 等）可以访问网页，但无法真正「观看」视频。当用户想让 Agent 分析某个 B 站视频的内容时，Agent 无从下手。

B2A 提供了三条互补的信息获取轨道：

- CC 字幕 — 最快速，直接拉取视频自带的字幕文本（含时间戳）
- ASR 语音识别（声） — 通过豆包语音大模型将音频转为带时间戳的文字，解决 B 站大量视频无 CC 字幕的问题
- 视觉抽帧（形） — 下载视频并按间隔截取关键帧图片，让 Agent 能「看到」画面内容

三条轨道可任意组合，支持全视频或指定时间片段。

## 安装

### 1. 安装 ffmpeg（前置依赖）

`--visual` 抽帧和 `--asr` 切片功能依赖 ffmpeg，版本需 5.0 以上。

Windows：

```bash
# 方式一：winget（Windows 11 自带，推荐）
winget install Gyan.FFmpeg

# 方式二：scoop
scoop install ffmpeg
```

安装后打开新的终端窗口，验证：

```bash
ffmpeg -version
# 应显示 ffmpeg version 5.x 或更高
```

如果提示找不到命令，需要将 ffmpeg 的 bin 目录加入系统 PATH 环境变量。

macOS：

```bash
brew install ffmpeg
```

Linux（Debian/Ubuntu）：

```bash
sudo apt update && sudo apt install ffmpeg
```

### 2. 安装 B2A

```bash
# 克隆仓库
git clone https://github.com/fanzhongli/B2A.git
cd B2A

# 安装
pip install -e .
```

安装完成后即可使用 `b2a` 命令。

## 快速上手

### 基础用法：获取视频信息 + CC 字幕

```bash
b2a BV1xx411c7mD
```

### 语音识别（ASR）

```bash
# 全视频 ASR
b2a BV1xx411c7mD --asr

# 指定片段 ASR（3分20秒到4分50秒）
b2a BV1xx411c7mD --asr --start 03:20 --end 04:50
```

### 视觉抽帧

```bash
# 全视频抽帧（每10秒一张）
b2a BV1xx411c7mD --visual

# 指定片段抽帧
b2a BV1xx411c7mD --visual --start 01:00 --end 02:30
```

### 声形同时获取

```bash
b2a BV1xx411c7mD --asr --visual --start 03:20 --end 04:50
```

### 分P视频

```bash
# 指定第3个分P
b2a BV1xx411c7mD --page 3 --asr
```

### 多种输入格式

```bash
# 完整链接（自动提取 BV 号、分P、时间跳转）
b2a "https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=180"

# b23.tv 短链
b2a "https://b23.tv/xxxxxx"

# AV 号
b2a av170001
```

### JSON 结构化输出（供 Agent 消费）

```bash
b2a BV1xx411c7mD --asr --format json
```

## ASR 配置

ASR 功能依赖豆包语音（火山引擎）API Key。不配置时，CC 字幕和视觉抽帧功能仍可正常使用。

1. 复制配置模板：
```bash
cp .env.example .env
```

2. 编辑 `.env`，填入你的 API Key：
```env
VOLC_ENV=test
VOLC_TEST_API_KEY=你的测试环境API_Key
VOLC_PROD_API_KEY=你的生产环境API_Key
```

## CLI 参数一览

```
b2a <url> [选项]

位置参数:
  url                B站视频URL、BV号或AV号

选项:
  --asr              启用语音识别（提取音频轨并转文字）
  --visual           启用视觉提取（抽取视频关键帧截图）
  --start TIME       截取开始时间（如 01:30 或 1:03:20）
  --end TIME         截取结束时间（如 02:40 或 1:05:00）
  --page N           指定分P编号（从1开始）
  --format {text,json}  输出格式（默认 text）
```

## 项目结构

```
B2A/
├── src/
│   ├── cli.py                 # CLI 入口
│   ├── core/
│   │   ├── api.py             # B站 API（视频信息、字幕、分P）
│   │   └── asr.py             # 火山引擎 ASR（含长音频自动分片）
│   ├── audio/
│   │   └── extractor.py       # 音频提取（yt-dlp）
│   ├── visual/
│   │   └── extractor.py       # 视觉提取（yt-dlp 下载 + ffmpeg 抽帧）
│   └── utils/
│       ├── config.py          # 环境变量与鉴权
│       ├── url_parser.py      # URL 解析（短链/BV/AV/分P/时间）
│       └── workspace.py       # 工作区目录管理（按视频隔离）
├── tests/                     # 测试用例（26个）
├── pyproject.toml             # 打包配置
├── requirements.txt           # 依赖清单
└── .env.example               # 环境变量模板
```

## 运行测试

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
