# pipeline.py — one‑shot workflow: PDF → Anki deck (+ JSON) → optional Game 2
from __future__ import annotations
import pathlib, sys, pickle, argparse
from driver import run_extraction
from flashcard_gen import build_deck
from game2_cli import load_cards
import random


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
            path_str = input("Path to PDF/DOCX/image  *or*  existing cards.json: ").strip('" ')
            pdf_path = pathlib.Path(path_str)
            if pdf_path.exists():
                break
            print("❌  File not found — try again.\n")

    # ── 1‑b. Quick‑play if user gave a .cards.json file ───────────────────────
    if pdf_path.suffix.lower() == ".json":
        json_path = pdf_path
        print(f"\n▶  Using pre‑existing card set: {json_path.name}")
        # ask play‑prompt just like normal build path
        goto_play = True
    else:
        goto_play = False

    # ── 2. Ask for test‑mode if flag not supplied ─────────────────────────
    if args.test_chunks is None:
        reply = input("Activate test mode? (y/n) ").lower().strip()
        if reply.startswith("y"):
            while True:
                cnt = input("How many random chunks (1‑5)? ").strip()
                if cnt.isdigit() and 1 <= int(cnt) <= 5:
                    args.test_chunks = int(cnt)
                    break
                print("Please enter a number between 1 and 5.")

    if not goto_play:
        # ── 3. Extract & chunk ────────────────────────────────────────────────
        print(f"\n▶  Extracting & chunking {pdf_path.name} …")
        chunks = run_extraction(pdf_path, max_tokens=args.tokens)
    if args.test_chunks:
        take = min(args.test_chunks, len(chunks))
        chunks = random.sample(chunks, take)
        print(f"[pipeline] Test mode ON — using {take} random chunk(s)")

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
        json_path = deck_path.with_suffix(".cards.json")

        # ── 6. Choose which game to play ─────────────────────────────────────
    game_choice = input(
        "\nPlay a game now?  1) Curate & Improve   2) Mastery Drill   (n = cancel) : "
    ).lower().strip()

    if game_choice.startswith("n"):
        print("Bye!  Import the .apkg into Anki whenever you like.")
        sys.exit()

    if game_choice not in {"1", "2"}:
        print("Invalid input. Exiting.")
        sys.exit()

    # ── 6‑b. Game‑specific options ──────────────────────────────────────
    if game_choice == "1":
        # Game 1 — no endless, no MC/BASIC distinction
        from game1_cli import play_curate as play_fn
        endless = False  # not used, but keep signature
    else:
        # Game 2 — ask for Basic vs Multiple‑choice and endless toggle
        while True:
            gm2_mode = input("Mode: 1) Basic  2) Multiple‑choice : ").strip()
            if gm2_mode in {"1", "2"}:
                break
        mode = "mc" if gm2_mode == "2" else "basic"

        endless = args.endless
        if not args.endless:
            endless_reply = input(
                "Enable endless mode (recycle correct cards)? (y/N) "
            ).lower().strip()
            endless = endless_reply.startswith("y")

        if mode == "mc":
            from game2_cli import play_mc as play_fn
        else:
            from game2_cli import play_basic as play_fn

    # ── 7. Launch the chosen game ───────────────────────────────────────
    play_fn(load_cards(json_path), endless=endless)

#----
if __name__ == "__main__":
        main()
