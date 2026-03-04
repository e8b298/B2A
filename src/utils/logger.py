import logging
import os
import sys

_logger = None

LOG_DIR = os.path.join(os.path.expanduser("~"), ".b2a")
LOG_FILE = os.path.join(LOG_DIR, "b2a.log")


def get_logger(name: str = "b2a") -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(LOG_DIR, exist_ok=True)

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # file handler (always on)
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", datefmt="%H:%M:%S")
    fh.setFormatter(fmt)
    _logger.addHandler(fh)

    # stderr handler (CLI mode only, controlled by env var)
    if os.environ.get("B2A_LOG_STDERR") == "1":
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(fmt)
        _logger.addHandler(sh)

    return _logger
