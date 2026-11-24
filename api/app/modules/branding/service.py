"""将系统 Logo 转为有尺寸上限的 PNG，并在 PostgreSQL 中保存。"""
import base64
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.db.session import execute_in_session, fetch_one_in_session
from app.modules.branding.schemas import Branding

MAX_LOGO_BYTES = 1024 * 1024
MAX_LOGO_PIXELS = 16 * 1024 * 1024
LOGO_SIZE = 512


class LogoValidationError(ValueError):
    """Logo输入不符合大小或尺寸限制。"""


def normalize_logo(data: bytes) -> str:
    """验证 PNG/JPEG/WebP，按原比例缩小到最长边 512 像素的 PNG 并返回无原始元数据的 Base64 Data URI。"""
    if not data or len(data) > MAX_LOGO_BYTES:
        raise ValueError("Logo不能为空且不能超过 1 MB")
    try:
        with Image.open(BytesIO(data), formats=["PNG", "JPEG", "WEBP"]) as source:
            if source.width * source.height > MAX_LOGO_PIXELS or max(source.size) > 4096:
                raise LogoValidationError("Logo尺寸不能超过 4096 像素")
            source.verify()
        with Image.open(BytesIO(data), formats=["PNG", "JPEG", "WEBP"]) as source:
            oriented = ImageOps.exif_transpose(source).convert("RGBA")
            oriented.thumbnail((LOGO_SIZE, LOGO_SIZE), Image.Resampling.LANCZOS)
            clean = Image.new("RGBA", oriented.size)
            clean.paste(oriented)
            output = BytesIO()
            clean.save(output, format="PNG")
    except LogoValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise ValueError("请选择有效的 PNG、JPEG 或 WebP 图片") from exc
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def get_branding(db: Session) -> Branding:
    row = fetch_one_in_session(db, "SELECT logo FROM app_branding WHERE id = 1")
    return Branding(logo=row["logo"] if row else None)


def save_logo(db: Session, logo: str | None) -> Branding:
    execute_in_session(
        db,
        """INSERT INTO app_branding (id, logo) VALUES (1, :logo)
           ON CONFLICT (id) DO UPDATE SET logo = EXCLUDED.logo""",
        {"logo": logo},
    )
    return Branding(logo=logo)
