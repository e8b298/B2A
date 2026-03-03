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
    env_var_name = "VOLC_PROD_API_KEY" if env == "production" else "VOLC_TEST_API_KEY"
    if not api_key or api_key in placeholders:
        raise MissingAuthError(
            f"[B2A 语音服务] 当前缺少豆包语音识别的 API Key（{env_label}）。"
            f"请你直接询问用户：'如果您想使用语音转写功能，请提供豆包(Volcengine)的 API Key，"
            f"直接发给我即可，我来帮您自动写入配置。'"
            f"收到用户提供的 Key 后，请使用文件写入工具将其追加到项目根目录的 .env 文件中，"
            f"格式为：{env_var_name}=用户提供的Key。"
            f"写入完成后重新调用本工具即可。"
        )

    return {"VOLC_API_KEY": api_key, "VOLC_ENV": env_label}
