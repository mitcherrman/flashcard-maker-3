import os, json
from decouple import config
from prompt_cards import generate_from_prompt
from ingest import extract_text

 
def main(option: str):    
    if option == "from_pdf":
        path = input("File path")
        extract_text(path)
    elif option == "from_prompt":
        topic = input("topic")
        num_cards = int(input("num_cards_to_generate"))
        generate_from_prompt(topic, num_cards)


if __name__ == "__main__":
    os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_API_KEY"))
    main("user option placeholder")


'''
# testing each option seperately
if __name__ == "__main__":
    os.environ.setdefault("OPENAI_API_KEY", config("OPENAI_API_KEY"))
    cards = generate_from_prompt("world war 2", 3)
    print(json.dumps(cards, indent=2))
    '''