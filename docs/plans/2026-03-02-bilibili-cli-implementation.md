# Bilibili Hybrid Extractor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个能够在终端一键提取 B站视频文本（字幕/核心信息）并在需要时进行视频关键帧抽取的 Python CLI 工具。

**Architecture:** 
1. `core/` 模块负责请求 B站公共/三方 API 获取视频元数据和 CC 字幕（文本主导）。
2. `cli.py` 提供统一的命令行入口，使用 `argparse` 处理 `--visual` 等参数。
3. `visual/` 模块负责包装 `yt-dlp` 和 `ffmpeg`，在视觉模式下执行视频下载与抽图像流水线（视觉辅助）。

**Tech Stack:** `Python 3.10+`, `httpx` (异步轻量请求), `yt-dlp` (绕过风控下载), `ffmpeg` (抽帧).

---

### Task 1: 初始化项目结构与依赖

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`, `src/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
# tests/test_cli.py
import subprocess

def test_cli_help():
    result = subprocess.run(["python", "-m", "src.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Bilibili Hybrid Extractor" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py -v`

**Step 3: Write minimal implementation**

```python
# src/cli.py
import argparse

def main():
    parser = argparse.ArgumentParser(description="Bilibili Hybrid Extractor - 文本与视觉多模态视频内容提取工具")
    parser.add_argument("url", help="B站视频URL或BV号")
    parser.add_argument("--visual", action="store_true", help="启用深度视觉提取（抽取视频关键帧）")
    args = parser.parse_args()
    print(f"Target: {args.url}, Visual Mode: {args.visual}")

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`

**Step 5: Commit**

```bash
git add requirements.txt src/ tests/
git commit -m "feat: 初始化 Bilibili Extractor 骨架与 CLI 接口"
```

### Task 2: 核心文本轨道 - 绕过风控获取基本信息与字幕

**Files:**
- Create: `src/core/api.py`
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

```python
# tests/test_api.py
import pytest
from src.core.api import get_video_info

@pytest.mark.asyncio
async def test_get_video_info():
    info = await get_video_info("BV1xx411c7mD") # B站知名视频
    assert "title" in info
    assert "desc" in info
```

### Task 3: 深度视觉轨道 - yt-dlp 与 ffmpeg 集成

**Files:**
- Create: `src/visual/extractor.py`
- Create: `tests/test_extractor.py`

**Goal:** 当传入 `--visual` 时，调用 `yt-dlp` 下载指定 BV 号的高清视频/音频，并调用 `ffmpeg` 按设定间隔（如 10 秒）截取关键帧输出图片供大模型阅读。
