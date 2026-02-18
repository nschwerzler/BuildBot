/**
 * Aetherian Abilities System
 * Based on Cube Kid's book series: Diary of an 8-Bit Warrior, 
 * Tales of an 8-Bit Kitten (Nether Kitten), and Diary of a Minecraft Wolf
 * 
 * Features abilities from the Aetherian universe including:
 * - Eeebs' Nether Kitten abilities (Obsidian Fur, Ghast Fireball, Creep, Flame Breath, etc.)
 * - Breeze's Dusk Elf abilities (Dash, Leap, Dual Wield, Smoke Bomb, Quietus)
 * - Runt's Warrior abilities (Dual Wield, Analyze Monster, Smite, Parry)
 * - Wolf pack abilities
 */

export type MobChoice = 'cat' | 'wolf' | 'bunny';

export interface AetherianAbility {
  id: string;
  name: string;
  description: string;
  school: 'physical' | 'magic' | 'nether' | 'passive';
  manaCost: number;
  cooldown: number; // seconds
  currentCooldown: number;
  level: number;
  maxLevel: number;
  unlockedAt: number; // player level
  isUltimate: boolean;
  mobSpecific?: MobChoice; // only available to certain mob types
}

export interface AbilityEffect {
  type: 'damage' | 'heal' | 'buff' | 'debuff' | 'movement' | 'stealth' | 'projectile';
  value: number;
  duration?: number;
  radius?: number;
}

export interface PlayerProgression {
  level: number;
  xp: number;
  xpToNext: number;
  mobType: MobChoice;
  isTransformed: boolean; // has taken the human-form potion
  attributes: {
    strength: number;
    agility: number;
    vitality: number;
    intelligence: number;
    devotion: number;
  };
  skills: {
    combat: number;
    mining: number;
    crafting: number;
    stealth: number;
    scouting: number;
    fishing: number;
    farming: number;
    building: number;
  };
  mana: number;
  maxMana: number;
  manaRegen: number;
}

export class AetherianAbilities {
  private abilities: Map<string, AetherianAbility> = new Map();
  private unlockedAbilities: Set<string> = new Set();
  private progression: PlayerProgression;
  private activeBuffs: Map<string, { effect: AbilityEffect; remaining: number }> = new Map();
  
  // Choice-based ability system
  private abilitiesLocked: boolean = true; // Start locked, unlock after sleeping
  private pendingChoices: number = 0;     // How many ability choices available
  
  // Mob-specific bonuses
  private mobBonuses: Record<MobChoice, {
    speedMult: number;
    damageMult: number;
    stealthMult: number;
    fallDamageMult: number;
    nightVision: boolean;
    creeperRepel: boolean;
    packBonus: boolean;
    wallClimb: boolean;
    description: string;
    startAbilities: string[];
  }> = {
    cat: {
      speedMult: 1.2,
      damageMult: 0.8,
      stealthMult: 1.5,
      fallDamageMult: 0.0, // Cats land on feet - no fall damage!
      nightVision: true,
      creeperRepel: true, // Creepers flee from cats
      packBonus: false,
      wallClimb: true, // Aspect of the Spider from Eeebs
      description: 'Nether Kitten - Like Eeebs! Stealthy, agile, no fall damage, creepers flee from you. Wall climbing via Aspect of the Spider.',
      startAbilities: ['obsidian_fur', 'creep', 'aspect_spider', 'fire_affinity', 'higher_intelligence']
    },
    wolf: {
      speedMult: 1.3,
      damageMult: 1.3,
      stealthMult: 0.8,
      fallDamageMult: 0.8,
      nightVision: false,
      creeperRepel: false,
      packBonus: true, // Bonus damage/defense near tamed wolves
      wallClimb: false,
      description: 'Loyal Wolf - Strong and fast! Pack bonus with nearby wolves, skeleton hunter, howl to alert.',
      startAbilities: ['pack_beast', 'dash', 'howl', 'skeleton_hunter']
    },
    bunny: {
      speedMult: 1.5,
      damageMult: 0.6,
      stealthMult: 1.2,
      fallDamageMult: 0.3,
      nightVision: false,
      creeperRepel: false,
      packBonus: false,
      wallClimb: false,
      description: 'Swift Bunny - Fastest mob! Great jumps, reduced fall damage, evasive.',
      startAbilities: ['leap', 'dash', 'scout', 'evasion']
    }
  };
  
