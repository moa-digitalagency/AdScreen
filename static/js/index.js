document.addEventListener('DOMContentLoaded', function() {
    const detectBtn = document.getElementById('detect-resolution-btn');
    if (detectBtn) {
        detectBtn.addEventListener('click', detectScreenResolution);
    }

    const modal = document.getElementById('resolution-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) closeResolutionModal();
        });
    }

    const closeBtn = document.getElementById('close-resolution-modal-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeResolutionModal);
    }
});

function detectScreenResolution() {
    const modal = document.getElementById('resolution-modal');
    const content = document.getElementById('resolution-content');
    const subtitle = document.getElementById('resolution-subtitle');

    if (!modal || !content || !subtitle) return;

    modal.classList.remove('hidden');

    // Get translations from data attributes
    const textResolution = modal.dataset.textResolution || 'Résolution';
    const textCreateFirst = modal.dataset.textCreateFirst || 'Créez votre premier écran avec cette résolution';
    const textLandscape = modal.dataset.textLandscape || 'Paysage';
    const textPortrait = modal.dataset.textPortrait || 'Portrait';

    setTimeout(() => {
        const width = window.screen.width;
        const height = window.screen.height;
        const ratio = (width / height).toFixed(2);

        let orientationText = width > height ? textLandscape : textPortrait;
        let orientation = `${textResolution} ${orientationText}`;

        let aspectRatio = '16:9';
        if (Math.abs(ratio - 1.78) < 0.1) aspectRatio = '16:9';
        else if (Math.abs(ratio - 1.33) < 0.1) aspectRatio = '4:3';
        else if (Math.abs(ratio - 1.6) < 0.1) aspectRatio = '16:10';
        else if (Math.abs(ratio - 0.56) < 0.1) aspectRatio = '9:16';

        subtitle.textContent = orientation;
        content.innerHTML = `
            <div class="bg-gray-50 rounded-xl p-4 mb-4">
                <div class="text-3xl font-bold text-emerald-600 mb-1">${width} x ${height}</div>
                <div class="text-sm text-gray-500">Ratio: ${aspectRatio}</div>
            </div>
            <p class="text-sm text-gray-600">
                ${textCreateFirst}
            </p>
        `;
    }, 1000);
}

function closeResolutionModal() {
    const modal = document.getElementById('resolution-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
