import argparse
import asyncio
import sys

from src.core.api import get_video_info, get_video_subtitles
from src.utils.workspace import setup_workspace
from src.visual.extractor import VisualExtractor

async def async_main():
    parser = argparse.ArgumentParser(description="BiliVision-Agent - B站多模态视频内容获取工具")
    parser.add_argument("url", help="B站视频URL或BV号")
    parser.add_argument("--visual", action="store_true", help="启用深度视觉提取（抽取视频关键帧）")
    parser.add_argument("--start", help="截取开始时间，如 01:30", default=None)
    parser.add_argument("--end", help="截取结束时间，如 02:40", default=None)
    args = parser.parse_args()

    # 极简提取 BV 号（支持输入完整链接）
    bvid = args.url
    if "BV" in bvid:
        bvid = "BV" + bvid.split("BV")[1][:10]

    print(f"[*] 目标视频: {bvid}")
    print("[*] 正在拉取基础文本信息...")

    info = await get_video_info(bvid)
    print("-" * 50)
    print(f"【标题】: {info.get('title', '未知')}")
    print(f"【简介】: {info.get('desc', '无')}")
    print("-" * 50)

    print("[*] 正在尝试抓取 CC 字幕...")
    subtitles = await get_video_subtitles(bvid)
    if subtitles:
         # 截断显示一部分
         preview = subtitles[:200].replace('\n', ' ')
         print(f"【字幕截取】: {preview}...\n(共计 {len(subtitles)} 字符)")
    else:
         print("[!] 检测到该视频未提供 CC 字幕。这可能是一个解说视频或纯画面视频。")
         if not args.visual:
             print("你可以追加以下参数深度解析文本：\n  --visual : 下载视频或抽帧截图\n  --asr    : (开发中) 调用火山引擎提取音频轨")
             return
    print("-" * 50)

    if args.visual:
        print("\n[!] 深度视觉轨道已触发 (--visual)")
        extractor = VisualExtractor(bvid, interval=10)
        dirs = setup_workspace()
        output_dir = dirs["downloads"]
        frame_dir = dirs["frames"]

        if args.start and args.end:
            print("[*] 开始流式切片下载...")
            video_path = extractor.download_video(output_dir, start_time=args.start, end_time=args.end)
        else:
            print("[*] 开始全量下载...")
            video_path = extractor.download_video(output_dir)

        print(f"[*] 视频流临时保存于: {video_path}")
        print("[*] 正在通过 ffmpeg 提取关键帧 (每10秒/帧)...")
        frames = extractor.extract_frames(video_path, output_dir=frame_dir)
        print(f"[*] 成功提取 {len(frames)} 张关键帧 (此为方法验证):")
        for f in frames[:3]:
            print(f"  - {f}")
        print("...")
    else:
        print("\n[i] 未开启视觉提取。如果需要获取视频画面，请加上 --visual 参数。")

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[!] 操作取消")

if __name__ == "__main__":
    main()
