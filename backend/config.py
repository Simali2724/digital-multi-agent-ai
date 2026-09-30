"""Configuration independent of the launch directory."""
import os
from pathlib import Path
from dotenv import load_dotenv
BACKEND_ROOT = Path(__file__).resolve().parent
load_dotenv(BACKEND_ROOT / '.env', override=False)
DATA_ROOT = Path(os.getenv('RAG_DATA_ROOT', r'D:\reliance-data'))
CHROMA_PATH = Path(os.getenv('CHROMA_PATH', str(DATA_ROOT / 'chroma_db')))

def key_present(name: str) -> bool:
    value = os.getenv(name, '').strip().strip('"\'')
    return bool(value) and not any(x in value.lower() for x in ('your_', 'paste', 'replace', 'xxx', 'here'))

def active_collection() -> str:
    pointer = CHROMA_PATH / 'active_collection.txt'
    return pointer.read_text(encoding='utf-8').strip() if pointer.exists() else os.getenv('CHROMA_COLLECTION', 'reliance_knowledge')
