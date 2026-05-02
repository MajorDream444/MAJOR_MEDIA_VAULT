#!/usr/bin/env python3
from __future__ import annotations

import platform
import shutil
import sys


REQUIRED_TOOLS = ["ffmpeg", "ffprobe", "whisper"]
OPTIONAL_TOOLS = ["exiftool", "ollama"]


def tool_status(tool_name: str) -> str:
    path = shutil.which(tool_name)
    if path:
        return f"installed ({path})"
    return "missing"


def main() -> int:
    version = sys.version_info
    python_ok = version.major == 3 and version.minor >= 9

    print("MAJOR_MEDIA_VAULT dependency check")
    print(f"Python: {platform.python_version()} ({'ok' if python_ok else 'needs Python 3.9+'})")
    print("")
    print("Required tools")
    for tool_name in REQUIRED_TOOLS:
        print(f"- {tool_name}: {tool_status(tool_name)}")
    print("")
    print("Optional tools")
    for tool_name in OPTIONAL_TOOLS:
        print(f"- {tool_name}: {tool_status(tool_name)}")

    return 0 if python_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
