import * as THREE from 'three';
import { MetalRegistry } from '../systems/MetalRegistry';

/**
 * PixelTexture - Manages pixel art textures with proper filtering
 */
export class PixelTexture {
  private static textureCache = new Map<string, THREE.Texture>();
  
  /**
   * Load a pixel art texture with nearest-neighbor filtering
   */
  static load(url: string): THREE.Texture {
    if (this.textureCache.has(url)) {
      return this.textureCache.get(url)!;
    }
    
    const texture = new THREE.TextureLoader().load(url);
    
    // Critical: Use nearest filtering for pixel art
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    texture.generateMipmaps = false;
    
    // Prevent texture bleeding
    texture.wrapS = THREE.ClampToEdgeWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    
    this.textureCache.set(url, texture);
    return texture;
  }
  
  /**
   * Create a texture atlas from multiple textures
   */
  static createAtlas(textures: { [key: string]: string }, size: number = 16): THREE.Texture {
    const tileSize = size;
    const tilesPerRow = Math.ceil(Math.sqrt(Object.keys(textures).length));
    const atlasSize = tilesPerRow * tileSize;
    
    const canvas = document.createElement('canvas');
    canvas.width = atlasSize;
    canvas.height = atlasSize;
    const ctx = canvas.getContext('2d')!;
    
    // Disable image smoothing for pixel art
    ctx.imageSmoothingEnabled = false;
    
    const textureMap: { [key: string]: { x: number; y: number } } = {};
    const textureEntries = Object.entries(textures);
    
    let loadedCount = 0;
    const totalCount = textureEntries.length;
    
    return new Promise<THREE.Texture>((resolve) => {
      textureEntries.forEach(([name, url], index) => {
        const img = new Image();
        img.onload = () => {
          const x = (index % tilesPerRow) * tileSize;
          const y = Math.floor(index / tilesPerRow) * tileSize;
          
          ctx.drawImage(img, x, y, tileSize, tileSize);
          textureMap[name] = { x: x / atlasSize, y: y / atlasSize };
          
          loadedCount++;
          if (loadedCount === totalCount) {
            const texture = new THREE.CanvasTexture(canvas);
            texture.magFilter = THREE.NearestFilter;
            texture.minFilter = THREE.NearestFilter;
            texture.generateMipmaps = false;
            texture.wrapS = THREE.ClampToEdgeWrapping;
            texture.wrapT = THREE.ClampToEdgeWrapping;
            
            resolve(texture);
          }
        };
        img.src = url;
      });
    }) as any;
  }
  
  /**
   * Create a procedural pixel art texture
   */
  static createProcedural(
    width: number,
    height: number,
    generator: (x: number, y: number) => { r: number; g: number; b: number }
  ): THREE.DataTexture {
    const size = width * height;
    const data = new Uint8Array(4 * size);
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const index = (y * width + x) * 4;
        const color = generator(x, y);
        
        data[index] = color.r;
        data[index + 1] = color.g;
        data[index + 2] = color.b;
        data[index + 3] = 255;
      }
    }
    
    const texture = new THREE.DataTexture(data, width, height);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    texture.generateMipmaps = false;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    
    return texture;
  }
  
  /**
   * Create a simple colored texture for testing
   */
  static createColor(color: THREE.Color): THREE.DataTexture {
    const data = new Uint8Array([
      Math.floor(color.r * 255),
      Math.floor(color.g * 255),
      Math.floor(color.b * 255),
      255
    ]);
    
    const texture = new THREE.DataTexture(data, 1, 1);
    texture.magFilter = THREE.NearestFilter;
    texture.minFilter = THREE.NearestFilter;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    
    return texture;
  }
}

/**
 * Create default textures for basic blocks
 */
export class BlockTextures {
  static grass: THREE.Texture;
  static dirt: THREE.Texture;
  static stone: THREE.Texture;
  static wood: THREE.Texture;
  static leaves: THREE.Texture;
  static sand: THREE.Texture;
  static water: THREE.Texture;
  static redWool: THREE.Texture;  // Bed block
  static chest: THREE.Texture;    // Chest block
  static potion: THREE.Texture;   // Growth Potion
  static netherrack: THREE.Texture; // Netherrack
  static lava: THREE.Texture;       // Lava
  static planks: THREE.Texture;     // Wood Planks
  
  // Cache for metal textures
  private static metalTextureCache: Map<number, THREE.Texture> = new Map();
  
