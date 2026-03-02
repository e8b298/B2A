import httpx
from src.utils.config import load_volc_config


class VolcengineASRClient:
    def __init__(self):
        config = load_volc_config()
        self.api_key = config["VOLC_API_KEY"]
        self.env_label = config["VOLC_ENV"]

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        调用豆包语音识别 API。
        使用单 API Key 鉴权模式。
        """
        url = "https://openspeech.bytedance.com/api/v3/asr/submit"
        headers = {
            "Authorization": f"Bearer;{self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "audio": {
                "format": "m4a",
                "url": audio_path
            },
            "addition": {
                "with_timestamp": True
            }
        }

        print(f"[i] 当前环境: {self.env_label}")

        # TODO: 替换为真实的 API 调用
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, json=payload, headers=headers)
        #     response.raise_for_status()
        #     result = response.json()

        return "【00:00】 测试 ASR 识别结果（豆包语音 Mock）"
