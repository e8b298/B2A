import base64
import os
import subprocess
import uuid
import httpx
from src.utils.config import load_volc_config
from src.utils.logger import get_logger

logger = get_logger()

# 单次 ASR 请求的最大音频时长（秒）。超过此值将自动分片。
MAX_CHUNK_DURATION = 60


class VolcengineASRClient:
    def __init__(self):
        # 不在初始化时读取 Key，避免 MCP 长驻进程缓存旧环境变量
        self.url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/recognize/flash"

    def _load_credentials(self):
        """在实际调用前才读取 Key，保证每次都能拿到最新的 .env 值"""
        config = load_volc_config()
        self.api_key = config["VOLC_API_KEY"]
        self.env_label = config["VOLC_ENV"]

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """解析 HH:MM:SS 或 MM:SS 格式为秒数"""
        parts = time_str.split(':')
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds

    @staticmethod
    def _get_audio_duration(audio_path: str) -> float:
        """通过 ffprobe 获取音频文件的时长（秒）"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    @staticmethod
    def _split_audio(audio_path: str, chunk_duration: int = MAX_CHUNK_DURATION) -> list[str]:
        """
        将音频文件按指定时长切割为多个片段。
        返回片段文件路径列表。
        """
        output_dir = os.path.dirname(audio_path)
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        ext = os.path.splitext(audio_path)[1]  # 保持原始格式

        pattern = os.path.join(output_dir, f"{base_name}_chunk_%03d{ext}")

        subprocess.run(
            ['ffmpeg', '-y', '-i', audio_path,
             '-f', 'segment', '-segment_time', str(chunk_duration),
             '-c', 'copy', pattern],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )

        # 收集生成的分片文件
        chunks = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith(f"{base_name}_chunk_") and f.endswith(ext)
        ])
        return chunks

    def transcribe_audio_sync(self, audio_path: str, start_offset: str = None) -> str:
        """
        同步版本的语音识别入口。
        在 MCP 模式下通过 anyio.to_thread.run_sync 调用，
        避免 async httpx 与 anyio 事件循环冲突导致 stdout 写入卡死。
        """
        self._load_credentials()
        logger.info("当前环境: %s", self.env_label)

        offset_ms = 0
        if start_offset:
            offset_ms = int(self._parse_time(start_offset) * 1000)
            logger.info("时间戳偏移: +%s (%dms)", start_offset, offset_ms)

        with httpx.Client(timeout=120.0) as client:
            duration = self._get_audio_duration(audio_path)
            if duration > MAX_CHUNK_DURATION:
                logger.info("音频时长 %.0fs 超过 %ds，启动自动分片...", duration, MAX_CHUNK_DURATION)
                return self._transcribe_chunked_sync(client, audio_path, offset_ms)
            else:
                return self._transcribe_single_sync(client, audio_path, offset_ms)

    def _transcribe_single_sync(self, client: httpx.Client, audio_path: str, offset_ms: int = 0) -> str:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        encoded_audio = base64.b64encode(audio_data).decode('utf-8')
        return self._call_asr_api_sync(client, encoded_audio, audio_path, offset_ms)

    def _transcribe_chunked_sync(self, client: httpx.Client, audio_path: str, offset_ms: int = 0) -> str:
        chunks = self._split_audio(audio_path)
        logger.info("已切割为 %d 个片段", len(chunks))

        all_lines = []
        chunk_offset_ms = offset_ms

        for i, chunk_path in enumerate(chunks):
            logger.info("正在识别第 %d/%d 段...", i + 1, len(chunks))
            with open(chunk_path, 'rb') as f:
                audio_data = f.read()
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            result = self._call_asr_api_sync(client, encoded_audio, chunk_path, chunk_offset_ms)

            if result and not result.startswith("[ASR"):
                all_lines.append(result)

            chunk_duration = self._get_audio_duration(chunk_path)
            chunk_offset_ms += int(chunk_duration * 1000)

            try:
                os.remove(chunk_path)
            except OSError:
                pass

        if all_lines:
            return "\n".join(all_lines)
        return "[ASR 未识别到人声内容。这段音频可能是纯音乐、环境音或无对白片段。]"

    def _call_asr_api_sync(self, client: httpx.Client, encoded_audio: str, audio_path: str, offset_ms: int) -> str:
        """同步版 ASR 请求"""
        req_id = str(uuid.uuid4())

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
                "uid": "b2a_agent"
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
                response = client.post(self.url, headers=headers, json=payload)

                if response.status_code != 200:
                    logger.warning("ASR 请求失败 (HTTP %d): %s", response.status_code, response.text[:200])
                    if attempt < max_retries - 1:
                        continue
                    return f"[ASR 错误 {response.status_code}]"

                resp_json = response.json()

                if resp_json.get("code", -1) == 0 or "result" in resp_json:
                    result = self._extract_result(resp_json, offset_ms)
                    if result:
                        return result
                    return ""

                logger.warning("ASR 第 %d 次尝试返回异常 code: %s", attempt+1, resp_json.get('code'))
                if attempt < max_retries - 1:
                    continue
                return "[ASR 未识别到人声内容。这段音频可能是纯音乐、环境音或无对白片段。]"

            except Exception as e:
                logger.warning("ASR 异常 (第 %d 次): %s", attempt+1, e)
                if attempt < max_retries - 1:
                    continue
                return f"[ASR 异常: {e}]"

        return "[ASR 失败: 超过最大重试次数]"

    # === async 版本保留给 CLI 使用 ===

    async def transcribe_audio(self, audio_path: str, start_offset: str = None) -> str:
        """
        异步版本，仅供 CLI 模式使用。MCP 模式请用 transcribe_audio_sync。
        """
        self._load_credentials()
        logger.info("当前环境: %s", self.env_label)

        offset_ms = 0
        if start_offset:
            offset_ms = int(self._parse_time(start_offset) * 1000)
            logger.info("时间戳偏移: +%s (%dms)", start_offset, offset_ms)

        async with httpx.AsyncClient(timeout=120.0) as client:
            duration = self._get_audio_duration(audio_path)
            if duration > MAX_CHUNK_DURATION:
                logger.info("音频时长 %.0fs 超过 %ds，启动自动分片...", duration, MAX_CHUNK_DURATION)
                return await self._transcribe_chunked_async(client, audio_path, offset_ms)
            else:
                return await self._transcribe_single_async(client, audio_path, offset_ms)

    async def _transcribe_single_async(self, client: httpx.AsyncClient, audio_path: str, offset_ms: int = 0) -> str:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        encoded_audio = base64.b64encode(audio_data).decode('utf-8')
        return await self._call_asr_api_async(client, encoded_audio, audio_path, offset_ms)

    async def _transcribe_chunked_async(self, client: httpx.AsyncClient, audio_path: str, offset_ms: int = 0) -> str:
        chunks = self._split_audio(audio_path)
        logger.info("已切割为 %d 个片段", len(chunks))

        all_lines = []
        chunk_offset_ms = offset_ms

        for i, chunk_path in enumerate(chunks):
            logger.info("正在识别第 %d/%d 段...", i + 1, len(chunks))
            with open(chunk_path, 'rb') as f:
                audio_data = f.read()
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            result = await self._call_asr_api_async(client, encoded_audio, chunk_path, chunk_offset_ms)

            if result and not result.startswith("[ASR"):
                all_lines.append(result)

            chunk_duration = self._get_audio_duration(chunk_path)
            chunk_offset_ms += int(chunk_duration * 1000)

            try:
                os.remove(chunk_path)
            except OSError:
                pass

        if all_lines:
            return "\n".join(all_lines)
        return "[ASR 未识别到人声内容。这段音频可能是纯音乐、环境音或无对白片段。]"

    async def _call_asr_api_async(self, client: httpx.AsyncClient, encoded_audio: str, audio_path: str, offset_ms: int) -> str:
        req_id = str(uuid.uuid4())

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
            "user": {"uid": "b2a_agent"},
            "audio": {
                "format": fmt, "codec": "raw",
                "rate": 16000, "bits": 16, "channel": 1,
                "data": encoded_audio
            },
            "request": {
                "model_name": "bigmodel",
                "enable_itn": True, "enable_punc": True,
                "show_utterances": True
            }
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.post(self.url, headers=headers, json=payload)

                if response.status_code != 200:
                    logger.warning("ASR 请求失败 (HTTP %d): %s", response.status_code, response.text[:200])
                    if attempt < max_retries - 1:
                        continue
                    return f"[ASR 错误 {response.status_code}]"

                resp_json = response.json()

                if resp_json.get("code", -1) == 0 or "result" in resp_json:
                    result = self._extract_result(resp_json, offset_ms)
                    if result:
                        return result
                    return ""

                logger.warning("ASR 第 %d 次尝试返回异常 code: %s", attempt+1, resp_json.get('code'))
                if attempt < max_retries - 1:
                    continue
                return "[ASR 未识别到人声内容。这段音频可能是纯音乐、环境音或无对白片段。]"

            except Exception as e:
                logger.warning("ASR 异常 (第 %d 次): %s", attempt+1, e)
                if attempt < max_retries - 1:
                    continue
                return f"[ASR 异常: {e}]"

        return "[ASR 失败: 超过最大重试次数]"

    def _extract_result(self, resp_json: dict, offset_ms: int = 0) -> str:
        """从 API 响应中提取带时间戳的文本，并加上偏移量修正为视频绝对时间"""
        result = resp_json.get("result")
        if not result:
            return ""

        utterances = []
        if isinstance(result, dict):
            utterances = result.get("utterances", [])
        elif isinstance(result, list) and len(result) > 0:
            utterances = result[0].get("utterances", [])

        if utterances:
            lines = []
            for u in utterances:
                start_ms = u.get("start_time", 0) + offset_ms
                text = u.get("text", "")
                total_secs = start_ms // 1000
                h, remainder = divmod(total_secs, 3600)
                m, s = divmod(remainder, 60)
                if h > 0:
                    ts = f"{h:02d}:{m:02d}:{s:02d}"
                else:
                    ts = f"{m:02d}:{s:02d}"
                lines.append(f"[{ts}] {text}")
            return "\n".join(lines)

        if isinstance(result, dict) and "text" in result:
            return result["text"]

        return ""
