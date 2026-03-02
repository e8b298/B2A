import os
import pytest
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
    # 模拟获取一段流输出路径
    path = extractor.download_video(start_time="01:30", end_time="02:40", output_dir="workspace/downloads")
    assert "0130" in path and "0240" in path
