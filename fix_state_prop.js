const fs = require('fs');
let content = fs.readFileSync('static/js/player.js', 'utf8');

if (!content.includes('recoveredState')) {
    content = content.replace('maxNetworkRetries: 10,', 'maxNetworkRetries: 10,\n    recoveredState: null,\n    stateSaverInterval: null,');
    fs.writeFileSync('static/js/player.js', content);
}
