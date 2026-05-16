"""Add NVIDIA pip package DLL dirs so faster-whisper can use the GPU on Windows."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_CONFIGURED = False


def ensure_nvidia_dll_paths() -> list[str]:
    """Register nvidia/*/bin from site-packages (Windows CUDA for ctranslate2)."""
    global _CONFIGURED
    if _CONFIGURED or sys.platform != "win32":
        return []

    added: list[str] = []
    for entry in sys.path:
        nvidia_root = Path(entry) / "nvidia"
        if not nvidia_root.is_dir():
            continue
        for pkg_dir in sorted(nvidia_root.iterdir()):
            bin_dir = pkg_dir / "bin"
            if not bin_dir.is_dir():
                continue
            path_str = str(bin_dir.resolve())
            if path_str in added:
                continue
            os.add_dll_directory(path_str)
            added.append(path_str)

    if added:
        os.environ["PATH"] = os.pathsep.join(added) + os.pathsep + os.environ.get("PATH", "")

    _CONFIGURED = True
    return added
