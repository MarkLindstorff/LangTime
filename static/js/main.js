document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.word').forEach(span => {
        span.addEventListener('click', async () => {
            document.querySelectorAll('.popup').forEach(p => p.remove());

            const word = span.textContent;
            const popup = document.createElement('div');
            popup.className = 'popup';
            popup.textContent = 'Oversætter...';
            document.body.appendChild(popup);

            const rect = span.getBoundingClientRect();
            popup.style.left = rect.left + 'px';
            popup.style.top = (rect.bottom + window.scrollY) + 'px';

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