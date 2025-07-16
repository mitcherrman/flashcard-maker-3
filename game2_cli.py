# game2_cli.py — Basic & Multiple‑choice drills
import json, random, pathlib, argparse

# ────────────────────────────────────────────────────────────────
def load_cards(json_file: str):
    data = json.loads(pathlib.Path(json_file).read_text(encoding="utf-8"))
    for i, c in enumerate(data):
        c.setdefault("id", f"c{i}")
        c.setdefault("distractors", [])          # may be empty
    return data
# ────────────────────────────────────────────────────────────────
# BASIC mode helpers
def ask_basic(card, idx, total, correct, wrong):
    print(f"\n── Card {idx}/{total}  |  ✔ {correct}  ✘ {wrong} ──")
    print(f"❓  {card['front']}")
    ans = input("Press Enter to reveal answer: ")
    print(f"✅  {card['back']}\n")
    return input("Did you recall it? (y/N) ").lower().startswith("y")

def play_basic(cards, endless=False):
    remaining = cards[:]            # cards still to master
    random.shuffle(remaining)
    total = len(remaining)
    correct = wrong = 0

    while remaining:
        card = remaining.pop(0)
        idx  = total - len(remaining)   # 1‑based position
        good = ask_basic(card, idx, total, correct, wrong)

        if good:
            correct += 1
            if endless:                 # recycle only in endless mode
                remaining.append(card)
        else:
            wrong += 1
            remaining.append(card)

    print(f"\n🎉  All {total} cards answered correctly!")
    print(f"Session summary → ✔ {correct}  ✘ {wrong}")
    print("Thank you — game over!\n")
# ────────────────────────────────────────────────────────────────
# MULTIPLE‑CHOICE helpers
def ask_mc(card, idx, total, correct, wrong):
    options = [card["back"]] + card["distractors"][:2]
    while len(options) < 3:
        options.append("N/A")
    random.shuffle(options)
    correct_idx = options.index(card["back"]) + 1

    print(f"\n── Card {idx}/{total}  |  ✔ {correct}  ✘ {wrong} ──")
    print(f"❓  {card['front']}\n")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    choice = input("\nSelect 1‑3: ").strip()
    right = choice == str(correct_idx)
    print("✅  Correct!\n" if right else f"❌  Wrong. Correct answer: {card['back']}\n")
    return right

def play_mc(cards, endless=False):
    remaining = cards[:]
    random.shuffle(remaining)
    total = len(remaining)
    correct = wrong = 0

    while remaining:
        card = remaining.pop(0)
        idx  = total - len(remaining)
        good = ask_mc(card, idx, total, correct, wrong)

        if good:
            correct += 1
            if endless:
                remaining.append(card)
        else:
            wrong += 1
            remaining.append(card)

    print(f"\n🎉  All {total} cards answered correctly!")
    print(f"Session summary → ✔ {correct}  ✘ {wrong}")
    print("Thank you — game over!\n")
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_json")
    ap.add_argument("--mode", choices=["basic", "mc"], default="basic",
                    help="'basic' (default) or 'mc' for multiple‑choice")
    ap.add_argument("--endless", action="store_true")
    args = ap.parse_args()

    cards = load_cards(args.cards_json)
    if args.mode == "mc":
        play_mc(cards, endless=args.endless)
    else:
        play_basic(cards, endless=args.endless)
