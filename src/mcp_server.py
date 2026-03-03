import asyncio
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
import os
import shutil

from src.core.api import get_video_info, get_video_subtitles, get_page_list, get_cid_by_page
from src.utils.url_parser import parse_video_url
from src.utils.workspace import setup_workspace
from src.core.asr import VolcengineASRClient
from src.audio.extractor import AudioExtractor
from src.visual.extractor import VisualExtractor

# 初始化 FastMCP 服务器
mcp = FastMCP("B2A-Agent-Vision")

def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

@mcp.tool()
async def bilibili_get_info_subtitles(url: str, page: Optional[int] = None) -> Dict[str, Any]:
    """
    Get Bilibili video metadata and CC subtitles (The fastest way to understand a video).
    Use this FIRST for any bilibili URL/BV to get the title, description, and available CC transcript.
    Args:
        url: The video URL, BV id (e.g., BV1xx411c7mD), or shortlink (b23.tv)
        page: Optional part number (for multi-part videos, 1-indexed)
    """
    try:
        parsed = await parse_video_url(url)
        bvid = parsed.bvid
        target_page = page or parsed.page

        info = await get_video_info(bvid)

        cid = None
        pages = await get_page_list(bvid)
        if len(pages) > 1:
            cid_result = await get_cid_by_page(bvid, target_page)
            if cid_result:
                cid = cid_result
            else:
                cid = pages[0]["cid"]
                target_page = 1
        elif pages:
            cid = pages[0]["cid"]

        subtitles = await get_video_subtitles(bvid, cid=cid)
        formatted_subs = []
        for item in subtitles:
            ts = _format_timestamp(item["from"])
            formatted_subs.append(f"[{ts}] {item['content']}")

        return {
            "bvid": bvid,
            "title": info.get("title", ""),
            "description": info.get("desc", ""),
            "duration": _format_timestamp(info.get("duration", 0)),
            "duration_seconds": info.get("duration", 0),
            "page": target_page,
            "has_cc_subtitles": len(subtitles) > 0,
            "subtitles": "\n".join(formatted_subs) if subtitles else "这个视频没有自带字幕。你可以尝试去听一下视频内容（bilibili_extract_voice，注意只能识别人声语音，纯音乐/音效无法识别），或者去看一下视频画面（bilibili_gen_storyboard）来理解它。"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def bilibili_extract_voice(url: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    [CRITICAL SAFETY LOCK]: NEVER call this tool in the same turn as your question. You MUST ask the user first AND wait for their explicit reply in a SEPARATE turn before calling this tool. Asking and calling in the same message is FORBIDDEN.
    [CRITICAL EQ RULE]: You are trying to LISTEN to the video to understand it, not "extracting audio for the user". Speak naturally! Tell the user: "这个视频没有字幕，我可以试着去听一下视频里说了什么吗？可能需要稍等几十秒哦~ 不过要提醒你，我的'听力'其实是语音识别，所以只能听懂人说的话，纯音乐或音效我是听不出来的～" Then STOP and WAIT for the user to reply. ONLY call this tool AFTER the user agrees in a subsequent message.
    [ENV RELOAD NOTE]: If the user JUST provided an API Key and you saved it to .env, do NOT retry this tool immediately. The MCP server process needs to be restarted to pick up the new key. Tell the user naturally: "Key 已经帮你存好啦！不过需要在设置里重启一下 MCP 服务让配置生效，重启完告诉我一声，我马上继续～" Do NOT loop-retry after a MissingAuthError if the key was just written.
    [WAIT TIME WARNING]: This tool may take several minutes to complete. BEFORE calling it, send a message to the user: "好，让我去听听看，视频比较长可能需要等几分钟～"

    Extract audio track and perform ASR (Speech-to-Text) using Volcengine API.
    Use this when a video has NO CC subtitles, or you need the absolute true transcript.
    Args:
        url: The video URL or BV id.
        start_time: Optional start offset (e.g., "01:30") to save time.
        end_time: Optional end offset (e.g., "05:00")
    """
    try:
        # [FAIL FAST]: 下载前先校验 Key，避免等几分钟下载完才发现没有 Key
        from src.utils.config import load_volc_config
        load_volc_config()

        parsed = await parse_video_url(url)
        bvid = parsed.bvid

        target_start = start_time or parsed.time_start

        dirs = setup_workspace(bvid=bvid)

        asr_client = VolcengineASRClient()
        audio_extractor = AudioExtractor(bvid)

        audio_path = await asyncio.to_thread(
            audio_extractor.download_audio,
            dirs["audios"],
            start_time=target_start,
            end_time=end_time
        )

        text = await asr_client.transcribe_audio(
            audio_path,
            start_offset=target_start
        )

        # 无人声时给 AI 明确的引导，而不是返回空字符串
        if not text or not text.strip():
            text = "[ASR 未识别到人声内容。这段音频可能是纯音乐、环境音或无对白片段，请据此回复用户。]"

        return {
            "bvid": bvid,
            "asr_transcript": text,
            "audio_file_saved_at": audio_path,
            "note": "Timestamps are included in the transcript. PLEASE call bilibili_cleanup_cache when you are done with this task!"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def bilibili_gen_storyboard(url: str, video_duration_seconds: int) -> Dict[str, Any]:
    """
    [CRITICAL SAFETY LOCK]: NEVER call this tool in the same turn as your question. You MUST ask the user first AND wait for their explicit reply in a SEPARATE turn before calling this tool. Asking and calling in the same message is FORBIDDEN.
    [CRITICAL EQ RULE]: You are trying to WATCH the video to understand it, not "extracting frames for the user". Do NOT act like a robot! Simply ask the user naturally like a friend: "我可以看一下这个视频的画面吗？我会快速浏览一遍大致了解内容，可能需要等一小会儿。" Then STOP and WAIT for the user to reply. ONLY call this tool AFTER the user agrees in a subsequent message.
    [PREREQUISITE CHECK]: Do NOT call this tool if there is an unresolved ASR/API Key error from a previous tool call in this conversation. Resolve the auth issue first before switching to visual analysis.
    [WAIT TIME WARNING]: This tool downloads a full video and may take 2-5 minutes. BEFORE calling it, tell the user: "好，让我去看看这个视频，需要一点时间加载画面，稍等哦～"

    [Storyboard Reading]: This tool acts as a radar. It uniformly samples roughly 30 frames across the entire video.
    ALWAYS use this BEFORE drilling down into specific timeframes to avoid missing plot twists.
    Quality is strictly forced to 360p to save time and bandwidth.

    Args:
        url: The video URL or BV id.
        video_duration_seconds: The total duration in seconds (get this from bilibili_get_info_subtitles first).
    """
    try:
        parsed = await parse_video_url(url)
        bvid = parsed.bvid
        dirs = setup_workspace(bvid=bvid)

        interval = max(int(video_duration_seconds / 30), 2)

        extractor = VisualExtractor(bvid, interval=interval, quality="360p")
        video_path = await asyncio.to_thread(extractor.download_video, dirs["downloads"])
        frames = await asyncio.to_thread(extractor.extract_frames, video_path, output_dir=dirs["frames"])

        return {
            "bvid": bvid,
            "action_required": "[SYSTEM EVENT: Storyboard is ready. YOU MUST NOT explain the process. Directly look at the images in extracted_frames and answer the user.]",
            "interval_seconds_used": interval,
            "quality": "360p",
            "extracted_frames": frames,
            "note": "If you cannot read text clearly due to 360p quality, explicitly ask the user for permission to use bilibili_drilldown_frames with 720p/1080p for a SPECIFIC SHORT timeframe."
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def bilibili_drilldown_frames(url: str, start_time: str, end_time: str, quality: str = "480p", interval_seconds: int = 5) -> Dict[str, Any]:
    """
    [Drilldown Reading]: Use this AFTER looking at the storyboard (bilibili_gen_storyboard), or if you strictly need a specific time segment.
    Downloads and extracts frames strictly within the [start_time, end_time] window.
    [WAIT TIME WARNING]: This tool downloads a video segment and may take 1-3 minutes. BEFORE calling it, tell the user: "让我仔细看看这一段的画面，稍等一下～"

    Args:
        url: The video URL or BV id.
        start_time: Mandatory start offset (e.g., "05:00").
        end_time: Mandatory end offset (e.g., "05:30"). Keep the window small (under 3 mins ideally).
        quality: "360p", "480p", "720p", "1080p". Default 480p. ONLY request "720p" or "1080p" if you proved the text is unreadable AND the user approved it.
        interval_seconds: Extract a frame every X seconds (default: 5).
    """
    try:
        parsed = await parse_video_url(url)
        bvid = parsed.bvid
        dirs = setup_workspace(bvid=bvid)

        extractor = VisualExtractor(bvid, interval=interval_seconds, quality=quality)
        video_path = await asyncio.to_thread(
            extractor.download_video, dirs["downloads"], start_time=start_time, end_time=end_time
        )
        frames = await asyncio.to_thread(extractor.extract_frames, video_path, output_dir=dirs["frames"])

        return {
            "bvid": bvid,
            "action_required": f"USE YOUR Read TOOL on the 'extracted_frames' below.",
            "time_window": f"{start_time} to {end_time}",
            "quality": quality,
            "interval_seconds": interval_seconds,
            "extracted_frames": frames,
            "note": "When you have finished analyzing the images and answered the user, YOU MUST call bilibili_cleanup_cache to free space!"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def bilibili_cleanup_cache(bvid: str) -> Dict[str, Any]:
    """
    [CRITICAL CLEANUP TOOL]: Calling this tool deletes all downloaded videos, audio, and extracted frames for a given video.
    You MUST call this tool automatically at the end of your conversation/task when you have provided the final answer to the user to prevent disk bloating.

    Args:
        bvid: The BV id of the target video (e.g., BV1xx411c7mD).
    """
    try:
        # [SECURITY LOCK]: 防止传入路径回退或非法的字符串导致灾难性的越界删库
        if not bvid or ".." in bvid or "/" in bvid or "\\" in bvid or not str(bvid).startswith("BV"):
            return {"error": f"Invalid BVID '{bvid}'. Cleanup rejected for safety reasons."}
            
        # 直接用绝对路径推算目标目录，不通过 setup_workspace（避免先建目录再删）
        from src.utils.workspace import _DEFAULT_BASE
        root_path = os.path.join(_DEFAULT_BASE, bvid)
        if os.path.exists(root_path):
            shutil.rmtree(root_path)

        return {
            "status": "success",
            "message": f"Successfully cleaned up all media cache for {bvid}. Disk space recovered."
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    """Start the MCP standard IO server"""
    # FastMCP 会自动接管 stdin/stdout 作为 MCP JSON-RPC 协议通道
    mcp.run()

if __name__ == "__main__":
    main()