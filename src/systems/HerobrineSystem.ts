import * as THREE from 'three';

/**
 * Herobrine System - "The Eyeless One" / "The Unseeing Wizard"
 * Based on Cube Kid's Aetherian series
 * 
 * Herobrine is a rare, terrifying encounter that appears only a few times
 * per 100 in-game days. He stalks the player with glowing white eyes,
 * creates eerie signs (2x2 tunnels, redstone torches, leaf pyramids),
 * and occasionally sends monster waves.
 * 
 * He is NOT a regular mob - he's an event/horror system.
 * 
 * From the books:
 * - "The Eyeless One" / "The Unseeing Wizard" / "He Who Never Blinks"
 * - Glowing white eyes (no pupils)
 * - Level 255 (was weakened from revival but still terrifying)
 * - Can use Fell Magic (corrupted magic, stronger but unstable)
 * - Commands vast armies of undead
 * - Destroyed Breeze's home (twice)
 * - Captured and experimented on Breeze and Brio using rune chambers
 * - Trains weaker mobs to prevent XP gain by heroes
 * - His presence causes mana storms and environmental disturbances
 */

export type HerobrineEventType = 
  | 'distant_sighting'   // See him standing far away staring at you, then vanishes
  | 'sign_left'          // Find a strange sign: 2x2 tunnels, redstone torches
  | 'stalking'           // He appears behind you briefly
  | 'monster_wave'       // Sends a wave of enhanced monsters
  | 'fell_magic'         // Environmental disturbance - fog, lightning, sky darkens
  | 'dream_warning'      // Screen flashes with cryptic message (like Runt's dream)
  | 'structure_found';   // Find a strange structure he built

export interface HerobrineState {
  isActive: boolean;
  currentEventType: HerobrineEventType | null;
  eventProgress: number;
  lastEncounterDay: number;
  totalEncounters: number;
  fearLevel: number; // 0-100, builds up during encounters
  isVisible: boolean;
  position: THREE.Vector3;
}

export class HerobrineSystem {
  private state: HerobrineState;
  private mesh: THREE.Group | null = null;
  private scene: THREE.Scene;
  private eventTimer: number = 0;
  private checkTimer: number = 0;
  private fadeAlpha: number = 0;
  
  // Spawn rate: ~3-5 encounters per 100 days
  // With 20-minute day cycles, 100 days = ~33 hours of gameplay
  // So roughly every 7-10 hours of play = 1 encounter
  // In game time: check every in-game day, ~3% chance per day
  private readonly ENCOUNTER_CHANCE_PER_DAY = 0.035; // ~3.5 encounters per 100 days
  private readonly MIN_DAYS_BETWEEN = 5; // At least 5 days between encounters
  private readonly EVENT_DURATION = 15; // seconds an event lasts
  
  // Messages from the books
  private readonly DREAM_MESSAGES = [
    "I'm coming for you...",
    "Your village cannot protect you.",
    "The Prophecy cannot save you now.",
    "You think you're safe? I destroyed Ioae. I destroyed Shadowbrook.",
    "Every hero falls eventually.",
    "The Eyeless One watches...",
    "He Who Never Blinks sees all.",
    "Surrender, and I'll make it quick.",
    "Your abilities are nothing compared to Fell Magic.",
    "The mobs serve ME.",
    "Run. It won't help.",
    "I was level 255 when your ancestors were still farming.",
  ];
  
  private readonly SIGN_MESSAGES = [
    "STOP",
    "TURN BACK",
    "HE WATCHES",
    "NO EYES",
    "THE UNSEEING WIZARD WAS HERE",
    "FELL MAGIC",
  ];
  
  private currentDay: number = 0;
  private onEventCallbacks: Array<(type: HerobrineEventType, data?: any) => void> = [];
  
  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.state = {
      isActive: false,
      currentEventType: null,
      eventProgress: 0,
      lastEncounterDay: -100,
      totalEncounters: 0,
      fearLevel: 0,
      isVisible: false,
      position: new THREE.Vector3()
    };
    
