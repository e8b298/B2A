import os
import shutil
import subprocess
import yt_dlp


class FFmpegNotFoundError(Exception):
    pass


class DownloadTimeoutError(Exception):
    pass


def _check_ffmpeg():
    """前置检测 ffmpeg 是否可用，不可用时抛出友好错误"""
    if not shutil.which("ffmpeg"):
        raise FFmpegNotFoundError(
            "[B2A 环境检测] 当前系统未安装 ffmpeg，视频抽帧功能无法使用。"
            "请告知用户：只需运行一条命令即可安装——"
            "Windows: winget install Gyan.FFmpeg | "
            "Mac: brew install ffmpeg | "
            "Linux: sudo apt install ffmpeg。"
            "安装完成后用户告知你即可，你来重试。"
        )


def _safe_remove(path: str):
    """安全删除单个文件，忽略不存在的情况"""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


class VisualExtractor:
    # yt-dlp 网络超时（秒），防止 B 站风控导致无限挂起
    SOCKET_TIMEOUT = 30
    # yt-dlp 最大重试次数
    MAX_RETRIES = 3
    # ffmpeg 子进程超时（秒），防止抽帧僵死
    FFMPEG_TIMEOUT = 300

    def __init__(self, bvid: str, interval: int = 10, quality: str = "480p"):
        self.bvid = bvid
        self.interval = interval
        self.quality = quality

    def _get_height_limit(self) -> int:
        mapping = {"360p": 360, "480p": 480, "720p": 720, "1080p": 1080}
        return mapping.get(self.quality, 480)

    def _make_base_opts(self):
        import time
        # 计时从第一次收到 downloading 状态时才开始，避免 info fetch 阶段误触发
        download_started_at = [None]
        def download_timeout_hook(d):
            if d['status'] == 'downloading':
                if download_started_at[0] is None:
                    download_started_at[0] = time.time()
                elif time.time() - download_started_at[0] > 60:
                    raise Exception("B2A_HARD_TIMEOUT: 视频已被强制阻断！由于遭到严苛限流或网速过慢，此视频无法在1分钟内完成拉取。")
        h = self._get_height_limit()
        return {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': self.SOCKET_TIMEOUT,
            'retries': self.MAX_RETRIES,
            'progress_hooks': [download_timeout_hook],
            'format': f'bestvideo[height<={h}][ext=mp4]/bestvideo[height<={h}]/bestvideo',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }

    def download_video(self, output_dir: str, start_time: str = None, end_time: str = None) -> str:
        """
        yt-dlp download with timeout and cleanup.
        output_dir is mandatory - never falls back to system temp.
        """
        _check_ffmpeg()
        os.makedirs(output_dir, exist_ok=True)

        if start_time and end_time:
            safe_start = start_time.replace(":", "")
            safe_end = end_time.replace(":", "")
            filename = f"{self.bvid}_{safe_start}_to_{safe_end}.mp4"
        else:
            filename = f"{self.bvid}_full.mp4"

        output_path = os.path.join(output_dir, filename)
        url = f"https://www.bilibili.com/video/{self.bvid}"
        full_tmp_path = None

        try:
            if start_time and end_time:
                # S1: yt-dlp native range
                try:
                    opts = {**self._make_base_opts(), 'outtmpl': output_path}
                    opts['download_ranges'] = yt_dlp.utils.download_range_func(
                        None,
                        [(yt_dlp.utils.parse_duration(start_time), yt_dlp.utils.parse_duration(end_time))]
                    )
                    opts['force_keyframes_at_cuts'] = True
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    return output_path
                except Exception as e:
                    _safe_remove(output_path)
                    if "B2A_HARD_TIMEOUT" in str(e):
                        raise DownloadTimeoutError(
                            "[B2A 下载超时] 视频下载因限流被强制熔断，已自动清理残留文件。"
                            "可能原因：B站风控拦截了无Cookie的请求，或当前网络过慢。"
                            "请告知用户检查网络后重试，不会浪费任何磁盘空间。"
                        ) from e
                    print("[i] yt-dlp native range failed, fallback to full download + trim...")

                # S2: full download then ffmpeg trim
                full_tmp_path = os.path.join(output_dir, f"{self.bvid}_full_tmp.mp4")
                opts = {**self._make_base_opts(), 'outtmpl': full_tmp_path}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])

                try:
                    self._trim_with_ffmpeg(full_tmp_path, output_path, start_time, end_time)
                    _safe_remove(full_tmp_path)
                except Exception:
                    print("[i] ffmpeg trim failed, using full file")
                    if os.path.exists(full_tmp_path):
                        os.rename(full_tmp_path, output_path)

                return output_path
            else:
                opts = {**self._make_base_opts(), 'outtmpl': output_path}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                return output_path

        except yt_dlp.utils.DownloadError as e:
            # cleanup on failure
            _safe_remove(output_path)
            _safe_remove(full_tmp_path)
            err_str = str(e).lower()
            if "timed out" in err_str or "timeout" in err_str:
                raise DownloadTimeoutError(
                    "[B2A 下载超时] 视频下载因网络超时被强制中止，已自动清理残留文件。"
                    "可能原因：B站风控拦截了无Cookie的请求，或当前网络不稳定。"
                    "请告知用户检查网络后重试，不会浪费任何磁盘空间。"
                ) from e
            raise
        except Exception as e:
            _safe_remove(output_path)
            _safe_remove(full_tmp_path)
            if "B2A_HARD_TIMEOUT" in str(e):
                raise DownloadTimeoutError(
                    "[B2A 下载超时] 视频下载因限流被强制熔断，已自动清理残留文件。"
                    "可能原因：B站风控拦截了无Cookie的请求，或当前网络过慢。"
                    "请告知用户检查网络后重试，不会浪费任何磁盘空间。"
                ) from e
            raise

    def _trim_with_ffmpeg(self, input_path: str, output_path: str, start_time: str, end_time: str):
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
            check=True, timeout=self.FFMPEG_TIMEOUT
        )

    def extract_frames(self, video_path: str, output_dir: str) -> list[str]:
        """
        ffmpeg frame extraction with timeout.
        output_dir is mandatory - never falls back to system temp.
        """
        _check_ffmpeg()
        os.makedirs(output_dir, exist_ok=True)

        output_pattern = os.path.join(output_dir, f"{self.bvid}_frame_%04d.jpg")

        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f'fps=1/{self.interval}',
            '-q:v', '2',
            output_pattern
        ]

        subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=True, timeout=self.FFMPEG_TIMEOUT
        )

        frames = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith(f"{self.bvid}_frame_") and f.endswith(".jpg")
        ])

        return frames
