import * as THREE from 'three';
import { Renderer } from './Renderer';
import { Player } from '../entities/Player';
import { World } from '../world/World';
import { InputManager } from '../systems/InputManager';
import { PhysicsSystem } from '../systems/PhysicsSystem';
import { Inventory } from '../systems/Inventory';
import { MetalRegistry } from '../systems/MetalRegistry';
import { ParticleSystem } from '../systems/ParticleSystem';
import { AchievementSystem } from '../systems/AchievementSystem';
import { SoundManager } from '../systems/SoundManager';
import { NotificationSystem } from '../systems/NotificationSystem';
import { AetherianAbilities, MobChoice } from '../systems/AetherianAbilities';
import { HerobrineSystem } from '../systems/HerobrineSystem';
import { ThirstSystem } from '../systems/ThirstSystem';
import { DayNightCycle } from '../systems/DayNightCycle';

export class Game {
  private canvas: HTMLCanvasElement;
  private renderer!: Renderer;
  private player!: Player;
  private particleSystem!: ParticleSystem;
  private achievementSystem!: AchievementSystem;
  private soundManager!: SoundManager;
  private notificationSystem!: NotificationSystem;
  private inputManager!: InputManager;
  private physicsSystem!: PhysicsSystem;
  private inventory!: Inventory;
  private world!: World;

  // Aetherian book systems
  private abilities!: AetherianAbilities;
  private herobrineSystem!: HerobrineSystem;
  private thirstSystem!: ThirstSystem;
  private dayNightCycle!: DayNightCycle;

  private clock: THREE.Clock;
  private isRunning: boolean = false;
  private lastTime: number = 0;
  private frameCount: number = 0;
  private fpsUpdateTime: number = 0;
  private blocksMined: number = 0;
  private blocksPlaced: number = 0;

  // Day tracking for Herobrine
  private currentGameDay: number = 1;
  private dayTimer: number = 0;
  private readonly DAY_DURATION = 1200; // 20 minutes real time = 1 in-game day

  // Mob selection
  private selectedMob: MobChoice = 'cat';
  private gameStarted: boolean = false;
  private hasPotion: boolean = false;

  // Player HP
  private playerHP: number = 20;
  private readonly MAX_HP: number = 20;
  private lavaDamageTimer: number = 0;
  private isDead: boolean = false;
  private damageFlashTimer: number = 0;

  // Herobrine UI
  private herobrineOverlay: HTMLDivElement | null = null;
  private heroBrineMessageTimeout: number | null = null;

  // === PROGRESSION STATE ===
  private hasDrunkWater: boolean = false;
  private hasSleptInBed: boolean = false;
  private netherPortalSpawned: boolean = false;
  private abilityChoiceOpen: boolean = false;

  // House location (near spawn) 
  private readonly HOUSE_X = 12;
  private readonly HOUSE_Z = 12;
  private readonly HOUSE_Y = 65; // On top of ground

  // Nether portal location
  private readonly PORTAL_X = 25;
  private readonly PORTAL_Z = 25;
  private readonly PORTAL_Y = 65;

  // Post-tutorial state
  private tutorialComplete: boolean = false;
  private inNether: boolean = false;
  private netherReturnPos: THREE.Vector3 | null = null;

