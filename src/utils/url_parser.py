import re
import httpx
from typing import Optional
from dataclasses import dataclass


@dataclass
class ParsedVideoURL:
    """解析后的 B 站视频信息"""
    bvid: str
    page: int = 1          # 分P编号，从 1 开始
    time_start: Optional[str] = None  # 从 URL 中提取的跳转时间（秒 -> MM:SS）


def _seconds_to_time_str(seconds: int) -> str:
    """将秒数转换为 MM:SS 或 HH:MM:SS 格式"""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


async def resolve_short_url(short_url: str) -> str:
    """解析 b23.tv 短链，跟踪重定向拿到最终 URL"""
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        resp = await client.get(short_url)
        return str(resp.url)


async def parse_video_url(raw_input: str) -> ParsedVideoURL:
    """
    解析用户输入的各种格式，统一提取 bvid、分P、时间跳转。
    支持的格式：
      - 纯 BV 号：BV1xx411c7mD
      - 完整链接：https://www.bilibili.com/video/BV1xx411c7mD?p=2&t=180
      - 短链：https://b23.tv/xxxxx
      - AV 号：av170001（转换为 BV 号）
    """
    text = raw_input.strip()

    # 处理 b23.tv 短链
    if "b23.tv" in text:
        text = await resolve_short_url(text)

    page = 1
    time_start = None

    # 提取 ?p=N 分P参数
    p_match = re.search(r'[?&]p=(\d+)', text)
    if p_match:
        page = int(p_match.group(1))

    # 提取 ?t=N 时间跳转参数（秒数）
    t_match = re.search(r'[?&]t=(\d+)', text)
    if t_match:
        time_start = _seconds_to_time_str(int(t_match.group(1)))

    # 提取 BV 号
    bv_match = re.search(r'(BV[A-Za-z0-9]{10})', text)
    if bv_match:
        return ParsedVideoURL(
            bvid=bv_match.group(1),
            page=page,
            time_start=time_start
        )

    # 尝试 AV 号 -> BV 号转换
    av_match = re.search(r'av(\d+)', text, re.IGNORECASE)
    if av_match:
        avid = int(av_match.group(1))
        bvid = await _av_to_bv(avid)
        if bvid:
            return ParsedVideoURL(
                bvid=bvid,
                page=page,
                time_start=time_start
            )

    raise ValueError(f"无法从输入中解析出视频ID: {raw_input}")


async def _av_to_bv(avid: int) -> Optional[str]:
    """通过 B 站 API 将 AV 号转换为 BV 号"""
    url = f"https://api.bilibili.com/x/web-interface/view?aid={avid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/"
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            data = resp.json()
            if data.get("code") == 0:
                return data["data"].get("bvid")
    except Exception:
        pass
    return None
