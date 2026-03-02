import pytest
from src.core.api import get_video_info, get_video_subtitles

@pytest.mark.asyncio
async def test_get_video_info():
    info = await get_video_info("BV1xx411c7mD")
    assert "title" in info
    assert "desc" in info

@pytest.mark.asyncio
async def test_get_video_subtitles_returns_list():
    # 返回类型已改为 list[dict]，无论有无字幕都应返回列表
    result = await get_video_subtitles("BV1yH4mzoEnD")
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_get_video_subtitles_structure():
    # 如果有字幕，每条应包含 from/to/content
    result = await get_video_subtitles("BV1yH4mzoEnD")
    if result:
        item = result[0]
        assert "from" in item
        assert "to" in item
        assert "content" in item
