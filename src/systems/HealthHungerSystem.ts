/**
 * Health and Hunger System - Manages player survival mechanics
 */

export interface HealthState {
  current: number;
  max: number;
  regeneration: number;
}

export interface HungerState {
  current: number;
  max: number;
  saturation: number;
  exhaustion: number;
}

export interface StatusEffect {
  id: string;
  name: string;
  duration: number;
  type: 'positive' | 'negative';
  effect: {
    healthRegen?: number;
    hungerDrain?: number;
    speedMultiplier?: number;
    damageMultiplier?: number;
  };
}

export class HealthHungerSystem {
  private health: HealthState;
  private hunger: HungerState;
  private statusEffects: Map<string, StatusEffect> = new Map();
  private isDead: boolean = false;
  
  private readonly HUNGER_DRAIN_RATE = 0.5; // per minute
  private readonly HEALTH_REGEN_RATE = 0.5; // per second when full hunger
  private readonly EXHAUSTION_THRESHOLD = 4.0;
  
  private listeners: {
    onDeath: Array<() => void>;
    onHealthChange: Array<(health: HealthState) => void>;
    onHungerChange: Array<(hunger: HungerState) => void>;
    onStatusEffect: Array<(effect: StatusEffect) => void>;
  } = {
    onDeath: [],
    onHealthChange: [],
    onHungerChange: [],
    onStatusEffect: []
  };
  
  constructor(maxHealth: number = 20, maxHunger: number = 20) {
    this.health = {
      current: maxHealth,
      max: maxHealth,
      regeneration: 0
    };
    
    this.hunger = {
      current: maxHunger,
      max: maxHunger,
      saturation: 5,
      exhaustion: 0
    };
    
    console.log('Health & Hunger System initialized');
  }
  
  update(deltaTime: number): void {
    if (this.isDead) return;
    
    // Update hunger
    this.updateHunger(deltaTime);
    
    // Update health
    this.updateHealth(deltaTime);
    
    // Update status effects
    this.updateStatusEffects(deltaTime);
  }
  
  private updateHunger(deltaTime: number): void {
    // Saturation drains first
    if (this.hunger.saturation > 0) {
      this.hunger.saturation = Math.max(0, this.hunger.saturation - deltaTime * 0.1);
    }
    
    // Convert exhaustion to hunger loss
    if (this.hunger.exhaustion >= this.EXHAUSTION_THRESHOLD) {
      this.hunger.current = Math.max(0, this.hunger.current - 1);
      this.hunger.exhaustion = 0;
      this.notifyHungerChange();
    }
    
    // Passive hunger drain
    this.hunger.exhaustion += (this.HUNGER_DRAIN_RATE / 60) * deltaTime;
    
    // Low hunger causes damage
    if (this.hunger.current === 0) {
      this.damage(0.5 * deltaTime, 'starvation');
    }
  }
  
  private updateHealth(deltaTime: number): void {
    if (this.health.current >= this.health.max) return;
    
    // Regenerate health when hunger is high
    if (this.hunger.current >= 18) {
      const baseRegen = this.HEALTH_REGEN_RATE * deltaTime;
      const effectRegen = this.health.regeneration * deltaTime;
      
      this.heal(baseRegen + effectRegen);
    }
  }
  
  private updateStatusEffects(deltaTime: number): void {
    const effectsToRemove: string[] = [];
    
    this.statusEffects.forEach((effect, id) => {
      effect.duration -= deltaTime;
      
      // Apply effect
      if (effect.effect.healthRegen) {
        this.heal(effect.effect.healthRegen * deltaTime);
      }
      
      if (effect.effect.hungerDrain) {
        this.addExhaustion(effect.effect.hungerDrain * deltaTime);
      }
      
      // Remove expired effects
      if (effect.duration <= 0) {
        effectsToRemove.push(id);
      }
    });
    
    effectsToRemove.forEach(id => {
      const effect = this.statusEffects.get(id);
      if (effect) {
        console.log(`⏱️ Status effect expired: ${effect.name}`);
        this.statusEffects.delete(id);
      }
    });
  }
  
