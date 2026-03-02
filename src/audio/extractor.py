import os
import subprocess
import yt_dlp


class AudioExtractor:
    def __init__(self, bvid: str):
        self.bvid = bvid
        self.url = f"https://www.bilibili.com/video/{self.bvid}"

    def _make_base_opts(self):
        return {
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
        }

    def _download_audio_simple(self, output_path: str):
        """
        多级回退下载音频：
        1. bestaudio[ext=m4a] 纯音频流
        2. bestaudio 任意格式
        """
        base = self._make_base_opts()
        for fmt in ['bestaudio[ext=m4a]/bestaudio', 'bestaudio/best']:
            try:
                opts = {**base, 'format': fmt, 'outtmpl': output_path}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([self.url])
                return
            except Exception:
                continue
        raise RuntimeError(f"无法下载音频: {self.bvid}")

    def download_audio(self, output_dir: str, start_time: str = None, end_time: str = None) -> str:
        """
        下载音频流。支持 start_time/end_time 切片。
        策略：先尝试 yt-dlp 原生切片，失败则回退为下载完整音频后用 ffmpeg 裁剪。
        """
        os.makedirs(output_dir, exist_ok=True)

        start_str = start_time.replace(":", "") if start_time else "start"
        end_str = end_time.replace(":", "") if end_time else "end"

        if start_time and end_time:
            filename = f"{self.bvid}_{start_str}_to_{end_str}.m4a"
        else:
            filename = f"{self.bvid}.m4a"

        output_path = os.path.abspath(os.path.join(output_dir, filename))

        if start_time and end_time:
            # 策略一：尝试 yt-dlp 原生切片
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
                print("[i] yt-dlp 原生切片失败，回退为下载后裁剪...")

            # 策略二：下载完整音频，再用 ffmpeg 裁剪
            full_path = os.path.abspath(os.path.join(output_dir, f"{self.bvid}_full_tmp.m4a"))
            self._download_audio_simple(full_path)

            try:
                self._trim_with_ffmpeg(full_path, output_path, start_time, end_time)
            except Exception:
                print("[i] ffmpeg 裁剪失败，使用完整文件")
                os.rename(full_path, output_path)
                return output_path

            try:
                os.remove(full_path)
            except OSError:
                pass

            return output_path
        else:
            self._download_audio_simple(output_path)
            return output_path

    @staticmethod
    def _trim_with_ffmpeg(input_path: str, output_path: str, start_time: str, end_time: str):
        """用 ffmpeg -ss/-to 裁剪音频片段"""
        cmd = [
            'ffmpeg', '-y',
            '-ss', start_time,
            '-to', end_time,
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """解析 HH:MM:SS 或 MM:SS 格式为秒数"""
        parts = time_str.split(':')
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds
