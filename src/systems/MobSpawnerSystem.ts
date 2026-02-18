import * as THREE from 'three';

/**
 * Mob Spawner System - Manages creature spawning and AI
 */

export type MobType = 'passive' | 'neutral' | 'hostile';

export interface MobDefinition {
  id: string;
  name: string;
  type: MobType;
  health: number;
  damage: number;
  speed: number;
  size: number;
  color: THREE.Color;
  spawnBiomes: string[];
  spawnTime: 'day' | 'night' | 'any';
  spawnChance: number;
  dropItems: Array<{ type: string; count: number; chance: number }>;
}

export interface Mob {
  id: string;
  definition: MobDefinition;
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  health: number;
  target: THREE.Vector3 | null;
  state: 'idle' | 'wander' | 'chase' | 'flee' | 'attack';
  stateTime: number;
  mesh: THREE.Mesh;
  alive: boolean;
}

export class MobSpawnerSystem {
  private mobDefinitions: Map<string, MobDefinition> = new Map();
  private spawnedMobs: Map<string, Mob> = new Map();
  private nextMobId: number = 0;
  private scene: THREE.Scene;
  private maxMobs: number = 50;
  private spawnInterval: number = 5; // seconds
  private timeSinceLastSpawn: number = 0;
  
  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.initializeMobTypes();
  }
  
  private initializeMobTypes(): void {
    // Passive mobs
    this.addMobDefinition({
      id: 'sheep',
      name: 'Sheep',
      type: 'passive',
      health: 8,
      damage: 0,
      speed: 2,
      size: 0.6,
      color: new THREE.Color(0xeeeeee),
      spawnBiomes: ['plains', 'forest'],
      spawnTime: 'any',
      spawnChance: 0.4,
      dropItems: [
        { type: 'wool', count: 2, chance: 1.0 },
        { type: 'meat', count: 1, chance: 0.5 }
      ]
    });
    
    this.addMobDefinition({
      id: 'cow',
      name: 'Cow',
      type: 'passive',
      health: 10,
      damage: 0,
      speed: 1.8,
      size: 0.7,
      color: new THREE.Color(0x8B4513),
      spawnBiomes: ['plains', 'forest'],
      spawnTime: 'any',
      spawnChance: 0.3,
      dropItems: [
        { type: 'leather', count: 2, chance: 1.0 },
        { type: 'meat', count: 2, chance: 1.0 }
      ]
    });
    
    this.addMobDefinition({
      id: 'chicken',
      name: 'Chicken',
      type: 'passive',
      health: 4,
      damage: 0,
      speed: 2.5,
      size: 0.4,
      color: new THREE.Color(0xFFFFFF),
      spawnBiomes: ['plains', 'forest', 'jungle'],
      spawnTime: 'any',
      spawnChance: 0.5,
      dropItems: [
        { type: 'feather', count: 1, chance: 1.0 },
        { type: 'meat', count: 1, chance: 0.7 }
      ]
    });
    
    // Neutral mobs
    this.addMobDefinition({
      id: 'wolf',
      name: 'Wolf',
      type: 'neutral',
      health: 12,
      damage: 4,
      speed: 4,
      size: 0.6,
      color: new THREE.Color(0x666666),
      spawnBiomes: ['forest', 'tundra'],
      spawnTime: 'any',
      spawnChance: 0.15,
      dropItems: [
        { type: 'fur', count: 1, chance: 0.8 }
      ]
    });
    
    this.addMobDefinition({
      id: 'bear',
      name: 'Bear',
      type: 'neutral',
      health: 20,
      damage: 6,
      speed: 3,
      size: 1.0,
      color: new THREE.Color(0x8B4513),
      spawnBiomes: ['forest', 'mountains'],
      spawnTime: 'any',
      spawnChance: 0.1,
      dropItems: [
        { type: 'fur', count: 3, chance: 1.0 },
        { type: 'meat', count: 4, chance: 1.0 }
      ]
    });
    
    // Hostile mobs
    this.addMobDefinition({
      id: 'zombie',
      name: 'Zombie',
      type: 'hostile',
      health: 20,
      damage: 3,
      speed: 2,
      size: 0.8,
      color: new THREE.Color(0x00aa00),
      spawnBiomes: ['plains', 'forest', 'swamp'],
      spawnTime: 'night',
      spawnChance: 0.3,
      dropItems: [
        { type: 'rotten_flesh', count: 1, chance: 1.0 },
        { type: 'iron', count: 1, chance: 0.1 }
      ]
    });
    
    this.addMobDefinition({
      id: 'skeleton',
      name: 'Skeleton',
      type: 'hostile',
      health: 16,
      damage: 4,
      speed: 2.5,
      size: 0.8,
      color: new THREE.Color(0xdddddd),
      spawnBiomes: ['plains', 'desert', 'mountains'],
      spawnTime: 'night',
      spawnChance: 0.25,
      dropItems: [
        { type: 'bone', count: 2, chance: 1.0 },
        { type: 'arrow', count: 3, chance: 0.5 }
      ]
    });
    
    this.addMobDefinition({
      id: 'spider',
      name: 'Spider',
      type: 'hostile',
      health: 12,
      damage: 2,
      speed: 3.5,
      size: 0.6,
      color: new THREE.Color(0x330000),
      spawnBiomes: ['forest', 'jungle', 'swamp'],
      spawnTime: 'night',
      spawnChance: 0.3,
      dropItems: [
        { type: 'string', count: 2, chance: 1.0 },
        { type: 'spider_eye', count: 1, chance: 0.3 }
      ]
    });
    
    this.addMobDefinition({
      id: 'slime',
      name: 'Slime',
      type: 'hostile',
      health: 8,
      damage: 2,
      speed: 1.5,
      size: 0.5,
      color: new THREE.Color(0x00ff00),
      spawnBiomes: ['swamp'],
      spawnTime: 'night',
      spawnChance: 0.2,
      dropItems: [
        { type: 'slime_ball', count: 1, chance: 0.5 }
      ]
    });
    
    this.addMobDefinition({
      id: 'enderman',
      name: 'Enderman',
      type: 'neutral',
      health: 40,
      damage: 7,
      speed: 5,
      size: 1.2,
      color: new THREE.Color(0x1a0033),
      spawnBiomes: ['plains', 'desert', 'mountains'],
      spawnTime: 'night',
      spawnChance: 0.05,
      dropItems: [
        { type: 'ender_pearl', count: 1, chance: 0.5 }
      ]
    });
    
    console.log(`Loaded ${this.mobDefinitions.size} mob types`);
  }
  
  private addMobDefinition(def: MobDefinition): void {
    this.mobDefinitions.set(def.id, def);
  }
  
  update(deltaTime: number, playerPosition: THREE.Vector3, timeOfDay: string): void {
    // Spawn new mobs
    this.timeSinceLastSpawn += deltaTime;
    if (this.timeSinceLastSpawn >= this.spawnInterval && this.spawnedMobs.size < this.maxMobs) {
      this.trySpawnMob(playerPosition, timeOfDay);
      this.timeSinceLastSpawn = 0;
    }
    
    // Update existing mobs
    const mobsToRemove: string[] = [];
    
    this.spawnedMobs.forEach((mob, id) => {
      if (!mob.alive) {
        mobsToRemove.push(id);
        return;
      }
      
      this.updateMob(mob, deltaTime, playerPosition);
      
      // Remove mobs too far from player
      const distance = mob.position.distanceTo(playerPosition);
      if (distance > 100) {
        mobsToRemove.push(id);
      }
    });
    
    // Clean up dead/far mobs
    mobsToRemove.forEach(id => this.removeMob(id));
  }
  
  private trySpawnMob(playerPosition: THREE.Vector3, timeOfDay: string): void {
    // Random spawn position around player (30-60 blocks away)
    const angle = Math.random() * Math.PI * 2;
    const distance = 30 + Math.random() * 30;
    
    const spawnPos = new THREE.Vector3(
      playerPosition.x + Math.cos(angle) * distance,
      65, // Ground level
      playerPosition.z + Math.sin(angle) * distance
    );
    
    // Select random mob type based on spawn chances
    const validMobs = Array.from(this.mobDefinitions.values()).filter(def => {
      if (def.spawnTime !== 'any') {
        const isNight = timeOfDay === 'night' || timeOfDay === 'dusk';
        const isDay = timeOfDay === 'day' || timeOfDay === 'dawn';
        
        if (def.spawnTime === 'night' && !isNight) return false;
        if (def.spawnTime === 'day' && !isDay) return false;
      }
      
      return Math.random() < def.spawnChance;
    });
    
    if (validMobs.length === 0) return;
    
    const mobDef = validMobs[Math.floor(Math.random() * validMobs.length)];
    this.spawnMob(mobDef.id, spawnPos);
  }
  
  spawnMob(mobDefId: string, position: THREE.Vector3): Mob | null {
    const definition = this.mobDefinitions.get(mobDefId);
    if (!definition) return null;
    
    const geometry = new THREE.BoxGeometry(definition.size, definition.size, definition.size);
    const material = new THREE.MeshLambertMaterial({ color: definition.color });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.copy(position);
    this.scene.add(mesh);
    
    const mob: Mob = {
      id: `mob_${this.nextMobId++}`,
      definition,
      position: position.clone(),
      velocity: new THREE.Vector3(),
      health: definition.health,
      target: null,
      state: 'wander',
      stateTime: 0,
      mesh,
      alive: true
    };
    
    this.spawnedMobs.set(mob.id, mob);
    return mob;
  }
  
  private updateMob(mob: Mob, deltaTime: number, playerPosition: THREE.Vector3): void {
    mob.stateTime += deltaTime;
    
    // Update AI state
    const distanceToPlayer = mob.position.distanceTo(playerPosition);
    
    if (mob.definition.type === 'hostile') {
      if (distanceToPlayer < 20) {
        mob.state = 'chase';
        mob.target = playerPosition.clone();
      } else if (mob.state === 'chase') {
        mob.state = 'wander';
        mob.target = null;
      }
    } else if (mob.definition.type === 'neutral') {
      if (distanceToPlayer < 10 && mob.health < mob.definition.health) {
        mob.state = 'chase';
        mob.target = playerPosition.clone();
      } else if (distanceToPlayer < 3) {
        mob.state = 'flee';
        mob.target = mob.position.clone().sub(playerPosition).normalize();
      } else {
        mob.state = 'wander';
        mob.target = null;
      }
    } else { // passive
      if (distanceToPlayer < 5) {
        mob.state = 'flee';
        const fleeDir = mob.position.clone().sub(playerPosition).normalize();
        mob.target = mob.position.clone().add(fleeDir.multiplyScalar(10));
      } else if (mob.stateTime > 5 && mob.state !== 'flee') {
        mob.state = 'wander';
        mob.stateTime = 0;
      }
    }
    
    // Move based on state
    switch (mob.state) {
      case 'chase':
        if (mob.target) {
          const direction = mob.target.clone().sub(mob.position).normalize();
          mob.velocity.copy(direction.multiplyScalar(mob.definition.speed));
        }
        break;
        
      case 'flee':
        if (mob.target) {
          const direction = mob.position.clone().sub(mob.target).normalize();
          mob.velocity.copy(direction.multiplyScalar(mob.definition.speed * 1.5));
        }
        break;
        
      case 'wander':
        if (mob.stateTime > 3) {
          const randomDir = new THREE.Vector3(
            Math.random() - 0.5,
            0,
            Math.random() - 0.5
          ).normalize();
          mob.velocity.copy(randomDir.multiplyScalar(mob.definition.speed * 0.3));
          mob.stateTime = 0;
        }
        break;
        
      case 'idle':
        mob.velocity.multiplyScalar(0.9);
        break;
    }
    
    // Apply velocity
    mob.position.add(mob.velocity.clone().multiplyScalar(deltaTime));
    mob.mesh.position.copy(mob.position);
    
    // Keep at ground level
    mob.position.y = 65;
    
    // Slow down velocity
    mob.velocity.multiplyScalar(0.95);
  }
  
  damageMob(mobId: string, damage: number): boolean {
    const mob = this.spawnedMobs.get(mobId);
    if (!mob || !mob.alive) return false;
    
    mob.health -= damage;
    
    if (mob.health <= 0) {
      mob.alive = false;
      console.log(`💀 ${mob.definition.name} defeated!`);
      this.dropLoot(mob);
      return true;
    }
    
    return false;
  }
  
  private dropLoot(mob: Mob): void {
    mob.definition.dropItems.forEach(drop => {
      if (Math.random() < drop.chance) {
        console.log(`📦 Dropped ${drop.count}x ${drop.type}`);
      }
    });
  }
  
  private removeMob(mobId: string): void {
    const mob = this.spawnedMobs.get(mobId);
    if (mob) {
      this.scene.remove(mob.mesh);
      mob.mesh.geometry.dispose();
      (mob.mesh.material as THREE.Material).dispose();
      this.spawnedMobs.delete(mobId);
    }
  }
  
  getMob(mobId: string): Mob | undefined {
    return this.spawnedMobs.get(mobId);
  }
  
  getAllMobs(): Mob[] {
    return Array.from(this.spawnedMobs.values());
  }
  
  getMobCount(): number {
    return this.spawnedMobs.size;
  }
  
  clearAllMobs(): void {
    this.spawnedMobs.forEach((mob, id) => this.removeMob(id));
  }
}
