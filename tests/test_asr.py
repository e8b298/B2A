import pytest
from src.core.asr import VolcengineASRClient
from src.utils.config import MissingAuthError

def test_asr_client_init_without_env():
    # 虽然可能本地环境没有配环境变量，只要正常实例化或抛出 MissingAuthError 都算符合预期。
    try:
        client = VolcengineASRClient()
        assert client.api_key is not None
    except MissingAuthError:
        pass
