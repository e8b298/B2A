import os
import shutil

# 固定在 B2A 项目根目录下的 workspace，避免 MCP 进程工作目录不确定导致乱存
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_BASE = os.path.join(_PROJECT_ROOT, "workspace")


def setup_workspace(base_dir: str = None, bvid: str = None) -> dict:
    """
    初始化并返回工作区各分类目录的路径。
    如果传入 bvid，则在 workspace/{bvid}/ 下建立隔离子目录，
    避免不同视频的文件互相污染。
    """
    base = base_dir or _DEFAULT_BASE
    if bvid:
        root = os.path.join(base, bvid)
    else:
        root = base

    dirs = {
        "root": root,
        "downloads": os.path.join(root, "downloads"),
        "frames": os.path.join(root, "frames"),
        "audios": os.path.join(root, "audios")
    }

    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    return dirs


def clean_workspace(base_dir: str = None, bvid: str = None):
    """清理工作区目录。传入 bvid 则只清理该视频的子目录。"""
    base = base_dir or _DEFAULT_BASE
    target = os.path.join(base, bvid) if bvid else base
    if os.path.exists(target):
        shutil.rmtree(target)
