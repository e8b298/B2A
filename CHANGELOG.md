# Changelog

## v0.5.6 (2026-03-04)

### 修复与文档
- **pyproject.toml 解析修复**：中文双引号导致 TOML 解析失败，editable 安装报错。
- **描述同步**：pyproject.toml 的 description 与 README 风格统一。
- **README 文案微调**：标点规范、新增对话式使用示例、去掉不必要的技术细节和"进阶"标签。

## v0.5.5 (2026-03-04)

### 重大修复与体验重构

- **环境变量路径隔离**：API Key 存储从项目目录的 `.env` 迁移到用户主目录 `~/.b2a/.env`，彻底解决沙盒测试污染发布版本的问题。向后兼容旧位置。
- **环境变量热重载**：`load_dotenv(override=True)` + ASR 客户端懒加载凭证，用户写入 Key 后无需重启即可生效。
- **workspace 绝对路径**：工作区路径固定为项目根目录下的绝对路径，不再依赖 MCP 进程的 cwd，解决文件乱存问题。
- **ASR 无人声智能识别**：区分"API 正常但无人声"和"API 异常需重试"，纯音乐/环境音不再盲目重试 3 次浪费时间。
- **超时熔断异常穿透**：`B2A_HARD_TIMEOUT` 异常不再被格式 fallback 循环吞掉，统一转为 `DownloadTimeoutError` 传递给 AI。
- **超时计时器修正**：下载超时钩子从第一次收到 `downloading` 状态时才开始计时，避免 info fetch 阶段误触发。
- **CLI fail-fast**：ASR 模式在下载音频前先校验 API Key，不再让用户等几分钟下载完才发现没有 Key。

### AI 交互话术重构

- **角色认知统一**：所有工具的 AI 话术从"帮你提取/下载"重构为"我去看/听"，AI 是在理解视频内容的智能体，不是爬虫工具。
- **语音识别局限性前置声明**：AI 在提议"听"视频前会主动告知用户："我的听力是语音识别，只能听懂人说的话，纯音乐或音效听不出来。"
- **安全锁强化**：禁止 AI 在同一 turn 内同时询问和调用工具，必须等用户在下一条消息中明确同意后才执行。
- **耗时预警全覆盖**：所有耗时工具（语音、全景故事板、下钻特写）调用前都会先给用户一句等待提示。
- **无字幕引导优化**：无字幕时的返回文案同时告知"看画面"和"听声音"两个方案，并附带语音识别能力边界说明。
- **MissingAuthError 路径更新**：CLI 和 MCP 模式下的 Key 缺失提示统一指向 `~/.b2a/.env`。

### 代码清理

- **删除过期调试脚本**：移除 `patch_mcp_threads.py` 和 `diag_download.py`（硬编码了开发者本地路径，且功能已过时）。
- **cleanup 逻辑简化**：`bilibili_cleanup_cache` 从循环删子目录改为直接删 root，不再调用 `setup_workspace` 先建目录再删。
- **死代码清理**：删除 `visual/extractor.py` 和 `audio/extractor.py` 中从未被调用的 `_parse_time` 方法。
- **依赖同步**：`requirements.txt` 补充 `mcp` 依赖，与 `pyproject.toml` 一致。
- **测试套件修复**：修正 `test_config.py` 断言字符串错误、`test_asr.py` 懒加载适配。

## v0.5.0 (2026-03-03)

### 重大架构更新（三刀重构）
这是一次专注于解决大语言模型“长耗时假死”和“阅读盲区”体验的里程碑式反思与重构：

- **防偷跑严格交互锁**：为视觉与语音提取工具增加 `[CRITICAL SAFETY LOCK]` 安全锁。彻底根除 AI 顺口拿到 URL 时便“无脑”默默下载全片原画导致的磁盘占用和漫长假死，强制所有高耗时操作必需首先停顿并征求用户明确同意。
- **全景故事板雷达（防反转架构）**：废弃原有从头到尾流水抽帧的不合理流程（易导致 AI 提前得出结论从而忽略片尾反转）。新增 `bilibili_gen_storyboard` 工具：以极低画质（360p）将全片均匀切割出缩略图，供大模型以上帝视角总览全局节奏走向。
- **下钻特写机制**：新增 `bilibili_drilldown_frames` 工具，大模型在看完“雷达故事板”后，需精确指定如 `[05:00-05:30]` 来二次请求局部特写，并内建画质协商出口（允许 AI 抱怨看不清并向用户提议使用更高画质）。
- **终审强制回收机制**：新增 `bilibili_cleanup_cache`。规定大模型在执行多模态结论前必须主动回收所有中转产生的 MP4 和 JPG 等多媒体残骸，杜绝磁盘爆满危险。

### 修复与打磨
- **主动式错误导向重塑**：重构 `config.py` 中的底抛异常链路。当缺少豆包 API Key 时，不再面向用户抛出冰冷的程序员栈提示去修改 `.env`，而是改写 Prompt 让 AI 化身为贴心助理主动说：“请将 Key 发给我，我来帮您写入”。
- **环境兜底安抚**：指导大模型在缺少 `ffmpeg` 宿主依赖时，不再崩溃挂起，而是直接抛出对小白极度友好的对应操作系统一键安装命令。

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
