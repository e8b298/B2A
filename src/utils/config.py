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
            f"请告知用户：'检测到您需要使用无字幕识别功能。为了顺畅使用，您可以前往 [火山引擎控制台](https://console.volcengine.com/speech/app) 获取豆包平台的 API Key。"
            f"获取后请直接将 Key 的字符串发给我即可，不需要任何特定的话术格式，我会自动帮您存储并应用。'"
            f"当用户回复了包含 Key 的文本时，请自动辨识出字符串，并使用文件写入工具将其以 {env_var_name}=提取出的KEY 追加写入到项目根目录的 .env 文件中。"
        )

    return {"VOLC_API_KEY": api_key, "VOLC_ENV": env_label}
