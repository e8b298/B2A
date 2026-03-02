import httpx
import json
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

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
                    "cid": video_data.get("cid", 0)
                }
            return {}
    except Exception as e:
        print(f"Error fetching video info: {e}")
        return {}

async def get_video_subtitles(bvid: str, cid: Optional[int] = None) -> str:
    """
    获取视频的CC字幕内容。
    1. 如果没有传入cid，先尝试获取cid。
    2. 获取视频播放信息，提取字幕URL。
    3. 请求字幕JSON内容并拼接纯文本。
    """
    try:
        if not cid:
            # 尝试通过 pagelist 获取 cid
            pagelist_url = f"https://api.bilibili.com/x/player/pagelist?bvid={bvid}"
            async with httpx.AsyncClient() as client:
                res = await client.get(pagelist_url, headers=HEADERS, timeout=10.0)
                res.raise_for_status()
                data = res.json()
                if data.get("code") == 0 and data.get("data"):
                    cid = data["data"][0].get("cid")
                else:
                    return ""

        if not cid:
            return ""

        # 获取含有 subtitle url 的 player v2 info
        player_info_url = f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}"
        async with httpx.AsyncClient() as client:
            res = await client.get(player_info_url, headers=HEADERS, timeout=10.0)
            res.raise_for_status()
            data = res.json()
            
            if data.get("code") != 0:
                print(f"异常或拦截: 获取播放器信息失败 ({data})")
                return ""
            
            sub_data = data.get("data", {}).get("subtitle", {})
            subtitles = sub_data.get("subtitles", [])
            
            if not subtitles:
                return ""
                
            # 取第一条字幕
            sub_url = subtitles[0].get("subtitle_url")
            if not sub_url:
                return ""
                
            if sub_url.startswith("//"):
                sub_url = "https:" + sub_url
                
            # 请求字幕JSON内容
            sub_res = await client.get(sub_url, headers=HEADERS, timeout=10.0)
            sub_res.raise_for_status()
            sub_json = sub_res.json()
            
            body = sub_json.get("body", [])
            text_lines = [item.get("content", "") for item in body if "content" in item]
            
            return "\n".join(text_lines)
            
    except Exception as e:
        print(f"获取视频字幕时出现网络或解析异常: {e}")
        return ""
