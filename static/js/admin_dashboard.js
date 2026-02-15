document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('refreshRatesForm');
    const btn = document.getElementById('refreshRatesBtn');
    const icon = document.getElementById('refreshIcon');
    const textDesktop = document.getElementById('refreshTextDesktop');
    const textMobile = document.getElementById('refreshTextMobile');

    if (form) {
        form.addEventListener('submit', function(e) {
            btn.disabled = true;
            icon.classList.add('fa-spin');
            textDesktop.textContent = 'Actualisation...';
            textMobile.textContent = 'En cours...';

            setTimeout(function() {
                if (btn.disabled) {
                    btn.disabled = false;
                    icon.classList.remove('fa-spin');
                    textDesktop.textContent = 'Actualiser les taux';
                    textMobile.textContent = 'Actualiser';
                }
            }, 15000);
        });
    }

    window.addEventListener('pageshow', function(event) {
        if (event.persisted && btn) {
            btn.disabled = false;
            icon.classList.remove('fa-spin');
            textDesktop.textContent = 'Actualiser les taux';
            textMobile.textContent = 'Actualiser';
        }
    });
});
