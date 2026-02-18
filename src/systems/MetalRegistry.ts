/**
 * MetalRegistry - Generates and manages 567+ unique metals/ores
 */
export class MetalRegistry {
  private static metals: Map<number, Metal> = new Map();
  private static initialized = false;
  
  // Base metal types with unique properties
  private static baseMetals = [
    'Iron', 'Copper', 'Gold', 'Silver', 'Platinum', 'Titanium', 'Aluminum',
    'Zinc', 'Tin', 'Lead', 'Nickel', 'Cobalt', 'Chromium', 'Manganese',
    'Tungsten', 'Molybdenum', 'Vanadium', 'Uranium', 'Thorium', 'Plutonium'
  ];
  
  private static prefixes = [
    'Ancient', 'Mystic', 'Dark', 'Light', 'Pure', 'Raw', 'Refined', 'Celestial',
    'Infernal', 'Frozen', 'Blazing', 'Crystalline', 'Prismatic', 'Ethereal',
    'Corrupted', 'Blessed', 'Cursed', 'Radiant', 'Shadow', 'Lunar', 'Solar',
    'Volcanic', 'Oceanic', 'Void', 'Astral', 'Cosmic', 'Quantum', 'Plasma',
    'Neon', 'Spectral'
  ];
  
  private static suffixes = [
    'Ore', 'Crystal', 'Shard', 'Ingot', 'Nugget', 'Dust', 'Chunk', 'Vein',
    'Deposit', 'Cluster', 'Fragment', 'Essence', 'Core', 'Bead'
  ];
  
  /**
   * Initialize all metals
   */
  static init(): void {
    if (this.initialized) return;
    
    let metalId = 100; // Start metals at ID 100
    
    // Generate base metals
    this.baseMetals.forEach(base => {
      this.createMetal(metalId++, base, this.generateColor(metalId));
    });
    
    // Generate prefixed variations
    for (const prefix of this.prefixes) {
      for (const base of this.baseMetals) {
        const name = `${prefix} ${base}`;
        this.createMetal(metalId++, name, this.generateColor(metalId));
      }
    }
    
    // Generate suffixed variations
    for (const base of this.baseMetals) {
      for (const suffix of this.suffixes) {
        const name = `${base} ${suffix}`;
        this.createMetal(metalId++, name, this.generateColor(metalId));
      }
    }
    
    // Generate combinations (prefix + base + suffix)
    for (let i = 0; i < 5; i++) {
      for (let j = 0; j < 10; j++) {
        const prefix = this.prefixes[i];
        const base = this.baseMetals[j];
        const suffix = this.suffixes[j % this.suffixes.length];
        const name = `${prefix} ${base} ${suffix}`;
        this.createMetal(metalId++, name, this.generateColor(metalId));
      }
    }
    
    console.log(`✨ Generated ${this.metals.size} unique metals/ores!`);
    this.initialized = true;
  }
  
  /**
   * Create a metal entry
   */
  private static createMetal(id: number, name: string, color: string): void {
    const rarity = this.calculateRarity(id);
    const hardness = Math.floor(Math.random() * 100) + 1;
    
    this.metals.set(id, {
      id,
      name,
      color,
      rarity,
      hardness,
      value: rarity * hardness
    });
  }
  
  /**
   * Generate unique color for metal
   */
  private static generateColor(id: number): string {
    // Use ID as seed for consistent colors
    const hue = (id * 137.508) % 360; // Golden angle for distribution
    const saturation = 50 + (id % 50);
    const lightness = 40 + (id % 40);
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  }
  
  /**
   * Calculate rarity (1-10, higher is rarer)
   */
  private static calculateRarity(id: number): number {
    // Base metals are common, exotic combinations are rare
    if (id < 120) return 1 + (id % 3);
    if (id < 200) return 3 + (id % 4);
    if (id < 400) return 5 + (id % 4);
    return 7 + (id % 3);
  }
  
  /**
   * Get metal by ID
   */
  static getMetal(id: number): Metal | undefined {
    return this.metals.get(id);
  }
  
  /**
   * Get all metal IDs
   */
  static getAllMetalIds(): number[] {
    return Array.from(this.metals.keys());
  }
  
  /**
   * Get random metal ID based on rarity
   */
  static getRandomMetalId(): number {
    const roll = Math.random() * 100;
    
    const metalIds = this.getAllMetalIds();
    const availableMetals = metalIds.filter(id => {
      const metal = this.getMetal(id)!;
      return roll >= (metal.rarity - 1) * 10;
    });
    
    if (availableMetals.length === 0) {
      return metalIds[0];
    }
    
    return availableMetals[Math.floor(Math.random() * availableMetals.length)];
  }
  
  /**
   * Check if a block ID is a metal
   */
  static isMetal(blockId: number): boolean {
    return this.metals.has(blockId);
  }
  
  /**
   * Get metal count
   */
  static getMetalCount(): number {
    return this.metals.size;
  }
}

export interface Metal {
  id: number;
  name: string;
  color: string;
  rarity: number; // 1-10
  hardness: number; // 1-100
  value: number;
}
