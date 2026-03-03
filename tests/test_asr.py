import pytest
from unittest.mock import patch, MagicMock
from src.core.asr import VolcengineASRClient, MAX_CHUNK_DURATION
from src.utils.config import MissingAuthError

def test_asr_client_init_without_env():
    # 懒加载改造后，__init__ 不再读取 Key，只验证实例能正常创建
    client = VolcengineASRClient()
    assert hasattr(client, 'url')
    assert not hasattr(client, 'api_key')

def test_asr_parse_time():
    """测试时间解析工具方法"""
    assert VolcengineASRClient._parse_time("01:30") == 90.0
    assert VolcengineASRClient._parse_time("1:03:20") == 3800.0
    assert VolcengineASRClient._parse_time("00:00") == 0.0
    assert VolcengineASRClient._parse_time("10:00") == 600.0

def test_asr_extract_result_with_offset():
    """测试时间戳偏移修正"""
    try:
        client = VolcengineASRClient()
    except MissingAuthError:
        client = object.__new__(VolcengineASRClient)

    mock_response = {
        "result": {
            "utterances": [
                {"start_time": 0, "text": "大家好"},
                {"start_time": 5000, "text": "今天我们来聊一下"},
            ]
        }
    }

    result_no_offset = client._extract_result(mock_response, offset_ms=0)
    assert "[00:00]" in result_no_offset
    assert "[00:05]" in result_no_offset

    result_with_offset = client._extract_result(mock_response, offset_ms=200000)
    assert "[03:20]" in result_with_offset
    assert "[03:25]" in result_with_offset

def test_max_chunk_duration_constant():
    """确认分片阈值常量存在且合理"""
    assert MAX_CHUNK_DURATION > 0
    assert MAX_CHUNK_DURATION == 60

def test_get_audio_duration_missing_file():
    """不存在的文件应返回 0"""
    duration = VolcengineASRClient._get_audio_duration("nonexistent_file.m4a")
    assert duration == 0.0

def test_split_audio_calls_ffmpeg():
    """分片方法应正确调用 ffmpeg"""
    with patch('subprocess.run') as mock_run, \
         patch('os.listdir', return_value=[
             "test_chunk_000.m4a",
             "test_chunk_001.m4a",
             "test_chunk_002.m4a"
         ]), \
         patch('os.path.dirname', return_value="workspace/audios"):
        chunks = VolcengineASRClient._split_audio("workspace/audios/test.m4a")
        mock_run.assert_called_once()
        assert len(chunks) == 3
