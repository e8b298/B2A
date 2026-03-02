import os
import subprocess
import tempfile
import yt_dlp


class VisualExtractor:
    def __init__(self, bvid: str, interval: int = 10):
        self.bvid = bvid
        self.interval = interval

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """解析 HH:MM:SS 或 MM:SS 格式为秒数"""
        parts = time_str.split(':')
        seconds = 0.0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds

    def _make_base_opts(self):
        return {
            'quiet': True,
            'no_warnings': True,
            # 只下载视频流，不需要音频，也就不需要 ffmpeg 合并
            'format': 'bestvideo[height<=720][ext=mp4]/bestvideo[height<=720]/bestvideo',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }

    def download_video(self, output_dir: str = None, start_time: str = None, end_time: str = None) -> str:
        """
        使用 yt-dlp 下载视频流（仅视频，无音频），分辨率不高于 720p。
        支持 start_time/end_time 进行切片。
        策略：先尝试 yt-dlp 原生切片 -> 下载完整后 ffmpeg 裁剪 -> 兜底用完整文件
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        os.makedirs(output_dir, exist_ok=True)

        if start_time and end_time:
            safe_start = start_time.replace(":", "")
            safe_end = end_time.replace(":", "")
            filename = f"{self.bvid}_{safe_start}_to_{safe_end}.mp4"
        else:
            filename = f"{self.bvid}_full.mp4"

        output_path = os.path.join(output_dir, filename)
        url = f"https://www.bilibili.com/video/{self.bvid}"

        if start_time and end_time:
            # 策略一：尝试 yt-dlp 原生切片
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
            except Exception:
                print("[i] yt-dlp 原生切片失败，回退为下载后裁剪...")

            # 策略二：下载完整视频流，再用 ffmpeg 裁剪
            full_path = os.path.join(output_dir, f"{self.bvid}_full_tmp.mp4")
            opts = {**self._make_base_opts(), 'outtmpl': full_path}
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            try:
                self._trim_with_ffmpeg(full_path, output_path, start_time, end_time)
                try:
                    os.remove(full_path)
                except OSError:
                    pass
            except Exception:
                print("[i] ffmpeg 裁剪失败，使用完整文件")
                os.rename(full_path, output_path)

            return output_path
        else:
            opts = {**self._make_base_opts(), 'outtmpl': output_path}
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            return output_path

    @staticmethod
    def _trim_with_ffmpeg(input_path: str, output_path: str, start_time: str, end_time: str):
        """用 ffmpeg -ss/-to 裁剪视频片段"""
        cmd = [
            'ffmpeg', '-y',
            '-ss', start_time,
            '-to', end_time,
            '-i', input_path,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    def extract_frames(self, video_path: str, output_dir: str = None) -> list[str]:
        """
        使用 ffmpeg 命令行按固定间隔抽取关键帧。
        返回生成的帧图片路径列表。
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        os.makedirs(output_dir, exist_ok=True)

        output_pattern = os.path.join(output_dir, f"{self.bvid}_frame_%04d.jpg")

        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f'fps=1/{self.interval}',
            '-q:v', '2',
            output_pattern
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        frames = sorted([
            os.path.join(output_dir, f)
            for f in os.listdir(output_dir)
            if f.startswith(f"{self.bvid}_frame_") and f.endswith(".jpg")
        ])

        return frames
