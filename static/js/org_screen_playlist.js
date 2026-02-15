document.addEventListener('DOMContentLoaded', function() {
    // Delegate click for preview items
    document.addEventListener('click', function(e) {
        const previewTrigger = e.target.closest('[data-preview-path]');
        if (previewTrigger) {
            const path = previewTrigger.dataset.previewPath;
            const type = previewTrigger.dataset.previewType;
            openPreviewModal(path, type);
        }
    });

    const closeBtn = document.getElementById('close-preview-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closePreviewModal);
    }

    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closePreviewModal();
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closePreviewModal();
    });
});

function openPreviewModal(filePath, contentType) {
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');

    if (!modal || !container) return;

    if (contentType === 'image') {
        container.innerHTML = `<img src="/${filePath}" alt="Preview" class="max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl">`;
    } else {
        container.innerHTML = `<video src="/${filePath}" controls autoplay class="max-w-full max-h-[80vh] object-contain rounded-lg shadow-2xl"></video>`;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');

    if (!modal || !container) return;

    const video = container.querySelector('video');
    if (video) video.pause();

    modal.classList.add('hidden');
    modal.classList.remove('flex');
    container.innerHTML = '';
}
