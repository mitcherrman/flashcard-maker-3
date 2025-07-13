# pipeline.py ------------------------------------------------------------------
"""Full PDF/DOCX/image → Anki pipeline with interactive prompts.

Usage examples
--------------
$ python pipeline.py                                    # prompts for file + test mode
$ python pipeline.py "C:/docs/file.pdf"                 # prompts for test mode only
$ python pipeline.py "file.pdf" --test-chunks 3 --cards 8  # fully scripted
"""

from __future__ import annotations

import argparse
import pathlib
import pickle
from driver import run_extraction
from flashcard_gen import build_deck

# ── CLI --------------------------------------------------------------------
cli = argparse.ArgumentParser(description="Full PDF→Anki pipeline — interactive")
cli.add_argument("file", nargs="?", type=pathlib.Path,
                 help="Path to PDF, DOCX, or image (if omitted, you will be prompted)")
cli.add_argument("--tokens", type=int, default=700,
                 help="Max tokens per chunk (default 700)")
cli.add_argument("--cards", type=int, default=10,
                 help="Max cards per chunk (default 10)")
cli.add_argument("-n", "--test-chunks", type=int, default=None,
                 help="Process only first N chunks (bypass interactive prompt)")
args = cli.parse_args()

# ── 1. Ask for file path if missing ----------------------------------------
if args.file is None:
    while True:
        path_str = input("Enter full path to PDF/DOCX/image: ").strip('" ')
        path = pathlib.Path(path_str)
        if path.exists():
            args.file = path
            break
        print("❌  File not found — try again.\n")

file_path: pathlib.Path = args.file

# ── 2. Ask for test mode if flag not provided ------------------------------
if args.test_chunks is None:
    reply = input("Activate test mode? (y/N) ").strip().lower()
    if reply.startswith("y"):
        args.test_chunks = 2  # default sample size

print(f"\n▶  Processing: {file_path.name}")
if args.test_chunks:
    print(f"⚡  Test mode ON — only first {args.test_chunks} chunk(s)\n")
else:
    print()

# ── 3. Extract & chunk -----------------------------------------------------
chunks = run_extraction(file_path, max_tokens=args.tokens)
if args.test_chunks:
    chunks = chunks[: args.test_chunks]

# ── 4. Cache chunks --------------------------------------------------------
cache_path = file_path.with_suffix(".chunks.pkl")
cache_path.write_bytes(pickle.dumps(chunks))
print(f"[pipeline] Chunks cached → {cache_path.name}")

# ── 5. Build Anki deck -----------------------------------------------------
deck_name = file_path.stem + ("_TEST" if args.test_chunks else "")
deck_path = build_deck(chunks, deck_name=deck_name, max_cards_per_chunk=args.cards)

print(f"\n✅  All done! Import {deck_path.name} into Anki.")
