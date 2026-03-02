import base64
import uuid
import httpx
from src.utils.config import load_volc_config


class VolcengineASRClient:
    def __init__(self):
        config = load_volc_config()
        self.api_key = config["VOLC_API_KEY"]
        self.env_label = config["VOLC_ENV"]
        self.url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        调用豆包语音 BigModel Flash API 进行语音识别。
        将本地音频文件 base64 编码后同步提交，返回带时间戳的识别文本。
        """
        print(f"[i] 当前环境: {self.env_label}")

        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        encoded_audio = base64.b64encode(audio_data).decode('utf-8')
        req_id = str(uuid.uuid4())

        # 根据文件后缀判断音频格式
        fmt = "m4a"
        if audio_path.endswith(".mp3"):
            fmt = "mp3"
        elif audio_path.endswith(".wav"):
            fmt = "wav"

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "X-Api-Resource-Id": "volc.seedasr.auc",
            "X-Api-Request-Id": req_id,
            "X-Api-Sequence": "-1"
        }

        payload = {
            "user": {
                "uid": "bilivision_agent"
            },
            "audio": {
                "format": fmt,
                "codec": "raw",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
                "data": encoded_audio
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True,
                "enable_punc": True,
                "show_utterances": True
            }
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(self.url, headers=headers, json=payload)

                if response.status_code != 200:
                    print(f"[!] ASR 请求失败 (HTTP {response.status_code}): {response.text[:200]}")
                    if attempt < max_retries - 1:
                        continue
                    return f"[ASR 错误 {response.status_code}]"

                resp_json = response.json()
                result = self._extract_result(resp_json)
                if result:
                    return result

                print(f"[!] ASR 第 {attempt+1} 次尝试未获得有效结果")
                if attempt < max_retries - 1:
                    continue
                return "[ASR 未能识别出文本内容]"

            except Exception as e:
                print(f"[!] ASR 异常 (第 {attempt+1} 次): {e}")
                if attempt < max_retries - 1:
                    continue
                return f"[ASR 异常: {e}]"

        return "[ASR 失败: 超过最大重试次数]"

    def _extract_result(self, resp_json: dict) -> str:
        """从 API 响应中提取带时间戳的文本"""
        result = resp_json.get("result")
        if not result:
            return ""

        # 提取 utterances（带时间戳的句子列表）
        utterances = []
        if isinstance(result, dict):
            utterances = result.get("utterances", [])
        elif isinstance(result, list) and len(result) > 0:
            utterances = result[0].get("utterances", [])

        if utterances:
            lines = []
            for u in utterances:
                start_ms = u.get("start_time", 0)
                text = u.get("text", "")
                mins = start_ms // 60000
                secs = (start_ms % 60000) // 1000
                lines.append(f"[{mins:02d}:{secs:02d}] {text}")
            return "\n".join(lines)

        # 没有 utterances 时退回纯文本
        if isinstance(result, dict) and "text" in result:
            return result["text"]

        return ""
