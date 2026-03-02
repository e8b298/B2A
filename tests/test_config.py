import pytest
from src.utils.config import load_volc_config, MissingAuthError

def test_load_volc_config_missing_auth(monkeypatch):
    monkeypatch.delenv("VOLC_TEST_ACCESS_KEY", raising=False)
    monkeypatch.delenv("VOLC_TEST_SECRET_KEY", raising=False)
    monkeypatch.delenv("VOLC_PROD_ACCESS_KEY", raising=False)
    monkeypatch.delenv("VOLC_PROD_SECRET_KEY", raising=False)
    monkeypatch.delenv("VOLC_ENV", raising=False)

    with pytest.raises(MissingAuthError) as exc_info:
        load_volc_config()

    assert "缺少火山引擎 ASR 鉴权信息" in str(exc_info.value)

def test_load_volc_config_dummy_value(monkeypatch):
    monkeypatch.setenv("VOLC_TEST_ACCESS_KEY", "your_test_access_key_here")
    monkeypatch.setenv("VOLC_TEST_SECRET_KEY", "dummy_sk")
    monkeypatch.delenv("VOLC_ENV", raising=False)

    with pytest.raises(MissingAuthError):
        load_volc_config()

def test_load_volc_config_success_test_env(monkeypatch):
    monkeypatch.setenv("VOLC_ENV", "test")
    monkeypatch.setenv("VOLC_TEST_ACCESS_KEY", "real_test_ak")
    monkeypatch.setenv("VOLC_TEST_SECRET_KEY", "real_test_sk")

    config = load_volc_config()
    assert config["VOLC_ACCESS_KEY"] == "real_test_ak"
    assert config["VOLC_ENV"] == "测试环境"

def test_load_volc_config_success_prod_env(monkeypatch):
    monkeypatch.setenv("VOLC_ENV", "production")
    monkeypatch.setenv("VOLC_PROD_ACCESS_KEY", "real_prod_ak")
    monkeypatch.setenv("VOLC_PROD_SECRET_KEY", "real_prod_sk")

    config = load_volc_config()
    assert config["VOLC_ACCESS_KEY"] == "real_prod_ak"
    assert config["VOLC_ENV"] == "生产环境"
