# game2_cli.py  – Mastery Drill with detailed counters
import json, random, pathlib, argparse

def load_cards(json_file: str):
    data = json.loads(pathlib.Path(json_file).read_text(encoding="utf-8"))
    for i, c in enumerate(data):
        c.setdefault("id", f"c{i}")
    return data

def ask(card, idx, total, correct, wrong):
    print(f"\n── Card {idx}/{total}  |  ✔ {correct}  ✘ {wrong} ──")
    print(f"❓  {card['front']}")
    ans = input("Your answer (press enter to reveal): ").strip()
    print(f"✅  {card['back']}\n")
    if ans == "":
        return input("Did you remember it? type 'y' for yes or 'n' for no) ").lower().startswith("y")
    return ans.lower().strip(" .,!") == card["back"].lower().strip(" .,!")

def play(cards, endless=False):
    draw_pile = cards[:]         # cards still to answer
    random.shuffle(draw_pile)

    total        = len(draw_pile)
    correct_cnt  = 0
    wrong_cnt    = 0
    seen_counter = 0             # how many cards have been shown so far

    while draw_pile:
        card = draw_pile.pop(0)
        seen_counter += 1        # this card is now being shown

        good = ask(card,
                    idx=seen_counter,
                    total=total,
                    correct=correct_cnt,
                    wrong=wrong_cnt)

        if good:
            correct_cnt += 1
            print("👍  Correct!")
            if endless:
                draw_pile.append(card)     # recycle for endless mode
        else:
            wrong_cnt += 1
            draw_pile.append(card)         # put back for another try
            print("👎  Wrong. Card goes back.")

    print(f"\n🎉  All {total} cards answered correctly!")
    print(f"Session summary → ✔ {correct_cnt}  ✘ {wrong_cnt}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_json", help="*.cards.json produced by flashcard_gen")
    ap.add_argument("--endless", action="store_true")
    args = ap.parse_args()
    play(load_cards(args.cards_json), endless=args.endless)