  static init(): void {
    // Create procedural textures (reduced to 8x8 for faster generation)
    this.grass = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 20;
      return { r: 60 + noise, g: 179 + noise, b: 113 + noise };
    });
    
    this.dirt = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 30;
      return { r: 134 + noise, g: 96 + noise, b: 67 + noise };
    });
    
    this.stone = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 40;
      return { r: 128 + noise, g: 128 + noise, b: 128 + noise };
    });
    
    this.wood = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 20;
      return { r: 139 + noise, g: 90 + noise, b: 43 + noise };
    });
    
    this.leaves = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 30;
      return { r: 34 + noise, g: 139 + noise, b: 34 + noise };
    });
    
    this.sand = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 20;
      return { r: 238 + noise, g: 214 + noise, b: 175 + noise };
    });
    
    this.water = PixelTexture.createColor(new THREE.Color(0x4A90E2));

    // Red wool for bed
    this.redWool = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 15;
      return { r: 180 + noise, g: 30 + noise, b: 30 + noise };
    });

    // Chest (golden wood with banding)
    this.chest = PixelTexture.createProcedural(8, 8, (x, y) => {
      const isBand = (y === 3 || y === 4);
      const noise = Math.random() * 15;
      if (isBand) {
        return { r: 200 + noise, g: 180 + noise, b: 50 + noise }; // Gold band
      }
      return { r: 160 + noise, g: 100 + noise, b: 40 + noise }; // Dark wood
    });

    // Growth Potion (purple/pink glowing)
    this.potion = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 20;
      const glow = Math.sin((x + y) * 0.8) * 20;
      return { r: 180 + noise + glow, g: 50 + noise, b: 200 + noise + glow };
    });

    // Netherrack (dark red, rough texture)
    this.netherrack = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 25;
      const pattern = Math.sin(x * 1.5 + y * 0.8) * 10;
      return { r: 100 + noise + pattern, g: 30 + noise * 0.4, b: 30 + noise * 0.3 };
    });

    // Lava (bright orange/yellow)
    this.lava = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 30;
      const glow = Math.sin((x + y) * 0.6) * 20;
      return { r: 220 + noise, g: 100 + noise + glow, b: 20 + noise * 0.3 };
    });

    // Wood Planks (light brown with grain lines)
    this.planks = PixelTexture.createProcedural(8, 8, (x, y) => {
      const noise = Math.random() * 15;
      const grain = (y % 4 === 0) ? -15 : 0; // Horizontal plank lines
      const plankVar = (x < 4) ? 0 : 8; // Slight variation between planks
      return { r: 190 + noise + plankVar + grain, g: 150 + noise + plankVar + grain, b: 90 + noise + grain };
    });
  }
  
  static getTexture(blockType: number): THREE.Texture {
    // Check if it's a metal
    const metal = MetalRegistry.getMetal(blockType);
    if (metal) {
      // Check cache first
      if (this.metalTextureCache.has(blockType)) {
        return this.metalTextureCache.get(blockType)!;
      }
      
      // Create and cache texture
      const texture = this.createMetalTexture(metal.color);
      this.metalTextureCache.set(blockType, texture);
      return texture;
    }
    
    switch (blockType) {
      case 1: return this.grass;
      case 2: return this.dirt;
      case 3: return this.stone;
      case 4: return this.wood;
      case 5: return this.leaves;
      case 6: return this.sand;
      case 7: return this.water;
      case 8: return this.redWool;
      case 9: return this.chest;
      case 10: return this.potion;
      case 11: return this.netherrack;
      case 12: return this.lava;
      case 13: return this.planks;
      default: return this.stone;
    }
  }
  
  /**
   * Create a metal texture with given color
   */
  private static createMetalTexture(colorString: string): THREE.Texture {
    // Parse HSL color
    const match = colorString.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
    if (!match) {
      return this.stone;
    }
    
    const h = parseInt(match[1]);
    const s = parseInt(match[2]) / 100;
    const l = parseInt(match[3]) / 100;
    
    // Simplified texture generation (8x8 instead of 16x16 for speed)
    return PixelTexture.createProcedural(8, 8, (x, y) => {
      // Simpler metallic effect
      const sparkle = (Math.random() > 0.85) ? 30 : 0;
      
      // Convert HSL to RGB (simplified)
      const c = (1 - Math.abs(2 * l - 1)) * s;
      const x1 = c * (1 - Math.abs(((h / 60) % 2) - 1));
      const m = l - c / 2;
      
      let r = 0, g = 0, b = 0;
      
      if (h < 60) { r = c; g = x1; b = 0; }
      else if (h < 120) { r = x1; g = c; b = 0; }
      else if (h < 180) { r = 0; g = c; b = x1; }
      else if (h < 240) { r = 0; g = x1; b = c; }
      else if (h < 300) { r = x1; g = 0; b = c; }
      else { r = c; g = 0; b = x1; }
      
      return {
        r: Math.min(255, (r + m) * 255 + sparkle),
        g: Math.min(255, (g + m) * 255 + sparkle),
        b: Math.min(255, (b + m) * 255 + sparkle)
      };
    });
  }
}
