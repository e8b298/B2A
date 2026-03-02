import pytest
from src.utils.config import load_volc_config, MissingAuthError

def test_load_volc_config_missing_auth(monkeypatch):
    monkeypatch.setenv("VOLC_TEST_API_KEY", "")
    monkeypatch.setenv("VOLC_PROD_API_KEY", "")
    monkeypatch.delenv("VOLC_ENV", raising=False)

    with pytest.raises(MissingAuthError) as exc_info:
        load_volc_config()

    assert "缺少豆包语音 API Key" in str(exc_info.value)

def test_load_volc_config_dummy_value(monkeypatch):
    monkeypatch.setenv("VOLC_TEST_API_KEY", "your_test_api_key_here")
    monkeypatch.delenv("VOLC_ENV", raising=False)

    with pytest.raises(MissingAuthError):
        load_volc_config()

def test_load_volc_config_success_test_env(monkeypatch):
    monkeypatch.setenv("VOLC_ENV", "test")
    monkeypatch.setenv("VOLC_TEST_API_KEY", "13b7cc0e-56b4-442f-9df1-bd2a65dbe2f6")

    config = load_volc_config()
    assert config["VOLC_API_KEY"] == "13b7cc0e-56b4-442f-9df1-bd2a65dbe2f6"
    assert config["VOLC_ENV"] == "测试环境"

def test_load_volc_config_success_prod_env(monkeypatch):
    monkeypatch.setenv("VOLC_ENV", "production")
    monkeypatch.setenv("VOLC_PROD_API_KEY", "some-prod-key")

    config = load_volc_config()
    assert config["VOLC_API_KEY"] == "some-prod-key"
    assert config["VOLC_ENV"] == "生产环境"
