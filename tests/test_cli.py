import subprocess

def test_cli_help():
    result = subprocess.run(["python", "-m", "src.cli", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Bilibili Hybrid Extractor" in result.stdout
