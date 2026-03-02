import pytest
from unittest.mock import patch
from src.audio.extractor import AudioExtractor

def test_audio_extractor_ranges():
    extractor = AudioExtractor("BV1xx411c7mD")
    
    # Mock the internal YoutubeDL.download call to avoid actual downloading
    with patch('yt_dlp.YoutubeDL.download') as mock_download:
        path = extractor.download_audio("workspace/audios", start_time="01:30", end_time="02:40")
        
        # Verify the filename formatting works correctly
        assert "0130_to_0240.m4a" in path
        
        # Verify it was "called"
        mock_download.assert_called_once()
