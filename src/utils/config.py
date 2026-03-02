import os
from dotenv import load_dotenv


class MissingAuthError(Exception):
    pass


def load_volc_config() -> dict[str, str]:
    """加载并检查火山引擎配置，自动区分测试/生产环境"""
    load_dotenv()
    env = os.getenv("VOLC_ENV", "test").lower()

    if env == "production":
        ak = os.getenv("VOLC_PROD_ACCESS_KEY")
        sk = os.getenv("VOLC_PROD_SECRET_KEY")
        env_label = "生产环境"
    else:
        ak = os.getenv("VOLC_TEST_ACCESS_KEY")
        sk = os.getenv("VOLC_TEST_SECRET_KEY")
        env_label = "测试环境"

    placeholders = {"your_test_access_key_here", "your_prod_access_key_here", "your_access_key_here"}
    if not ak or not sk or ak in placeholders:
        raise MissingAuthError(
            f"缺少火山引擎 ASR 鉴权信息（当前: {env_label}）。"
            f"请在根目录 .env 文件中配置对应的 ACCESS_KEY 和 SECRET_KEY。"
        )

    return {"VOLC_ACCESS_KEY": ak, "VOLC_SECRET_KEY": sk, "VOLC_ENV": env_label}
