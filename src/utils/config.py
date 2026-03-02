import os
from dotenv import load_dotenv

class MissingAuthError(Exception):
    pass

def load_volc_config() -> dict[str, str]:
    """加载并检查火山引擎配置"""
    load_dotenv()
    ak = os.getenv("VOLC_ACCESS_KEY")
    sk = os.getenv("VOLC_SECRET_KEY")
    
    if not ak or not sk or ak == "your_access_key_here":
        raise MissingAuthError("缺少火山引擎 ASR 鉴权信息。请在根目录 .env 文件中配置 VOLC_ACCESS_KEY 和 VOLC_SECRET_KEY。")
        
    return {"VOLC_ACCESS_KEY": ak, "VOLC_SECRET_KEY": sk}
