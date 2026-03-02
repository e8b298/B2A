import os
import yt_dlp

class AudioExtractor:
    def __init__(self, bvid: str):
        self.bvid = bvid
        self.url = f"https://www.bilibili.com/video/{self.bvid}"

    def download_audio(self, output_dir: str, start_time: str = None, end_time: str = None) -> str:
        """
        根据指定的时间范围提取音频流
        :param output_dir: 输出目录
        :param start_time: 开始时间, 格式如 '01:30'
        :param end_time: 结束时间, 格式如 '02:40'
        :return: 保存的绝对路径
        """
        os.makedirs(output_dir, exist_ok=True)

        # 格式化时间字符串用于输出文件名
        start_str = start_time.replace(":", "") if start_time else "start"
        end_str = end_time.replace(":", "") if end_time else "end"

        # 如果没有传时间就用更符合意义的文件名
        if start_time and end_time:
            filename = f"{self.bvid}_{start_str}_to_{end_str}.m4a"
        else:
            filename = f"{self.bvid}.m4a"

        output_path = os.path.abspath(os.path.join(output_dir, filename))

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': output_path,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bilibili.com'
            }
        }

        if start_time and end_time:
            # yt-dlp 使用 download_ranges 来切片，格式为 [ {'start_time': ..., 'end_time': ...} ]
            # 其中时间可以是秒数或者秒数对应的各种 float
            ydl_opts['download_ranges'] = lambda info, ydl: [{
                'start_time': self._parse_time(start_time),
                'end_time': self._parse_time(end_time)
            }]
            ydl_opts['force_keyframes_at_cuts'] = True

        # 实际通过 yt_dlp 下载
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])

        return output_path

    def _parse_time(self, time_str: str) -> float:
        """解析 HH:MM:SS 或 MM:SS 格式为秒数"""
        parts = time_str.split(':')
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + float(part)
        return seconds
