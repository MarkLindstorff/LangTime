#!/usr/bin/env python3
"""Importerer en PDF-fil til LangTime-biblioteket.

Brug: python import_pdf.py <sti-til-pdf-fil> [<titel>] [--lang <kode>]

Eksempel:
    python import_pdf.py bog.pdf "Krige og fred" --lang ru

BEMÆRK: Scannede PDF'er (billeder af tekst) kan ikke udtrækkes uden OCR.
"""

import argparse
import sys

try:
    from pypdf import PdfReader
except ImportError:
    print('✗ pypdf er ikke installeret. Installer med: pip install pypdf')
    sys.exit(1)

from db import init_db, add_text

def extract_pdf_text(path: str) -> str:
    """Læser alle sider i PDF'en og samler teksten.
    
    Hver side afsluttes med blanklinje, så afsnits-opdelingen
    (\\n\\n-splitting i read_text) får en chance.
    """
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ''
        text = text.strip()
        if text:
            pages.append(text)
    if not pages:
        raise ValueError('PDF\'en indeholder ingen udtrækkelig tekst.')
    return '\\n\\n'.join(pages)

def main():
    parser = argparse.ArgumentParser(
        description='Importér PDF til LangTime'
    )
    parser.add_argument('file', help='Sti til PDF-filen')
    parser.add_argument('--title', default='', help='Titel (standard: filnavnet)')
    parser.add_argument('--lang', default='ru', choices=[
        'ru', 'da', 'en', 'de', 'fr', 'es', 'it', 'nl',
        'pl', 'sv', 'nb', 'fi', 'uk', 'cs', 'pt',
    ], help='Kilde-sprog (standard: ru)')
    args = parser.parse_args()

    init_db()

    try:
        content = extract_pdf_text(args.file)
    except FileNotFoundError:
        print(f'✗ Filen findes ikke: {args.file}')
        sys.exit(1)
    except ValueError as e:
        print(f'✗ {e}')
        print('(Scannede PDF er uden tekstlag kan ikke importeres uden OCR.)')
        sys.exit(1)

    title = args.title or args.file.rsplit('/', 1)[-1].rsplit('\\\\', 1)[-1][:-4] \
        if args.file.lower().endswith('.pdf') else args.title

    text_id = add_text(title, content, args.lang)
    print(f'✓ Importeret: "{title}" ({args.lang}) → tekst #{text_id} '
          f'({len(content)} tegn, {content.count("\\n\\n")+1} afsnit)')

if __name__ == '__main__':
    main()