  damage(amount: number, source: string = 'unknown'): void {
    if (this.isDead) return;
    
    this.health.current = Math.max(0, this.health.current - amount);
    console.log(`💔 Took ${amount.toFixed(1)} damage from ${source}`);
    
    this.notifyHealthChange();
    
    if (this.health.current <= 0) {
      this.die();
    }
  }
  
  heal(amount: number): void {
    if (this.isDead) return;
    
    const oldHealth = this.health.current;
    this.health.current = Math.min(this.health.max, this.health.current + amount);
    
    if (this.health.current > oldHealth) {
      this.notifyHealthChange();
    }
  }
  
  eat(foodValue: number, saturationValue: number): void {
    const oldHunger = this.hunger.current;
    
    this.hunger.current = Math.min(this.hunger.max, this.hunger.current + foodValue);
    this.hunger.saturation = Math.min(
      this.hunger.current,
      this.hunger.saturation + saturationValue
    );
    
    if (this.hunger.current > oldHunger) {
      console.log(`🍖 Ate food: +${foodValue} hunger, +${saturationValue} saturation`);
      this.notifyHungerChange();
    }
  }
  
  addExhaustion(amount: number): void {
    this.hunger.exhaustion += amount;
  }
  
  addStatusEffect(effect: StatusEffect): void {
    this.statusEffects.set(effect.id, effect);
    console.log(`✨ Status effect applied: ${effect.name} (${effect.duration}s)`);
    this.listeners.onStatusEffect.forEach(listener => listener(effect));
  }
  
  removeStatusEffect(effectId: string): boolean {
    return this.statusEffects.delete(effectId);
  }
  
  hasStatusEffect(effectId: string): boolean {
    return this.statusEffects.has(effectId);
  }
  
  private die(): void {
    this.isDead = true;
    console.log('☠️ You died!');
    this.listeners.onDeath.forEach(listener => listener());
  }
  
  respawn(): void {
    this.isDead = false;
    this.health.current = this.health.max;
    this.hunger.current = this.hunger.max;
    this.hunger.saturation = 5;
    this.hunger.exhaustion = 0;
    this.statusEffects.clear();
    
    console.log('♻️ Respawned');
    this.notifyHealthChange();
    this.notifyHungerChange();
  }
  
  // Exhaustion causes
  addMiningExhaustion(): void {
    this.addExhaustion(0.005);
  }
  
  addJumpExhaustion(): void {
    this.addExhaustion(0.05);
  }
  
  addSprintExhaustion(distance: number): void {
    this.addExhaustion(0.01 * distance);
  }
  
  addSwimmingExhaustion(distance: number): void {
    this.addExhaustion(0.01 * distance);
  }
  
  // Getters
  getHealth(): HealthState {
    return { ...this.health };
  }
  
  getHunger(): HungerState {
    return { ...this.hunger };
  }
  
  getHealthPercent(): number {
    return (this.health.current / this.health.max) * 100;
  }
  
  getHungerPercent(): number {
    return (this.hunger.current / this.hunger.max) * 100;
  }
  
  isAlive(): boolean {
    return !this.isDead;
  }
  
  getStatusEffects(): StatusEffect[] {
    return Array.from(this.statusEffects.values());
  }
  
  // Event listeners
  onDeath(callback: () => void): void {
    this.listeners.onDeath.push(callback);
  }
  
  onHealthChange(callback: (health: HealthState) => void): void {
    this.listeners.onHealthChange.push(callback);
  }
  
  onHungerChange(callback: (hunger: HungerState) => void): void {
    this.listeners.onHungerChange.push(callback);
  }
  
  onStatusEffect(callback: (effect: StatusEffect) => void): void {
    this.listeners.onStatusEffect.push(callback);
  }
  
  private notifyHealthChange(): void {
    this.listeners.onHealthChange.forEach(listener => listener(this.health));
  }
  
  private notifyHungerChange(): void {
    this.listeners.onHungerChange.forEach(listener => listener(this.hunger));
  }
}
