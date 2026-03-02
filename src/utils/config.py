import os
from dotenv import load_dotenv


class MissingAuthError(Exception):
    pass


def load_volc_config() -> dict[str, str]:
    """加载并检查豆包语音 API Key 配置，自动区分测试/生产环境"""
    load_dotenv()
    env = os.getenv("VOLC_ENV", "test").lower()

    if env == "production":
        api_key = os.getenv("VOLC_PROD_API_KEY")
        env_label = "生产环境"
    else:
        api_key = os.getenv("VOLC_TEST_API_KEY")
        env_label = "测试环境"

    placeholders = {"your_test_api_key_here", "your_prod_api_key_here"}
    if not api_key or api_key in placeholders:
        raise MissingAuthError(
            f"缺少豆包语音 API Key（当前: {env_label}）。"
            f"请在根目录 .env 文件中配置对应的 API Key。"
        )

    return {"VOLC_API_KEY": api_key, "VOLC_ENV": env_label}
