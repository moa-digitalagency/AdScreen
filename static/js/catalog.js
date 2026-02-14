document.addEventListener('DOMContentLoaded', function() {
    const countryFilterForm = document.getElementById('countryFilterForm');
    if (countryFilterForm) {
        const select = countryFilterForm.querySelector('select[name="country"]');
        if (select) {
            select.addEventListener('change', function() {
                countryFilterForm.submit();
            });
        }
    }
});
