import pytest
from src.utils.url_parser import parse_video_url, _seconds_to_time_str, ParsedVideoURL


def test_seconds_to_time_str():
    assert _seconds_to_time_str(0) == "00:00"
    assert _seconds_to_time_str(90) == "01:30"
    assert _seconds_to_time_str(180) == "03:00"
    assert _seconds_to_time_str(3661) == "01:01:01"


@pytest.mark.asyncio
async def test_parse_plain_bvid():
    result = await parse_video_url("BV1xx411c7mD")
    assert result.bvid == "BV1xx411c7mD"
    assert result.page == 1
    assert result.time_start is None


@pytest.mark.asyncio
async def test_parse_full_url_with_params():
    result = await parse_video_url("https://www.bilibili.com/video/BV1xx411c7mD?p=3&t=180")
    assert result.bvid == "BV1xx411c7mD"
    assert result.page == 3
    assert result.time_start == "03:00"


@pytest.mark.asyncio
async def test_parse_url_with_only_page():
    result = await parse_video_url("https://www.bilibili.com/video/BV1xx411c7mD?p=2")
    assert result.bvid == "BV1xx411c7mD"
    assert result.page == 2
    assert result.time_start is None


@pytest.mark.asyncio
async def test_parse_url_with_only_time():
    result = await parse_video_url("https://www.bilibili.com/video/BV1xx411c7mD?t=90")
    assert result.bvid == "BV1xx411c7mD"
    assert result.page == 1
    assert result.time_start == "01:30"


@pytest.mark.asyncio
async def test_parse_invalid_input():
    with pytest.raises(ValueError, match="无法从输入中解析出视频ID"):
        await parse_video_url("这不是一个链接")
