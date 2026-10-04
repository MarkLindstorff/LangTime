from flask import Flask, render_template, request, jsonify
import requests
from translator import translate_word

app = Flask(__name__)

@app.route('/')
def home():
    with open('texts/example.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    words = text.split()
    return render_template('index.html', words=words)

@app.route('/api/translate', methods=['POST'])
def api_translate():
    word = request.json.get('word', '').strip()
    if not word:
        return jsonify({'error': 'Mangler ord'}), 400
    try:
        translation = translate_word(word)
        return jsonify({'word': word, 'translation': translation})
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'LibreTranslate kører ikke'}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Oversættelse tog for lang tid'}), 504

if __name__ == '__main__':
    app.run(debug=True)