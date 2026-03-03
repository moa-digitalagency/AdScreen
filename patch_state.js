const fs = require('fs');

let code = fs.readFileSync('static/js/player.js', 'utf8');

// The player.js has duplicate definitions for savePlayerState, restorePlayerState, and startStateSaver.
// I will clean them up.
const regexDuplicate = /function savePlayerState\(\) \{[\s\S]*?function startStateSaver\(\) \{\n.*?\n.*?\n\}/g;
const matches = [...code.matchAll(regexDuplicate)];

if (matches.length > 1) {
    console.log("Found duplicates");
    // Only keep the first one
    let newCode = code.substring(0, matches[1].index) + code.substring(matches[1].index + matches[1][0].length);
    fs.writeFileSync('static/js/player.js', newCode);
    console.log("Removed duplicate state functions.");
}
