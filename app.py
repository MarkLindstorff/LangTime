from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # Her læser vi filen og splittet op i ord
    with open('texts/example.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Opdel i ord (simpelt split)
    words = text.split()
    
    return render_template('index.html', words=words)

if __name__ == '__main__':
    app.run(debug=True)