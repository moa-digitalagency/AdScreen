const fs = require('fs');
const content = fs.readFileSync('static/js/player.js', 'utf8');

// I'll add state management functions
const saveStateFunction = `
function savePlayerState() {
    if (player.state !== PlayerState.PLAYING || player.playlist.length === 0 || !player.currentItemStartTime) {
        return;
    }

    const item = player.playlist[player.currentIndex];
    if (!item) return;

    const state = {
        timestamp: Date.now(),
        currentIndex: player.currentIndex,
        itemId: item.id,
        elapsedInSlot: Date.now() - player.currentItemStartTime,
        videoTime: player.videoEl && !player.videoEl.paused ? player.videoEl.currentTime : 0
    };

    try {
        localStorage.setItem('shabakaPlayerState', JSON.stringify(state));
    } catch (e) {
        debug('Error saving state: ' + e.message);
    }
}

function restorePlayerState() {
    try {
        const saved = localStorage.getItem('shabakaPlayerState');
        if (!saved) return null;

        const state = JSON.parse(saved);

        // Only restore if less than 5 minutes old
        if (Date.now() - state.timestamp > 300000) {
            localStorage.removeItem('shabakaPlayerState');
            return null;
        }

        return state;
    } catch (e) {
        return null;
    }
}

// Add state saving interval
function startStateSaver() {
    if (player.stateSaverInterval) clearInterval(player.stateSaverInterval);
    player.stateSaverInterval = setInterval(savePlayerState, 1000);
}
`;

const withStateSave = content.replace('function startPlayer() {', saveStateFunction + '\nfunction startPlayer() {');
fs.writeFileSync('static/js/player.js', withStateSave);
