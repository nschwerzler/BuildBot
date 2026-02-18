/**
 * Thirst System - Adds thirst as a survival mechanic
 * Player starts thirsty near an abandoned house (from the book lore)
 * Must find water sources to drink
 */

export interface ThirstState {
  current: number;
  max: number;
  drainRate: number; // per minute
}

export class ThirstSystem {
  private thirst: ThirstState;
  private isDying: boolean = false;
  
  private readonly BASE_DRAIN_RATE = 0.8; // per minute  
  private readonly SPRINT_DRAIN_MULT = 2.0;
  private readonly DESERT_DRAIN_MULT = 1.5;
  
  private listeners: {
    onThirstChange: Array<(thirst: ThirstState) => void>;
    onDehydration: Array<() => void>;
  } = {
    onThirstChange: [],
    onDehydration: []
  };
  
  constructor(startThirst: number = 5, maxThirst: number = 20) {
    // Start low on thirst (player starts thirsty per book lore)
    this.thirst = {
      current: startThirst,
      max: maxThirst,
      drainRate: this.BASE_DRAIN_RATE
    };
    
    console.log('Thirst System initialized (starting thirsty!)');
  }
  
  update(deltaTime: number, isSprinting: boolean = false, inDesert: boolean = false): void {
    // Calculate drain rate with modifiers
    let drain = (this.BASE_DRAIN_RATE / 60) * deltaTime;
    
    if (isSprinting) drain *= this.SPRINT_DRAIN_MULT;
    if (inDesert) drain *= this.DESERT_DRAIN_MULT;
    
    this.thirst.current = Math.max(0, this.thirst.current - drain);
    
    // Dehydration damage
    if (this.thirst.current <= 0 && !this.isDying) {
      this.isDying = true;
      this.listeners.onDehydration.forEach(cb => cb());
    } else if (this.thirst.current > 0) {
      this.isDying = false;
    }
    
    // Periodic UI update
    this.listeners.onThirstChange.forEach(cb => cb(this.thirst));
  }
  
  drink(amount: number): void {
    const old = this.thirst.current;
    this.thirst.current = Math.min(this.thirst.max, this.thirst.current + amount);
    
    if (this.thirst.current > old) {
      console.log(`💧 Drank water: +${(this.thirst.current - old).toFixed(1)} thirst`);
      this.listeners.onThirstChange.forEach(cb => cb(this.thirst));
    }
  }
  
  getThirst(): ThirstState {
    return { ...this.thirst };
  }
  
  getThirstPercent(): number {
    return (this.thirst.current / this.thirst.max) * 100;
  }
  
  isDehydrated(): boolean {
    return this.thirst.current <= 0;
  }
  
  isLowThirst(): boolean {
    return this.thirst.current <= 4;
  }
  
  onThirstChange(callback: (thirst: ThirstState) => void): void {
    this.listeners.onThirstChange.push(callback);
  }
  
  onDehydration(callback: () => void): void {
    this.listeners.onDehydration.push(callback);
  }
  
  // Serialize
  serialize(): object {
    return { current: this.thirst.current };
  }
  
  deserialize(data: any): void {
    if (data.current !== undefined) this.thirst.current = data.current;
  }
}