  constructor(mobType: MobChoice) {
    this.progression = {
      level: 1,
      xp: 0,
      xpToNext: 100,
      mobType,
      isTransformed: false,
      attributes: {
        strength: mobType === 'wolf' ? 8 : mobType === 'cat' ? 5 : 3,
        agility: mobType === 'bunny' ? 10 : mobType === 'cat' ? 8 : 5,
        vitality: mobType === 'wolf' ? 7 : 5,
        intelligence: mobType === 'cat' ? 10 : 5, // Eeebs has Higher Intelligence V
        devotion: 3
      },
      skills: {
        combat: mobType === 'wolf' ? 15 : mobType === 'cat' ? 10 : 5,
        mining: 1,
        crafting: 1,
        stealth: mobType === 'cat' ? 20 : mobType === 'bunny' ? 15 : 5,
        scouting: mobType === 'cat' ? 18 : mobType === 'bunny' ? 10 : 8,
        fishing: mobType === 'cat' ? 5 : 1,
        farming: 1,
        building: 1
      },
      mana: 50,
      maxMana: 50 + (mobType === 'cat' ? 30 : 0), // Cats get more mana (Nether powers)
      manaRegen: 2
    };
    
    this.initializeAbilities();
    
    // DON'T unlock starting abilities yet - they come via choice system
    // Passives (speed, fall damage, etc.) still work via mobBonuses
    
    console.log(`Aetherian Abilities initialized for ${mobType} (abilities locked until first sleep)`);
  }
  
