# pipeline.py — one‑shot workflow: PDF → Anki deck (+ JSON) → optional Game 2
from __future__ import annotations
import pathlib, sys, pickle, argparse
from driver import run_extraction
from flashcard_gen import build_deck
from game2_cli import play, load_cards

def main():
    # ── 0. CLI flags ───────────────────────────────────────────────────────
    cli = argparse.ArgumentParser(description="PDF → flash‑cards → Game 2")
    cli.add_argument("file", nargs="?", type=pathlib.Path,
                     help="Path to PDF / DOCX / image (prompted if omitted)")
    cli.add_argument("--tokens", type=int, default=700,
                     help="Max tokens per chunk (default 700)")
    cli.add_argument("--cards", type=int, default=10,
                     help="Max cards per chunk (default 10)")
    cli.add_argument("-n", "--test-chunks", type=int, default=None,
                     help="Process only first N chunks (interactive prompt if missing)")
    cli.add_argument("--endless", action="store_true",
                     help="Endless mode for Game 2")
    args = cli.parse_args()

    # ── 1. Ask for file path if missing ───────────────────────────────────
    pdf_path: pathlib.Path
    if args.file and args.file.exists():
        pdf_path = args.file
    else:
        while True:
            path_str = input("Path to deposition PDF/DOCX/image: ").strip('" ')
            pdf_path = pathlib.Path(path_str)
            if pdf_path.exists():
                break
            print("❌  File not found — try again.\n")

    # ── 2. Ask for test‑mode if flag not supplied ─────────────────────────
    if args.test_chunks is None:
        reply = input("Activate test mode? (y/N) ").lower().strip()
        if reply.startswith("y"):
            args.test_chunks = 2   # default sample size

    # ── 3. Extract & chunk ────────────────────────────────────────────────
    print(f"\n▶  Extracting & chunking {pdf_path.name} …")
    chunks = run_extraction(pdf_path, max_tokens=args.tokens)
    if args.test_chunks:
        chunks = chunks[: args.test_chunks]
        print(f"[pipeline] Test mode ON — using first {args.test_chunks} chunks")

    # ── 4. Cache chunks to .pkl ───────────────────────────────────────────
    cache_path = pdf_path.with_suffix(".chunks.pkl")
    cache_path.write_bytes(pickle.dumps(chunks))
    print(f"[pipeline] Chunks cached → {cache_path.name}")

    # ── 5. Build deck + JSON ─────────────────────────────────────────────
    deck_name = pdf_path.stem + ("_TEST" if args.test_chunks else "")
    deck_path = build_deck(chunks, deck_name=deck_name,
                           max_cards_per_chunk=args.cards)
    json_path = deck_path.with_suffix(".cards.json")

    print(f"\n✅  Deck:  {deck_path.name}")
    print(f"✅  JSON:  {json_path.name}")

    # ── 6. Prompt to play Game 2 ──────────────────────────────────────────
    reply = input("\nPlay Game 2 now? (y/n) Ctrl + C to exit at any time").lower().strip()
    if reply.startswith("n"):
        print("Done!  Import the .apkg into Anki.")
        sys.exit()

    # ── 7. Launch Mastery Drill ──────────────────────────────────────────
    play(load_cards(json_path), endless=args.endless)

if __name__ == "__main__":
    main()
