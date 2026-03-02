import pytest
from src.utils.config import load_volc_config, MissingAuthError

def test_load_volc_config_missing_auth(monkeypatch):
    monkeypatch.delenv("VOLC_ACCESS_KEY", raising=False)
    monkeypatch.delenv("VOLC_SECRET_KEY", raising=False)
    
    with pytest.raises(MissingAuthError) as exc_info:
        load_volc_config()
    
    assert "缺少火山引擎 ASR 鉴权信息" in str(exc_info.value)

def test_load_volc_config_dummy_value(monkeypatch):
    monkeypatch.setenv("VOLC_ACCESS_KEY", "your_access_key_here")
    monkeypatch.setenv("VOLC_SECRET_KEY", "your_secret_key_here")
    
    with pytest.raises(MissingAuthError):
        load_volc_config()

def test_load_volc_config_success(monkeypatch):
    monkeypatch.setenv("VOLC_ACCESS_KEY", "real_ak")
    monkeypatch.setenv("VOLC_SECRET_KEY", "real_sk")
    
    config = load_volc_config()
    assert config["VOLC_ACCESS_KEY"] == "real_ak"
    assert config["VOLC_SECRET_KEY"] == "real_sk"
