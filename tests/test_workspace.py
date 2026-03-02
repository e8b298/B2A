import os
import shutil
from src.utils.workspace import setup_workspace, clean_workspace

def test_setup_workspace():
    test_dir = "test_workspace"
    dirs = setup_workspace(test_dir)

    assert "downloads" in dirs
    assert "frames" in dirs
    assert "audios" in dirs

    assert os.path.exists(dirs["downloads"])
    assert test_dir in dirs["downloads"]
    assert os.path.exists(dirs["frames"])
    assert os.path.exists(dirs["audios"])

    # 清理并验证
    clean_workspace(test_dir)
    assert not os.path.exists(test_dir)
