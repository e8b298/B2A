"""
Subprocess worker for running yt-dlp downloads and ffmpeg operations
outside the MCP process to avoid stdin/stdout interference.

Usage: python -m src.utils.subprocess_worker <command> <json_args>
Commands: download_video, download_audio, extract_frames
"""
import json
import sys
import os

# Ensure project root is on path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def cmd_download_video(args):
    from src.visual.extractor import VisualExtractor
    ext = VisualExtractor(
        bvid=args["bvid"],
        interval=args.get("interval", 10),
        quality=args.get("quality", "480p")
    )
    path = ext.download_video(
        args["output_dir"],
        start_time=args.get("start_time"),
        end_time=args.get("end_time")
    )
    return {"video_path": path}


def cmd_extract_frames(args):
    from src.visual.extractor import VisualExtractor
    ext = VisualExtractor(
        bvid=args["bvid"],
        interval=args.get("interval", 10),
        quality=args.get("quality", "480p")
    )
    frames = ext.extract_frames(args["video_path"], output_dir=args["output_dir"])
    return {"frames": frames}


def cmd_download_audio(args):
    from src.audio.extractor import AudioExtractor
    ext = AudioExtractor(bvid=args["bvid"])
    path = ext.download_audio(
        args["output_dir"],
        start_time=args.get("start_time"),
        end_time=args.get("end_time")
    )
    return {"audio_path": path}


COMMANDS = {
    "download_video": cmd_download_video,
    "download_audio": cmd_download_audio,
    "extract_frames": cmd_extract_frames,
}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: subprocess_worker <command> <json_args>"}))
        sys.exit(1)

    command = sys.argv[1]
    try:
        args = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON args: {e}"}))
        sys.exit(1)

    func = COMMANDS.get(command)
    if not func:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)

    try:
        result = func(args)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