  private initializeAbilities(): void {
    // === NETHER KITTEN (Eeebs) ABILITIES ===
    this.addAbility({
      id: 'obsidian_fur',
      name: 'Obsidian Fur',
      description: 'Makes your fur extremely dense and tough, increasing armor. Critical hits deal 5% less damage per level.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 1,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'creep',
      name: 'Creep',
      description: 'Move more quietly. Standing still makes you nearly invisible at high levels.',
      school: 'nether',
      manaCost: 5,
      cooldown: 8,
      currentCooldown: 0,
      level: 2,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'aspect_spider',
      name: 'Aspect of the Spider',
      description: 'Move up the side of ANY block as if it had a ladder attached.',
      school: 'nether',
      manaCost: 10,
      cooldown: 15,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'ghast_fireball',
      name: 'Ghast Fireball',
      description: 'Shoot a fireball! Copied from Ghasts in the Nether. Higher levels increase damage and speed.',
      school: 'nether',
      manaCost: 20,
      cooldown: 5,
      currentCooldown: 0,
      level: 1,
      maxLevel: 10,
      unlockedAt: 5,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'fire_affinity',
      name: 'Fire Affinity',
      description: 'Increases fire resistance. Complete immunity at level 10.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 10,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'higher_intelligence',
      name: 'Higher Intelligence',
      description: 'Increased AI and awareness. Better threat detection and combat strategy.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 5,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'pigman_frenzy',
      name: 'Pigman Frenzy',
      description: 'Increases movement, sprinting, and swimming speed. Ignores slowing effects at high levels.',
      school: 'nether',
      manaCost: 15,
      cooldown: 20,
      currentCooldown: 0,
      level: 3,
      maxLevel: 10,
      unlockedAt: 8,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'tail_sweep',
      name: 'Tail Sweep',
      description: 'Sweep your tail across the ground, damaging all nearby enemies.',
      school: 'physical',
      manaCost: 12,
      cooldown: 6,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 10,
      isUltimate: false,
      mobSpecific: 'cat'
    });
    
    // Cat Ultimates
    this.addAbility({
      id: 'flame_breath',
      name: 'Flame Breath',
      description: 'Creates a stream of fire to damage enemies. Grows weaker the longer it is used. Copied from Wyrm.',
      school: 'nether',
      manaCost: 40,
      cooldown: 60,
      currentCooldown: 0,
      level: 1,
      maxLevel: 3,
      unlockedAt: 15,
      isUltimate: true,
      mobSpecific: 'cat'
    });
    
    this.addAbility({
      id: 'rage_of_ao',
      name: 'Rage of Ao',
      description: 'A flying kick launching you forward 10 blocks! First enemy hit takes 20 damage and is sent sailing. Copied from Goblin.',
      school: 'physical',
      manaCost: 35,
      cooldown: 120,
      currentCooldown: 0,
      level: 1,
      maxLevel: 3,
      unlockedAt: 20,
      isUltimate: true,
      mobSpecific: 'cat'
    });
    
    // === WOLF ABILITIES ===
    this.addAbility({
      id: 'pack_beast',
      name: 'Pack Beast',
      description: 'Adds 1 additional inventory slot per level. Bonus stats near other wolves.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 2,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'wolf'
    });
    
    this.addAbility({
      id: 'howl',
      name: 'Howl',
      description: 'Alert nearby friendly mobs and scare weak enemies. Buffs allies with courage.',
      school: 'physical',
      manaCost: 10,
      cooldown: 30,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'wolf'
    });
    
    this.addAbility({
      id: 'skeleton_hunter',
      name: 'Skeleton Hunter',
      description: 'Deal 2x damage to skeletons. Wolves naturally chase skeletons.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'wolf'
    });
    
    this.addAbility({
      id: 'chomp',
      name: 'Chomp',
      description: 'Grab enemy in your jaws, dealing heavy damage and brief stun.',
      school: 'physical',
      manaCost: 15,
      cooldown: 8,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 8,
      isUltimate: false,
      mobSpecific: 'wolf'
    });
    
    this.addAbility({
      id: 'unholy_strength',
      name: 'Unholy Strength',
      description: 'Grants a massive attack damage buff for 15 seconds.',
      school: 'physical',
      manaCost: 30,
      cooldown: 90,
      currentCooldown: 0,
      level: 1,
      maxLevel: 3,
      unlockedAt: 15,
      isUltimate: true,
      mobSpecific: 'wolf'
    });
    
    // === BUNNY ABILITIES ===
    this.addAbility({
      id: 'evasion',
      name: 'Evasion',
      description: 'Chance to dodge incoming attacks. 10% per level.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 2,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false,
      mobSpecific: 'bunny'
    });
    
    this.addAbility({
      id: 'burrow',
      name: 'Burrow',
      description: 'Dig into the ground to hide and regenerate health.',
      school: 'physical',
      manaCost: 15,
      cooldown: 30,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 5,
      isUltimate: false,
      mobSpecific: 'bunny'
    });
    
    this.addAbility({
      id: 'verdant_bloom',
      name: 'Verdant Bloom',
      description: 'Makes nearby plants grow faster. Grass slightly slows enemies.',
      school: 'magic',
      manaCost: 20,
      cooldown: 45,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 10,
      isUltimate: false,
      mobSpecific: 'bunny'
    });
    
    // === SHARED ABILITIES (all mobs can learn after transformation) ===
    this.addAbility({
      id: 'dash',
      name: 'Dash',
      description: 'Move 1+1 blocks at incredible speed. Instant cast.',
      school: 'physical',
      manaCost: 8,
      cooldown: 3,
      currentCooldown: 0,
      level: 1,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'leap',
      name: 'Leap',
      description: 'Make a giant leap in the direction you\'re facing. Higher levels increase distance.',
      school: 'physical',
      manaCost: 10,
      cooldown: 5,
      currentCooldown: 0,
      level: 1,
      maxLevel: 10,
      unlockedAt: 1,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'scout',
      name: 'Scout',
      description: 'Notice hidden elements. See hidden traps, invisible mobs, and distant enemies.',
      school: 'passive',
      manaCost: 0,
      cooldown: 0,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 1,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'analyze_monster',
      name: 'Analyze Monster',
      description: 'Discern hidden properties of any monster. Shows health, weaknesses, inventory at higher levels.',
      school: 'passive',
      manaCost: 5,
      cooldown: 10,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 3,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'dual_wield',
      name: 'Dual Wield',
      description: 'Wield two weapons at once. Uses 10% of combat skill per level.',
      school: 'physical',
      manaCost: 5,
      cooldown: 0,
      currentCooldown: 0,
      level: 1,
      maxLevel: 10,
      unlockedAt: 10,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'smoke_bomb',
      name: 'Smoke Bomb',
      description: 'Creates a cloud of smoke as a distraction, then turns you invisible. Breeze\'s signature move.',
      school: 'physical',
      manaCost: 20,
      cooldown: 30,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 12,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'parry',
      name: 'Parry',
      description: 'Reduces damage while blocking by 10% per level. 20% chance to stun attacker.',
      school: 'physical',
      manaCost: 3,
      cooldown: 1,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 5,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'smite',
      name: 'Smite',
      description: 'Deal extra damage to undead mobs (zombies, skeletons, wither skeletons).',
      school: 'magic',
      manaCost: 15,
      cooldown: 10,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 8,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'air_dash',
      name: 'Air Dash',
      description: 'Improved Dash that uses air mana. Can be used mid-air!',
      school: 'magic',
      manaCost: 15,
      cooldown: 5,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 15,
      isUltimate: false
    });
    
    this.addAbility({
      id: 'telekinesis',
      name: 'Telekinesis',
      description: 'Move blocks and objects with your mind.',
      school: 'magic',
      manaCost: 25,
      cooldown: 15,
      currentCooldown: 0,
      level: 1,
      maxLevel: 5,
      unlockedAt: 20,
      isUltimate: false
    });
    
    // Ultimate shared abilities
    this.addAbility({
      id: 'overblade',
      name: 'Overblade',
      description: 'Swing your weapon overhead and slam into target for 25 damage. Ignores stoneskin.',
      school: 'physical',
      manaCost: 30,
      cooldown: 120,
      currentCooldown: 0,
      level: 1,
      maxLevel: 3,
      unlockedAt: 25,
      isUltimate: true
    });
    
    console.log(`Loaded ${this.abilities.size} Aetherian abilities`);
  }
  
