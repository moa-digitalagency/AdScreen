const fs = require('fs');
let content = fs.readFileSync('static/js/player.js', 'utf8');
content = content.replace("async \nfunction savePlayerState", "function savePlayerState");
content = content.replace("function startPlayer() {\n    document.getElementById('startScreen')", "async function startPlayer() {\n    document.getElementById('startScreen')");
fs.writeFileSync('static/js/player.js', content);