    this.createHerobrineModel();
    console.log('Herobrine System initialized - The Eyeless One watches...');
  }
  
  private createHerobrineModel(): void {
    this.mesh = new THREE.Group();
    
    // Body - dark Steve-like figure
    const bodyGeo = new THREE.BoxGeometry(0.6, 1.2, 0.3);
    const bodyMat = new THREE.MeshBasicMaterial({ color: 0x1a1a2e });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.y = 0.6;
    this.mesh.add(body);
    
    // Head
    const headGeo = new THREE.BoxGeometry(0.5, 0.5, 0.5);
    const headMat = new THREE.MeshBasicMaterial({ color: 0xc49a6c }); // Skin color
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = 1.45;
    this.mesh.add(head);
    
    // THE EYES - Glowing white, no pupils (the defining feature)
    const eyeGeo = new THREE.BoxGeometry(0.12, 0.06, 0.05);
    const eyeMat = new THREE.MeshBasicMaterial({ 
      color: 0xffffff,
      emissive: new THREE.Color(0xffffff),
      emissiveIntensity: 3
    });
    
    const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
    leftEye.position.set(-0.1, 1.5, 0.26);
    this.mesh.add(leftEye);
    
    const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
    rightEye.position.set(0.1, 1.5, 0.26);
    this.mesh.add(rightEye);
    
    // Eye glow (point lights)
    const eyeGlow = new THREE.PointLight(0xffffff, 2, 8);
    eyeGlow.position.set(0, 1.5, 0.3);
    this.mesh.add(eyeGlow);
    
    // Legs
    const legGeo = new THREE.BoxGeometry(0.25, 0.6, 0.25);
    const legMat = new THREE.MeshBasicMaterial({ color: 0x0d0d3b }); // Dark blue jeans
    
    const leftLeg = new THREE.Mesh(legGeo, legMat);
    leftLeg.position.set(-0.15, -0.3, 0);
    this.mesh.add(leftLeg);
    
    const rightLeg = new THREE.Mesh(legGeo, legMat);
    rightLeg.position.set(0.15, -0.3, 0);
    this.mesh.add(rightLeg);
    
    // Arms
    const armGeo = new THREE.BoxGeometry(0.2, 0.9, 0.25);
    const armMat = new THREE.MeshBasicMaterial({ color: 0x1a6e6e }); // Teal shirt
    
    const leftArm = new THREE.Mesh(armGeo, armMat);
    leftArm.position.set(-0.4, 0.55, 0);
    this.mesh.add(leftArm);
    
    const rightArm = new THREE.Mesh(armGeo, armMat);
    rightArm.position.set(0.4, 0.55, 0);
    this.mesh.add(rightArm);
    
    // Hair
    const hairGeo = new THREE.BoxGeometry(0.52, 0.2, 0.52);
    const hairMat = new THREE.MeshBasicMaterial({ color: 0x3d2b1f }); // Brown hair
    const hair = new THREE.Mesh(hairGeo, hairMat);
    hair.position.y = 1.75;
    this.mesh.add(hair);
    
    // Start hidden
    this.mesh.visible = false;
    this.scene.add(this.mesh);
  }
  
  update(deltaTime: number, playerPosition: THREE.Vector3, currentGameDay: number): void {
    this.currentDay = currentGameDay;
    
    // Gradual fear decay
    if (!this.state.isActive) {
      this.state.fearLevel = Math.max(0, this.state.fearLevel - deltaTime * 0.5);
    }
    
    // Check for new encounter
    this.checkTimer += deltaTime;
    if (this.checkTimer >= 60) { // Check every 60 real seconds
      this.checkTimer = 0;
      this.tryTriggerEncounter();
    }
    
    // Update active event
    if (this.state.isActive) {
      this.updateEvent(deltaTime, playerPosition);
    }
  }
  
  private tryTriggerEncounter(): void {
    if (this.state.isActive) return;
    
    // Minimum days between encounters
    const daysSinceLastEncounter = this.currentDay - this.state.lastEncounterDay;
    if (daysSinceLastEncounter < this.MIN_DAYS_BETWEEN) return;
    
    // Random chance per day check (adjusted for 60s check interval)
    // A day is 1200 seconds real time, so 20 checks per day
    const adjustedChance = this.ENCOUNTER_CHANCE_PER_DAY / 20;
    
    if (Math.random() < adjustedChance) {
      this.triggerEncounter();
    }
  }
  
  private triggerEncounter(): void {
    // Weighted random event type
    const events: { type: HerobrineEventType; weight: number }[] = [
      { type: 'distant_sighting', weight: 30 },
      { type: 'dream_warning', weight: 25 },
      { type: 'fell_magic', weight: 15 },
      { type: 'stalking', weight: 10 },
      { type: 'sign_left', weight: 10 },
      { type: 'monster_wave', weight: 5 },
      { type: 'structure_found', weight: 5 },
    ];
    
    const totalWeight = events.reduce((sum, e) => sum + e.weight, 0);
    let random = Math.random() * totalWeight;
    let selectedEvent: HerobrineEventType = 'distant_sighting';
    
    for (const event of events) {
      random -= event.weight;
      if (random <= 0) {
        selectedEvent = event.type;
        break;
      }
    }
    
    this.state.isActive = true;
    this.state.currentEventType = selectedEvent;
    this.state.eventProgress = 0;
    this.state.totalEncounters++;
    this.state.lastEncounterDay = this.currentDay;
    this.eventTimer = 0;
    
    console.log(`⚠️ Herobrine event triggered: ${selectedEvent} (encounter #${this.state.totalEncounters})`);
    
    // Notify listeners
    this.onEventCallbacks.forEach(cb => cb(selectedEvent));
  }
  
  private updateEvent(deltaTime: number, playerPosition: THREE.Vector3): void {
    this.eventTimer += deltaTime;
    this.state.eventProgress = this.eventTimer / this.EVENT_DURATION;
    
    switch (this.state.currentEventType) {
      case 'distant_sighting':
        this.updateDistantSighting(deltaTime, playerPosition);
        break;
      case 'stalking':
        this.updateStalking(deltaTime, playerPosition);
        break;
      case 'dream_warning':
        this.updateDreamWarning(deltaTime);
        break;
      case 'fell_magic':
        this.updateFellMagic(deltaTime);
        break;
      case 'monster_wave':
        this.updateMonsterWave(deltaTime, playerPosition);
        break;
      default:
        break;
    }
    
    // Fear increases during events
    this.state.fearLevel = Math.min(100, this.state.fearLevel + deltaTime * 5);
    
    // End event after duration
    if (this.eventTimer >= this.EVENT_DURATION) {
      this.endEvent();
    }
  }
  
  private updateDistantSighting(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.mesh) return;
    
    if (this.eventTimer < 1) {
      // Place Herobrine 40-60 blocks away, facing the player
      const angle = Math.random() * Math.PI * 2;
      const distance = 40 + Math.random() * 20;
      const pos = new THREE.Vector3(
        playerPosition.x + Math.cos(angle) * distance,
        65,
        playerPosition.z + Math.sin(angle) * distance
      );
      
      this.state.position.copy(pos);
      this.mesh.position.copy(pos);
      
      // Face the player
      this.mesh.lookAt(playerPosition.x, 65, playerPosition.z);
      
      this.mesh.visible = true;
      this.state.isVisible = true;
    }
    
    // Flicker effect - he appears and disappears
    if (this.eventTimer > 8) {
      this.fadeAlpha = Math.max(0, 1 - (this.eventTimer - 8) / 2);
      this.mesh.visible = this.fadeAlpha > 0.1;
    }
    
    // Vanish instantly if player gets too close
    const dist = playerPosition.distanceTo(this.state.position);
    if (dist < 15) {
      this.mesh.visible = false;
      this.state.isVisible = false;
    }
  }
  
  private updateStalking(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.mesh) return;
    
    // Herobrine appears behind the player for brief moments
    const behindDist = 8;
    const cameraDir = new THREE.Vector3(0, 0, -1); // Default forward
    
    // Place behind player
    const behindPos = new THREE.Vector3(
      playerPosition.x - cameraDir.x * behindDist,
      65,
      playerPosition.z - cameraDir.z * behindDist
    );
    
    this.state.position.copy(behindPos);
    this.mesh.position.copy(behindPos);
    this.mesh.lookAt(playerPosition.x, 65, playerPosition.z);
    
    // Rapidly blink in and out
    const blinkRate = 3 + this.eventTimer * 0.5; // Gets faster
    this.mesh.visible = Math.sin(this.eventTimer * blinkRate) > 0.3;
    this.state.isVisible = this.mesh.visible;
    
    // Vanish after a few seconds
    if (this.eventTimer > 5) {
      this.mesh.visible = false;
      this.state.isVisible = false;
    }
  }
  
  private updateDreamWarning(_deltaTime: number): void {
    // This is handled by the UI - just set the message
    if (this.eventTimer < 0.1) {
      const message = this.DREAM_MESSAGES[Math.floor(Math.random() * this.DREAM_MESSAGES.length)];
      this.onEventCallbacks.forEach(cb => cb('dream_warning', { message }));
    }
  }
  
  private updateFellMagic(_deltaTime: number): void {
    // Environmental disturbance - fog gets closer, sky darkens, brief lightning
    // Handled via callbacks to renderer
    if (this.eventTimer < 0.1) {
      this.onEventCallbacks.forEach(cb => cb('fell_magic', {
        fogDensity: 2.0,
        skyDarken: 0.7,
        lightning: true
      }));
    }
  }
  
  private updateMonsterWave(_deltaTime: number, playerPosition: THREE.Vector3): void {
    // Trigger mob spawner to send enhanced monsters
    if (this.eventTimer < 0.1) {
      this.onEventCallbacks.forEach(cb => cb('monster_wave', {
        position: playerPosition.clone(),
        count: 5 + Math.floor(this.state.totalEncounters * 2),
        enhanced: true
      }));
    }
  }
  
  private endEvent(): void {
    if (this.mesh) {
      this.mesh.visible = false;
    }
    
    this.state.isActive = false;
    this.state.isVisible = false;
    this.state.currentEventType = null;
    this.state.eventProgress = 0;
    this.eventTimer = 0;
    
    console.log('Herobrine event ended');
    this.onEventCallbacks.forEach(cb => cb('distant_sighting', { ended: true }));
  }
  
  // === PUBLIC API ===
  
  onEvent(callback: (type: HerobrineEventType, data?: any) => void): void {
    this.onEventCallbacks.push(callback);
  }
  
  getState(): HerobrineState {
    return { ...this.state };
  }
  
  getFearLevel(): number {
    return this.state.fearLevel;
  }
  
  isEncounterActive(): boolean {
    return this.state.isActive;
  }
  
  getTotalEncounters(): number {
    return this.state.totalEncounters;
  }
  
  getDreamMessage(): string {
    return this.DREAM_MESSAGES[Math.floor(Math.random() * this.DREAM_MESSAGES.length)];
  }
  
  getSignMessage(): string {
    return this.SIGN_MESSAGES[Math.floor(Math.random() * this.SIGN_MESSAGES.length)];
  }
  
  // Force trigger for testing
  forceTrigger(eventType?: HerobrineEventType): void {
    if (eventType) {
      this.state.currentEventType = eventType;
    }
    this.triggerEncounter();
  }
  
  // Serialize for save/load
  serialize(): object {
    return {
      lastEncounterDay: this.state.lastEncounterDay,
      totalEncounters: this.state.totalEncounters,
      fearLevel: this.state.fearLevel
    };
  }
  
  deserialize(data: any): void {
    if (data.lastEncounterDay !== undefined) this.state.lastEncounterDay = data.lastEncounterDay;
    if (data.totalEncounters !== undefined) this.state.totalEncounters = data.totalEncounters;
    if (data.fearLevel !== undefined) this.state.fearLevel = data.fearLevel;
  }
}
