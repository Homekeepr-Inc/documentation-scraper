import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .config import DB_PATH
from .logging_config import get_logger

logger = get_logger("database")


def _ensure_data_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    _ensure_data_dir()
    conn = get_db()
    cur = conn.cursor()

    # file_sha256 is no longer UNIQUE as we can have multiple models that share the same
    # PDF. If we left it as UNIQUE, we would not be able to cache previously fetched PDFs
    # if they end up being assigned to multiple models.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            brand TEXT,
            model_number TEXT,
            doc_type TEXT,
            equipment_category TEXT DEFAULT 'appliance',
            equipment_type TEXT DEFAULT 'unknown',
            title TEXT,
            language TEXT,
            published_at TEXT,
            source_url TEXT,
            file_url TEXT,
            file_sha256 TEXT,
            size_bytes INTEGER,
            pages INTEGER,
            ocr_applied INTEGER DEFAULT 0,
            english_present INTEGER DEFAULT 0,
            status TEXT,
            http_status INTEGER,
            local_path TEXT,
            text_path TEXT,
            text TEXT,
            ingested_at TEXT,
            last_seen_at TEXT
        );
        """
    )



    # Basic indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_brand ON documents(brand);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_model ON documents(model_number);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_equipment_category ON documents(equipment_category);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_equipment_type ON documents(equipment_type);")

    # Performance indexes for common queries
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_composite ON documents(brand, equipment_category, doc_type);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_english ON documents(english_present) WHERE english_present = 1;")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_size ON documents(size_bytes);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_ingested ON documents(ingested_at);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(file_sha256);")

    cur.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            text,
            content='documents',
            content_rowid='id'
        );
        """
    )

    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, text) VALUES (new.id, new.text);
        END;
        """
    )
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, text) VALUES('delete', old.id, old.text);
        END;
        """
    )
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, text) VALUES('delete', old.id, old.text);
            INSERT INTO documents_fts(rowid, text) VALUES (new.id, new.text);
        END;
        """
    )

    conn.commit()
    conn.close()


def insert_or_ignore_document(doc: Dict[str, Any]) -> Optional[int]:
    conn = get_db()
    cur = conn.cursor()
    columns = ",".join(doc.keys())
    placeholders = ":" + ",:".join(doc.keys())
    try:
        cur.execute(f"INSERT OR IGNORE INTO documents ({columns}) VALUES ({placeholders})", doc)
        conn.commit()
        if cur.lastrowid:
            return int(cur.lastrowid)
        return None
    finally:
        conn.close()


def update_document(doc_id: int, fields: Dict[str, Any]) -> None:
    if not fields:
        return
    conn = get_db()
    cur = conn.cursor()
    sets = ", ".join([f"{k} = :{k}" for k in fields.keys()])
    fields["id"] = doc_id
    cur.execute(f"UPDATE documents SET {sets} WHERE id = :id", fields)
    conn.commit()
    conn.close()


def fetch_document(doc_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def search_documents(query: Optional[str] = None, brand: Optional[str] = None, doc_type: Optional[str] = None, model: Optional[str] = None, equipment_category: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_db()
    cur = conn.cursor()
    where = []
    params: Dict[str, Any] = {}

    if query:
        where.append("id IN (SELECT rowid FROM documents_fts WHERE documents_fts MATCH :q)")
        params["q"] = query
    if brand:
        where.append("brand = :brand")
        params["brand"] = brand
    if doc_type:
        where.append("doc_type = :doc_type")
        params["doc_type"] = doc_type
    if model:
        where.append("model_number = :model")
        params["model"] = model
    if equipment_category:
        where.append("equipment_category = :equipment_category")
        params["equipment_category"] = equipment_category

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    params["limit"] = limit
    params["offset"] = offset

    cur.execute(
        f"SELECT * FROM documents{where_sql} ORDER BY id DESC LIMIT :limit OFFSET :offset",
        params,
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
