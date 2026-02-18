import * as THREE from 'three';
import { MetalRegistry } from './MetalRegistry';

/**
 * Biome System - Defines different terrain types and their characteristics
 */

export interface BiomeType {
  id: string;
  name: string;
  color: THREE.Color;
  surfaceBlock: string;
  subsurfaceBlock: string;
  temperature: number; // -1 to 1
  humidity: number; // 0 to 1
  heightVariation: number; // multiplier for terrain height
  treeChance: number; // 0 to 1
  grassChance: number; // 0 to 1
  rockChance: number; // 0 to 1
  flowerChance: number; // 0 to 1
  oreMultiplier: number; // multiplier for ore generation
  commonMetals: string[]; // more common in this biome
  rareMetals: string[]; // rare finds in this biome
}

export class BiomeSystem {
  private biomes: Map<string, BiomeType> = new Map();
  private metalRegistry: MetalRegistry;
  
  constructor(metalRegistry: MetalRegistry) {
    this.metalRegistry = metalRegistry;
    this.initializeBiomes();
  }
  
  private initializeBiomes(): void {
    // Plains biome
    this.addBiome({
      id: 'plains',
      name: 'Plains',
      color: new THREE.Color(0x7db857),
      surfaceBlock: 'grass',
      subsurfaceBlock: 'dirt',
      temperature: 0.5,
      humidity: 0.5,
      heightVariation: 0.3,
      treeChance: 0.02,
      grassChance: 0.6,
      rockChance: 0.01,
      flowerChance: 0.15,
      oreMultiplier: 1.0,
      commonMetals: ['iron', 'copper', 'tin'],
      rareMetals: ['silver', 'gold']
    });
    
    // Forest biome
    this.addBiome({
      id: 'forest',
      name: 'Forest',
      color: new THREE.Color(0x4d8c3f),
      surfaceBlock: 'grass',
      subsurfaceBlock: 'dirt',
      temperature: 0.4,
      humidity: 0.7,
      heightVariation: 0.5,
      treeChance: 0.15,
      grassChance: 0.8,
      rockChance: 0.02,
      flowerChance: 0.1,
      oreMultiplier: 0.8,
      commonMetals: ['copper', 'bronze'],
      rareMetals: ['emerald', 'jade']
    });
    
    // Desert biome
    this.addBiome({
      id: 'desert',
      name: 'Desert',
      color: new THREE.Color(0xedc9af),
      surfaceBlock: 'sand',
      subsurfaceBlock: 'sandstone',
      temperature: 0.9,
      humidity: 0.1,
      heightVariation: 0.2,
      treeChance: 0.001,
      grassChance: 0.05,
      rockChance: 0.03,
      flowerChance: 0.01,
      oreMultiplier: 1.5,
      commonMetals: ['gold', 'brass'],
      rareMetals: ['diamond', 'ruby']
    });
    
    // Mountains biome
    this.addBiome({
      id: 'mountains',
      name: 'Mountains',
      color: new THREE.Color(0x8b8b8b),
      surfaceBlock: 'stone',
      subsurfaceBlock: 'stone',
      temperature: -0.3,
      humidity: 0.3,
      heightVariation: 2.0,
      treeChance: 0.01,
      grassChance: 0.1,
      rockChance: 0.1,
      flowerChance: 0.02,
      oreMultiplier: 2.0,
      commonMetals: ['iron', 'coal', 'silver'],
      rareMetals: ['platinum', 'mithril', 'adamantite']
    });
    
    // Tundra biome
    this.addBiome({
      id: 'tundra',
      name: 'Tundra',
      color: new THREE.Color(0xdddddd),
      surfaceBlock: 'snow',
      subsurfaceBlock: 'ice',
      temperature: -0.8,
      humidity: 0.2,
      heightVariation: 0.1,
      treeChance: 0.005,
      grassChance: 0.05,
      rockChance: 0.05,
      flowerChance: 0.001,
      oreMultiplier: 0.6,
      commonMetals: ['ice_crystal', 'frost_metal'],
      rareMetals: ['blue_diamond', 'sapphire']
    });
    
    // Swamp biome
    this.addBiome({
      id: 'swamp',
      name: 'Swamp',
      color: new THREE.Color(0x5a7a42),
      surfaceBlock: 'mud',
      subsurfaceBlock: 'clay',
      temperature: 0.6,
      humidity: 0.9,
      heightVariation: 0.1,
      treeChance: 0.08,
      grassChance: 0.9,
      rockChance: 0.01,
      flowerChance: 0.2,
      oreMultiplier: 0.7,
      commonMetals: ['copper', 'tin'],
      rareMetals: ['emerald', 'peridot']
    });
    
    // Volcanic biome
    this.addBiome({
      id: 'volcanic',
      name: 'Volcanic',
      color: new THREE.Color(0x3d1f1f),
      surfaceBlock: 'basalt',
      subsurfaceBlock: 'obsidian',
      temperature: 1.0,
      humidity: 0.0,
      heightVariation: 1.5,
      treeChance: 0.0,
      grassChance: 0.0,
      rockChance: 0.2,
      flowerChance: 0.0,
      oreMultiplier: 3.0,
      commonMetals: ['iron', 'coal'],
      rareMetals: ['diamond', 'ruby', 'obsidian_shard']
    });
    
    // Crystal biome
    this.addBiome({
      id: 'crystal',
      name: 'Crystal Caves',
      color: new THREE.Color(0xb19cd9),
      surfaceBlock: 'crystal',
      subsurfaceBlock: 'crystal',
      temperature: 0.0,
      humidity: 0.5,
      heightVariation: 0.8,
      treeChance: 0.0,
      grassChance: 0.0,
      rockChance: 0.3,
      flowerChance: 0.0,
      oreMultiplier: 5.0,
      commonMetals: ['amethyst', 'quartz'],
      rareMetals: ['diamond', 'sapphire', 'ruby', 'emerald']
    });
    
    // Jungle biome
    this.addBiome({
      id: 'jungle',
      name: 'Jungle',
      color: new THREE.Color(0x2d5016),
      surfaceBlock: 'grass',
      subsurfaceBlock: 'dirt',
      temperature: 0.8,
      humidity: 0.95,
      heightVariation: 0.6,
      treeChance: 0.25,
      grassChance: 0.95,
      rockChance: 0.01,
      flowerChance: 0.3,
      oreMultiplier: 0.9,
      commonMetals: ['copper', 'tin', 'bronze'],
      rareMetals: ['gold', 'emerald', 'jade']
    });
    
    // Mushroom biome
    this.addBiome({
      id: 'mushroom',
      name: 'Mushroom Fields',
      color: new THREE.Color(0xb592c7),
      surfaceBlock: 'mycelium',
      subsurfaceBlock: 'dirt',
      temperature: 0.3,
      humidity: 0.8,
      heightVariation: 0.2,
      treeChance: 0.0,
      grassChance: 0.3,
      rockChance: 0.05,
      flowerChance: 0.4,
      oreMultiplier: 1.2,
      commonMetals: ['copper', 'silver'],
      rareMetals: ['platinum', 'orichalcum']
    });
    
    console.log(`Loaded ${this.biomes.size} biomes`);
  }
  
