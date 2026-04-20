document.addEventListener('DOMContentLoaded', () => {
  const bootScreen = document.getElementById('boot-screen');
  const mainGrid = document.getElementById('main-grid');

  console.log('--- EuclidCam Boot Sequence Initiated ---');

  // Simulate a brief "boot" period matching the construction GIF vibe
  setTimeout(() => {
    console.log('--- Geometry Verified. Expanding UI. ---');

    // Step 1: Fade out boot screen
    bootScreen.style.opacity = '0';

    // Step 2: Show and expand main grid
    setTimeout(() => {
      bootScreen.style.display = 'none';
      mainGrid.classList.remove('hidden');
    }, 800); // Match transition duration in CSS
  }, 2800); // 2.8 seconds of GIF playback

  // Interactive handling for grid items
  const gridItems = document.querySelectorAll('.grid-item');
  gridItems.forEach(item => {
    item.addEventListener('click', () => {
      const label = item.querySelector('h2').innerText;
      console.log(`Navigation triggered: /${label.toLowerCase()}`);

      // Add a "flash" effect like before
      item.style.backgroundColor = 'rgba(235, 210, 255, 0.1)';
      setTimeout(() => {
        item.style.backgroundColor = '';
      }, 200);
    });
  });
});
