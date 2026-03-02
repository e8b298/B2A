import os
import shutil


def setup_workspace(base_dir="workspace", bvid: str = None) -> dict:
    """
    初始化并返回工作区各分类目录的路径。
    如果传入 bvid，则在 workspace/{bvid}/ 下建立隔离子目录，
    避免不同视频的文件互相污染。
    """
    if bvid:
        root = os.path.join(base_dir, bvid)
    else:
        root = base_dir

    dirs = {
        "root": root,
        "downloads": os.path.join(root, "downloads"),
        "frames": os.path.join(root, "frames"),
        "audios": os.path.join(root, "audios")
    }

    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    return dirs


def clean_workspace(base_dir="workspace", bvid: str = None):
    """清理工作区目录。传入 bvid 则只清理该视频的子目录。"""
    target = os.path.join(base_dir, bvid) if bvid else base_dir
    if os.path.exists(target):
        shutil.rmtree(target)
