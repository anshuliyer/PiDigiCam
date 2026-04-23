document.addEventListener('DOMContentLoaded', () => {
  const bootScreen = document.getElementById('boot-screen');
  const conceptScreen = document.getElementById('concept-screen');
  const mainGrid = document.getElementById('main-grid');

  console.log('--- EuclidCam Sequence Initiated ---');

  // Sequence 1: Boot Screen (Splash)
  setTimeout(() => {
    console.log('--- Boot Complete. Transitioning to Concept. ---');
    bootScreen.style.opacity = '0';

    setTimeout(() => {
      bootScreen.style.display = 'none';
      conceptScreen.classList.remove('hidden');
      conceptScreen.style.display = 'grid';
      conceptScreen.style.opacity = '1';

      // Sequence 2: Concept Screen (Chalk Sunflower Show)
      setTimeout(() => {
        generateSunflowerSeeds();

        console.log('--- Concept Explained. Loading Dashboard. ---');
        setTimeout(() => {
          conceptScreen.style.opacity = '0';
          setTimeout(() => {
            conceptScreen.style.display = 'none';
            mainGrid.classList.remove('hidden');
          }, 1000);
        }, 8500); // Increased time for chalk animation
      }, 800);
    }, 800);
  }, 2800);

  function generateSunflowerSeeds() {
    const sunflowerGroup = document.querySelector('.sunflower');
    if (!sunflowerGroup) {
      console.warn('Sunflower group not found. Skipping seed generation.');
      return;
    }
    const centerX = 250;
    const centerY = 175;
    const c = 7; // Scaling factor

    for (let i = 0; i < 80; i++) {
      const theta = i * 137.5 * (Math.PI / 180);
      const r = c * Math.sqrt(i);
      const x = centerX + r * Math.cos(theta);
      const y = centerY + r * Math.sin(theta);

      const seed = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      seed.setAttribute("cx", x);
      seed.setAttribute("cy", y);
      seed.setAttribute("r", "1.5");
      seed.setAttribute("fill", "rgba(235, 210, 255, 0.7)");
      seed.style.opacity = "0";
      seed.style.animation = `fadeIn 0.2s ease-out ${i * 0.04}s forwards`;

      sunflowerGroup.appendChild(seed);
    }
  }

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