  // Village location (along path from house)
  private readonly VILLAGE_X = 60;
  private readonly VILLAGE_Z = 60;
  private readonly VILLAGE_Y = 65;
  private villageBuilt: boolean = false;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.clock = new THREE.Clock();
  }

  async init(): Promise<void> {
    console.log('Initializing game...');

    // Initialize renderer
    this.renderer = new Renderer(this.canvas);

    // Initialize systems
    this.inputManager = new InputManager(this.canvas);
    this.physicsSystem = new PhysicsSystem();
    this.inventory = new Inventory();
    this.inventory.init();
    this.particleSystem = new ParticleSystem(this.renderer.scene);
    this.achievementSystem = new AchievementSystem();
    this.soundManager = new SoundManager();
    this.notificationSystem = new NotificationSystem();

    // Setup achievement listeners
    this.achievementSystem.onAchievementUnlocked((achievement) => {
      this.notificationSystem.achievementUnlocked(achievement.name, achievement.icon);
      console.log(`Achievement unlocked: ${achievement.name}!`);
    });

    // Initialize world
    this.world = new World();
    await this.world.init();
    this.renderer.scene.add(this.world.getWorldGroup());

    // Initialize player
    this.player = new Player(this.renderer.camera, this.inputManager);
    this.player.position.set(0, 64.5, 0);
    this.player.velocity.set(0, 0, 0);
    this.player.onGround = true;

    // Generate spawn chunks
    const playerChunkX = Math.floor(this.player.position.x / 16);
    const playerChunkZ = Math.floor(this.player.position.z / 16);

    console.log('Quick-loading spawn area...');
    for (let x = playerChunkX; x <= playerChunkX + 1; x++) {
      for (let z = playerChunkZ; z <= playerChunkZ + 1; z++) {
        this.world.generateChunk(x, z);
      }
    }
    console.log('Spawn area ready!');

    await new Promise(resolve => setTimeout(resolve, 50));

    this.player.position.set(0.5, 65, 0.5);
    this.player.velocity.set(0, 0, 0);
    this.player.onGround = true;

    // Initialize Day/Night Cycle
    this.dayNightCycle = new DayNightCycle(
      this.renderer.scene,
      this.renderer.sunLight,
      this.renderer.ambientLight
    );

    // Build the abandoned house near spawn
    this.buildAbandonedHouse();

    // Create Herobrine overlay for events
    this.createHerobrineOverlay();

    console.log('Game initialization complete!');
  }

  /**
   * Start the game with chosen mob type.
   * Called after mob selection screen.
   */
  startWithMob(mobType: MobChoice): void {
    this.selectedMob = mobType;
    this.gameStarted = true;

    // Set player size for chosen mob
    this.player.setMobSize(mobType);

    // Initialize Aetherian systems with chosen mob
    this.abilities = new AetherianAbilities(mobType);
    this.herobrineSystem = new HerobrineSystem(this.renderer.scene);
    this.thirstSystem = new ThirstSystem(5, 20); // Start thirsty!

    // Setup Herobrine event callbacks
    this.herobrineSystem.onEvent((type, data) => {
      this.handleHerobrineEvent(type, data);
    });

    // Setup thirst dehydration
    this.thirstSystem.onDehydration(() => {
      this.showNotification('You are dehydrating! Find water!', '#ff4444');
    });

    // Update UI
    this.updateAbilityBar();
    this.updateStatsDisplay();

    // Notification - guide player to house
    const mobNames: Record<MobChoice, string> = {
      cat: 'Nether Kitten (like Eeebs!)',
      wolf: 'Loyal Wolf',
      bunny: 'Swift Bunny',
    };
    this.showNotification(`You are a ${mobNames[mobType]}! Survive and explore...`, '#00ff88');
    
    setTimeout(() => {
      this.showNotification('You see an abandoned house nearby... Go investigate!', '#ffdd44');
    }, 3000);

    const bonuses = this.abilities.getMobBonuses();
    if (bonuses.creeperRepel) {
      this.showNotification('Creepers flee from you!', '#88ff88');
    }
    if (bonuses.nightVision) {
      this.showNotification('You have night vision!', '#aaaaff');
    }

    console.log(`Game started as ${mobType} (no abilities yet - find the house!)`);
  }

  start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.lastTime = performance.now();
    this.loop();
  }

  stop(): void {
    this.isRunning = false;
  }

  private loop = (): void => {
    if (!this.isRunning) return;
    requestAnimationFrame(this.loop);

    const currentTime = performance.now();
    const deltaTime = (currentTime - this.lastTime) / 1000;
    this.lastTime = currentTime;

    this.update(deltaTime);
    this.renderer.render();
    this.updateFPS(currentTime);
  };

  private update(deltaTime: number): void {
    const dt = Math.min(deltaTime, 0.016);

    // Update particle system
    this.particleSystem.update(dt);

    // Update Day/Night Cycle
    if (this.dayNightCycle) {
      this.dayNightCycle.update(dt);
    }

    // Skip movement if dead
    if (this.isDead) {
      this.player.syncCamera();
      this.world.updateChunks(this.player.position);
      return;
    }

    // Update player movement with mob speed bonus
    if (this.gameStarted && this.abilities) {
      const speedMult = this.abilities.getSpeedMultiplier();
      this.player.setSpeedMultiplier(speedMult);
    }

    // Save position before movement for collision
    const oldX = this.player.position.x;
    const oldY = this.player.position.y;
    const oldZ = this.player.position.z;

    this.player.update(dt);

    // After player.update(), position.x and position.z have moved
    const newX = this.player.position.x;
    const newZ = this.player.position.z;

    // --- AXIS-SEPARATED HORIZONTAL COLLISION ---
    // Test X axis only (revert Z)
    this.player.position.x = newX;
    this.player.position.z = oldZ;
    if (this.checkSolidCollision(this.player.position)) {
      this.player.position.x = oldX; // X blocked
    }
    // Test Z axis (keep resolved X)
    this.player.position.z = newZ;
    if (this.checkSolidCollision(this.player.position)) {
      this.player.position.z = oldZ; // Z blocked
    }

    // --- VERTICAL PHYSICS + COLLISION ---
    if (!this.player.onGround) {
      this.physicsSystem.applyGravity(this.player, dt);
      this.player.position.y += this.player.velocity.y * dt;
    }

    // Ground / ceiling collision
    const feetBlockY = Math.floor(this.player.position.y - 0.01);
    const blockBelow = this.world.getBlock(
      Math.floor(this.player.position.x),
      feetBlockY,
      Math.floor(this.player.position.z)
    );

    if (blockBelow !== 0 && this.player.velocity.y <= 0) {
      this.player.position.y = feetBlockY + 1;
      this.player.velocity.y = 0;
      this.player.onGround = true;
    }

    // Head collision (block above player)
    if (this.player.velocity.y > 0) {
      const headY = Math.floor(this.player.position.y + this.player.getHeight());
      const blockAbove = this.world.getBlock(
        Math.floor(this.player.position.x),
        headY,
        Math.floor(this.player.position.z)
      );
      if (blockAbove !== 0) {
        this.player.velocity.y = 0;
      }
    }

    // Void safety
    if (this.player.position.y < 1) {
      this.player.position.y = 65;
      this.player.velocity.y = 0;
      this.player.onGround = true;
    }

    // --- COOLDOWNS ---
    if (this.attackCooldown > 0) this.attackCooldown -= dt;
    if (this.talkCooldown > 0) this.talkCooldown -= dt;

    // Update attack swing animation
    this.updateAttackSwing(dt);

    // --- LAVA DAMAGE ---
    const feetBlock = this.world.getBlock(
      Math.floor(this.player.position.x),
      Math.floor(this.player.position.y - 0.01),
      Math.floor(this.player.position.z)
    );
    const standingBlock = this.world.getBlock(
      Math.floor(this.player.position.x),
      Math.floor(this.player.position.y),
      Math.floor(this.player.position.z)
    );
    if ((feetBlock === 12 || standingBlock === 12) && !this.isDead) {
      this.lavaDamageTimer += dt;
      if (this.lavaDamageTimer >= 0.5) { // 2 damage per second
        this.lavaDamageTimer = 0;
        this.playerHP -= 2;
        this.damageFlashTimer = 0.2;
        this.showNotification(`Burning! HP: ${Math.max(0, this.playerHP)}/${this.MAX_HP}`, '#ff2200');
        if (this.playerHP <= 0) {
          this.playerDeath();
        }
      }
    } else {
      this.lavaDamageTimer = 0;
    }

    // Damage flash effect
    if (this.damageFlashTimer > 0) {
      this.damageFlashTimer -= dt;
      this.applyDamageFlash(this.damageFlashTimer / 0.2);
    }

    // Sync camera after all collision
    this.player.syncCamera();

    // Update world chunks
    this.world.updateChunks(this.player.position);

    // Update block interaction
    this.updatePlayerInteraction();
    this.updateHotbarSelection();

    // === AETHERIAN SYSTEMS ===
    if (this.gameStarted && this.abilities) {
      // Update abilities (cooldowns, mana regen)
      this.abilities.update(dt);

      // Update thirst
      const isSprinting = this.inputManager.isKeyHeld('ShiftLeft');
      this.thirstSystem.update(dt, isSprinting, false);

      // Update Herobrine
      this.dayTimer += dt;
      if (this.dayTimer >= this.DAY_DURATION) {
        this.dayTimer -= this.DAY_DURATION;
        this.currentGameDay++;
        this.showNotification(`Day ${this.currentGameDay}`, '#ffdd44');
      }
      this.herobrineSystem.update(dt, this.player.position, this.currentGameDay);

      // XP from survival (small passive gain)
      if (Math.random() < 0.001) {
        const result = this.abilities.addXP(1);
        if (result.choiceAvailable) {
          this.showAbilityChoice();
        }
      }

      // Ability hotkeys (only if abilities unlocked)
      if (!this.abilities.isAbilitySystemLocked()) {
        this.handleAbilityInput();
      }

      // Check progression events
      this.checkProgressionEvents();

      // Check for potion pickup
      this.checkPotionPickup();

      // Update UI elements
      this.updateGameUI();
    }

    this.updateDebugInfo();
  }

  private handleAbilityInput(): void {
    if (!this.abilities) return;

    const abilitySlots = this.abilities
      .getUnlockedAbilities()
      .filter((a) => a.school !== 'passive')
      .slice(0, 4);

    // F1-F4 for abilities
    for (let i = 0; i < 4; i++) {
      if (this.inputManager.isKeyPressed(`F${i + 1}`)) {
        if (i < abilitySlots.length) {
          const ability = abilitySlots[i];
          const effect = this.abilities.useAbility(ability.id);
          if (effect) {
            this.executeAbilityEffect(ability.id, effect);
            this.showNotification(`${ability.name}!`, '#aa88ff');
          } else if (ability.currentCooldown > 0) {
            this.showNotification(
              `${ability.name} on cooldown (${ability.currentCooldown.toFixed(1)}s)`,
              '#888888'
            );
          } else {
            this.showNotification(`Not enough mana for ${ability.name}`, '#ff8888');
          }
        }
      }
    }

    // R key - drink water (backup key, left-click water is primary)
    if (this.inputManager.isKeyPressed('KeyR')) {
      const nearWater = this.checkNearWater();
      if (nearWater) {
        this.thirstSystem.drink(5);
        if (!this.hasDrunkWater) {
          this.hasDrunkWater = true;
          this.showNotification('Refreshing! Now right-click the bed to rest...', '#4488ff');
        } else {
          this.showNotification('Drank water!', '#4488ff');
        }
      }
    }
  }

  private executeAbilityEffect(abilityId: string, effect: any): void {
    switch (effect.type) {
      case 'movement': {
        // Dash/Leap - boost player forward
        const forward = new THREE.Vector3(0, 0, -1);
        forward.applyQuaternion(this.renderer.camera.quaternion);
        forward.y = abilityId === 'leap' ? 0.5 : 0;
        forward.normalize().multiplyScalar(effect.value * 2);
        this.player.position.add(forward);
        if (abilityId === 'leap') {
          this.player.velocity.y = 8;
          this.player.onGround = false;
        }
        break;
      }

      case 'projectile': {
        // Ghast Fireball - create particle effect forward
        const fireDir = new THREE.Vector3(0, 0, -1);
        fireDir.applyQuaternion(this.renderer.camera.quaternion);
        const firePos = this.player.position.clone().add(fireDir.multiplyScalar(3));
        this.particleSystem.createBlockBreakParticles(firePos, new THREE.Color(0xff4400));
        break;
      }

      case 'stealth':
        this.abilities.activateBuff(abilityId, effect);
        break;

      case 'buff':
        this.abilities.activateBuff(abilityId, effect);
        break;

      case 'damage':
        if (effect.radius) {
          this.particleSystem.createBlockBreakParticles(
            this.player.position.clone(),
            new THREE.Color(0xff6600)
          );
        }
        break;

      case 'heal':
        this.abilities.activateBuff(abilityId, effect);
        break;
    }
  }

  private checkNearWater(): boolean {
    const px = Math.floor(this.player.position.x);
    const py = Math.floor(this.player.position.y);
    const pz = Math.floor(this.player.position.z);

    for (let dx = -2; dx <= 2; dx++) {
      for (let dy = -2; dy <= 2; dy++) {
        for (let dz = -2; dz <= 2; dz++) {
          if (this.world.getBlock(px + dx, py + dy, pz + dz) === 7) {
            return true;
          }
        }
      }
    }
    return false;
  }

  private checkPotionPickup(): void {
    // Potion is now inside the chest - no proximity pickup
    // Handled by right-clicking the chest block (type 9)
  }

  // === PROGRESSION SYSTEM ===

  private buildAbandonedHouse(): void {
    const hx = this.HOUSE_X;
    const hy = this.HOUSE_Y;
    const hz = this.HOUSE_Z;
    
    // Floor (5x5 wood)
    for (let x = 0; x < 6; x++) {
      for (let z = 0; z < 6; z++) {
        this.world.setBlock(hx + x, hy - 1, hz + z, 4); // Wood floor
      }
    }
    
    // Walls (4 high, wood, with gaps for door and windows)
    for (let y = 0; y < 4; y++) {
      for (let x = 0; x < 6; x++) {
        // Front wall (z = 0) with door gap
        if (!(x === 2 && y < 2) && !(x === 3 && y < 2)) {
          this.world.setBlock(hx + x, hy + y, hz, 4);
        }
        // Back wall (z = 5)
        if (!(x === 3 && y === 1)) { // small window
          this.world.setBlock(hx + x, hy + y, hz + 5, 4);
        }
      }
      for (let z = 0; z < 6; z++) {
        // Left wall (x = 0) with window
        if (!(z === 2 && y === 1) && !(z === 3 && y === 1)) {
          this.world.setBlock(hx, hy + y, hz + z, 4);
        }
        // Right wall (x = 5) with window
        if (!(z === 2 && y === 1) && !(z === 3 && y === 1)) {
          this.world.setBlock(hx + 5, hy + y, hz + z, 4);
        }
      }
    }
    
    // Roof (leaves for thatched look)
    for (let x = -1; x < 7; x++) {
      for (let z = -1; z < 7; z++) {
        this.world.setBlock(hx + x, hy + 4, hz + z, 5); // Leaves roof
      }
    }
    
    // BED inside (single red wool block, renders as 2-long bed visually)
    this.world.setBlock(hx + 4, hy, hz + 4, 8); // Red wool bed
    
    // CHEST near the bed (golden chest block)
    this.world.setBlock(hx + 3, hy, hz + 4, 9); // Chest
    
    // Water pool outside the door
    for (let x = 1; x < 4; x++) {
      for (let z = -3; z < -1; z++) {
        this.world.setBlock(hx + x, hy - 1, hz + z, 7); // Water
      }
    }
    
    console.log(`Abandoned house built at (${hx}, ${hy}, ${hz})`);
  }

  private checkProgressionEvents(): void {
    if (!this.abilities || this.abilityChoiceOpen) return;
    
    const px = Math.floor(this.player.position.x);
    const pz = Math.floor(this.player.position.z);
    
    // Show hint when near bed and have drunk water but not slept
    if (this.hasDrunkWater && !this.hasSleptInBed) {
      const bedDist = Math.sqrt(
        Math.pow(px - (this.HOUSE_X + 4), 2) + 
        Math.pow(pz - (this.HOUSE_Z + 3), 2)
      );
      if (bedDist < 4) {
        const hintEl = document.getElementById('unlock-hint');
        if (hintEl) {
          hintEl.style.display = 'block';
          hintEl.style.opacity = '1';
          hintEl.textContent = 'Right-click the bed to sleep';
        }
      }
    }
    
    // Check if near nether portal - TELEPORT to nether
    if (this.netherPortalSpawned && !this.inNether) {
      const portalDist = Math.sqrt(
        Math.pow(px - (this.PORTAL_X + 1), 2) + 
        Math.pow(pz - this.PORTAL_Z, 2)
      );
      if (portalDist < 2) {
        this.enterNether();
      }
    }
    // Check if in nether and near return portal
    if (this.inNether) {
      const returnDist = Math.sqrt(
        Math.pow(px - 9, 2) + Math.pow(pz - 8, 2)
      );
      if (returnDist < 2) {
        this.exitNether();
      }
    }
    
    // Check if ability choice is pending
    if (this.abilities.hasPendingChoice() && !this.abilityChoiceOpen) {
      this.showAbilityChoice();
    }
  }
  
  private spawnNetherPortal(): void {
    if (this.netherPortalSpawned) return;
    this.netherPortalSpawned = true;
    
    const px = this.PORTAL_X;
    const py = this.PORTAL_Y;
    const pz = this.PORTAL_Z;
    
    // Build obsidian frame (using stone blocks with dark appearance)
    // Portal frame: 4 wide, 5 tall
    for (let y = 0; y < 5; y++) {
      this.world.setBlock(px, py + y, pz, 3);     // Left pillar
      this.world.setBlock(px + 3, py + y, pz, 3); // Right pillar
    }
    for (let x = 0; x < 4; x++) {
      this.world.setBlock(px + x, py, pz, 3);     // Bottom
      this.world.setBlock(px + x, py + 4, pz, 3); // Top
    }
    // Portal interior (water blocks glow purple-ish)
    for (let x = 1; x < 3; x++) {
      for (let y = 1; y < 4; y++) {
        this.world.setBlock(px + x, py + y, pz, 7); // Water as portal fill
      }
    }
    
    this.showNotification('A Nether Portal has appeared in the distance!', '#aa00ff');
    this.showNotification('The Eyeless One stirs...', '#ff0000');
    
    // Trigger Herobrine activity
    this.currentGameDay = Math.max(this.currentGameDay, 3);
    
    console.log(`Nether Portal spawned at (${px}, ${py}, ${pz})`);
  }

  /** Called after sleeping - expand the world, build path and village */
  private completeTutorial(): void {
    if (this.tutorialComplete) return;
    this.tutorialComplete = true;

    // Expand render distance so the world opens up
    this.world.setRenderDistance(4);
    this.showNotification('The world feels bigger now...', '#88ffaa');

    // Build a dirt/stone path from house to village
    this.buildPathToVillage();

    // Build the village at the end of the path
    this.buildVillage();

    setTimeout(() => {
      this.showNotification('You notice a path leading to a village...', '#ffdd44');
    }, 2000);
  }

  /** Build a winding path from house area to village */
  private buildPathToVillage(): void {
    const startX = this.HOUSE_X + 3;
    const startZ = this.HOUSE_Z + 7; // Front of house
    const endX = this.VILLAGE_X + 2; // Into village center
    const endZ = this.VILLAGE_Z + 2;

    // Create path points with slight curves - 80 steps for smooth coverage
    const steps = 80;
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      // Slight sine wave for a natural path
      const px = Math.round(startX + (endX - startX) * t + Math.sin(t * Math.PI * 2) * 3);
      const pz = Math.round(startZ + (endZ - startZ) * t);

      // Use actual terrain height at this position
      const y = this.world.getTerrainHeight(px, pz);

      // 3-wide path
      for (let w = -1; w <= 1; w++) {
        this.world.setBlock(px + w, y, pz, 3); // Stone path
        // Clear above so you can walk
        this.world.setBlock(px + w, y + 1, pz, 0);
        this.world.setBlock(px + w, y + 2, pz, 0);
        this.world.setBlock(px + w, y + 3, pz, 0);
      }
    }
    console.log('Path to village built');
  }

  /** Build a small village with buildings */
  private buildVillage(): void {
    if (this.villageBuilt) return;
    this.villageBuilt = true;

    const vx = this.VILLAGE_X;
    const vy = this.world.getTerrainHeight(this.VILLAGE_X, this.VILLAGE_Z);
    const vz = this.VILLAGE_Z;

    // === Clear village area ===
    for (let x = -8; x <= 12; x++) {
      for (let z = -8; z <= 12; z++) {
        for (let y = 1; y <= 6; y++) {
          this.world.setBlock(vx + x, vy + y, vz + z, 0);
        }
        // Flatten ground
        this.world.setBlock(vx + x, vy - 1, vz + z, 2); // Dirt
        this.world.setBlock(vx + x, vy, vz + z, 1); // Grass
      }
    }

    // === Village square (stone floor) ===
    for (let x = -1; x <= 5; x++) {
      for (let z = -1; z <= 5; z++) {
        this.world.setBlock(vx + x, vy, vz + z, 3); // Stone floor
      }
    }

    // === House 1: Blacksmith (left) - stone with planks ===
    this.buildVillageHouse(vx - 6, vy + 1, vz, 5, 4, 5, 3, 13); // Stone walls, planks roof
    // Anvil (stone block inside)
    this.world.setBlock(vx - 4, vy + 1, vz + 2, 3);

    // === House 2: Shop (right) - all planks ===
    this.buildVillageHouse(vx + 7, vy + 1, vz, 5, 4, 5, 13, 13); // Planks 

    // === House 3: Inn (back) - planks ===
    this.buildVillageHouse(vx + 1, vy + 1, vz + 7, 6, 4, 5, 13, 13); // Planks

    // === Spawn villagers ===
    this.spawnVillagers(vx, vy, vz);

    // === Well in center ===
    for (let y = 0; y < 3; y++) {
      this.world.setBlock(vx + 2, vy + 1 + y, vz + 2, 3); // Stone pillar
      this.world.setBlock(vx + 2, vy + 1 + y, vz + 3, 3);
      this.world.setBlock(vx + 3, vy + 1 + y, vz + 2, 3);
      this.world.setBlock(vx + 3, vy + 1 + y, vz + 3, 3);
    }
    // Water inside well
    this.world.setBlock(vx + 2, vy + 1, vz + 2, 7);
    this.world.setBlock(vx + 3, vy + 1, vz + 3, 7);

    // Lamp posts (wood + leaves as lanterns)
    const lampSpots = [[0, 0], [4, 0], [0, 4], [4, 4]];
    for (const [lx, lz] of lampSpots) {
      this.world.setBlock(vx + lx, vy + 1, vz + lz, 4); // Wood post
      this.world.setBlock(vx + lx, vy + 2, vz + lz, 4);
      this.world.setBlock(vx + lx, vy + 3, vz + lz, 5); // Leaves (lantern)
    }

    this.showNotification('A village! Maybe someone lives here...', '#88ff88');
    console.log(`Village built at (${vx}, ${vy}, ${vz})`);
  }

  /** Build a small village house */
  private buildVillageHouse(hx: number, hy: number, hz: number, w: number, h: number, d: number, wallBlock: number, roofBlock: number = 13): void {
    // Floor (planks)
    for (let x = 0; x < w; x++) {
      for (let z = 0; z < d; z++) {
        this.world.setBlock(hx + x, hy - 1, hz + z, 13); // Plank floor
      }
    }
    // Walls
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        for (let z = 0; z < d; z++) {
          const isWall = (x === 0 || x === w - 1 || z === 0 || z === d - 1);
          const isDoor = (x === Math.floor(w / 2) && z === 0 && y < 2);
          const isWindow = (y === 1 && ((x === 1 && z === 0) || (x === w - 2 && z === 0)));
          if (isWall && !isDoor && !isWindow) {
            this.world.setBlock(hx + x, hy + y, hz + z, wallBlock);
          }
        }
      }
    }
    // Roof (planks)
    for (let x = -1; x <= w; x++) {
      for (let z = -1; z <= d; z++) {
        this.world.setBlock(hx + x, hy + h, hz + z, roofBlock);
      }
    }
  }

  /** Spawn villager NPCs in the village */
  private villagerMeshes: THREE.Mesh[] = [];
  private villagerGroups: { group: THREE.Group; name: string; dialogues: string[] }[] = [];
  private talkCooldown: number = 0;
  private attackCooldown: number = 0;
  private attackSwingMesh: THREE.Mesh | null = null;

  private spawnVillagers(vx: number, vy: number, vz: number): void {
    // Villager body colors
    const villagerDefs = [
      { x: vx - 4, z: vz - 1, name: 'Blacksmith', skinColor: 0x8B6914, clothColor: 0x444444, label: '⚒ Blacksmith',
        dialogues: [
          'Need a sword? I can forge one... if you bring me iron.',
          'The anvil rings true! Best blades in the land.',
          'Watch yourself in the Nether. Fire burns hot.',
          'My grandfather forged weapons for the old heroes.',
          'Iron, steel, diamond... I work with them all.'
        ] },
      { x: vx + 9, z: vz - 1, name: 'Merchant', skinColor: 0xC4A67B, clothColor: 0x2244AA, label: '💰 Merchant',
        dialogues: [
          'Welcome! Got rare goods from distant lands.',
          'Trade is the lifeblood of our village.',
          'I hear the Nether has valuable ores...',
          'Business is slow since the monsters appeared.',
          'Buy something, will ya?'
        ] },
      { x: vx + 3, z: vz + 6, name: 'Innkeeper', skinColor: 0xC4A67B, clothColor: 0x884422, label: '🍺 Innkeeper',
        dialogues: [
          'Rest your weary legs, traveler.',
          'The stew is fresh! Well... fresh-ish.',
          'Strange sounds at night lately...',
          'You look like you could use a warm bed.',
          'Watch out for Herobrine... just a rumor though.'
        ] },
      { x: vx + 1, z: vz + 1, name: 'Villager', skinColor: 0xC4A67B, clothColor: 0x228833, label: '🏠 Villager',
        dialogues: [
          'Nice day, isn\'t it?',
          'The village has been here for generations.',
          'Have you seen the old ruins to the east?',
          'Be careful at night. Things spawn in the dark.',
          'Welcome to our little village!'
        ] },
    ];

    for (const v of villagerDefs) {
      const group = new THREE.Group();

      // Body (clothes)
      const bodyGeo = new THREE.BoxGeometry(0.6, 0.9, 0.4);
      const bodyMat = new THREE.MeshLambertMaterial({ color: v.clothColor });
      const body = new THREE.Mesh(bodyGeo, bodyMat);
      body.position.y = 0.45;
      group.add(body);

      // Head (skin)
      const headGeo = new THREE.BoxGeometry(0.4, 0.4, 0.4);
      const headMat = new THREE.MeshLambertMaterial({ color: v.skinColor });
      const head = new THREE.Mesh(headGeo, headMat);
      head.position.y = 1.1;
      group.add(head);

      // Nose
      const noseGeo = new THREE.BoxGeometry(0.12, 0.2, 0.12);
      const noseMat = new THREE.MeshLambertMaterial({ color: v.skinColor });
      const nose = new THREE.Mesh(noseGeo, noseMat);
      nose.position.set(0, 1.05, 0.25);
      group.add(nose);

      // Eyes
      const eyeGeo = new THREE.BoxGeometry(0.08, 0.08, 0.05);
      const eyeMat = new THREE.MeshLambertMaterial({ color: 0x222222 });
      const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
      leftEye.position.set(-0.1, 1.15, 0.21);
      group.add(leftEye);
      const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
      rightEye.position.set(0.1, 1.15, 0.21);
      group.add(rightEye);

      // Arms
      const armGeo = new THREE.BoxGeometry(0.2, 0.75, 0.3);
      const armMat = new THREE.MeshLambertMaterial({ color: v.clothColor });
      const leftArm = new THREE.Mesh(armGeo, armMat);
      leftArm.position.set(-0.4, 0.45, 0);
      group.add(leftArm);
      const rightArm = new THREE.Mesh(armGeo, armMat);
      rightArm.position.set(0.4, 0.45, 0);
      group.add(rightArm);

      // Legs
      const legGeo = new THREE.BoxGeometry(0.25, 0.5, 0.3);
      const legMat = new THREE.MeshLambertMaterial({ color: 0x333355 });
      const leftLeg = new THREE.Mesh(legGeo, legMat);
      leftLeg.position.set(-0.15, -0.25, 0);
      group.add(leftLeg);
      const rightLeg = new THREE.Mesh(legGeo, legMat);
      rightLeg.position.set(0.15, -0.25, 0);
      group.add(rightLeg);

      group.position.set(v.x + 0.5, vy + 1, v.z + 0.5);

      // Add name label as a sprite
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d')!;
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(0, 0, 256, 64);
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 28px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(v.label, 128, 42);
      const spriteTexture = new THREE.CanvasTexture(canvas);
      const spriteMat = new THREE.SpriteMaterial({ map: spriteTexture });
      const sprite = new THREE.Sprite(spriteMat);
      sprite.position.set(0, 1.8, 0);
      sprite.scale.set(2, 0.5, 1);
      group.add(sprite);

      this.renderer.scene.add(group);
      this.villagerMeshes.push(body);
      this.villagerGroups.push({ group, name: v.name, dialogues: v.dialogues });
    }
  }

  /** Teleport player into the Nether */
  private enterNether(): void {
    if (this.inNether) return;
    this.inNether = true;

    // Save return position
    this.netherReturnPos = this.player.position.clone();

    this.showNotification('Entering the Nether...', '#ff4400');
    this.showNotification('Everything is red and dangerous here!', '#ff8800');

    // Teleport to a nether area (far away, coords 500+)
    const nx = 500;
    const nz = 500;
    const ny = 65;

    // Generate nether terrain with netherrack
    for (let x = -10; x <= 15; x++) {
      for (let z = -10; z <= 15; z++) {
        // Netherrack floor
        this.world.setBlock(nx + x, ny, nz + z, 11);
        this.world.setBlock(nx + x, ny - 1, nz + z, 11);
        this.world.setBlock(nx + x, ny - 2, nz + z, 11);
        // Clear above 
        for (let y = 1; y <= 8; y++) {
          this.world.setBlock(nx + x, ny + y, nz + z, 0);
        }
        // Netherrack ceiling (gives it the enclosed nether feel)
        this.world.setBlock(nx + x, ny + 9, nz + z, 11);
        this.world.setBlock(nx + x, ny + 10, nz + z, 11);
      }
    }

    // Lava pools
    for (let x = 5; x <= 8; x++) {
      for (let z = -5; z <= -2; z++) {
        this.world.setBlock(nx + x, ny, nz + z, 12); // Lava
      }
    }
    for (let x = -7; x <= -5; x++) {
      for (let z = 3; z <= 6; z++) {
        this.world.setBlock(nx + x, ny, nz + z, 12); // Lava
      }
    }

    // Netherrack pillars
    for (let y = 0; y < 9; y++) {
      this.world.setBlock(nx - 5, ny + y, nz - 5, 11);
      this.world.setBlock(nx + 10, ny + y, nz - 5, 11);
      this.world.setBlock(nx - 5, ny + y, nz + 10, 11);
      this.world.setBlock(nx + 10, ny + y, nz + 10, 11);
    }

    // Netherrack walls around edges for enclosure
    for (let i = -10; i <= 15; i++) {
      for (let y = 0; y <= 10; y++) {
        this.world.setBlock(nx - 10, ny + y, nz + i, 11);
        this.world.setBlock(nx + 15, ny + y, nz + i, 11);
        this.world.setBlock(nx + i, ny + y, nz - 10, 11);
        this.world.setBlock(nx + i, ny + y, nz + 15, 11);
      }
    }

    // Return portal (netherrack frame at nether side)
    for (let y = 0; y < 5; y++) {
      this.world.setBlock(nx + 8, ny + y, nz + 8, 11);
      this.world.setBlock(nx + 11, ny + y, nz + 8, 11);
    }
    for (let x = 8; x <= 11; x++) {
      this.world.setBlock(nx + x, ny, nz + 8, 11);
      this.world.setBlock(nx + x, ny + 4, nz + 8, 11);
    }
    for (let x = 9; x <= 10; x++) {
      for (let y = 1; y < 4; y++) {
        this.world.setBlock(nx + x, ny + y, nz + 8, 7); // Portal fill
      }
    }

    // Teleport player
    this.player.position.set(nx + 2, ny + 1, nz + 2);
    this.player.velocity.set(0, 0, 0);
    this.player.onGround = true;

    this.abilities.addXP(50);
    console.log('Entered the Nether!');
  }

  /** Return from the Nether to overworld */
  private exitNether(): void {
    if (!this.inNether) return;
    this.inNether = false;

    this.showNotification('Returning to the Overworld...', '#88ff88');
    this.showNotification('You survived the Nether!', '#ffdd44');

    // Return to saved position (or near portal)
    if (this.netherReturnPos) {
      this.player.position.copy(this.netherReturnPos);
      this.player.position.x += 3; // Offset so we don't re-enter
    } else {
      this.player.position.set(this.PORTAL_X + 5, this.PORTAL_Y + 1, this.PORTAL_Z + 3);
    }
    this.player.velocity.set(0, 0, 0);
    this.player.onGround = true;

    this.abilities.addXP(100);
    console.log('Exited the Nether!');
  }

  private showAbilityChoice(): void {
    if (this.abilityChoiceOpen || !this.abilities.hasPendingChoice()) return;
    this.abilityChoiceOpen = true;
    
    const choices = this.abilities.getAbilityChoices(3);
    if (choices.length === 0) {
      this.abilityChoiceOpen = false;
      return;
    }
    
    // Show the ability choice overlay
    const overlay = document.getElementById('ability-choice-screen');
    if (!overlay) {
      this.abilityChoiceOpen = false;
      return;
    }
    
    const cardsContainer = overlay.querySelector('.ability-choice-cards');
    if (!cardsContainer) {
      this.abilityChoiceOpen = false;
      return;
    }
    
    // Build choice cards
    cardsContainer.innerHTML = choices.map((ability, i) => {
      const schoolColor = {
        physical: '#ff8844',
        magic: '#aa44ff',
        nether: '#ff4444',
        passive: '#44ff88'
      }[ability.school] || '#ffffff';
      
      return `
        <div class="ability-choice-card" onclick="window.chooseAbility('${ability.id}')" style="
          width: 220px; padding: 20px; margin: 10px;
          background: rgba(0,0,0,0.85);
          border: 2px solid ${schoolColor};
          border-radius: 10px;
          cursor: pointer;
          text-align: center;
          transition: all 0.3s;
        " onmouseenter="this.style.transform='translateY(-5px)';this.style.boxShadow='0 10px 30px ${schoolColor}66'"
           onmouseleave="this.style.transform='';this.style.boxShadow=''">
          <div style="font-size: 18px; font-weight: bold; color: ${schoolColor}; margin-bottom: 8px;">
            ${ability.name}
          </div>
          <div style="font-size: 10px; color: #888; margin-bottom: 8px; text-transform: uppercase;">
            ${ability.school} ${ability.isUltimate ? '★ ULTIMATE' : ''}
          </div>
          <div style="font-size: 12px; color: #ccc; line-height: 1.5; margin-bottom: 10px;">
            ${ability.description}
          </div>
          <div style="font-size: 11px; color: #aaaaff;">
            ${ability.manaCost > 0 ? `Mana: ${ability.manaCost}` : 'Passive'} 
            ${ability.cooldown > 0 ? `| CD: ${ability.cooldown}s` : ''}
          </div>
        </div>
      `;
    }).join('');
    
    overlay.style.display = 'flex';
    
    // Release pointer for clicking
    document.exitPointerLock();
  }

  handleAbilityChoice(abilityId: string): void {
    if (!this.abilities) return;
    
    const success = this.abilities.chooseAbility(abilityId);
    if (success) {
      const ability = this.abilities.getAbility(abilityId);
      this.showNotification(`Ability learned: ${ability?.name || abilityId}!`, '#aa88ff');
      this.updateAbilityBar();
    }
    
    // Hide overlay
    const overlay = document.getElementById('ability-choice-screen');
    if (overlay) {
      overlay.style.display = 'none';
    }
    this.abilityChoiceOpen = false;
    
    // Re-lock pointer
    this.canvas.requestPointerLock();
  }

  private handleHerobrineEvent(type: string, data?: any): void {
    switch (type) {
      case 'distant_sighting':
        if (data?.ended) {
          this.hideHerobrineOverlay();
        } else {
          this.showHerobrineOverlay('You feel watched... The Eyeless One is near.');
        }
        break;

      case 'dream_warning':
        if (data?.message) {
          this.showHerobrineOverlay(data.message);
        }
        break;

      case 'stalking':
        this.showHerobrineOverlay('Something is behind you...');
        break;

      case 'fell_magic':
        this.showHerobrineOverlay('Fell Magic distorts the air around you...');
        // Darken sky temporarily
        if (this.renderer.scene.fog) {
          (this.renderer.scene.fog as THREE.Fog).near = 5;
          (this.renderer.scene.fog as THREE.Fog).far = 30;
          setTimeout(() => {
            if (this.renderer.scene.fog) {
              (this.renderer.scene.fog as THREE.Fog).near = 30;
              (this.renderer.scene.fog as THREE.Fog).far = 80;
            }
          }, 10000);
        }
        break;

      case 'monster_wave':
        this.showHerobrineOverlay('The Eyeless One sends his forces!');
        break;
    }
  }

  private createHerobrineOverlay(): void {
    this.herobrineOverlay = document.createElement('div');
    this.herobrineOverlay.id = 'herobrine-overlay';
    this.herobrineOverlay.style.cssText = `
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      display: none;
      justify-content: center;
      align-items: center;
      background: rgba(0, 0, 0, 0);
      z-index: 9999;
      pointer-events: none;
      transition: background 2s;
    `;

    const text = document.createElement('div');
    text.id = 'herobrine-text';
    text.style.cssText = `
      color: #ff0000;
      font-family: 'Courier New', monospace;
      font-size: 28px;
      text-shadow: 0 0 20px #ff0000, 0 0 40px #ff0000;
      text-align: center;
      animation: herobrineFlicker 0.1s infinite;
      opacity: 0;
      transition: opacity 1s;
    `;

    this.herobrineOverlay.appendChild(text);
    document.body.appendChild(this.herobrineOverlay);

    // Add flicker animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes herobrineFlicker {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.7; }
      }
    `;
    document.head.appendChild(style);
  }

  private showHerobrineOverlay(message: string): void {
    if (!this.herobrineOverlay) return;

    this.herobrineOverlay.style.display = 'flex';
    this.herobrineOverlay.style.background = 'rgba(20, 0, 0, 0.4)';

    const textEl = this.herobrineOverlay.querySelector('#herobrine-text') as HTMLDivElement;
    if (textEl) {
      textEl.textContent = message;
      textEl.style.opacity = '1';
    }

    if (this.heroBrineMessageTimeout) {
      clearTimeout(this.heroBrineMessageTimeout);
    }
    this.heroBrineMessageTimeout = window.setTimeout(() => {
      this.hideHerobrineOverlay();
    }, 8000);
  }

  private hideHerobrineOverlay(): void {
    if (!this.herobrineOverlay) return;

    this.herobrineOverlay.style.background = 'rgba(0, 0, 0, 0)';
    const textEl = this.herobrineOverlay.querySelector('#herobrine-text') as HTMLDivElement;
    if (textEl) {
      textEl.style.opacity = '0';
    }

    setTimeout(() => {
      if (this.herobrineOverlay) {
        this.herobrineOverlay.style.display = 'none';
      }
    }, 2000);
  }

  private updatePlayerInteraction(): void {
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(new THREE.Vector2(0, 0), this.renderer.camera);

    const maxDistance = 5;
    const hit = this.world.raycast(raycaster.ray, maxDistance);

    if (hit) {
      const blockType = this.world.getBlock(hit.blockPos.x, hit.blockPos.y, hit.blockPos.z);

      // Left click
      if (this.inputManager.isMouseButtonPressed(0)) {
        // Left click on WATER = drink
        if (blockType === 7 && this.gameStarted && this.thirstSystem) {
          this.thirstSystem.drink(5);
          if (!this.hasDrunkWater) {
            this.hasDrunkWater = true;
            this.showNotification('Refreshing! Now right-click the bed in the house to rest...', '#4488ff');
          } else {
            this.showNotification('Drank water!', '#4488ff');
          }
          return; // Don't break water
        }

        // Left click while holding potion (type 10) = drink it
        const selectedType = this.inventory.getSelectedBlockType();
        if (selectedType === 10 && this.hasPotion && !this.abilities.isTransformed()) {
          this.inventory.removeSelectedItem(1);
          this.abilities.transform();
          this.player.setMobSize('human');
          const mobName = this.selectedMob.charAt(0).toUpperCase() + this.selectedMob.slice(1);
          this.showNotification(
            `You drink the potion... your body shifts! You stand upright as an Anthro ${mobName}!`,
            '#ff00ff'
          );
          this.showNotification(
            'You now walk on 2 legs with arms!',
            '#cc88ff'
          );
          this.abilities.addXP(50);
          this.updateStatsDisplay();
          return;
        }

        // Left click = ATTACK (melee swing)
        if (this.attackCooldown <= 0) {
          this.performAttack();
          this.attackCooldown = 0.4; // Attack speed
        }
      }

      // Right click
      if (this.inputManager.isMouseButtonPressed(2)) {
        // Right click on BED = sleep
        if (this.isBedBlock(hit.blockPos.x, hit.blockPos.y, hit.blockPos.z)) {
          this.handleBedSleep();
          return;
        }

        // Right click on CHEST = open chest
        if (blockType === 9) {
          this.handleChestOpen();
          return;
        }

        // Right click near villager = talk
        if (this.talkToNearbyVillager()) {
          return;
        }

        // Right click on block = break block
        if (hit.blockPos.y > 0 && blockType !== 7) {
          this.world.removeBlock(hit.blockPos.x, hit.blockPos.y, hit.blockPos.z);
          const blockColor = new THREE.Color(
            Math.random() * 0.5 + 0.5,
            Math.random() * 0.5 + 0.5,
            Math.random() * 0.5 + 0.5
          );
          this.particleSystem.createBlockBreakParticles(
            new THREE.Vector3(
              hit.blockPos.x + 0.5,
              hit.blockPos.y + 0.5,
              hit.blockPos.z + 0.5
            ),
            blockColor
          );
          this.soundManager.playBlockBreak();
          const added = this.inventory.addItem(blockType, 1);
          if (added) {
            const blockName = this.getBlockName(blockType);
            this.notificationSystem.itemPickedUp(blockName, 1);
          }
          this.blocksMined++;
          this.achievementSystem.updateProgress('first_block', 1);
          this.achievementSystem.updateProgress('miner', 1);
          if (this.abilities) {
            this.abilities.addXP(2);
            this.abilities.trainSkill('mining', 0.1);
          }
        }
      }
    }
  }

  /** Check if a world position is a bed block (red wool, type 8) */
  private isBedBlock(x: number, y: number, z: number): boolean {
    const blockType = this.world.getBlock(x, y, z);
    return blockType === 8; // Red wool = bed
  }

  /** Perform melee attack - swing arm and hit entities in front */
  private performAttack(): void {
    // Create swing visual
    if (this.attackSwingMesh) {
      this.renderer.scene.remove(this.attackSwingMesh);
    }
    const swingGeo = new THREE.BoxGeometry(0.15, 0.15, 1.2);
    const swingMat = new THREE.MeshLambertMaterial({ color: 0xcccccc, transparent: true, opacity: 0.8 });
    this.attackSwingMesh = new THREE.Mesh(swingGeo, swingMat);
    this.renderer.scene.add(this.attackSwingMesh);

    // Position swing in front of player
    const forward = new THREE.Vector3(0, 0, -1);
    forward.applyQuaternion(this.renderer.camera.quaternion);
    const swingPos = this.player.position.clone().add(forward.clone().multiplyScalar(1.5));
    swingPos.y += 1.2;
    this.attackSwingMesh.position.copy(swingPos);
    this.attackSwingMesh.lookAt(this.player.position.clone().add(new THREE.Vector3(0, 1.2, 0)));

    // Create hit particles
    const hitPos = this.player.position.clone().add(forward.clone().multiplyScalar(2));
    hitPos.y += 1;
    this.particleSystem.createBlockBreakParticles(hitPos, new THREE.Color(0xffffff));

    // Check if hitting a block to break it
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(new THREE.Vector2(0, 0), this.renderer.camera);
    const blockHit = this.world.raycast(raycaster.ray, 4);
    if (blockHit && blockHit.distance < 4) {
      const blockType = this.world.getBlock(blockHit.blockPos.x, blockHit.blockPos.y, blockHit.blockPos.z);
      if (blockHit.blockPos.y > 0 && blockType !== 7) {
        this.world.removeBlock(blockHit.blockPos.x, blockHit.blockPos.y, blockHit.blockPos.z);
        const blockColor = new THREE.Color(
          Math.random() * 0.5 + 0.5,
          Math.random() * 0.5 + 0.5,
          Math.random() * 0.5 + 0.5
        );
        this.particleSystem.createBlockBreakParticles(
          new THREE.Vector3(
            blockHit.blockPos.x + 0.5,
            blockHit.blockPos.y + 0.5,
            blockHit.blockPos.z + 0.5
          ),
          blockColor
        );
        this.soundManager.playBlockBreak();
        const added = this.inventory.addItem(blockType, 1);
        if (added) {
          const blockName = this.getBlockName(blockType);
          this.notificationSystem.itemPickedUp(blockName, 1);
        }
        this.blocksMined++;
        this.achievementSystem.updateProgress('first_block', 1);
        this.achievementSystem.updateProgress('miner', 1);
        if (this.abilities) {
          this.abilities.addXP(2);
          this.abilities.trainSkill('mining', 0.1);
        }
      }
    }

    // Play sound
    this.soundManager.playBlockBreak();

    // XP from combat
    if (this.abilities) {
      this.abilities.addXP(1);
    }
  }

  /** Update attack swing animation */
  private attackSwingTimer: number = 0;
  private updateAttackSwing(dt: number): void {
    if (this.attackSwingMesh) {
      this.attackSwingTimer += dt;
      // Fade out over 0.2 seconds
      const mat = this.attackSwingMesh.material as THREE.MeshLambertMaterial;
      mat.opacity = Math.max(0, 1 - this.attackSwingTimer / 0.2);
      if (this.attackSwingTimer > 0.2) {
        this.renderer.scene.remove(this.attackSwingMesh);
        this.attackSwingMesh = null;
        this.attackSwingTimer = 0;
      }
    }
  }

  /** Try to talk to a nearby villager, returns true if talked */
  private talkToNearbyVillager(): boolean {
    if (this.talkCooldown > 0) return false;
    if (this.villagerGroups.length === 0) return false;

    const playerPos = this.player.position;
    let closest: { group: THREE.Group; name: string; dialogues: string[] } | null = null;
    let closestDist = Infinity;

    for (const v of this.villagerGroups) {
      const dist = playerPos.distanceTo(v.group.position);
      if (dist < closestDist) {
        closestDist = dist;
        closest = v;
      }
    }

    if (closest && closestDist < 4) {
      this.talkCooldown = 1.5; // Prevent spam
      const dialogue = closest.dialogues[Math.floor(Math.random() * closest.dialogues.length)];
      this.showVillagerDialogue(closest.name, dialogue);
      // XP for socializing
      if (this.abilities) {
        this.abilities.addXP(3);
      }
      return true;
    }
    return false;
  }

  /** Show villager dialogue in a nice chat bubble */
  private showVillagerDialogue(name: string, text: string): void {
    // Remove any existing dialogue
    const existing = document.getElementById('villager-dialogue');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.id = 'villager-dialogue';
    div.style.cssText = `
      position: fixed;
      bottom: 200px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.9);
      border: 2px solid #88aa44;
      border-radius: 10px;
      padding: 15px 25px;
      max-width: 400px;
      z-index: 1000;
      font-family: 'Courier New', monospace;
      animation: fadeInUp 0.3s ease;
    `;
    div.innerHTML = `
      <div style="color: #88ff44; font-weight: bold; font-size: 16px; margin-bottom: 8px;">${name}</div>
      <div style="color: #ffffff; font-size: 14px; line-height: 1.4;">"${text}"</div>
    `;
    document.body.appendChild(div);

    // Add animation style if not present
    if (!document.getElementById('dialogue-style')) {
      const style = document.createElement('style');
      style.id = 'dialogue-style';
      style.textContent = `
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateX(-50%) translateY(20px); }
          to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
      `;
      document.head.appendChild(style);
    }

    // Remove after 3 seconds
    setTimeout(() => {
      if (div.parentNode) {
        div.style.opacity = '0';
        div.style.transition = 'opacity 0.5s';
        setTimeout(() => div.remove(), 500);
      }
    }, 3000);
  }

  /** Apply red damage flash overlay */
  private applyDamageFlash(intensity: number): void {
    let overlay = document.getElementById('damage-flash');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'damage-flash';
      overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9998;';
      document.body.appendChild(overlay);
    }
    if (intensity > 0) {
      overlay.style.backgroundColor = `rgba(255, 0, 0, ${intensity * 0.4})`;
    } else {
      overlay.style.backgroundColor = 'transparent';
    }
  }

  /** Handle player death */
  private playerDeath(): void {
    if (this.isDead) return;
    this.isDead = true;
    this.showNotification('You died!', '#ff0000');
    this.applyDamageFlash(1.0);

    // Respawn after 2 seconds
    setTimeout(() => {
      this.playerHP = this.MAX_HP;
      this.isDead = false;
      this.damageFlashTimer = 0;
      this.applyDamageFlash(0);

      // Respawn at overworld spawn
      if (this.inNether) {
        this.inNether = false;
      }
      this.player.position.set(0.5, 65, 0.5);
      this.player.velocity.set(0, 0, 0);
      this.player.onGround = true;
      this.showNotification('Respawned!', '#88ff88');
    }, 2000);
  }

  /** Check if player bounding box overlaps any solid block (water is passable) */
  private checkSolidCollision(pos: THREE.Vector3): boolean {
    const hw = 0.3; // half-width for collision
    const h = this.player.getHeight();
    // Check all blocks the player overlaps
    const minX = Math.floor(pos.x - hw);
    const maxX = Math.floor(pos.x + hw);
    const minZ = Math.floor(pos.z - hw);
    const maxZ = Math.floor(pos.z + hw);
    const minY = Math.floor(pos.y);
    const maxY = Math.floor(pos.y + h - 0.01);

    for (let bx = minX; bx <= maxX; bx++) {
      for (let bz = minZ; bz <= maxZ; bz++) {
        for (let by = minY; by <= maxY; by++) {
          const block = this.world.getBlock(bx, by, bz);
          // Solid = not air(0) and not water(7)
          if (block !== 0 && block !== 7) {
            return true;
          }
        }
      }
    }
    return false;
  }

  /** Handle sleeping in the bed */
  private handleBedSleep(): void {
    if (!this.hasDrunkWater) {
      this.showNotification('You should drink some water first... left-click the water outside.', '#ffdd44');
      return;
    }
    if (this.hasSleptInBed) {
      // Can still sleep to skip night
      if (this.dayNightCycle) {
        this.dayNightCycle.skipToDay();
      }
      this.showNotification('You rest until morning...', '#aaaaff');
      return;
    }

    this.hasSleptInBed = true;
    this.showNotification('You curl up and rest in the abandoned bed...', '#aaaaff');

    // Skip to morning
    if (this.dayNightCycle) {
      this.dayNightCycle.skipToDay();
    }

    // Unlock abilities!
    this.abilities.unlockAbilitySystem();

    setTimeout(() => {
      this.showNotification('You feel power awakening within you!', '#ff88ff');
      this.showNotification('Choose your first ability!', '#ffdd44');
      this.showAbilityChoice();
    }, 2000);

    // Post-tutorial: expand map, build path + village, spawn nether portal
    setTimeout(() => {
      this.completeTutorial();
    }, 4000);

    // Spawn nether portal after a delay
    setTimeout(() => {
      this.spawnNetherPortal();
    }, 5000);
  }

  /** Handle right-clicking the chest */
  private handleChestOpen(): void {
    if (this.hasPotion || this.abilities.isTransformed()) {
      this.showNotification('The chest is empty.', '#888888');
      return;
    }

    // Release pointer so player can click the chest UI
    document.exitPointerLock();

    // Show chest UI overlay
    let overlay = document.getElementById('chest-screen');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'chest-screen';
      overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(0,0,0,0.75); z-index: 1000;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        font-family: 'Courier New', monospace;
      `;
      document.body.appendChild(overlay);
    }

    overlay.innerHTML = `
      <div style="font-size: 24px; color: #dda044; margin-bottom: 16px; text-shadow: 0 0 10px #dda044;">Chest</div>
      <div style="
        width: 320px; height: 200px;
        background: rgba(60,40,20,0.95);
        border: 3px solid #aa8844;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        gap: 16px;
        padding: 20px;
      ">
        <div id="chest-potion-slot" style="
          width: 80px; height: 80px;
          background: rgba(0,0,0,0.5);
          border: 2px solid #666;
          border-radius: 6px;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        " onmouseenter="this.style.borderColor='#ff44ff';this.style.boxShadow='0 0 15px #ff44ff66'"
           onmouseleave="this.style.borderColor='#666';this.style.boxShadow=''"
           onclick="window.takePotion()">
          <div style="font-size: 32px;">🧪</div>
          <div style="font-size: 10px; color: #ff88ff; margin-top: 4px;">Growth Potion</div>
        </div>
      </div>
      <div style="font-size: 12px; color: #aaa; margin-top: 12px;">Click the potion to take it</div>
      <div style="font-size: 11px; color: #666; margin-top: 6px; cursor: pointer;" onclick="window.closeChest()">[ Close ]</div>
    `;

    overlay.style.display = 'flex';
  }

  /** Take the potion from the chest */
  public takePotionFromChest(): void {
    if (this.hasPotion || this.abilities.isTransformed()) return;

    this.hasPotion = true;

    // Add potion to inventory (type 10 = Growth Potion)
    this.inventory.addItem(10, 1);
    this.showNotification('Growth Potion added to inventory!', '#ff88ff');
    this.showNotification('Select it and click to drink!', '#cc88ff');

    // Close chest UI
    this.closeChest();
  }

  /** Close the chest UI */
  public closeChest(): void {
    const overlay = document.getElementById('chest-screen');
    if (overlay) {
      overlay.style.display = 'none';
    }
    // Re-lock pointer
    this.canvas.requestPointerLock();
  }

  private updateHotbarSelection(): void {
    for (let i = 0; i < 9; i++) {
      const keyCode = `Digit${i + 1}`;
      if (this.inputManager.isKeyPressed(keyCode)) {
        this.inventory.selectSlot(i);
      }
    }
  }

  private updateGameUI(): void {
    if (!this.abilities || !this.thirstSystem) return;

    // Update thirst bar
    const thirstBar = document.getElementById('thirst-fill');
    if (thirstBar) {
      thirstBar.style.width = `${this.thirstSystem.getThirstPercent()}%`;
      thirstBar.style.backgroundColor = this.thirstSystem.isLowThirst()
        ? '#ff4444'
        : '#4488ff';
    }

    // Update mana bar
    const manaBar = document.getElementById('mana-fill');
    if (manaBar) {
      const manaPercent = (this.abilities.getMana() / this.abilities.getMaxMana()) * 100;
      manaBar.style.width = `${manaPercent}%`;
    }

    // Update level display
    const levelEl = document.getElementById('player-level');
    if (levelEl) {
      const prog = this.abilities.getProgression();
      const emoji = this.getMobEmoji();
      const formText = prog.isTransformed ? `(Anthro ${this.selectedMob})` : `(${this.selectedMob})`;
      levelEl.textContent = `Lv.${prog.level} ${emoji} ${formText}`;
    }

    // Update XP bar
    const xpBar = document.getElementById('xp-fill');
    if (xpBar) {
      const prog = this.abilities.getProgression();
      xpBar.style.width = `${(prog.xp / prog.xpToNext) * 100}%`;
    }

    // Update day counter
    const dayEl = document.getElementById('day-counter');
    if (dayEl) {
      dayEl.textContent = `Day ${this.currentGameDay}`;
    }

    // Update ability bar
    this.updateAbilityBar();

    // Herobrine fear indicator
    const fearEl = document.getElementById('fear-indicator');
    if (fearEl) {
      const fear = this.herobrineSystem.getFearLevel();
      if (fear > 10) {
        fearEl.style.display = 'block';
        fearEl.style.opacity = (fear / 100).toString();
        fearEl.textContent = fear > 50 ? 'THE EYELESS ONE...' : '...';
      } else {
        fearEl.style.display = 'none';
      }
    }
  }

  private updateAbilityBar(): void {
    if (!this.abilities) return;

    const abilityBar = document.getElementById('ability-bar');
    if (!abilityBar) return;

    const activeAbilities = this.abilities
      .getUnlockedAbilities()
      .filter((a) => a.school !== 'passive')
      .slice(0, 4);

    abilityBar.innerHTML = activeAbilities
      .map((ability, i) => {
        const ready = this.abilities.isAbilityReady(ability.id);
        const cdText =
          ability.currentCooldown > 0
            ? `${ability.currentCooldown.toFixed(0)}s`
            : '';
        const color = ready ? '#88ff88' : '#666666';
        const border = ability.isUltimate
          ? '2px solid #ff8800'
          : '2px solid #444';

        return `<div style="
        display: inline-block;
        width: 60px; height: 60px;
        margin: 4px;
        background: rgba(0,0,0,0.7);
        border: ${border};
        border-radius: 4px;
        text-align: center;
        color: ${color};
        font-size: 10px;
        font-family: monospace;
        position: relative;
        cursor: pointer;
      " title="${ability.description}">
        <div style="font-size: 8px; margin-top: 4px;">F${i + 1}</div>
        <div style="font-size: 9px; font-weight: bold; margin-top: 2px;">${ability.name.substring(0, 8)}</div>
        <div style="font-size: 8px; color: #aaaaff;">${ability.manaCost}MP</div>
        ${cdText ? `<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:14px;color:#ff4444;">${cdText}</div>` : ''}
      </div>`;
      })
      .join('');
  }

  private updateStatsDisplay(): void {
    if (!this.abilities) return;

    const statsEl = document.getElementById('mob-stats');
    if (!statsEl) return;

    const bonuses = this.abilities.getMobBonuses();
    const prog = this.abilities.getProgression();

    let statsHTML = `<div style="font-size: 10px; line-height: 1.4;">`;
    statsHTML += `<div style="color:#ff4444;">HP: ${this.playerHP}/${this.MAX_HP} ${'❤️'.repeat(Math.ceil(this.playerHP / 4))}${'🖤'.repeat(Math.ceil((this.MAX_HP - this.playerHP) / 4))}</div>`;
    statsHTML += `<div>STR: ${prog.attributes.strength} | AGI: ${prog.attributes.agility}</div>`;
    statsHTML += `<div>VIT: ${prog.attributes.vitality} | INT: ${prog.attributes.intelligence}</div>`;
    statsHTML += `<div>Speed: x${bonuses.speedMult.toFixed(1)} | DMG: x${this.abilities.getDamageMultiplier().toFixed(1)}</div>`;
    if (bonuses.creeperRepel) statsHTML += `<div style="color:#88ff88;">Creepers flee!</div>`;
    if (bonuses.nightVision) statsHTML += `<div style="color:#aaaaff;">Night vision</div>`;
    if (bonuses.packBonus) statsHTML += `<div style="color:#ffaa44;">Pack bonus</div>`;
    if (bonuses.wallClimb) statsHTML += `<div style="color:#ff88ff;">Wall climb</div>`;
    if (bonuses.fallDamageMult === 0) statsHTML += `<div style="color:#88ffaa;">No fall damage!</div>`;
    statsHTML += `</div>`;

    statsEl.innerHTML = statsHTML;
  }

  private getMobEmoji(): string {
    switch (this.selectedMob) {
      case 'cat':
        return '(=^..^=)';
      case 'wolf':
        return '/wolf/';
      case 'bunny':
        return '(\\/)';
      default:
        return '???';
    }
  }

  private updateFPS(currentTime: number): void {
    this.frameCount++;

    if (currentTime - this.fpsUpdateTime >= 1000) {
      const fps = Math.round(
        (this.frameCount * 1000) / (currentTime - this.fpsUpdateTime)
      );
      const fpsElement = document.getElementById('fps');
      if (fpsElement) {
        fpsElement.textContent = fps.toString();
      }
      this.frameCount = 0;
      this.fpsUpdateTime = currentTime;
    }
  }

  private updateDebugInfo(): void {
    const posElement = document.getElementById('position');
    if (posElement) {
      const pos = this.player.position;
      posElement.textContent = `${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}, ${pos.z.toFixed(1)}`;
    }

    const chunksElement = document.getElementById('chunks');
    if (chunksElement) {
      chunksElement.textContent = this.world.getLoadedChunkCount().toString();
    }
  }

  private getBlockName(blockType: number): string {
    const metal = MetalRegistry.getMetal(blockType);
    if (metal) return metal.name;

    const names: { [key: number]: string } = {
      1: 'Grass',
      2: 'Dirt',
      3: 'Stone',
      4: 'Wood',
      5: 'Leaves',
      6: 'Sand',
      7: 'Water',
      8: 'Bed',
      9: 'Chest',
      10: 'Growth Potion',
      11: 'Netherrack',
      12: 'Lava',
      13: 'Planks',
    };
    return names[blockType] || 'Block';
  }

  private showNotification(message: string, color: string = '#ffffff'): void {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: ${100 + Math.random() * 20}px;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.85);
      color: ${color};
      padding: 10px 20px;
      border-radius: 5px;
      font-size: 14px;
      z-index: 1000;
      pointer-events: none;
      font-family: 'Courier New', monospace;
      border: 1px solid ${color}44;
      text-shadow: 0 0 5px ${color};
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.transition = 'opacity 0.5s';
      notification.style.opacity = '0';
      setTimeout(() => notification.remove(), 500);
    }, 3000);
  }

  onResize(): void {
    this.renderer.onResize();
  }

  // Expose for mob selection
  getAbilities(): AetherianAbilities | null {
    return this.abilities || null;
  }

  getHerobrineSystem(): HerobrineSystem | null {
    return this.herobrineSystem || null;
  }
}
