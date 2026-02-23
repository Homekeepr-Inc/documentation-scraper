from pathlib import Path
from typing import Tuple
import re

from .config import BLOB_ROOT
from .logging_config import get_logger

logger = get_logger("storage")

SAFE_BRAND_SEGMENT = re.compile(r"^[a-zA-Z0-9_.\-]+$")
SAFE_MODEL_SEGMENT = re.compile(r"^[a-zA-Z0-9_.\- ]+$")


def sanitize_path_segment(value: str, *, allow_spaces: bool) -> str:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("Invalid brand or model")
    if "\x00" in cleaned or "/" in cleaned or "\\" in cleaned:
        raise ValueError("Invalid brand or model")
    pattern = SAFE_MODEL_SEGMENT if allow_spaces else SAFE_BRAND_SEGMENT
    if not pattern.match(cleaned):
        raise ValueError("Invalid brand or model")
    return cleaned


def ensure_no_traversal(value: str) -> None:
    raw = value or ""
    if "\x00" in raw or raw.startswith(("/", "\\")):
        raise ValueError("Invalid brand or model")
    if re.match(r"^[A-Za-z]:", raw):
        raise ValueError("Invalid brand or model")
    if "\\" in raw:
        raise ValueError("Invalid brand or model")
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("Invalid brand or model")


def is_within_blob_root(path_str: str) -> bool:
    try:
        resolved = Path(path_str).resolve(strict=False)
        root = BLOB_ROOT.resolve()
        resolved.relative_to(root)
        return True
    except Exception:
        return False


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def paths_for(brand: str, model_number: str, doc_type: str, sha256: str, equipment_category: str = "appliance") -> Tuple[Path, Path]:
    base = BLOB_ROOT / equipment_category / brand.lower() / (model_number or "unknown") / doc_type
    ensure_dir(base)
    pdf_path = base / f"{sha256}.pdf"
    text_path = base / f"{sha256}.txt.gz"
    return pdf_path, text_path
