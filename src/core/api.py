import httpx
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# === Sync versions (for MCP mode, avoid async httpx polluting anyio event loop) ===

def get_video_info_sync(bvid: str) -> dict:
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            if data.get("code") == 0 and "data" in data:
                video_data = data["data"]
                return {
                    "title": video_data.get("title", ""),
                    "desc": video_data.get("desc", ""),
                    "cid": video_data.get("cid", 0),
                    "duration": video_data.get("duration", 0)
                }
            return {}
    except Exception as e:
        logger.warning("Error fetching video info: %s", e)
        return {}

def get_page_list_sync(bvid: str) -> list[dict]:
    url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, headers=HEADERS)
            res.raise_for_status()
            data = res.json()
            if data.get("code") == 0 and data.get("data"):
                return [
                    {
                        "page": item.get("page", i + 1),
                        "cid": item.get("cid", 0),
                        "part": item.get("part", ""),
                        "duration": item.get("duration", 0)
                    }
                    for i, item in enumerate(data["data"])
                ]
    except Exception as e:
        logger.warning("获取分P列表失败: %s", e)
    return []

def get_cid_by_page_sync(bvid: str, page: int = 1) -> Optional[int]:
    pages = get_page_list_sync(bvid)
    for p in pages:
        if p["page"] == page:
            return p["cid"]
    return None

def get_video_subtitles_sync(bvid: str, cid: Optional[int] = None) -> list[dict]:
    try:
        with httpx.Client(timeout=10.0) as client:
            if not cid:
                pagelist_url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
                res = client.get(pagelist_url, headers=HEADERS)
                res.raise_for_status()
                data = res.json()
                if data.get("code") == 0 and data.get("data"):
                    cid = data["data"][0].get("cid")
                else:
                    return []

            if not cid:
                return []

            player_info_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
            res = client.get(player_info_url, headers=HEADERS)
            res.raise_for_status()
            data = res.json()

            if data.get("code") != 0:
                logger.warning("异常或拦截: 获取播放器信息失败 (%s)", data)
                return []

            sub_data = data.get("data", {}).get("subtitle", {})
            subtitles = sub_data.get("subtitles", [])

            if not subtitles:
                return []

            sub_url = subtitles[0].get("subtitle_url")
            if not sub_url:
                return []

            if sub_url.startswith("//"):
                sub_url = "https:" + sub_url

            sub_res = client.get(sub_url, headers=HEADERS)
            sub_res.raise_for_status()
            sub_json = sub_res.json()

            body = sub_json.get("body", [])
            result = []
            for item in body:
                if "content" in item:
                    result.append({
                        "from": item.get("from", 0),
                        "to": item.get("to", 0),
                        "content": item.get("content", "")
                    })
            return result

    except Exception as e:
        logger.warning("获取视频字幕时出现网络或解析异常: %s", e)
        return []

# === Async versions (for CLI mode) ===

async def get_video_info(bvid: str) -> dict:
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS, timeout=10.0)
            response.raise_for_status()

            data = response.json()
            if data.get("code") == 0 and "data" in data:
                video_data = data["data"]
                return {
                    "title": video_data.get("title", ""),
                    "desc": video_data.get("desc", ""),
                    "cid": video_data.get("cid", 0),
                    "duration": video_data.get("duration", 0)
                }
            return {}
    except Exception as e:
        logger.warning("Error fetching video info: %s", e)
        return {}

async def get_page_list(bvid: str) -> list[dict]:
    """
    获取视频的分P列表。
    返回格式: [{"page": 1, "cid": 12345, "part": "分P标题", "duration": 120}, ...]
    """
    url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=HEADERS, timeout=10.0)
            res.raise_for_status()
            data = res.json()
            if data.get("code") == 0 and data.get("data"):
                return [
                    {
                        "page": item.get("page", i + 1),
                        "cid": item.get("cid", 0),
                        "part": item.get("part", ""),
                        "duration": item.get("duration", 0)
                    }
                    for i, item in enumerate(data["data"])
                ]
    except Exception as e:
        logger.warning("获取分P列表失败: %s", e)
    return []


async def get_cid_by_page(bvid: str, page: int = 1) -> Optional[int]:
    """根据分P编号获取对应的 cid"""
    pages = await get_page_list(bvid)
    for p in pages:
        if p["page"] == page:
            return p["cid"]
    return None


async def get_video_subtitles(bvid: str, cid: Optional[int] = None) -> list[dict]:
    """
    获取视频的CC字幕内容，返回带时间戳的结构化数据。
    返回格式: [{"from": 1.5, "to": 3.2, "content": "字幕文本"}, ...]
    无字幕时返回空列表。
    """
    try:
        if not cid:
            pagelist_url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
            async with httpx.AsyncClient() as client:
                res = await client.get(pagelist_url, headers=HEADERS, timeout=10.0)
                res.raise_for_status()
                data = res.json()
                if data.get("code") == 0 and data.get("data"):
                    cid = data["data"][0].get("cid")
                else:
                    return []

        if not cid:
            return []

        player_info_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        async with httpx.AsyncClient() as client:
            res = await client.get(player_info_url, headers=HEADERS, timeout=10.0)
            res.raise_for_status()
            data = res.json()

            if data.get("code") != 0:
                logger.warning("异常或拦截: 获取播放器信息失败 (%s)", data)
                return []

            sub_data = data.get("data", {}).get("subtitle", {})
            subtitles = sub_data.get("subtitles", [])

            if not subtitles:
                return []

            sub_url = subtitles[0].get("subtitle_url")
            if not sub_url:
                return []

            if sub_url.startswith("//"):
                sub_url = "https:" + sub_url

            sub_res = await client.get(sub_url, headers=HEADERS, timeout=10.0)
            sub_res.raise_for_status()
            sub_json = sub_res.json()

            body = sub_json.get("body", [])
            # 保留完整的时间戳信息
            result = []
            for item in body:
                if "content" in item:
                    result.append({
                        "from": item.get("from", 0),
                        "to": item.get("to", 0),
                        "content": item.get("content", "")
                    })
            return result

    except Exception as e:
        logger.warning("获取视频字幕时出现网络或解析异常: %s", e)
        return []
