

```markdown
# LangTime — Lokal Læser & Oversætter

LangTime er en privat, lokal alternativ til platforme som LingQ. Målet er at skabe et værktøj, hvor man kan læse tekster, slå ord op, og gemme sin egen læreforløb uden abonnementer eller langsomme oversættelser. Alt sker lokalt på din maskine.

## Funktioner

- **Tekst-styring:** Upload `.txt`-filer via browseren eller importér fra kommandolinjen. Hver tekst får sin egen URL.
- **Interaktiv læsning:** Tekster renderes ord-for-ord. Klik på ethvert ord for at se en oversættelse.
- **Lokal oversættelse:** Bruger LibreTranslate-serveren kørende lokalt. Hurtigere og ingen grænser.
- **Ord-bog & Statistik:** 
  - Gem ord med en status (Ny, Lærer, Kender).
  - Farvekodning i teksten baseret på status (blå/orange/grøn).
  - Caching: Hentede oversættelser gemmes i SQLite, så genopslag er øjeblikkelige.
- **Persistens:** Dine ord og tekster gemmes i en database og overlever genstart af serveren.

## Teknologi-stack

| Komponent | Værktøj / Bibliotek |
|-----------|---------------------|
| **Backend** | Python 3, Flask |
| **Database** | SQLite (via `sqlite3` modulet) |
| **Oversættelse** | LibreTranslate (lokal instans) |
| **HTTP-klient** | `requests` |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |

## Installation og Opsætning

Projektet kræver to virtuelle miljöer: ét til selve appen og ét til LibreTranslate-tjenesten (for at isolere afhængigheder).

### 1. Klone projektet

```bash
git clone <din-git-url>
cd LangTime
```

### 2. Opret virtuelle miljöer

Appens miljø (`.venv`):
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

LibreTranslate-miljø (`lt-env`):
```bash
python3 -m venv lt-env
source lt-env/bin/activate
pip install libretranslate
deactivate
```

### 3. Start LibreTranslate

I et terminalvindue med `lt-env` aktiveret:
```bash
libretranslate --port 5001
```
*Lad dette vindue køre i baggrunden. Det er oversættelsesserveren.*

### 4. Start appen

I et nyt terminalvindue med `.venv` aktiveret:
```bash
python app.py
```

### 5. Brug
Åbn **http://127.0.0.1:5000** i din browser.

## Brugervejledning

1. **Importér tekst:** Upload en `.txt`-fil via forsiden eller brug kommandoen `python import_text.py <fil> <titel>`.
2. **Læs:** Klik på en teksttitel i biblioteket.
3. **Slå op:** Klik på et ukendt ord for at se oversættelsen.
4. **Gem status:** Vælg "Ny", "Lærer" eller "Kender" i popup'en. Ordet farves herefter i teksten.

## Udvidelser og Fremtid

- Automatisk start af LibreTranslate ved opstart af appen (én-kommando-launch).
- Support for `.epub`-filer via `ebooklib`.
- Mere avanceret statistik pr. tekst.

## Licens

MIT License.
```