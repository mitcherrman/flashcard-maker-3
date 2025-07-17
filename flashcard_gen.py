# flashcard_gen.py --------------------------------------------------------
import os, json, random, pathlib, sys
from typing import List
from decouple import config
from openai import OpenAI
import genanki

os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_API_KEY"))
client = OpenAI()                               # picks up key from env

def _cards_from_chunk(chunk: str, max_cards=10):
    sys_msg = SYSTEM_PROMPT = """
You are an expert flash‑card author.

Goals:
1. Create *multiple‑choice* Q‑A pairs that help a student remember the
   substantive facts, definitions, dates, or numbers in the text.
2. Each card must be self‑contained; never refer to pages or exhibits.
3. Provide **exactly one** correct answer and **two** plausible but wrong
   answers (distractors).
4. Do not give vague or redundant answers.

Return JSON:
{
  "cards": [
    {
      "front": "...question...",
      "back":  "...correct answer...",
      "distractors": ["wrong A", "wrong B"]
    }
  ]
}
Limit to {max_cards} cards.
"""


    resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT.replace("{{max_cards}}", str(max_cards))},
        {"role": "user",   "content": chunk},
    ],
    response_format={"type": "json_object"},
    max_tokens=800,
)
    return json.loads(resp.choices[0].message.content)["cards"][:max_cards]

def build_deck(chunks: List[str], deck_name: str,
               max_cards_per_chunk: int = 10) -> pathlib.Path:
    """Return Path to the generated .apkg file and also write a .cards.json file."""
    all_cards: list[dict] = []
    for i, ch in enumerate(chunks, 1):
        new_cards = _cards_from_chunk(ch, max_cards_per_chunk)
        print(f"[flashcard_gen] Chunk {i}/{len(chunks)} → {len(new_cards)} card(s)")
        all_cards.extend(new_cards)
    total_cards = len(all_cards)
    print(f"[flashcard_gen] Total cards generated: {total_cards}")


    # --- JSON dump for Game 2 ---
    json_path = pathlib.Path(deck_name.replace(" ", "_") + ".cards.json")
    json_path.write_text(json.dumps(all_cards, ensure_ascii=False, indent=2))
    print("[flashcard_gen] Card JSON written →", json_path)

    deck = genanki.Deck(random.randrange(1<<30), deck_name[:90])
    model = genanki.Model(
        random.randrange(1<<30), "Basic",
        fields=[{"name":"Front"},{"name":"Back"}],
        templates=[{"name":"Card",
                    "qfmt":"{{Front}}",
                    "afmt":"{{Back}}<hr id=answer>"}],
    )
    for c in all_cards:
        deck.add_note(genanki.Note(model, [c["front"], c["back"]]))

    out = pathlib.Path(deck_name.replace(" ", "_") + ".apkg")
    genanki.Package(deck).write_to_file(out)
    print("[flashcard_gen] Deck written →", out.resolve())
    return out