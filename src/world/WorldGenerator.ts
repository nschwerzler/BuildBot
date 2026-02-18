/**
 * WorldGenerator - Procedural terrain generation using noise
 */
export class WorldGenerator {
  private seed: number;
  
  constructor(seed: number = Math.random() * 1000000) {
    this.seed = seed;
  }
  
  /**
   * Get terrain height at world coordinates
   */
  getHeight(x: number, z: number): number {
    // Distance from spawn (0, 0)
    const distanceFromSpawn = Math.sqrt(x * x + z * z);
    
    // Flat area around spawn (48 block radius for house/village area)
    if (distanceFromSpawn < 48) {
      return 64; // Flat spawn area
    }
    
    // Smooth transition from flat to gentle hills
    const transitionZone = Math.min((distanceFromSpawn - 48) / 64, 1);
    
    // Gentle noise - small hills only (+/- 8 blocks max)
    const scale1 = 0.015;
    const scale2 = 0.04;
    
    const noise1 = this.noise2D(x * scale1, z * scale1) * 6;
    const noise2 = this.noise2D(x * scale2, z * scale2) * 3;
    
    const terrainHeight = 64 + (noise1 + noise2) * transitionZone;
    
    return Math.floor(Math.max(60, Math.min(80, terrainHeight)));
  }
  
  /**
   * Determine biome at coordinates
   */
  getBiome(x: number, z: number): 'plains' | 'forest' | 'desert' | 'mountains' {
    const temperature = this.noise2D(x * 0.001, z * 0.001);
    const humidity = this.noise2D(x * 0.001 + 1000, z * 0.001 + 1000);
    
    if (temperature > 0.5) {
      return 'desert';
    } else if (humidity > 0.3) {
      return 'forest';
    } else if (temperature < -0.3) {
      return 'mountains';
    } else {
      return 'plains';
    }
  }
  
  /**
   * Determine decoration type
   */
  getDecoration(x: number, z: number): 'tree' | 'rock' | 'grass' | 'flower' | 'none' {
    const decorationNoise = this.noise2D(x * 0.1, z * 0.1 + 5000);
    
    if (decorationNoise > 0.6) {
      return 'tree';
    } else if (decorationNoise > 0.3) {
      return 'rock';
    } else if (decorationNoise > 0) {
      return 'grass';
    } else if (decorationNoise > -0.3) {
      return 'flower';
    } else {
      return 'none';
    }
  }
  
  /**
   * Simple 2D noise function (pseudo-Perlin)
   */
  private noise2D(x: number, y: number): number {
    // Integer coordinates
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    
    // Fractional coordinates
    const xf = x - xi;
    const yf = y - yi;
    
    // Smooth interpolation
    const u = this.fade(xf);
    const v = this.fade(yf);
    
    // Hash coordinates
    const aa = this.hash(xi, yi);
    const ab = this.hash(xi, yi + 1);
    const ba = this.hash(xi + 1, yi);
    const bb = this.hash(xi + 1, yi + 1);
    
    // Interpolate
    const x1 = this.lerp(aa, ba, u);
    const x2 = this.lerp(ab, bb, u);
    
    return this.lerp(x1, x2, v) * 2 - 1; // Range: -1 to 1
  }
  
  /**
   * Hash function for noise
   */
  private hash(x: number, y: number): number {
    let h = this.seed + x * 374761393 + y * 668265263;
    h = (h ^ (h >> 13)) * 1274126177;
    h = h ^ (h >> 16);
    return (h & 0x7fffffff) / 0x7fffffff; // Range: 0 to 1
  }
  
  /**
   * Smooth fade function
   */
  private fade(t: number): number {
    return t * t * t * (t * (t * 6 - 15) + 10);
  }
  
  /**
   * Linear interpolation
   */
  private lerp(a: number, b: number, t: number): number {
    return a + t * (b - a);
  }
}
