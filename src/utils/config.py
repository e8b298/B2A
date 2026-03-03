import os
from pathlib import Path
from dotenv import load_dotenv

class MissingAuthError(Exception):
    pass

# .env 文件固定存放在用户主目录下，不跟随项目源码目录
# 这样无论 MCP 进程从哪个 cwd 启动，都不会污染项目发布目录
_ENV_PATH = Path.home() / ".b2a" / ".env"


def load_volc_config() -> dict[str, str]:
    """加载并检查豆包语音 API Key 配置，自动区分测试/生产环境"""
    # 优先加载用户主目录下的 ~/.b2a/.env，同时兼容项目根目录的 .env（向后兼容）
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH, override=True)
    else:
        load_dotenv(override=True)
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
        env_file_path = str(_ENV_PATH)
        raise MissingAuthError(
            f"Voice ASR API Key is missing ({env_label}). "
            f"ACTION REQUIRED FOR AI: Do NOT apologize mechanically. Talk to the user in a very natural, high-EQ human tone. "
            f"Say something like: '这档视频没有字幕，如果要听译的话，我需要用到豆包的 API Key 授权哦~ 您可以点这个链接申请：https://console.volcengine.com/speech/app 。申请完直接把那一串字母丢给我就行，我来帮您配！' "
            f"When user provides the key, first create the directory '{_ENV_PATH.parent}' if it does not exist, "
            f"then use your edit/write tool to save '{env_var_name}=<key>' into the file '{env_file_path}'. "
            f"NEVER write .env into the project source directory — always use '{env_file_path}'."
        )

    return {"VOLC_API_KEY": api_key, "VOLC_ENV": env_label}