  private addAbility(ability: AetherianAbility): void {
    this.abilities.set(ability.id, ability);
  }
  
  // === XP & LEVELING ===
  
  addXP(amount: number): { leveledUp: boolean; newLevel: number; choiceAvailable: boolean } {
    this.progression.xp += amount;
    let leveledUp = false;
    let choiceAvailable = false;
    
    while (this.progression.xp >= this.progression.xpToNext) {
      this.progression.xp -= this.progression.xpToNext;
      this.progression.level++;
      this.progression.xpToNext = Math.floor(this.progression.xpToNext * 1.5);
      leveledUp = true;
      
      // Increase max mana on level up
      this.progression.maxMana += 5;
      this.progression.mana = this.progression.maxMana;
      
      // Offer ability choice every 3 levels (if abilities unlocked)
      if (!this.abilitiesLocked && this.progression.level % 3 === 0) {
        this.pendingChoices++;
        choiceAvailable = true;
      }
      
      console.log(`Level Up! Now level ${this.progression.level}`);
    }
    
    return { leveledUp, newLevel: this.progression.level, choiceAvailable };
  }
  
  private checkAbilityUnlocks(): void {
    // Kept for transform() but no longer auto-called from addXP
    this.abilities.forEach((ability, id) => {
      if (this.unlockedAbilities.has(id)) return;
      if (ability.unlockedAt > this.progression.level) return;
      if (ability.mobSpecific && ability.mobSpecific !== this.progression.mobType) return;
      
      // Only unlock non-mob-specific abilities after transformation
      if (!ability.mobSpecific && !this.progression.isTransformed && ability.unlockedAt > 5) return;
      
      this.unlockedAbilities.add(id);
      console.log(`New ability unlocked: ${ability.name}!`);
    });
  }
  
  // === CHOICE-BASED ABILITY SYSTEM ===
  
  /** Unlock the ability system (called after first sleep in bed) */
  unlockAbilitySystem(): void {
    this.abilitiesLocked = false;
    this.pendingChoices = 1; // Give first choice immediately
  }
  
  isAbilitySystemLocked(): boolean {
    return this.abilitiesLocked;
  }
  
  hasPendingChoice(): boolean {
    return this.pendingChoices > 0 && !this.abilitiesLocked;
  }
  
  /** Get N random abilities available for choice (not yet unlocked, matching mob type & level) */
  getAbilityChoices(count: number = 3): AetherianAbility[] {
    const available: AetherianAbility[] = [];
    
    this.abilities.forEach((ability, id) => {
      if (this.unlockedAbilities.has(id)) return;
      if (ability.mobSpecific && ability.mobSpecific !== this.progression.mobType) return;
      if (!ability.mobSpecific && !this.progression.isTransformed && ability.unlockedAt > 5) return;
      if (ability.isUltimate && this.progression.level < 15) return;
      available.push(ability);
    });
    
    // Shuffle and take N
    for (let i = available.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [available[i], available[j]] = [available[j], available[i]];
    }
    
    return available.slice(0, count);
  }
  
