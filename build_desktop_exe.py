"""Build script to package Desktop Agent into a single standalone Windows .exe using PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def build_exe():
    print("=====================================================")
    print(" Building Standalone Windows Executable for Desktop Agent")
    print("=====================================================")

    root_dir = Path(__file__).parent.resolve()
    desktop_agent_entry = root_dir / "desktop_agent" / "__main__.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "AviatorDesktopAgent",
        "--add-data",
        f"{root_dir / 'aviator_bot'};aviator_bot",
        "--add-data",
        f"{root_dir / 'desktop_agent'};desktop_agent",
        str(desktop_agent_entry),
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(root_dir))
    if result.returncode == 0:
        print("\n[SUCCESS] Desktop Agent packaged successfully!")
        print(f"Executable folder: {root_dir / 'dist' / 'AviatorDesktopAgent'}")
    else:
        print(f"\n[FAILED] PyInstaller exited with code {result.returncode}")


if __name__ == "__main__":
    build_exe()
