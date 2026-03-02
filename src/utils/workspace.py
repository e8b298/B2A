import os
import shutil

def setup_workspace(base_dir="workspace") -> dict:
    """初始化并返回工作区各分类目录的路径"""
    dirs = {
        "downloads": os.path.join(base_dir, "downloads"),
        "frames": os.path.join(base_dir, "frames"),
        "audios": os.path.join(base_dir, "audios")
    }

    for path in dirs.values():
        os.makedirs(path, exist_ok=True)

    return dirs

def clean_workspace(base_dir="workspace"):
    """清理整个工作区目录"""
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