  /** Manually unlock a specific ability by choice */
  chooseAbility(abilityId: string): boolean {
    if (this.pendingChoices <= 0 || this.abilitiesLocked) return false;
    
    const ability = this.abilities.get(abilityId);
    if (!ability || this.unlockedAbilities.has(abilityId)) return false;
    
    this.unlockedAbilities.add(abilityId);
    this.pendingChoices--;
    console.log(`Ability chosen: ${ability.name}!`);
    return true;
  }
  
  // === ABILITY USAGE ===
  
  useAbility(abilityId: string): AbilityEffect | null {
    const ability = this.abilities.get(abilityId);
    if (!ability) return null;
    if (!this.unlockedAbilities.has(abilityId)) return null;
    if (ability.currentCooldown > 0) return null;
    if (this.progression.mana < ability.manaCost) return null;
    
    // Spend mana
    this.progression.mana -= ability.manaCost;
    ability.currentCooldown = ability.cooldown;
    
    // Calculate effect based on ability
    return this.calculateEffect(ability);
  }
  
  private calculateEffect(ability: AetherianAbility): AbilityEffect {
    switch (ability.id) {
      case 'ghast_fireball':
        return { type: 'projectile', value: 5 + ability.level * 2, radius: 3 };
      case 'flame_breath':
        return { type: 'damage', value: 8 + ability.level * 4, duration: 5, radius: 5 };
      case 'rage_of_ao':
        return { type: 'damage', value: 20 + ability.level * 5 };
      case 'dash':
      case 'air_dash':
        return { type: 'movement', value: 2 + ability.level };
      case 'leap':
        return { type: 'movement', value: 5 + ability.level * 2 };
      case 'creep':
        return { type: 'stealth', value: ability.level * 10, duration: 10 + ability.level * 2 };
      case 'smoke_bomb':
        return { type: 'stealth', value: 100, duration: 5 };
      case 'howl':
        return { type: 'buff', value: 20, duration: 15, radius: 20 };
      case 'chomp':
        return { type: 'damage', value: 8 + ability.level * 3 };
      case 'unholy_strength':
        return { type: 'buff', value: 50, duration: 15 };
      case 'tail_sweep':
        return { type: 'damage', value: 4 + ability.level * 2, radius: 3 };
      case 'smite':
        return { type: 'damage', value: 10 + ability.level * 3 };
      case 'overblade':
        return { type: 'damage', value: 25 + ability.level * 10 };
      case 'parry':
        return { type: 'buff', value: 10 * ability.level, duration: 2 };
      case 'burrow':
        return { type: 'heal', value: 5, duration: 10 };
      case 'verdant_bloom':
        return { type: 'debuff', value: 20, duration: 30, radius: 10 };
      default:
        return { type: 'buff', value: ability.level };
    }
  }
  
  update(deltaTime: number): void {
    // Update cooldowns
    this.abilities.forEach(ability => {
      if (ability.currentCooldown > 0) {
        ability.currentCooldown = Math.max(0, ability.currentCooldown - deltaTime);
      }
    });
    
    // Regenerate mana
    if (this.progression.mana < this.progression.maxMana) {
      this.progression.mana = Math.min(
        this.progression.maxMana,
        this.progression.mana + this.progression.manaRegen * deltaTime
      );
    }
    
    // Update active buffs
    const expiredBuffs: string[] = [];
    this.activeBuffs.forEach((buff, id) => {
      buff.remaining -= deltaTime;
      if (buff.remaining <= 0) expiredBuffs.push(id);
    });
    expiredBuffs.forEach(id => this.activeBuffs.delete(id));
    
    // Train skills passively based on actions
    this.progression.skills.combat += deltaTime * 0.001;
  }
  
  // === TRANSFORMATION ===
  
