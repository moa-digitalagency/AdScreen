document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('screen-form-container');
    const currencySymbol = container ? (container.dataset.currencySymbol || '€') : '€';

    const priceInput = document.getElementById('price_per_minute');

    if (priceInput) {
        priceInput.addEventListener('input', function() {
            const pricePerMinute = parseFloat(this.value) || 2.0;
            const p10 = document.getElementById('price_10s');
            const p15 = document.getElementById('price_15s');
            const p30 = document.getElementById('price_30s');

            if(p10) p10.textContent = ((10 / 60) * pricePerMinute).toFixed(2) + currencySymbol;
            if(p15) p15.textContent = ((15 / 60) * pricePerMinute).toFixed(2) + currencySymbol;
            if(p30) p30.textContent = ((30 / 60) * pricePerMinute).toFixed(2) + currencySymbol;
        });

        // Trigger initial update
        priceInput.dispatchEvent(new Event('input'));
    }
});
