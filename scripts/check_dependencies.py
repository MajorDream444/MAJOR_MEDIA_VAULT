#!/usr/bin/env python3
from __future__ import annotations

import platform
import sys
from pathlib import Path


REQUIRED_TOOLS = ["ffmpeg", "ffprobe", "whisper"]
OPTIONAL_TOOLS = ["exiftool", "ollama"]
COMMON_TOOL_DIRS = [Path("/opt/homebrew/bin"), Path("/usr/local/bin"), Path("/opt/local/bin")]


def find_tool(tool_name: str) -> str:
    from shutil import which

    path = which(tool_name)
    if path:
        return path
    for tool_dir in COMMON_TOOL_DIRS:
        candidate = tool_dir / tool_name
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return ""


def tool_status(tool_name: str) -> str:
    path = find_tool(tool_name)
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
    print("Python packages")
    try:
        import PIL

        print(f"- Pillow: installed ({PIL.__version__})")
    except Exception:
        print("- Pillow: missing")
    print("")
    print("Optional tools")
    for tool_name in OPTIONAL_TOOLS:
        print(f"- {tool_name}: {tool_status(tool_name)}")

    return 0 if python_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