  transform(): void {
    this.progression.isTransformed = true;
    
    // Boost all attributes on transformation (like Eeebs' Wildshape potion)
    this.progression.attributes.strength += 3;
    this.progression.attributes.agility += 2;
    this.progression.attributes.vitality += 3;
    this.progression.attributes.intelligence += 2;
    this.progression.maxMana += 20;
    this.progression.mana = this.progression.maxMana;
    
    // Unlock human-form abilities
    this.checkAbilityUnlocks();
    
    console.log('Transformation complete! You are now in human form.');
  }
  
  // === GETTERS ===
  
  getMobBonuses(): typeof this.mobBonuses[MobChoice] {
    return this.mobBonuses[this.progression.mobType];
  }
  
  getProgression(): PlayerProgression {
    return { ...this.progression };
  }
  
  getUnlockedAbilities(): AetherianAbility[] {
    return Array.from(this.unlockedAbilities)
      .map(id => this.abilities.get(id))
      .filter((a): a is AetherianAbility => a !== undefined);
  }
  
  getAbility(id: string): AetherianAbility | undefined {
    return this.abilities.get(id);
  }
  
  isAbilityUnlocked(id: string): boolean {
    return this.unlockedAbilities.has(id);
  }
  
  isAbilityReady(id: string): boolean {
    const ability = this.abilities.get(id);
    if (!ability) return false;
    return ability.currentCooldown <= 0 && this.progression.mana >= ability.manaCost;
  }
  
  getMana(): number {
    return this.progression.mana;
  }
  
  getMaxMana(): number {
    return this.progression.maxMana;
  }
  
  getLevel(): number {
    return this.progression.level;
  }
  
  getMobType(): MobChoice {
    return this.progression.mobType;
  }
  
  isTransformed(): boolean {
    return this.progression.isTransformed;
  }
  
  getSpeedMultiplier(): number {
    let mult = this.mobBonuses[this.progression.mobType].speedMult;
    
    // Pigman Frenzy buff
    if (this.activeBuffs.has('pigman_frenzy')) {
      mult *= 1.3;
    }
    
    return mult;
  }
  
  getDamageMultiplier(): number {
    let mult = this.mobBonuses[this.progression.mobType].damageMult;
    
    // Unholy Strength buff  
    if (this.activeBuffs.has('unholy_strength')) {
      mult *= 1.5;
    }
    
    // Transformed bonus
    if (this.progression.isTransformed) {
      mult *= 1.2;
    }
    
    return mult;
  }
  
  getArmorBonus(): number {
    let armor = 0;
    
    // Obsidian Fur
    if (this.unlockedAbilities.has('obsidian_fur')) {
      const ability = this.abilities.get('obsidian_fur')!;
      armor += ability.level * 2;
    }
    
    return armor;
  }
  
  canEvade(): boolean {
    if (!this.unlockedAbilities.has('evasion')) return false;
    const ability = this.abilities.get('evasion')!;
    return Math.random() < (ability.level * 0.1);
  }
  
  getStealthLevel(): number {
    let stealth = this.mobBonuses[this.progression.mobType].stealthMult;
    
    if (this.activeBuffs.has('creep')) {
      stealth *= 2;
    }
    if (this.activeBuffs.has('smoke_bomb')) {
      stealth *= 10; // Nearly invisible
    }
    
    return stealth;
  }
  
  activateBuff(abilityId: string, effect: AbilityEffect): void {
    if (effect.duration) {
      this.activeBuffs.set(abilityId, { effect, remaining: effect.duration });
    }
  }
  
  // Skill training
  trainSkill(skill: keyof PlayerProgression['skills'], amount: number): void {
    this.progression.skills[skill] += amount;
  }
  
  // Serialize for save/load
  serialize(): object {
    return {
      progression: this.progression,
      unlockedAbilities: Array.from(this.unlockedAbilities),
      cooldowns: Array.from(this.abilities.entries())
        .map(([id, a]) => ({ id, cooldown: a.currentCooldown }))
    };
  }
  
  deserialize(data: any): void {
    if (data.progression) {
      Object.assign(this.progression, data.progression);
    }
    if (data.unlockedAbilities) {
      this.unlockedAbilities = new Set(data.unlockedAbilities);
    }
    if (data.cooldowns) {
      data.cooldowns.forEach((cd: any) => {
        const ability = this.abilities.get(cd.id);
        if (ability) ability.currentCooldown = cd.cooldown;
      });
    }
  }
}
