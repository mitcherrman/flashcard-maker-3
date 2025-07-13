# driver.py ---------------------------------------------------------------
import os
from pathlib import Path
from decouple import config
from ingest import extract_text
from chunker import make_chunks

# ensure the key is in the environment before any sub-imports need it
os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_API_KEY"))

def run_extraction(path: Path, max_tokens: int = 700):
    """Return a list[str] of GPT-sized chunks from a document."""
    raw = extract_text(path)
    chunks = make_chunks(raw, max_tokens=max_tokens)
    print(f"[driver] {len(chunks)} chunks (≈ {sum(len(c) for c in chunks)//1000}k chars)")
    return chunks

# — optional CLI for quick tests —
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("file", type=Path)
    p.add_argument("--tokens", type=int, default=700)
    a = p.parse_args()
    run_extraction(a.file, a.tokens)
