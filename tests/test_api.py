import pytest
from src.core.api import get_video_info, get_video_subtitles

@pytest.mark.asyncio
async def test_get_video_info():
    info = await get_video_info("BV1xx411c7mD")
    assert "title" in info
    assert "desc" in info

@pytest.mark.asyncio
async def test_get_video_subtitles():
    # 测试获取字幕，B站官方视频等可能有字幕
    # BV1yH4mzoEnD (如果实际不存在或403则返回字符串)
    text = await get_video_subtitles("BV1yH4mzoEnD")
    assert isinstance(text, str)
