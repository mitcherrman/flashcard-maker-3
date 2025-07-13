"""
make_deck.py  –  one-shot PDF → Anki deck
------------------------------------------------
Usage:
    python make_deck.py "path/to/file.pdf"         # up to 10 Q-A per chunk
    python make_deck.py "file.pdf"  --cards 5      # limit to 5 per chunk
Prereqs:
    .env file with OPENAI_API_KEY=sk-…
"""

import argparse, os, json, random, pathlib
from pathlib import Path
from dotenv import load_dotenv

# ── load secrets BEFORE importing anything that might need them ────────────
load_dotenv()                                         # reads .env
OPENAI_KEY = os.environ["OPENAI_API_KEY"]             # crash early if missing

# ── runtime imports (after key is in env) ───────────────────────────────────
from openai import OpenAI
import tiktoken, genanki

# ingestion libs
import fitz, docx, pytesseract
from PIL import Image

# ── 0. helper: extract plain text from PDF / DOCX / image ───────────────────
def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        with fitz.open(path) as pdf:
            return "\n".join(p.get_text() for p in pdf)
    elif ext in {".docx", ".doc"}:
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    else:  # image → OCR
        img = Image.open(path)
        return pytesseract.image_to_string(img)

# ── 1. chunker (same logic as before) ───────────────────────────────────────
enc = tiktoken.encoding_for_model("gpt-4o-mini")

def make_chunks(text: str, max_tokens: int = 700):
    paras = text.split("\n\n")
    buf, toks, out = [], 0, []
    for p in paras:
        ptoks = len(enc.encode(p))
        if toks + ptoks > max_tokens and buf:
            out.append("\n\n".join(buf)); buf, toks = [], 0
        buf.append(p); toks += ptoks
    if buf: out.append("\n\n".join(buf))
    return out

# ── 2. LLM call to build cards ──────────────────────────────────────────────
client = OpenAI(api_key=OPENAI_KEY)

def cards_from_chunk(chunk: str, max_cards=10):
    sys_prompt = ("You are an expert flash-card writer. "
                  "Return an array named 'cards', each with 'front' & 'back'.")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":sys_prompt},
                  {"role":"user","content":chunk}],
        response_format={"type":"json_object"},
        max_tokens=800,
    )
    data = json.loads(resp.choices[0].message.content)
    return data.get("cards", [])[:max_cards]

# ── 3. glue everything together & build Anki deck ───────────────────────────
def build_deck(infile: Path, per_chunk: int):
    raw = extract_text(infile)
    chks = make_chunks(raw)
    print(f"Chunks: {len(chks)}  (≈ {sum(len(c) for c in chks)//1000}k chars)")

    cards = []
    for i, ch in enumerate(chks, start=1):
        print(f"  • GPT on chunk {i}/{len(chks)} …")
        cards.extend(cards_from_chunk(ch, per_chunk))
    print(f"Total cards: {len(cards)}")

    deck_id = random.randrange(1<<30)
    deck = genanki.Deck(deck_id, infile.stem[:60])
    model = genanki.Model(
        random.randrange(1<<30), "Basic",
        fields=[{"name":"Front"},{"name":"Back"}],
        templates=[{"name":"Card 1",
                    "qfmt":"{{Front}}",
                    "afmt":"{{Back}}<hr id=answer>"}],
    )
    for c in cards:
        deck.add_note(genanki.Note(model, [c["front"], c["back"]]))

    out = infile.with_suffix(".apkg")
    genanki.Package(deck).write_to_file(out)
    print("Deck written ➜", out.resolve())

# ── 4. CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path, help="PDF/DOCX/image to convert")
    ap.add_argument("--cards", type=int, default=10,
                    help="max cards per chunk (default 10)")
    args = ap.parse_args()
    build_deck(args.file, args.cards)
