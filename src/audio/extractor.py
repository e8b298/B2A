import os
import shutil
import subprocess
import yt_dlp

from src.visual.extractor import FFmpegNotFoundError, DownloadTimeoutError, _check_ffmpeg, _safe_remove


class AudioExtractor:
    SOCKET_TIMEOUT = 30
    MAX_RETRIES = 3
    FFMPEG_TIMEOUT = 300

    def __init__(self, bvid: str):
        self.bvid = bvid
        self.url = f"https://www.bilibili.com/video/{self.bvid}"

    def _make_base_opts(self):
        import time
        # 计时从第一次收到 downloading 状态时才开始，避免 info fetch 阶段误触发
        download_started_at = [None]
        def download_timeout_hook(d):
            if d['status'] == 'downloading':
                if download_started_at[0] is None:
                    download_started_at[0] = time.time()
                elif time.time() - download_started_at[0] > 90:
                    raise Exception("B2A_HARD_TIMEOUT: 视频音频已被强制阻断！遭到B站严苛限流或网路过慢，无法在90秒内完成。")
        return {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': self.SOCKET_TIMEOUT,
            'progress_hooks': [download_timeout_hook],
            'retries': self.MAX_RETRIES,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
        }

    def _download_audio_simple(self, output_path: str):
        """
        multi-fallback audio download with timeout protection.
        """
        base = self._make_base_opts()
        last_err = None
        for fmt in ['bestaudio[ext=m4a]/bestaudio', 'bestaudio/best']:
            try:
                opts = {**base, 'format': fmt, 'outtmpl': output_path}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([self.url])
                return
            except Exception as e:
                # B2A_HARD_TIMEOUT 是我们自己的熔断异常，不能被吞掉降级重试
                if "B2A_HARD_TIMEOUT" in str(e):
                    _safe_remove(output_path)
                    raise DownloadTimeoutError(
                        "[B2A 下载超时] 音频下载因限流被强制熔断，已自动清理残留文件。"
                        "可能原因：B站风控拦截了无Cookie的请求，或当前网络过慢。"
                        "请告知用户检查网络后重试，不会浪费任何磁盘空间。"
                    ) from e
                last_err = e
                _safe_remove(output_path)
                continue

        err_str = str(last_err).lower() if last_err else ""
        if "timed out" in err_str or "timeout" in err_str:
            raise DownloadTimeoutError(
                "[B2A 下载超时] 音频下载因网络超时被强制中止，已自动清理残留文件。"
                "可能原因：B站风控拦截了无Cookie的请求，或当前网络不稳定。"
                "请告知用户检查网络后重试，不会浪费任何磁盘空间。"
            ) from last_err
        raise RuntimeError(f"无法下载音频: {self.bvid}") from last_err

    def download_audio(self, output_dir: str, start_time: str = None, end_time: str = None) -> str:
        """
        Audio download with timeout and cleanup.
        """
        _check_ffmpeg()
        os.makedirs(output_dir, exist_ok=True)

        start_str = start_time.replace(":", "") if start_time else "start"
        end_str = end_time.replace(":", "") if end_time else "end"

        if start_time and end_time:
            filename = f"{self.bvid}_{start_str}_to_{end_str}.m4a"
        else:
            filename = f"{self.bvid}.m4a"

        output_path = os.path.abspath(os.path.join(output_dir, filename))
        full_tmp_path = None

        try:
            if start_time and end_time:
                # S1: yt-dlp native range
                try:
                    base = self._make_base_opts()
                    opts = {
                        **base,
                        'format': 'bestaudio[ext=m4a]/bestaudio',
                        'outtmpl': output_path,
                        'download_ranges': yt_dlp.utils.download_range_func(
                            None,
                            [(yt_dlp.utils.parse_duration(start_time), yt_dlp.utils.parse_duration(end_time))]
                        ),
                        'force_keyframes_at_cuts': True,
                    }
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([self.url])
                    return output_path
                except Exception:
                    _safe_remove(output_path)
                    print("[i] yt-dlp native range failed, fallback to full download + trim...")

                # S2: full download then ffmpeg trim
                full_tmp_path = os.path.abspath(os.path.join(output_dir, f"{self.bvid}_full_tmp.m4a"))
                self._download_audio_simple(full_tmp_path)

                try:
                    self._trim_with_ffmpeg(full_tmp_path, output_path, start_time, end_time)
                    _safe_remove(full_tmp_path)
                except Exception:
                    print("[i] ffmpeg trim failed, using full file")
                    if os.path.exists(full_tmp_path):
                        os.rename(full_tmp_path, output_path)

                return output_path
            else:
                self._download_audio_simple(output_path)
                return output_path

        except (DownloadTimeoutError, FFmpegNotFoundError):
            _safe_remove(output_path)
            _safe_remove(full_tmp_path)
            raise
        except Exception:
            _safe_remove(output_path)
            _safe_remove(full_tmp_path)
            raise

    @staticmethod
    def _trim_with_ffmpeg(input_path: str, output_path: str, start_time: str, end_time: str):
        cmd = [
            'ffmpeg', '-y',
            '-ss', start_time,
            '-to', end_time,
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=True, timeout=300
        )


