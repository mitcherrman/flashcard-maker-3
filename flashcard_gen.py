# flashcard_gen.py --------------------------------------------------------
import os, json, random, pathlib
from typing import List
from decouple import config
from openai import OpenAI
import genanki

os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_API_KEY"))
client = OpenAI()                               # picks up key from env

def _cards_from_chunk(chunk: str, max_cards=10):
    sys_msg = SYSTEM_PROMPT = """
You are an expert flash-card author.

Goals:
1. Create Q-A pairs that help a student remember the *substantive* facts,
   definitions, dates, or numbers in the text.
2. Each card must be self-contained – never refer to “page X”, “see above”,
   or “the exhibit”.
3. Answers must be concrete and complete, never “he had issues with exhibits”.
4. Skip cards if the answer would be too vague or redundant.

Return JSON:
{
  "cards": [
    {"front": "...", "back": "..."},
    ...
  ]
}
Limit to **{{max_cards}}** cards.
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
    """Return Path to the generated .apkg file."""
    all_cards = []
    for i, ch in enumerate(chunks, 1):
        print(f"[flashcard_gen] GPT on chunk {i}/{len(chunks)}")
        all_cards.extend(_cards_from_chunk(ch, max_cards_per_chunk))

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

# — optional CLI for pickle replay —
if __name__ == "__main__":
    import argparse, pickle
    p = argparse.ArgumentParser()
    p.add_argument("pickle", type=pathlib.Path, help="*.chunks.pkl file")
    p.add_argument("--cards", type=int, default=10)
    a = p.parse_args()
    chunks = pickle.loads(a.pickle.read_bytes())
    build_deck(chunks, a.pickle.stem, a.cards)
