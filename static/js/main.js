document.addEventListener('DOMContentLoaded', () => {
    // --- SÆTNINGSOVERSKÆTTELSE: markering af tekst ---
    const readerText = document.querySelector('.reader-text');
    let selectionBtn = null;

    function hideSelectionButton() {
        if (selectionBtn) {
            selectionBtn.remove();
            selectionBtn = null;
        }
    }

    document.addEventListener('mouseup', (e) => {
        // IGNORÉR mouseup fra knappen selv — ellers genskaber den sig!
        if (e.target.closest && e.target.closest('.selection-btn')) return;

        // setTimeout: markeringen er først færdigregistreret lige efter mouseup
        setTimeout(() => {
            const selection = window.getSelection();
            const text = selection ? selection.toString().trim() : '';

            const isValid =
                text &&
                text.includes(' ') &&                       // mere end ét ord
                selection.rangeCount > 0 &&
                readerText && readerText.contains(selection.anchorNode);   // markeringen er i teksten

            if (!isValid) {
                hideSelectionButton();
                return;
            }

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            showSelectionButton(text, rect);
        }, 0);
    });

    function showSelectionButton(text, rect) {
        hideSelectionButton();

        selectionBtn = document.createElement('button');
        selectionBtn.className = 'selection-btn';
        selectionBtn.textContent = 'Oversæt';

        selectionBtn.onclick = (e) => {
            e.stopPropagation();

            // Ryd tekstmarkeringen, så systemet er i ren tilstand,
            // og mouseup-listeneren ikke ser noget at genskabe
            window.getSelection().removeAllRanges();

            hideSelectionButton();
            showPhrasePopup(text, rect);
        };

        document.body.appendChild(selectionBtn);
        selectionBtn.style.left = (rect.left + rect.width / 2) + 'px';
        selectionBtn.style.top = (rect.bottom + window.scrollY + 8) + 'px';
        selectionBtn.style.zIndex = 1002;
    }

    function showPhrasePopup(phrase, rect) {
        document.querySelectorAll('.popup').forEach(p => p.remove());

        const popup = document.createElement('div');
        popup.className = 'popup';
        popup.textContent = 'Oversætter...';
        document.body.appendChild(popup);

        popup.style.left = Math.max(10, rect.left) + 'px';
        popup.style.top = (rect.bottom + window.scrollY + 8) + 'px';
        popup.style.zIndex = 1001;

        fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phrase: true, text: phrase })
        })
        .then(res => res.json())
        .then(data => {
            popup.innerHTML = '';
            const title = document.createElement('strong');
            title.textContent = data.translation || data.error;
            popup.appendChild(title);
        })
        .catch(() => {
            popup.textContent = 'Netværksfejl';
        });

        // Luk popup ved klik udenfor
        setTimeout(() => {
            document.addEventListener('click', function close(e) {
                if (!popup.contains(e.target)) {
                    popup.remove();
                    document.removeEventListener('click', close);
                }
            });
        }, 100);
    }

    // --- ORD-OVERSKÆTTELSE (klik på ét ord) ---
    document.querySelectorAll('.word').forEach(span => {
        span.addEventListener('click', async () => {
            // Spring over hvis brugeren har lavet en tekstmarkering
            const sel = window.getSelection();
            if (sel && sel.toString().trim().length > 0) return;

            document.querySelectorAll('.popup').forEach(p => p.remove());
            hideSelectionButton();

            const word = span.textContent;
            const popup = document.createElement('div');
            popup.className = 'popup';
            popup.textContent = 'Oversætter...';
            document.body.appendChild(popup);

            const rect = span.getBoundingClientRect();
            popup.style.left = rect.left + 'px';
            popup.style.top = (rect.bottom + window.scrollY) + 'px';
            popup.style.zIndex = 1001;

            let translation = '';
            try {
                const res = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word })
                });
                const data = await res.json();
                if (data.error) {
                    popup.textContent = data.error;
                    setTimeout(() => popup.remove(), 3000);
                    return;
                }
                translation = data.translation;
                buildPopupContent(popup, span, word, translation, data.status);
            } catch (err) {
                popup.textContent = 'Netværksfejl';
                setTimeout(() => popup.remove(), 2000);
            }
        });
    });

    function buildPopupContent(popup, span, word, translation, existingStatus) {
        popup.textContent = '';

        const title = document.createElement('strong');
        title.textContent = `${word} → ${translation}`;
        popup.appendChild(title);

        const buttons = document.createElement('div');
        buttons.className = 'popup-buttons';

        [['new', 'Ny'], ['learning', 'Lærer'], ['known', 'Kender']].forEach(([status, label]) => {
            const btn = document.createElement('button');
            btn.textContent = label;
            if (existingStatus === status) btn.classList.add('active');
            btn.onclick = async () => {
                await fetch('/api/word', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word, translation, status })
                });
                span.className = 'word status-' + status;
                popup.remove();
            };
            buttons.appendChild(btn);
        });
        popup.appendChild(buttons);

        // Luk ved klik udenfor
        setTimeout(() => {
            document.addEventListener('click', function close(e) {
                if (!popup.contains(e.target)) {
                    popup.remove();
                    document.removeEventListener('click', close);
                }
            });
        }, 100);
    }
});