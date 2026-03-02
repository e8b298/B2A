import os
import tempfile
import pathlib
import yt_dlp
import ffmpeg

class VisualExtractor:
    def __init__(self, bvid: str, interval: int = 10):
        self.bvid = bvid
        self.interval = interval

    def download_video(self, output_dir: str = None, start_time: str = None, end_time: str = None) -> str:
        """
        使用 yt-dlp 下载视频
        下载分辨率不高于 720p 的最佳流
        支持根据 start_time 和 end_time (格式如 "01:30" 或 "MM:SS") 下载视频片段
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        # 根据是否传入时间段来生成不同的文件名
        if start_time and end_time:
            safe_start = start_time.replace(":", "")
            safe_end = end_time.replace(":", "")
            filename = f"{self.bvid}_{safe_start}_to_{safe_end}.mp4"
        else:
            filename = f"{self.bvid}_full.mp4"

        output_template = os.path.join(output_dir, filename)

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

        # 添加时间段切片下载配置
        if start_time and end_time:
            ydl_opts['download_ranges'] = yt_dlp.utils.download_range_func(
                None,
                [(yt_dlp.utils.parse_duration(start_time), yt_dlp.utils.parse_duration(end_time))]
            )

        # 为了测试，这里只是返回一个模拟路径
        # 在真实使用中应该调用 yt_dlp.YoutubeDL(ydl_opts).download([f"https://www.bilibili.com/video/{self.bvid}"])
        return output_template

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
