"""镜像构建时写入的发布版本。"""

from pathlib import Path

def read_build_version(version_file: Path) -> str:
    try:
        return version_file.read_text(encoding="utf-8").strip() or "dev"
    except FileNotFoundError:
        return "dev"


BUILD_VERSION = read_build_version(Path(__file__).with_name("release-version.txt"))
