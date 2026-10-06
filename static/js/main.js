document.addEventListener('DOMContentLoaded', () => {
    // --- SÆTNINGSOVERSKÆTTELSE: markering af tekst ---
    const readerText = document.querySelector('.reader-text');
    let selectionBtn = null;
    let selectionHighlight = null;
    let isSelectionActive = false;  // Track om der er en aktiv markering

    // Hent mål-sprog-select elementet
    const targetLangSelect = document.getElementById('target-lang');

    // Gem mål-sprog-valget når brugeren skifter det
    if (targetLangSelect) {
        targetLangSelect.addEventListener('change', () => {
            fetch('/api/settings/target-lang', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_lang: targetLangSelect.value })
            });
        });
    }

    function hideSelectionButton() {
        if (selectionBtn) {
            selectionBtn.remove();
            selectionBtn = null;
        }
    }

    function removeHighlight() {
        if (selectionHighlight) {
            selectionHighlight.remove();
            selectionHighlight = null;
        }
        isSelectionActive = false;
        // Fjern selected-word klasser fra alle ord
        document.querySelectorAll('.word.selected-word').forEach(w => {
            w.classList.remove('selected-word');
        });
    }

    function updateHighlight() {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return;

        const range = selection.getRangeAt(0);
        
        // Tjek om markeringen er inden for readerText
        if (!readerText || !readerText.contains(range.commonAncestorContainer)) {
            return;
        }

        // Få bounding rect for hele selectionen
        const rects = range.getClientRects();
        if (rects.length === 0) {
            return;
        }

        // Beregn den samlede boks omkring alt markeret
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;

        for (let rect of rects) {
            minX = Math.min(minX, rect.left);
            minY = Math.min(minY, rect.top);
            maxX = Math.max(maxX, rect.right);
            maxY = Math.max(maxY, rect.bottom);
        }

        // Fjern gamle selected-word classes og tilføj dem til de ord der er i selectionen
        document.querySelectorAll('.word.selected-word').forEach(w => w.classList.remove('selected-word'));
        
        // Find alle .word elementer der overlapper selectionen
        const walker = document.createTreeWalker(
            readerText,
            NodeFilter.SHOW_ELEMENT,
            { acceptNode: node => node.classList.contains('word') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP }
        );

        let node;
        while (node = walker.nextNode()) {
            const wordRect = node.getBoundingClientRect();
            // Tjek om ordet overlapper nogen af selection rects
            const overlaps = Array.from(rects).some(r => 
                !(wordRect.right < r.left || 
                  wordRect.left > r.right || 
                  wordRect.bottom < r.top || 
                  wordRect.top > r.bottom)
            );
            if (overlaps) {
                node.classList.add('selected-word');
            }
        }

        // Opret eller opdater highlight boks
        if (!selectionHighlight) {
            selectionHighlight = document.createElement('div');
            selectionHighlight.className = 'selection-highlight';
            document.body.appendChild(selectionHighlight);
        }

        selectionHighlight.style.left = (minX - 2) + 'px';
        selectionHighlight.style.top = (minY - 2) + 'px';
        selectionHighlight.style.width = (maxX - minX + 4) + 'px';
        selectionHighlight.style.height = (maxY - minY + 4) + 'px';
    }

    // --- Markering undervejs (mouse drag med rAF-loop) ---
    let isMouseDown = false;
    let rafId = null;

    // Animations-loop der kører MENS man trækker
    function animateHighlight() {
        updateHighlight();
        if (isMouseDown) {
            rafId = requestAnimationFrame(animateHighlight);
        } else {
            rafId = null;
        }
    }

    document.addEventListener('mousedown', (e) => {
        if (e.target.closest && e.target.closest('.selection-btn')) return;
        
        // VIGTIGT: kun start selection hvis man klikker DIREKTE på et .word element
        // Ellers ignorer og lad browseren gøre hvad den vil (cursor etc.)
        if (!e.target.classList.contains('word')) return;
        
        // Hvis man ikke er i .reader-text, ignorer
        if (!readerText || !readerText.contains(e.target)) return;
        
        isMouseDown = true;
        document.body.classList.add('is-selecting');
        // Hvis der allerede var en markering, ryd den først
        if (isSelectionActive) {
            removeHighlight();
        }
        if (!rafId) {
            rafId = requestAnimationFrame(animateHighlight);
        }
    });

    document.addEventListener('mouseup', (e) => {
        isMouseDown = false;
        document.body.classList.remove('is-selecting');
        if (rafId) {
            cancelAnimationFrame(rafId);
            rafId = null;
        }

        // IGNORÉR mouseup fra knappen selv
        if (e.target.closest && e.target.closest('.selection-btn')) return;

        // setTimeout: markeringen er først færdigregistreret lige efter mouseup
        setTimeout(() => {
            const selection = window.getSelection();
            const text = selection ? selection.toString().trim() : '';

            // VIGTIGT: kræv mindst 2 tegn for at betragtes som gyldig markering
            // Dette fjerner de "tomme" selections der kun er et enkelt tegn
            const isValid =
                text.length >= 2 &&  // mindst 2 tegn (så "|" eller enkelttegns ikke virker)
                text.includes(' ') &&                       // mere end ét ord
                selection.rangeCount > 0 &&
                readerText && readerText.contains(selection.anchorNode);

            if (!isValid) {
                hideSelectionButton();
                return;
            }

            isSelectionActive = true;
            
            // Fiks boksen — lav den mere tydelig
            if (selectionHighlight) {
                selectionHighlight.classList.add('fixed');
            }

            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            showSelectionButton(text, rect);
        }, 0);
    });

    // Fjern highlight når man klikker udenfor
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.reader-text') && !e.target.closest('.selection-btn')) {
            removeHighlight();
            hideSelectionButton();
        }
    });

    function showSelectionButton(text, rect) {
        // Fjern ALLE eksisterende popups før vi viser knappen
        document.querySelectorAll('.popup').forEach(p => p.remove());

        hideSelectionButton();

        selectionBtn = document.createElement('button');
        selectionBtn.className = 'selection-btn';
        selectionBtn.textContent = 'Oversæt';

        // VIGTIGT: gem teksten NU, og FIJN KNAPPEN før popup vises
        selectionBtn.onclick = (e) => {
            e.stopPropagation();  // forhindrer at klikket "percolates" videre
            
            // Ryd tekstmarkeringen, så systemet er i ren tilstand
            window.getSelection().removeAllRanges();

            removeHighlight(); // Fjern highlight boksen OG reset flaget
            hideSelectionButton();
            
            // Vent et øjeblik så knappen er væk før popup vises
            setTimeout(() => {
                showPhrasePopup(text, rect);
            }, 50);
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
        
        // Sørg for at popup ikke havder uden for viewport
        popup.style.left = Math.max(10, rect.left) + 'px';
        popup.style.top = (rect.bottom + window.scrollY + 8) + 'px';
        popup.style.zIndex = 1001;

        fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                phrase: true, 
                text: phrase, 
                target: targetLangSelect ? targetLangSelect.value : undefined 
            })
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

        // Luk popup når man klikker udenfor
        setTimeout(() => {
            document.addEventListener('click', function close(e) {
                if (!popup.contains(e.target)) {
                    popup.remove();
                    document.removeEventListener('click', close);
                }
            });
        }, 100);
    }

    // --- ORD-OVERSKÆTTELSE (klick på ét ord) ---
    document.querySelectorAll('.word').forEach(span => {
        span.addEventListener('click', async (e) => {
            e.stopPropagation();  // STOP click fra at gå videre til mousedown handler
            
            // SPRING OVER hvis brugeren har lavet en tekstmarkering
            const sel = window.getSelection();
            if (sel && sel.toString().trim().length > 0) return;

            document.querySelectorAll('.popup').forEach(p => p.remove());
            hideSelectionButton(); // Fjern også knappen hvis den er der
            removeHighlight();     // Fjern også highlight hvis den er der

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
                    body: JSON.stringify({ 
                        word, 
                        target: targetLangSelect ? targetLangSelect.value : undefined 
                    })
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
                    body: JSON.stringify({ 
                        word, 
                        translation, 
                        status,
                        target: targetLangSelect ? targetLangSelect.value : undefined 
                    })
                });
                // Opdater ALLE forekomster af ordet i teksten —
                // status gælder ordet, ikke bare dette span
                document.querySelectorAll('.word').forEach(wordSpan => {
                    if (wordSpan.dataset.word === word) {
                        wordSpan.className = 'word status-' + status;
                    }
                });
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