import string
import requests
from flask import Flask, render_template, request, jsonify, abort
from translator import translate_word
from db import init_db, get_words_bulk, get_word, upsert_word, list_texts, get_text

app = Flask(__name__)

PUNCTUATION = string.punctuation + "«»—…„“”'"

def clean_word(raw: str) -> str:
    """Fjerner tegnsætning og mellemrum fra et råt ord."""
    return raw.strip(PUNCTUATION)

@app.route('/')
def home():
    texts = list_texts()
    return render_template('index.html', texts=texts)

@app.route('/read/<int:text_id>')
def read_text(text_id):
    text = get_text(text_id)
    if text is None:
        abort(404)

    raw_words = text['content'].split()
    words = []
    for raw in raw_words:
        cleaned = clean_word(raw)
        words.append({
            'raw': raw,
            'clean': cleaned,
        })

    statuses = get_words_bulk([w['clean'] for w in words])

    for w in words:
        w['status'] = statuses.get(w['clean'], None)

    return render_template('reader.html', text=text, words=words)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    raw = request.json.get('word', '').strip()
    word = clean_word(raw)
    if not word:
        return jsonify({'error': 'Mangler ord'}), 400

    # --- CACHE-TJEK ---
    cached = get_word(word)
    if cached:
        return jsonify({
            'word': word,
            'translation': cached['translation'],
            'status': cached['status'],
            'cached': True
        })

    try:
        translation = translate_word(word)
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

    if not word:
        return jsonify({'error': 'Mangler ord'}), 400
    if status not in ('new', 'learning', 'known'):
        return jsonify({'error': 'Ugyldig status'}), 400

    upsert_word(word, translation, status)
    return jsonify({'success': True, 'word': word, 'status': status})

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