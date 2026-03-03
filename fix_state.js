const fs = require('fs');
let content = fs.readFileSync('static/js/player.js', 'utf8');

if (!content.includes('recoveredState')) {
    content = content.replace('maxNetworkRetries: 10,', 'maxNetworkRetries: 10,\n    recoveredState: null,\n    stateSaverInterval: null,');
}

content = content.replace(/function playCurrentItem\(\) \{[\s\S]*?(?=function playImage)/, `function playCurrentItem() {
    if (player.state === PlayerState.PAUSED) {
        debug('Paused, not playing');
        return;
    }

    if (player.playlist.length === 0) {
        debug('No items to play');
        player.state = PlayerState.IDLE;
        updateInfoDisplay(null);
        return;
    }

    const item = player.playlist[player.currentIndex];
    if (!item) {
        debug('Invalid item at index ' + player.currentIndex);
        player.currentIndex = 0;
        if (player.playlist.length > 0) {
            setTimeout(() => playCurrentItem(), 100);
        }
        return;
    }

    player.state = PlayerState.PLAYING;

    let isResuming = false;
    if (player.recoveredState && player.recoveredState.itemId === item.id) {
        player.currentItemStartTime = Date.now() - (player.recoveredState.elapsedInSlot || 0);
        isResuming = true;
        debug('Resuming item from state: ' + item.id);
    } else {
        player.currentItemStartTime = Date.now();
    }

    const duration = Math.max(3, parseInt(item.duration) || 10);
    debug(\`Playing: \${item.category}/\${item.name || item.id} for \${duration}s\`);

    updateInfoDisplay(item);

    if (item.type === 'image') {
        playImage(item, duration, isResuming);
    } else if (item.type === 'video') {
        playVideo(item, duration, isResuming);
    } else {
        debug('Unknown content type: ' + item.type);
        scheduleNext(1000);
    }
}
`);

content = content.replace(/function playImage\(item, duration\) \{[\s\S]*?(?=function playVideo)/, `function playImage(item, duration, isResuming = false) {
    player.videoEl.pause();
    player.videoEl.removeAttribute('src');
    player.videoEl.style.display = 'none';

    player.imageEl.style.display = 'block';
    player.imageEl.src = item.url;

    if (isResuming && player.recoveredState) {
        player.recoveredState = null; // Clear state after use
    }

    player.imageEl.onload = () => {
        debug('Image loaded: ' + item.url);
        if (!isResuming) {
            logPlay(item);
        }
    };

    player.imageEl.onerror = () => {
        debug('Image error: ' + item.url);
        scheduleNext(500);
    };

    const slotDuration = duration * 1000;
    const remainingToSchedule = Math.max(1000, slotDuration - (Date.now() - player.currentItemStartTime));
    scheduleNext(remainingToSchedule);
}
`);

content = content.replace(/function playVideo\(item, duration\) \{[\s\S]*?(?=function updateInfoDisplay)/, `function playVideo(item, duration, isResuming = false) {
    player.imageEl.style.display = 'none';

    player.videoEl.onended = null;
    player.videoEl.onerror = null;
    player.videoEl.onloadeddata = null;
    player.videoEl.ontimeupdate = null;

    player.videoEl.style.display = 'block';
    player.videoEl.src = item.url;
    player.videoEl.currentTime = 0;
    player.videoEl.loop = false;
    player.videoEl.muted = player.isMuted;

    let hasLogged = false;
    let videoEnded = false;
    const slotDuration = duration * 1000;
    const startTime = player.currentItemStartTime;

    let resumeTime = 0;
    if (isResuming && player.recoveredState) {
        resumeTime = player.recoveredState.videoTime || 0;
        player.recoveredState = null; // Clear state after use
    }

    const handleVideoEnd = () => {
        if (videoEnded) return;
        videoEnded = true;

        const videoDuration = player.videoEl.duration || 0;
        const elapsedTime = Date.now() - startTime;
        const remainingSlotTime = slotDuration - elapsedTime;

        if (remainingSlotTime > 100) {
            debug(\`Video ended (\${videoDuration.toFixed(1)}s), keeping last frame for \${(remainingSlotTime/1000).toFixed(1)}s to complete \${duration}s slot\`);
            player.videoEl.pause();
        } else {
            debug('Video ended, slot duration reached');
        }
    };

    player.videoEl.onloadeddata = () => {
        const videoDuration = player.videoEl.duration || 0;
        debug(\`Video loaded, video duration: \${videoDuration.toFixed(1)}s, slot duration: \${duration}s\`);

        if (videoDuration < duration) {
            debug(\`Video shorter than slot (\${videoDuration.toFixed(1)}s < \${duration}s) - will hold last frame\`);
        }

        if (resumeTime > 0 && resumeTime < videoDuration) {
            player.videoEl.currentTime = resumeTime;
            debug(\`Resuming video at \${resumeTime}s\`);
        }

        player.videoEl.play().then(() => {
            if (!hasLogged && !isResuming) {
                hasLogged = true;
                logPlay(item);
            }
        }).catch(e => {
            debug('Video play error: ' + e.message);
            scheduleNext(500);
        });
    };

    player.videoEl.onended = handleVideoEnd;

    player.videoEl.onerror = (e) => {
        debug('Video error: ' + (e.message || 'unknown'));
        scheduleNext(500);
    };

    player.videoEl.ontimeupdate = () => {
        if (!videoEnded && player.videoEl.currentTime >= player.videoEl.duration - 0.1) {
            handleVideoEnd();
        }
    };

    const remainingToSchedule = Math.max(1000, slotDuration - (Date.now() - startTime));
    scheduleNext(remainingToSchedule);
}
`);

content = content.replace(/if \(player\.state === PlayerState\.IDLE && player\.playlist\.length > 0\) \{[\s\S]*?playCurrentItem\(\);[\s\S]*?\}/, `if (player.state === PlayerState.IDLE && player.playlist.length > 0) {
            debug('Starting playback from idle');

            // Try to restore state
            const state = restorePlayerState();
            if (state && state.currentIndex >= 0 && state.currentIndex < player.playlist.length) {
                // Ensure the item at this index matches the saved item ID
                if (player.playlist[state.currentIndex].id === state.itemId) {
                    player.currentIndex = state.currentIndex;
                    player.recoveredState = state;
                    debug('Recovered player state for item: ' + state.itemId);
                } else {
                    player.currentIndex = 0;
                }
            } else {
                player.currentIndex = 0;
            }

            playCurrentItem();
        }`);

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

content = content.replace('async function startPlayer() {', saveStateFunction + '\nasync function startPlayer() {');
content = content.replace('scheduleAutoReload();', 'scheduleAutoReload();\n    startStateSaver();');

fs.writeFileSync('static/js/player.js', content);
