import os
import shutil
from src.utils.workspace import setup_workspace, clean_workspace

def test_setup_workspace_default():
    test_dir = "test_workspace"
    dirs = setup_workspace(test_dir)

    assert "downloads" in dirs
    assert "frames" in dirs
    assert "audios" in dirs
    assert os.path.exists(dirs["downloads"])
    assert os.path.exists(dirs["frames"])
    assert os.path.exists(dirs["audios"])

    clean_workspace(test_dir)
    assert not os.path.exists(test_dir)

def test_setup_workspace_with_bvid():
    test_dir = "test_workspace"
    dirs = setup_workspace(test_dir, bvid="BV1test12345")

    # 应该在 test_workspace/BV1test12345/ 下建立子目录
    assert "BV1test12345" in dirs["root"]
    assert "BV1test12345" in dirs["downloads"]
    assert "BV1test12345" in dirs["frames"]
    assert "BV1test12345" in dirs["audios"]
    assert os.path.exists(dirs["downloads"])

    # 只清理该视频的子目录
    clean_workspace(test_dir, bvid="BV1test12345")
    assert not os.path.exists(os.path.join(test_dir, "BV1test12345"))

    # 整体清理
    clean_workspace(test_dir)

def test_workspace_isolation():
    """两个不同视频的工作区应该互相隔离"""
    test_dir = "test_workspace"
    dirs_a = setup_workspace(test_dir, bvid="BV_video_aaa")
    dirs_b = setup_workspace(test_dir, bvid="BV_video_bbb")

    assert dirs_a["downloads"] != dirs_b["downloads"]
    assert dirs_a["frames"] != dirs_b["frames"]
    assert os.path.exists(dirs_a["downloads"])
    assert os.path.exists(dirs_b["downloads"])

    clean_workspace(test_dir)
