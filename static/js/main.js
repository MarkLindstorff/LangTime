document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.word').forEach(span => {
        span.addEventListener('click', async () => {
            const word = span.textContent;

            // Undgå spam ved dobbeltklik
            if (span.dataset.loading) return;
            span.dataset.loading = "1";

            // Fjern evt. gammel popup
            document.querySelectorAll('.popup').forEach(p => p.remove());

            const popup = document.createElement('div');
            popup.className = 'popup';
            popup.textContent = 'Oversætter...';
            document.body.appendChild(popup);

            // Placér popup lige under ordet
            const rect = span.getBoundingClientRect();
            popup.style.left = rect.left + 'px';
            popup.style.top = (rect.bottom + window.scrollY) + 'px';

            try {
                const res = await fetch('/api/translate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ word: word })
                });
                const data = await res.json();
                popup.textContent = data.translation || data.error;
            } catch (err) {
                popup.textContent = 'Netværksfejl';
            } finally {
                span.dataset.loading = "";
            }

            // Popup forsvinder efter 5 sekunder
            setTimeout(() => popup.remove(), 5000);
        });
    });
});