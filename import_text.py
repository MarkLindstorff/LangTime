#!/usr/bin/env python3
"""Importerer en .txt-fil til LangTime-databasen.

Brug: python import_text.py <sti-til-txt-fil> [<titel>] [--lang <kode>]

Eksempel:
    python import_text.py tekst.txt "Krig og Fred" --lang ru
"""

import argparse
import sys

from db import init_db, add_text

def main():
    parser = argparse.ArgumentParser(
        description='Importér .txt-fil til LangTime-biblioteket'
    )
    parser.add_argument('file', help='Sti til .txt-filen')
    parser.add_argument('--title', default='', help='Titel (standard: filnavnet)')
    parser.add_argument('--lang', default='ru', choices=[
        'ru', 'da', 'en', 'de', 'fr', 'es', 'it', 'nl',
        'pl', 'sv', 'nb', 'fi', 'uk', 'cs', 'pt',
    ], help='Kilde-sprog (standard: ru)')
    args = parser.parse_args()

    init_db()

    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f'✗ Filen findes ikke: {args.file}')
        sys.exit(1)
    except UnicodeDecodeError:
        print(f'✗ Kunne ikke læse filen som UTF-8: {args.file}')
        sys.exit(1)

    if not content.strip():
        print('✗ Filen er tom — importer ikke.')
        sys.exit(1)

    title = args.title or args.file.rsplit('/', 1)[-1].rsplit('\\', 1)[-1][:-4] \
        if args.file.lower().endswith('.txt') else args.title

    text_id = add_text(title, content, args.lang)
    print(f'✓ Importeret: "{title}" ({args.lang}) → tekst #{text_id} '
          f'({len(content)} tegn)')

if __name__ == '__main__':
    main()