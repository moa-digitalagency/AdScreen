const fs = require('fs');

let code = fs.readFileSync('static/js/player.js', 'utf8');

// For playVideo, before setting a new src, ensure we unset properly
code = code.replace(
  /player\.imageEl\.style\.display = "none";\s*player\.videoEl\.onended = null;/g,
  `player.imageEl.style.display = "none";
  player.imageEl.removeAttribute("src"); // Clear previous image

  player.videoEl.pause();
  player.videoEl.removeAttribute("src"); // Clear previous video src
  player.videoEl.load(); // Ensure old stream is dropped

  player.videoEl.onended = null;`
);

fs.writeFileSync('static/js/player.js', code);
