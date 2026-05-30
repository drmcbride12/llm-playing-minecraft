from __future__ import annotations

from pathlib import Path
import runpy
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT / "build-tools" / "pyinstaller"))
sys.path.insert(0, str(REPO_ROOT / "src"))

sys.argv = [
    "pyinstaller",
    "--clean",
    "--onefile",
    "--console",
    "--name",
    "llm-playing-minecraft-controller",
    "--paths",
    "src",
    "--add-data",
    r"src\llm_playing_minecraft\profiles;llm_playing_minecraft\profiles",
    "packaging/controller_entry.py",
]

runpy.run_path(
    str(REPO_ROOT / "build-tools" / "pyinstaller" / "PyInstaller" / "__main__.py"),
    run_name="__main__",
)
