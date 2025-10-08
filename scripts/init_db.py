import sys
import os

# Add the parent directory to the Python path to allow sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import init_db
from app.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    init_db()