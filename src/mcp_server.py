import asyncio
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
import os

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
            "page": target_page,
            "has_cc_subtitles": len(subtitles) > 0,
            "subtitles": "\n".join(formatted_subs) if subtitles else "No CC subtitles available. Consider using bilibili_extract_voice for ASR."
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def bilibili_extract_voice(url: str, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract audio track and perform ASR (Speech-to-Text) using Volcengine API.
    Use this when a video has NO CC subtitles, or you need the absolute true transcript.
    Args:
        url: The video URL or BV id.
        start_time: Optional start offset (e.g., "01:30") to save time.
        end_time: Optional end offset (e.g., "05:00")
    """
    try:
        parsed = await parse_video_url(url)
        bvid = parsed.bvid
        
        target_start = start_time or parsed.time_start
        
        dirs = setup_workspace(bvid=bvid)
        
        asr_client = VolcengineASRClient()
        audio_extractor = AudioExtractor(bvid)
        
        audio_path = audio_extractor.download_audio(
            dirs["audios"],
            start_time=target_start,
            end_time=end_time
        )
        
        text = await asr_client.transcribe_audio(
            audio_path,
            start_offset=target_start
        )
        
        return {
            "bvid": bvid,
            "asr_transcript": text,
            "audio_file_saved_at": audio_path,
            "note": "Timestamps are included in the transcript."
        }
    except Exception as e:
        return {"error": f"ASR Extraction failed. Make sure VOLC_API_KEY is configured in .env. Details: {str(e)}"}

@mcp.tool()
async def bilibili_extract_frames(url: str, interval_seconds: int = 10, start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract visual keyframes from a Bilibili video as Local Image Files.
    Use this when you need to "SEE" the video content (graphs, slides, gameplay).
    The tool returns a list of local image paths. YOU MUST USE YOUR 'Read' TOOL ON THESE IMAGES to actually inspect them.
    Args:
        url: The video URL or BV id.
        interval_seconds: Extract a frame every X seconds (default: 10).
        start_time: Optional start offset (e.g., "01:30") to avoid downloading the whole video.
        end_time: Optional end offset (e.g., "05:00")
    """
    try:
        parsed = await parse_video_url(url)
        bvid = parsed.bvid
        
        target_start = start_time or parsed.time_start
        dirs = setup_workspace(bvid=bvid)
        
        extractor = VisualExtractor(bvid, interval=interval_seconds)
        
        video_path = extractor.download_video(dirs["downloads"], start_time=target_start, end_time=end_time)
        frames = extractor.extract_frames(video_path, output_dir=dirs["frames"])
        
        return {
            "bvid": bvid,
            "action_required": "USE YOUR Read TOOL on the 'extracted_frames' paths below to view the images visually.",
            "interval_seconds": interval_seconds,
            "extracted_frames": frames,
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    """Start the MCP standard IO server"""
    # FastMCP 会自动接管 stdin/stdout 作为 MCP JSON-RPC 协议通道
    mcp.run()

if __name__ == "__main__":
    main()
