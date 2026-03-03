# Changelog

## v0.4.5 (2026-03-03)

### 文档更新
- **文案精简**：移除专门针对开发者的源码挂载方式说明（本地免打包测试指南），缩小面向早期使用者的认知负担，目前仅提供适合普通用户的标准包安装模式说明。

## v0.4.4 (2026-03-03)

### 文档更新
- **排版优化**：彻底分离各个 MCP 客户端（Claude Code, Codex, Cursor, Antigravity, Windsurf, Claude Desktop）的接入指南，不再合并说明，降低用户配置门槛。

## v0.4.2 (2026-03-03)

### 修复与文档更新
- **发布修复**：修复 `v0.4.1` 的内部 `pyproject.toml` 版本号未更新导致 PyPI 上传被拒的问题。
- **文档优化**：调整 MCP 客户端支持列表的优先级（Claude Code、Codex、Cursor、Antigravity、Windsurf），并增加了 **“开发者模式”** 直接挂载源码热更新的路径说明，方便本地测试与开发解耦。

## v0.4.0 (2026-03-03)

### 重大更新 (Major)
- **原生支持 MCP 协议 (Model Context Protocol)**：大幅提升在 Agent 生态中的融合度。
  - 新增 `mcp` 依赖库和基于 `mcp.server.fastmcp.FastMCP` 的服务端实现 (`src/mcp_server.py`)。
  - 注册全新的 `b2a-mcp` CLI 启动命令，提供给各主流 AI IDE（Cursor, Windsurf, Claude Desktop）作为本地 MCP Server 挂载。
  - 对大模型暴露三个原生工具节点，自带强语境提示：
    - `bilibili_get_info_subtitles`: 获取分P、元数据、CC 字幕
    - `bilibili_extract_voice`: 调度火山引擎执行 ASR
    - `bilibili_extract_frames`: 提取视觉关键帧并自动指引模型调用其本地 Read 工具进行多模态视觉连结

## v0.3.2 (2026-03-03)

### 修复
- **PyPI 包名冲突**：因原名被占用，将发布包名从 `b2a` 更改为 `b2a777`（CLI 命令名 `b2a` 保持不变）。更新文档中的安装指引。

## v0.3.1 (2026-03-03)

### 新增
- **PyPI 发布支持**：增加 `pyproject.toml` 中的 `authors`, `keywords`, `classifiers` 和项目 URL 元数据。
- **CI/CD 自动化**：新增 `.github/workflows/publish.yml`，在 GitHub 触发 v* 标签或 Release 时，自动经由 Trusted Publishing 推送至 PyPI。

## v0.3.0 (2026-03-03)

### 新增
- **URL 解析模块** (`src/utils/url_parser.py`)：支持 b23.tv 短链重定向、`?p=N` 分P参数、`?t=N` 时间跳转、AV 号自动转 BV 号
- **分P支持**：`api.py` 新增 `get_page_list` / `get_cid_by_page`，CLI 新增 `--page` 参数
- **工作区按视频隔离**：目录结构改为 `workspace/{bvid}/downloads|frames|audios`，不同视频文件不再混杂
- **长音频自动分片 ASR**：超过 60 秒的音频自动用 ffmpeg 切割后分批提交火山引擎，时间戳逐段累加
- **JSON 结构化输出**：CLI 新增 `--format json`，输出标题、字幕、ASR 结果、帧图路径等统一 JSON 对象
- **发布基础设施**：README.md、pyproject.toml（`b2a` 命令行入口）、LICENSE (MIT)
- **项目改名**：BiliVision-Agent -> B2A (Bilibili to Agents)

### 修复
- **CLI 控制流重构**：ASR 和 Visual 从互斥改为独立并行，无论有无 CC 字幕都可触发，且可同时使用
- **VisualExtractor 实现真实逻辑**：替换桩代码，实际调用 yt-dlp 下载 + ffmpeg 抽帧
- **CC 字幕保留时间戳**：`get_video_subtitles` 返回 `list[dict]`（含 from/to/content），不再丢弃时间信息
- **ASR 时间戳偏移修正**：指定 `--start` 切片时，ASR 输出自动加上起始偏移量
- **下载多级回退策略**：yt-dlp 原生切片 -> 下载后 ffmpeg 裁剪 -> 兜底完整文件，兼容不同 ffmpeg 版本
- **视觉提取仅下载视频流**：不再请求音频流合并，避免因 ffmpeg 版本问题导致合并失败
- **清理硬编码密钥**：测试中的疑似真实 API Key UUID 替换为虚拟值
- **补全依赖**：加入 pytest-asyncio，去掉未使用的 ffmpeg-python

## v0.2.0 (2026-03-03 早期)

### 新增
- 工作区目录管理 (`src/utils/workspace.py`)
- VisualExtractor 支持 start_time/end_time 切片参数
- CLI 无字幕时挂起提示用户选择轨道

## v0.1.0 (2026-03-02)

### 新增
- 项目骨架：CLI 入口 (argparse)、core/api 模块
- B 站视频基础信息获取 (`get_video_info`)
- CC 字幕拉取 (`get_video_subtitles`)
- 火山引擎 ASR 集成 (`VolcengineASRClient`)
- 音频提取器 (`AudioExtractor`)
- 环境变量管理 (`config.py`，区分测试/生产环境)
