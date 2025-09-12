from pathlib import Path
from typing import Tuple

from .config import BLOB_ROOT
from .logging_config import get_logger

logger = get_logger("storage")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def paths_for(brand: str, model_number: str, doc_type: str, sha256: str, equipment_category: str = "appliance") -> Tuple[Path, Path]:
    base = BLOB_ROOT / equipment_category / brand.lower() / (model_number or "unknown") / doc_type
    ensure_dir(base)
    pdf_path = base / f"{sha256}.pdf"
    text_path = base / f"{sha256}.txt.gz"
    return pdf_path, text_path
