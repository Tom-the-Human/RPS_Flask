document.addEventListener('DOMContentLoaded', () => {
  // Check if the body tag has the 'data-play-sound' attribute
  if (document.body.dataset.playSound) {

    // We still need the sound URLs. A simple way is to embed them in a hidden element.
    const sfxContainer = document.getElementById('sfx-urls');
    if (sfxContainer) {
      const sfxUrls = JSON.parse(sfxContainer.dataset.urls);

      if (sfxUrls && sfxUrls.length > 0) {
        const randomIndex = Math.floor(Math.random() * sfxUrls.length);
        const randomSoundUrl = sfxUrls[randomIndex];

        const sound = new Audio(randomSoundUrl);
        sound.play().catch(error => {
          console.error("Error playing sound:", error);
        });
      }
    }
  }
});