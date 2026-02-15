document.addEventListener('DOMContentLoaded', function() {
    const quickActionSelect = document.getElementById('quick-action-screen');
    if (quickActionSelect) {
        quickActionSelect.addEventListener('change', function(e) {
            updateQuickActions(e.target.value);
        });
    }
});

function updateQuickActions(screenId) {
    const select = document.getElementById('quick-action-screen');
    if (!select) return;

    const selectedOption = select.options[select.selectedIndex];
    const screenName = selectedOption.dataset.name;
    const screenStatus = selectedOption.dataset.status;

    const playlistLink = document.getElementById('qa-playlist-link');
    const iptvLink = document.getElementById('qa-iptv-link');
    const playlistForm = document.getElementById('qa-playlist-form');
    const iptvForm = document.getElementById('qa-iptv-form');
    const currentScreenName = document.getElementById('qa-current-screen-name');
    const currentScreenInfo = document.getElementById('qa-current-screen-info');

    if (playlistLink) playlistLink.href = `/org/screen/${screenId}/playlist`;
    if (iptvLink) iptvLink.href = `/org/screen/${screenId}/iptv`;
    if (playlistForm) playlistForm.action = `/screen/${screenId}/mode`;
    if (iptvForm) iptvForm.action = `/screen/${screenId}/mode`;

    if (currentScreenName) currentScreenName.textContent = screenName;

    if (currentScreenInfo) {
        const statusDot = currentScreenInfo.querySelector('.status-dot');
        if (statusDot) {
            statusDot.className = `status-dot status-${screenStatus} w-2 h-2 ml-2 inline-block`;
        }
    }
}
