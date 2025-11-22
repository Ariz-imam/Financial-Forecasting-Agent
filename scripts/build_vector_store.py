# scripts/build_vector_store.py
import os
from tools.qualitative_rag import build_or_get_chroma
from dotenv import load_dotenv

load_dotenv()
DATA_ROOT = os.getenv("DATA_ROOT", "./data")
transcript_dir = os.path.join(DATA_ROOT, "transcripts")
persist_dir = os.getenv("CHROMA_DB_DIR", "./db/chroma")

print("Building vector store from:", transcript_dir)
_ = build_or_get_chroma(transcript_dir, persist_dir=persist_dir)
print("Chroma built at", persist_dir)
