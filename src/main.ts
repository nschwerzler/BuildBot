import { Game } from './engine/Game';
import { MobChoice } from './systems/AetherianAbilities';
import { MetalRegistry } from './systems/MetalRegistry';
import './style.css';

// Wait for DOM to be ready
window.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('game-canvas') as HTMLCanvasElement;
  const loadingScreen = document.getElementById('loading-screen') as HTMLDivElement;
  const mobSelectScreen = document.getElementById('mob-select-screen') as HTMLDivElement;
  const hud = document.getElementById('hud') as HTMLDivElement;

  if (!canvas) {
    console.error('Canvas element not found!');
    return;
  }

  // Create game instance
  const game = new Game(canvas);

  // Initialize game (loads world, but doesn't start gameplay loop with mob yet)
  game.init().then(() => {
    console.log('Game initialized!');

    // Show metal count on loading screen
    const metalCountElement = document.getElementById('metal-count');
    if (metalCountElement) {
      metalCountElement.textContent = `${MetalRegistry.getMetalCount()} unique metals/ores generated!`;
    }

    // Start the render/physics loop (world renders, but Aetherian systems not active yet)
    game.start();

    // Transition: hide loading screen, show mob selection
    setTimeout(() => {
      loadingScreen.classList.add('hidden');
      mobSelectScreen.style.display = 'flex';
    }, 500);
  }).catch((error) => {
    console.error('Failed to initialize game:', error);
    const loadingText = document.getElementById('loading-text');
    if (loadingText) {
      loadingText.textContent = 'Error loading game. Check console.';
      loadingText.style.color = '#ff6b6b';
    }
  });

  // Global mob selection function called by the HTML onclick
  (window as any).selectMob = (mobType: string) => {
    console.log(`Selected mob: ${mobType}`);

    // Hide mob selection screen
    mobSelectScreen.classList.add('hidden');
    setTimeout(() => {
      mobSelectScreen.style.display = 'none';
    }, 500);

    // Show HUD
    hud.style.display = 'block';

    // Start Aetherian game systems with chosen mob
    game.startWithMob(mobType as MobChoice);

    // Lock pointer for FPS controls
    canvas.requestPointerLock();

    // Show hint briefly
    const hint = document.getElementById('unlock-hint');
    if (hint) {
      hint.style.display = 'block';
      setTimeout(() => {
        hint.style.transition = 'opacity 0.5s';
        hint.style.opacity = '0';
        setTimeout(() => (hint.style.display = 'none'), 500);
      }, 3000);
    }
  };

  // Ability choice callback
  (window as any).chooseAbility = (abilityId: string) => {
    game.handleAbilityChoice(abilityId);
  };

  // Chest callbacks
  (window as any).takePotion = () => {
    game.takePotionFromChest();
  };
  (window as any).closeChest = () => {
    game.closeChest();
  };

  // Handle window resize
  window.addEventListener('resize', () => {
    game.onResize();
  });

  // Expose game to window for debugging
  (window as any).game = game;
});
