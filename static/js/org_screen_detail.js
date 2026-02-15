document.addEventListener('DOMContentLoaded', function() {
    // Delete confirmation
    const deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Preview click
    const previewDiv = document.getElementById('preview-click-zone');
    if (previewDiv) {
        previewDiv.addEventListener('click', function() {
            window.open(this.dataset.url, '_blank');
        });
    }
});
