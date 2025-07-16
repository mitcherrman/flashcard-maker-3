# game2_cli.py  –  Mastery Drill in plain terminal
import json, random, pathlib, argparse

def load_cards(json_file):
    data = json.loads(pathlib.Path(json_file).read_text(encoding="utf-8"))
    # normalise: each dict must have id/front/back
    for i, c in enumerate(data):
        c.setdefault("id", f"c{i}")
    return data

def ask(card):
    print(f"\n❓  {card['front']}")
    ans = input("Your answer (leave blank to self-reveal): ").strip()
    print(f"✅  {card['back']}\n")
    if ans == "":
        correct = input("Did you remember it? (y/N) ").lower().startswith("y")
    else:
        # crude check: exact match ignoring case/punct
        correct = ans.lower().strip(". ,") == card["back"].lower().strip(". ,")
    return correct

def play(cards, endless=False):
    draw_pile = cards[:]
    correct_pile = []
    random.shuffle(draw_pile)

    while draw_pile:
        card = draw_pile.pop(0)
        if ask(card):
            correct_pile.append(card)
            print(f"👍  Correct! {len(correct_pile)}/{len(cards)} mastered.")
            if endless:
                draw_pile.append(card)  # re-insert for endless mode
        else:
            draw_pile.append(card)
            print(f"👎  Wrong. Card shuffled back.")
    print("\n🎉  All cards answered correctly!")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cards_json", help="*.cards.json produced by flashcard_gen")
    ap.add_argument("--endless", action="store_true", help="re-insert correct cards")
    args = ap.parse_args()
    play(load_cards(args.cards_json), endless=args.endless)
