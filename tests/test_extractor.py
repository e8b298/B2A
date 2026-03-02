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