  private addBiome(biome: BiomeType): void {
    this.biomes.set(biome.id, biome);
  }
  
  getBiome(id: string): BiomeType | undefined {
    return this.biomes.get(id);
  }
  
  /**
   * Determine biome based on temperature and humidity
   */
  getBiomeAtPoint(temperature: number, humidity: number): BiomeType {
    // Temperature and humidity are noise values from -1 to 1
    // Normalize to 0 to 1
    const normTemp = (temperature + 1) / 2;
    const normHumidity = (humidity + 1) / 2;
    
    // Select biome based on conditions
    if (normTemp > 0.8 && normHumidity < 0.2) {
      return this.biomes.get('desert')!;
    } else if (normTemp < 0.2) {
      return this.biomes.get('tundra')!;
    } else if (normTemp > 0.7 && normHumidity > 0.8) {
      return this.biomes.get('jungle')!;
    } else if (normTemp > 0.85 && normHumidity < 0.3) {
      return this.biomes.get('volcanic')!;
    } else if (normHumidity > 0.75 && normTemp > 0.4 && normTemp < 0.7) {
      return this.biomes.get('swamp')!;
    } else if (normHumidity > 0.6 && normTemp > 0.3 && normTemp < 0.6) {
      return this.biomes.get('forest')!;
    } else if (normTemp > 0.6 && normHumidity < 0.6) {
      // Check for special biomes with lower chance
      if (Math.random() < 0.02) {
        return this.biomes.get('crystal')!;
      }
      if (Math.random() < 0.03) {
        return this.biomes.get('mushroom')!;
      }
    }
    
    // Check for mountains based on height variation preference
    if (Math.abs(temperature) > 0.4 && Math.abs(humidity) > 0.3) {
      if (Math.random() < 0.15) {
        return this.biomes.get('mountains')!;
      }
    }
    
    // Default to plains
    return this.biomes.get('plains')!;
  }
  
  getAllBiomes(): BiomeType[] {
    return Array.from(this.biomes.values());
  }
  
  getBiomeCount(): number {
    return this.biomes.size;
  }
}
