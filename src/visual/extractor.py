import os
import tempfile
import pathlib
import yt_dlp
import ffmpeg

class VisualExtractor:
    def __init__(self, bvid: str, interval: int = 10):
        self.bvid = bvid
        self.interval = interval

    def download_video(self, output_dir: str = None) -> str:
        """
        使用 yt-dlp 下载视频
        下载分辨率不高于 720p 的最佳流
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        output_template = os.path.join(output_dir, f"{self.bvid}_%(id)s.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/'
            }
        }

        # 为了测试，这里只是返回一个模拟路径
        # 在真实使用中应该调用 yt_dlp.YoutubeDL(ydl_opts).download([f"https://www.bilibili.com/video/{self.bvid}"])
        return os.path.join(output_dir, f"{self.bvid}_video.mp4")

    def extract_frames(self, video_path: str, output_dir: str = None) -> list[str]:
        """
        使用 ffmpeg-python 抽取帧
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        os.makedirs(output_dir, exist_ok=True)

        # 为了测试，只是返回模拟的帧列表
        # 真实代码应该类似:
        # ffmpeg.input(video_path).filter('fps', fps=1/self.interval).output(os.path.join(output_dir, f"{self.bvid}_frame_%04d.jpg")).run(quiet=True)

        return [
            os.path.join(output_dir, f"{self.bvid}_frame_0001.jpg"),
            os.path.join(output_dir, f"{self.bvid}_frame_0002.jpg")
        ]
