import * as THREE from 'three';
import { Chunk } from './Chunk';
import { WorldGenerator } from './WorldGenerator';
import { BlockTextures } from '../graphics/PixelTexture';
import { MetalRegistry } from '../systems/MetalRegistry';

export class World {
  private chunks: Map<string, Chunk> = new Map();
  private worldGroup: THREE.Group;
  private generator: WorldGenerator;
  private renderDistance: number = 2; // Start short, expand after tutorial

  setRenderDistance(dist: number): void {
    this.renderDistance = dist;
  }

  getRenderDistance(): number {
    return this.renderDistance;
  }
  
  constructor() {
    this.worldGroup = new THREE.Group();
    this.generator = new WorldGenerator();
  }
  
  async init(): Promise<void> {
    // Initialize textures
    BlockTextures.init();
    
    // Initialize metal registry
    MetalRegistry.init();
    
    console.log('World initialized');
  }
  
  updateChunks(playerPosition: THREE.Vector3): void {
    const playerChunkX = Math.floor(playerPosition.x / 16);
    const playerChunkZ = Math.floor(playerPosition.z / 16);
    
    // Generate chunks around player
    for (let x = playerChunkX - this.renderDistance; x <= playerChunkX + this.renderDistance; x++) {
      for (let z = playerChunkZ - this.renderDistance; z <= playerChunkZ + this.renderDistance; z++) {
        const key = `${x},${z}`;
        
        if (!this.chunks.has(key)) {
          this.generateChunk(x, z);
        }
      }
    }
    
    // Unload distant chunks
    const chunksToRemove: string[] = [];
    this.chunks.forEach((chunk, key) => {
      const [x, z] = key.split(',').map(Number);
      const distance = Math.max(Math.abs(x - playerChunkX), Math.abs(z - playerChunkZ));
      
      if (distance > this.renderDistance + 1) {
        chunksToRemove.push(key);
        this.worldGroup.remove(chunk.getMesh());
        chunk.dispose();
      }
    });
    
    chunksToRemove.forEach(key => this.chunks.delete(key));
  }
  
  getBlock(x: number, y: number, z: number): number {
    // Treat bedrock layer (y=0) as always solid
    if (y === 0) return 3;
    
    const chunkX = Math.floor(x / 16);
    const chunkZ = Math.floor(z / 16);
    const key = `${chunkX},${chunkZ}`;
    
    const chunk = this.chunks.get(key);
    if (!chunk) return 0;
    
    const localX = ((x % 16) + 16) % 16;
    const localZ = ((z % 16) + 16) % 16;
    
    return chunk.getBlock(localX, y, localZ);
  }
  
  setBlock(x: number, y: number, z: number, blockType: number): void {
    const chunkX = Math.floor(x / 16);
    const chunkZ = Math.floor(z / 16);
    const key = `${chunkX},${chunkZ}`;
    
    // Auto-generate chunk if it doesn't exist yet
    if (!this.chunks.has(key)) {
      this.generateChunk(chunkX, chunkZ);
    }
    
    const chunk = this.chunks.get(key);
    if (!chunk) return;
    
    const localX = ((x % 16) + 16) % 16;
    const localZ = ((z % 16) + 16) % 16;
    
    chunk.setBlock(localX, y, localZ, blockType);
    chunk.regenerateMesh();
  }
  
  removeBlock(x: number, y: number, z: number): void {
    this.setBlock(x, y, z, 0);
  }
  
