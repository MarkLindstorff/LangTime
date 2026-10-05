"""Importerer en .txt-fil til LangTime-databasen.

Brug: python import_text.py sti/til/fil.txt "Titel på teksten"
"""
import sys
from db import add_text

def main():
    if len(sys.argv) != 3:
        print("Brug: python import_text.py <sti-til-txt-fil> <titel>")
        sys.exit(1)

    path, title = sys.argv[1], sys.argv[2]

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Fandt ikke filen: {path}")
        sys.exit(1)

    if not content.strip():
        print("Filen er tom — importer ikke.")
        sys.exit(1)

    text_id = add_text(title, content)
    print(f"'{title}' gemt med id {text_id}. Åbn den på /read/{text_id}")

if __name__ == '__main__':
    main()