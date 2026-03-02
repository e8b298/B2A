import argparse
import asyncio
import json as json_lib
import sys

from src.core.api import get_video_info, get_video_subtitles, get_page_list, get_cid_by_page
from src.utils.workspace import setup_workspace
from src.utils.url_parser import parse_video_url
from src.visual.extractor import VisualExtractor
from src.audio.extractor import AudioExtractor
from src.core.asr import VolcengineASRClient
from src.utils.config import MissingAuthError


def _format_timestamp(seconds: float) -> str:
    """将秒数格式化为 MM:SS 或 HH:MM:SS"""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def async_main():
    parser = argparse.ArgumentParser(description="B2A (Bilibili to Agents) - B站视频多模态内容提取工具")
    parser.add_argument("url", help="B站视频URL、BV号或AV号")
    parser.add_argument("--visual", action="store_true", help="启用视觉提取（抽取视频关键帧截图）")
    parser.add_argument("--asr", action="store_true", help="启用语音识别（提取音频轨并转文字）")
    parser.add_argument("--start", help="截取开始时间，如 01:30 或 1:03:20", default=None)
    parser.add_argument("--end", help="截取结束时间，如 02:40 或 1:05:00", default=None)
    parser.add_argument("--page", type=int, help="指定分P编号（从1开始）", default=None)
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="输出格式：text（人类可读）或 json（结构化，供 agent 消费）")
    args = parser.parse_args()

    json_mode = args.format == "json"
    output = {}  # JSON 模式下收集所有结果

    # ── 解析用户输入 ──
    try:
        parsed = await parse_video_url(args.url)
    except ValueError as e:
        if json_mode:
            print(json_lib.dumps({"error": str(e)}, ensure_ascii=False))
        else:
            print(f"[!] {e}")
        return

    bvid = parsed.bvid
    page = args.page or parsed.page  # CLI 参数优先，其次 URL 中提取的

    # 如果 URL 中带了 ?t=N 且用户没手动指定 --start，自动设为起始时间
    if parsed.time_start and not args.start:
        args.start = parsed.time_start

    if not json_mode:
        print(f"[*] 目标视频: {bvid}")

    # ── 第一步：拉取视频基础信息 ──
    if not json_mode:
        print("[*] 正在拉取基础文本信息...")

    info = await get_video_info(bvid)
    if json_mode:
        output["video_info"] = info
        output["bvid"] = bvid
    else:
        print("-" * 50)
        print(f"【标题】: {info.get('title', '未知')}")
        print(f"【简介】: {info.get('desc', '无')}")
        print("-" * 50)

    # ── 分P处理 ──
    pages = await get_page_list(bvid)
    cid = None

    if len(pages) > 1:
        if json_mode:
            output["pages"] = pages
        else:
            print(f"[*] 检测到该视频有 {len(pages)} 个分P:")
            for p in pages:
                marker = " <--" if p["page"] == page else ""
                print(f"  P{p['page']}: {p['part']} ({_format_timestamp(p['duration'])}){marker}")

        cid_result = await get_cid_by_page(bvid, page)
        if cid_result:
            cid = cid_result
            if not json_mode:
                print(f"[*] 当前选择: P{page}")
        else:
            if not json_mode:
                print(f"[!] 分P {page} 不存在，回退到 P1")
            page = 1
            cid = pages[0]["cid"] if pages else None
    elif pages:
        cid = pages[0]["cid"]

    if json_mode:
        output["selected_page"] = page

    # ── 第二步：尝试获取 CC 字幕 ──
    if not json_mode:
        print("[*] 正在尝试抓取 CC 字幕...")

    subtitle_data = await get_video_subtitles(bvid, cid=cid)

    if subtitle_data:
        if json_mode:
            output["subtitles"] = subtitle_data
        else:
            print(f"[+] 成功获取 CC 字幕（共 {len(subtitle_data)} 条）")
            preview_lines = subtitle_data[:5]
            for item in preview_lines:
                ts = _format_timestamp(item["from"])
                print(f"  [{ts}] {item['content']}")
            if len(subtitle_data) > 5:
                print(f"  ... 还有 {len(subtitle_data) - 5} 条")
    else:
        if json_mode:
            output["subtitles"] = []
        else:
            print("[!] 该视频未提供 CC 字幕。")

    # ── 如果既无字幕又没指定高级轨道，给出提示后退出 ──
    if not subtitle_data and not args.visual and not args.asr:
        if json_mode:
            output["hint"] = "无 CC 字幕，建议使用 --asr 或 --visual 获取更多信息"
            print(json_lib.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("\n你可以追加以下参数获取更多信息：")
            print("  --asr    : 提取音频轨并语音识别为文字（需配置豆包 API Key）")
            print("  --visual : 下载视频并抽取关键帧截图")
            print("  两者可同时使用，分别对应视频的\"声\"与\"形\"。")
        return

    # 初始化工作区（按视频隔离）
    dirs = None
    if args.asr or args.visual:
        dirs = setup_workspace(bvid=bvid)

    # ── 第三步：ASR 语音识别轨道 ──
    if args.asr:
        if not json_mode:
            print("\n" + "=" * 50)
            print("[*] 语音识别轨道 (ASR)")
            print("=" * 50)
        try:
            asr_client = VolcengineASRClient()
            if not json_mode:
                print("[*] 启动音频轨道抽取...")
            audio_extractor = AudioExtractor(bvid)
            audio_path = audio_extractor.download_audio(
                dirs["audios"],
                start_time=args.start,
                end_time=args.end
            )
            if not json_mode:
                print(f"[*] 音频已保存: {audio_path}")
                print("[*] 正在提交至火山引擎 ASR 进行语音识别...")
            text = await asr_client.transcribe_audio(
                audio_path,
                start_offset=args.start
            )
            if json_mode:
                output["asr"] = {
                    "audio_path": audio_path,
                    "text": text,
                    "start": args.start,
                    "end": args.end
                }
            else:
                print(f"【ASR 识别结果】:\n{text}")
        except MissingAuthError:
            msg = "未配置豆包语音 API Key，跳过 ASR"
            if json_mode:
                output["asr"] = {"error": msg}
            else:
                print(f"[!] 错误: {msg}")
                print("[i] 请在 .env 文件中配置 VOLC_TEST_API_KEY 或 VOLC_PROD_API_KEY。")

    # ── 第四步：视觉抽帧轨道 ──
    if args.visual:
        if not json_mode:
            print("\n" + "=" * 50)
            print("[*] 视觉抽帧轨道 (Visual)")
            print("=" * 50)
        extractor = VisualExtractor(bvid, interval=10)
        output_dir = dirs["downloads"]
        frame_dir = dirs["frames"]

        if args.start and args.end:
            if not json_mode:
                print(f"[*] 切片下载: {args.start} -> {args.end}")
            video_path = extractor.download_video(output_dir, start_time=args.start, end_time=args.end)
        else:
            if not json_mode:
                print("[*] 全量下载...")
            video_path = extractor.download_video(output_dir)

        if not json_mode:
            print(f"[*] 视频已保存: {video_path}")
            print(f"[*] 正在抽取关键帧 (每{extractor.interval}秒/帧)...")

        frames = extractor.extract_frames(video_path, output_dir=frame_dir)

        if json_mode:
            output["visual"] = {
                "video_path": video_path,
                "frames": frames,
                "frame_count": len(frames),
                "interval_seconds": extractor.interval,
                "start": args.start,
                "end": args.end
            }
        else:
            print(f"[+] 成功提取 {len(frames)} 张关键帧:")
            for f in frames:
                print(f"  - {f}")

    # ── 最终输出 ──
    if json_mode:
        print(json_lib.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("\n[*] 完成。")


def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[!] 操作取消")


if __name__ == "__main__":
    main()