  checkCollision(
    position: THREE.Vector3,
    boundingBox: THREE.Box3
  ): { collision: boolean; correctedPosition: THREE.Vector3; onGround: boolean } {
    const testBox = boundingBox.clone().translate(position);
    let onGround = false;
    const correctedPosition = position.clone();
    
    // Expand check area to prevent falling through blocks
    const minX = Math.floor(testBox.min.x - 0.1);
    const minY = Math.floor(testBox.min.y - 0.1);
    const minZ = Math.floor(testBox.min.z - 0.1);
    const maxX = Math.ceil(testBox.max.x + 0.1);
    const maxY = Math.ceil(testBox.max.y + 0.1);
    const maxZ = Math.ceil(testBox.max.z + 0.1);
    
    for (let y = minY; y <= maxY; y++) {
      for (let x = minX; x <= maxX; x++) {
        for (let z = minZ; z <= maxZ; z++) {
          const block = this.getBlock(x, y, z);
          
          if (block !== 0) {
            const blockBox = new THREE.Box3(
              new THREE.Vector3(x, y, z),
              new THREE.Vector3(x + 1, y + 1, z + 1)
            );
            
            if (testBox.intersectsBox(blockBox)) {
              // Calculate penetration on each axis
              const penetrationX = Math.min(
                testBox.max.x - blockBox.min.x,
                blockBox.max.x - testBox.min.x
              );
              const penetrationY = Math.min(
                testBox.max.y - blockBox.min.y,
                blockBox.max.y - testBox.min.y
              );
              const penetrationZ = Math.min(
                testBox.max.z - blockBox.min.z,
                blockBox.max.z - testBox.min.z
              );
              
              // Resolve collision on smallest penetration axis
              const minPenetration = Math.min(penetrationX, penetrationY, penetrationZ);
              
              if (minPenetration === penetrationY) {
                if (testBox.min.y < blockBox.min.y) {
                  correctedPosition.y = blockBox.max.y - boundingBox.min.y;
                  onGround = true;
                } else {
                  correctedPosition.y = blockBox.min.y - boundingBox.max.y;
                }
              } else if (minPenetration === penetrationX) {
                if (testBox.min.x < blockBox.min.x) {
                  correctedPosition.x = blockBox.max.x - boundingBox.min.x;
                } else {
                  correctedPosition.x = blockBox.min.x - boundingBox.max.x;
                }
              } else {
                if (testBox.min.z < blockBox.min.z) {
                  correctedPosition.z = blockBox.max.z - boundingBox.min.z;
                } else {
                  correctedPosition.z = blockBox.min.z - boundingBox.max.z;
                }
              }
              
              return { collision: true, correctedPosition, onGround };
            }
          }
        }
      }
    }
    
    return { collision: false, correctedPosition: position, onGround: false };
  }
  
  /**
   * Generate a single chunk
   */
  generateChunk(x: number, z: number): void {
    const key = `${x},${z}`;
    if (this.chunks.has(key)) return;
    
    const chunk = new Chunk(x, z, this.generator);
    chunk.generate();
    this.chunks.set(key, chunk);
    this.worldGroup.add(chunk.getMesh());
  }
  
  raycast(ray: THREE.Ray, maxDistance: number): { 
    blockPos: THREE.Vector3; 
    normal: THREE.Vector3;
    distance: number;
  } | null {
    const step = 0.1;
    let distance = 0;
    
    while (distance < maxDistance) {
      const point = ray.origin.clone().add(ray.direction.clone().multiplyScalar(distance));
      const blockPos = new THREE.Vector3(
        Math.floor(point.x),
        Math.floor(point.y),
        Math.floor(point.z)
      );
      
      const block = this.getBlock(blockPos.x, blockPos.y, blockPos.z);
      
      if (block !== 0) {
        // Determine which face was hit
        const localPoint = point.clone().sub(blockPos);
        let normal = new THREE.Vector3();
        
        const epsilon = 0.01;
        if (localPoint.x < epsilon) normal.set(-1, 0, 0);
        else if (localPoint.x > 1 - epsilon) normal.set(1, 0, 0);
        else if (localPoint.y < epsilon) normal.set(0, -1, 0);
        else if (localPoint.y > 1 - epsilon) normal.set(0, 1, 0);
        else if (localPoint.z < epsilon) normal.set(0, 0, -1);
        else if (localPoint.z > 1 - epsilon) normal.set(0, 0, 1);
        
        return { blockPos, normal, distance };
      }
      
      distance += step;
    }
    
    return null;
  }
  
  /** Get terrain height from the world generator at given world coords */
  getTerrainHeight(x: number, z: number): number {
    return this.generator.getHeight(x, z);
  }

  getWorldGroup(): THREE.Group {
    return this.worldGroup;
  }
  
  getLoadedChunkCount(): number {
    return this.chunks.size;
  }
}
