import os
import pytest
from unittest.mock import patch, MagicMock
from src.visual.extractor import VisualExtractor

def test_extractor_init():
    extractor = VisualExtractor("BV1xx411c7mD", interval=10)
    assert extractor.bvid == "BV1xx411c7mD"
    assert extractor.interval == 10

def test_extractor_methods_exist():
    extractor = VisualExtractor("BV1xx411c7mD", interval=10)
    assert hasattr(extractor, "download_video")
    assert hasattr(extractor, "extract_frames")

def test_extractor_download_with_ranges():
    extractor = VisualExtractor("BV1xx411c7mD", interval=10)
    # mock yt-dlp 避免实际下载
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        path = extractor.download_video(
            output_dir="workspace/downloads",
            start_time="01:30",
            end_time="02:40"
        )
    assert "0130" in path and "0240" in path

def test_extractor_download_full():
    extractor = VisualExtractor("BV1xx411c7mD", interval=10)
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        path = extractor.download_video(output_dir="workspace/downloads")
    assert "full.mp4" in path

def test_extract_frames_calls_ffmpeg():
    extractor = VisualExtractor("BV1test12345", interval=10)
    with patch('subprocess.run') as mock_run, \
         patch('os.listdir', return_value=[
             "BV1test12345_frame_0001.jpg",
             "BV1test12345_frame_0002.jpg",
             "BV1test12345_frame_0003.jpg"
         ]):
        frames = extractor.extract_frames("fake_video.mp4", output_dir="workspace/frames")
        mock_run.assert_called_once()
        assert len(frames) == 3
        assert all("BV1test12345_frame_" in f for f in frames)
