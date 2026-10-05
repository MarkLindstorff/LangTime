import os
import string
import requests
from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from translator import translate_word, translate_text
from db import (init_db, get_words_bulk, get_word, upsert_word, list_texts,
                get_text, add_text, get_setting, set_setting)

app = Flask(__name__)

PUNCTUATION = string.punctuation + "«»—…„“”'"

LANGUAGES = {
    'ru': 'Russisk', 'da': 'Dansk', 'en': 'Engelsk', 'de': 'Tysk',
    'fr': 'Fransk', 'es': 'Spansk', 'it': 'Italiensk', 'nl': 'Hollandsk',
    'pl': 'Polsk', 'sv': 'Svensk', 'nb': 'Norsk', 'fi': 'Finsk',
    'uk': 'Ukrainsk', 'cs': 'Tjekkisk', 'pt': 'Portugisisk',
}

def clean_word(raw: str) -> str:
    """Fjerner tegnsætning og mellemrum fra et råt ord."""
    return raw.strip(PUNCTUATION)

@app.route('/')
def home():
    texts = list_texts()
    return render_template('index.html', texts=texts, languages=LANGUAGES)

@app.route('/upload', methods=['POST'])
def upload_text():
    """Modtager en .txt-fil og titel fra formularen, gemmer i databasen."""
    file = request.files.get('file')

    if file is None or file.filename == '':
        return render_template(
            'index.html',
            texts=list_texts(),
            languages=LANGUAGES,
            error='Du skal vælge en fil.'
        ), 400

    if not file.filename.lower().endswith('.txt'):
        return render_template(
            'index.html',
            texts=list_texts(),
            languages=LANGUAGES,
            error='Kun .txt-filer er understøttet indtil videre.'
        ), 400

    try:
        content = file.read().decode('utf-8')
    except UnicodeDecodeError:
        return render_template(
            'index.html',
            texts=list_texts(),
            languages=LANGUAGES,
            error='Kunne ikke læse filen som UTF-8 tekst. Er det en almindelig tekstfil?'
        ), 400

    if not content.strip():
        return render_template(
            'index.html',
            texts=list_texts(),
            languages=LANGUAGES,
            error='Filen er tom.'
        ), 400

    # Titel: brug formularens titel, ellers filnavnet uden .txt
    title = request.form.get('title', '').strip()
    if not title:
        title = os.path.splitext(file.filename)[0]

    # Kilde-sprog: brug formularens valg, med fallback til russisk
    source_lang = request.form.get('source_lang', 'ru')
    if source_lang not in LANGUAGES:
        source_lang = 'ru'

    text_id = add_text(title, content, source_lang)
    return redirect(url_for('read_text', text_id=text_id))

@app.route('/read/<int:text_id>')
def read_text(text_id):
    text = get_text(text_id)
    if text is None:
        abort(404)

    target_lang = get_setting('target_lang', 'da')

    # Normaliser linjeskift (Windows-filer bruger \r\n) og del i afsnit
    content = text['content'].replace('\r\n', '\n')
    paragraphs_raw = [p for p in content.split('\n\n') if p.strip()]

    paragraphs = []
    for para_raw in paragraphs_raw:
        words = []
        for raw in para_raw.split():
            words.append({'raw': raw, 'clean': clean_word(raw)})
        if words:
            paragraphs.append(words)

    # Slå alle ordene op i databasen på én gang (i det valgte målsprog)
    all_clean = [w['clean'] for para in paragraphs for w in para]
    statuses = get_words_bulk(all_clean, target_lang)

    for para in paragraphs:
        for w in para:
            w['status'] = statuses.get(w['clean'], None)

    return render_template('reader.html', text=text, paragraphs=paragraphs,
                           languages=LANGUAGES, target_lang=target_lang)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data = request.json or {}
    target = data.get('target', get_setting('target_lang', 'da'))

    # --- SÆTNINGSOVERSKÆTTELSE (først) ---
    if data.get('phrase'):
        phrase = (data.get('text') or '').strip()
        if not phrase:
            return jsonify({'error': 'Mangler tekst'}), 400
        if len(phrase) > 500:
            return jsonify({'error': 'Teksten er for lang (max 500 tegn)'}), 400
        try:
            translation = translate_text(phrase, target=target)
            return jsonify({'text': phrase, 'translation': translation})
        except requests.exceptions.ConnectionError:
            return jsonify({'error': 'LibreTranslate kører ikke'}), 503
        except requests.exceptions.Timeout:
            return jsonify({'error': 'Oversættelse tog for lang tid'}), 504

    # --- ORD-OVERSKÆTTELSE ---
    raw = data.get('word', '').strip()
    word = clean_word(raw)
    if not word:
        return jsonify({'error': 'Mangler ord'}), 400

    # --- CACHE-TJEK (pr. målsprog) ---
    cached = get_word(word, target)
    if cached:
        return jsonify({
            'word': word,
            'translation': cached['translation'],
            'status': cached['status'],
            'cached': True
        })

    try:
        translation = translate_word(word, target=target)
        return jsonify({'word': word, 'translation': translation, 'cached': False})
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'LibreTranslate kører ikke'}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Oversættelse tog for lang tid'}), 504

@app.route('/api/word', methods=['POST'])
def api_save_word():
    """Gem eller opdater et ord med en status."""
    data = request.json
    word = clean_word(data.get('word', ''))
    translation = data.get('translation', '')
    status = data.get('status', 'new')
    target = data.get('target', get_setting('target_lang', 'da'))

    if not word:
        return jsonify({'error': 'Mangler ord'}), 400
    if status not in ('new', 'learning', 'known'):
        return jsonify({'error': 'Ugyldig status'}), 400

    upsert_word(word, translation, status, target)
    return jsonify({'success': True, 'word': word, 'status': status})

@app.route('/api/settings/target-lang', methods=['POST'])
def api_set_target_lang():
    """Gem brugerens foretrukne målsprog."""
    data = request.json or {}
    lang = data.get('target_lang', '')
    if lang not in LANGUAGES:
        return jsonify({'error': 'Ugyldigt sprog'}), 400
    set_setting('target_lang', lang)
    return jsonify({'success': True, 'target_lang': lang})

@app.route('/api/stats')
def api_stats():
    """Små statistikker til forsiden."""
    from db import get_connection
    with get_connection() as conn:
        counts = dict(conn.execute(
            "SELECT status, COUNT(*) as n FROM words GROUP BY status"
        ).fetchall())
    return jsonify(counts)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)