const fs = require('fs');
let content = fs.readFileSync('static/js/player.js', 'utf8');

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

fs.writeFileSync('static/js/player.js', content);
