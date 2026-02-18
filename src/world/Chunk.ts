import * as THREE from 'three';
import { VoxelModel } from '../graphics/VoxelModel';
import { WorldGenerator } from './WorldGenerator';
import { MetalRegistry } from '../systems/MetalRegistry';
import { BlockTextures } from '../graphics/PixelTexture';

export class Chunk {
  private chunkX: number;
  private chunkZ: number;
  private blocks: Uint8Array; // 16x256x16 = 65536 blocks
  private mesh: THREE.Group;
  private generator: WorldGenerator;
  
  // Shared geometry for all blocks in all chunks
  private static sharedBoxGeometry: THREE.BoxGeometry | null = null;
  private static bedGeometry: THREE.BoxGeometry | null = null;
  private static chestGeometry: THREE.BoxGeometry | null = null;
  // Cache materials by block type to reuse across chunks
  private static materialCache: Map<number, THREE.MeshLambertMaterial> = new Map();
  
  static readonly SIZE = 16;
  static readonly HEIGHT = 256;
  
  constructor(chunkX: number, chunkZ: number, generator: WorldGenerator) {
    this.chunkX = chunkX;
    this.chunkZ = chunkZ;
    this.generator = generator;
    this.blocks = new Uint8Array(Chunk.SIZE * Chunk.HEIGHT * Chunk.SIZE);
    this.mesh = new THREE.Group();
    this.mesh.position.set(chunkX * Chunk.SIZE, 0, chunkZ * Chunk.SIZE);
  }
  
  generate(): void {
    // First, fill entire chunk with bedrock at y=0 and stone below ground
    for (let x = 0; x < Chunk.SIZE; x++) {
      for (let z = 0; z < Chunk.SIZE; z++) {
        // Bedrock layer
        this.setBlock(x, 0, z, 3);
        
        // Fill with stone up to y=63 to ensure solid ground
        for (let y = 1; y < 63; y++) {
          this.setBlock(x, y, z, 3);
        }
      }
    }
    
    // Generate terrain on top
    for (let x = 0; x < Chunk.SIZE; x++) {
      for (let z = 0; z < Chunk.SIZE; z++) {
        const worldX = this.chunkX * Chunk.SIZE + x;
        const worldZ = this.chunkZ * Chunk.SIZE + z;
        
        const height = this.generator.getHeight(worldX, worldZ);
        const biome = this.generator.getBiome(worldX, worldZ);
        
        // Fill dirt from y=63 up to height-1, then surface block at height
        for (let y = 63; y < height; y++) {
          this.setBlock(x, y, z, 2); // Dirt fill
        }
        this.setBlock(x, height, z, biome === 'desert' ? 6 : 1); // Grass or sand surface
      }
    }
    
    // Add decorations (trees, rocks, grass)
    this.addDecorations();
    
    // Generate ore veins
    this.generateOres();
    
    // Generate mesh
    this.regenerateMesh();
  }
  
  /**
   * Generate ore veins throughout the chunk
   */
  private generateOres(): void {
    // Reduced ore generation for faster loading (5 veins instead of 15)
    const veinCount = 5;
    
    for (let i = 0; i < veinCount; i++) {
      const metalId = MetalRegistry.getRandomMetalId();
      const metal = MetalRegistry.getMetal(metalId);
      
      if (!metal) continue;
      
      // Random position in chunk
      const centerX = Math.floor(Math.random() * Chunk.SIZE);
      const centerY = Math.floor(Math.random() * 50) + 10; // Between y=10 and y=60
      const centerZ = Math.floor(Math.random() * Chunk.SIZE);
      
      // Smaller veins for faster generation
      const veinSize = Math.min(2, Math.max(1, Math.floor(3 / metal.rarity)));
      
      // Simple sphere placement - optimized
      for (let dx = -veinSize; dx <= veinSize; dx++) {
        for (let dy = -veinSize; dy <= veinSize; dy++) {
          for (let dz = -veinSize; dz <= veinSize; dz++) {
            const distSq = dx * dx + dy * dy + dz * dz;
            
            if (distSq <= veinSize * veinSize && Math.random() > 0.5) {
              const x = centerX + dx;
              const y = centerY + dy;
              const z = centerZ + dz;
              
              // Only replace stone blocks
              if (this.getBlock(x, y, z) === 3) {
                this.setBlock(x, y, z, metalId);
              }
            }
          }
        }
      }
    }
  }
  
  private addDecorations(): void {
    // Minimal decorations for faster loading
    for (let x = 4; x < Chunk.SIZE - 4; x += 8) {
      for (let z = 4; z < Chunk.SIZE - 4; z += 8) {
        const worldX = this.chunkX * Chunk.SIZE + x;
        const worldZ = this.chunkZ * Chunk.SIZE + z;
        
        const height = this.generator.getHeight(worldX, worldZ);
        const biome = this.generator.getBiome(worldX, worldZ);
        const decoration = this.generator.getDecoration(worldX, worldZ);
        
        if (decoration === 'tree' && biome !== 'desert' && Math.random() > 0.8) {
          // Add tree (minimal)
          const tree = VoxelModel.createTree(x, height, z);
          tree.userData.decoration = true;
          this.mesh.add(tree);
        }
      }
    }
  }
  
  regenerateMesh(): void {
    // Clear existing block meshes (but keep decorations)
    const decorations: THREE.Object3D[] = [];
    this.mesh.children.forEach(child => {
      if (child.userData.decoration) {
        decorations.push(child);
      }
    });
    
    this.mesh.clear();
    decorations.forEach(decoration => this.mesh.add(decoration));
    
    // Use greedy meshing for better performance
    this.generateGreedyMesh();
  }
  
  private generateGreedyMesh(): void {
    // Get or create shared geometries
    if (!Chunk.sharedBoxGeometry) {
      Chunk.sharedBoxGeometry = new THREE.BoxGeometry(1, 1, 1);
    }
    if (!Chunk.bedGeometry) {
      Chunk.bedGeometry = new THREE.BoxGeometry(1, 0.35, 2); // 1 wide, half-height, 2 long
    }
    if (!Chunk.chestGeometry) {
      Chunk.chestGeometry = new THREE.BoxGeometry(0.85, 0.75, 0.85); // Smaller chest
    }
    
    // Group visible blocks by block type
    const blockGroups: Map<number, { x: number; y: number; z: number }[]> = new Map();
    // Special shaped blocks rendered individually
    const specialBlocks: { x: number; y: number; z: number; type: number }[] = [];
    
    for (let y = 0; y < Chunk.HEIGHT; y++) {
      for (let x = 0; x < Chunk.SIZE; x++) {
        for (let z = 0; z < Chunk.SIZE; z++) {
          const block = this.getBlock(x, y, z);
          if (block === 0) continue;
          
          // Only render if at least one face is exposed
          const hasExposedFace = 
            this.getBlock(x + 1, y, z) === 0 ||
            this.getBlock(x - 1, y, z) === 0 ||
            this.getBlock(x, y + 1, z) === 0 ||
            this.getBlock(x, y - 1, z) === 0 ||
            this.getBlock(x, y, z + 1) === 0 ||
            this.getBlock(x, y, z - 1) === 0;
          
          if (hasExposedFace) {
            // Bed (8) and Chest (9) are special shaped blocks
            if (block === 8 || block === 9) {
              specialBlocks.push({ x, y, z, type: block });
            } else {
              if (!blockGroups.has(block)) blockGroups.set(block, []);
              blockGroups.get(block)!.push({ x, y, z });
            }
          }
        }
      }
    }
    
    // Create one InstancedMesh per block type (massively fewer draw calls)
    const matrix = new THREE.Matrix4();
    
    blockGroups.forEach((positions, blockType) => {
      // Get or create cached material for this block type
      if (!Chunk.materialCache.has(blockType)) {
        const texture = BlockTextures.getTexture(blockType);
        const mat = new THREE.MeshLambertMaterial({ map: texture });
        Chunk.materialCache.set(blockType, mat);
      }
      const material = Chunk.materialCache.get(blockType)!;
      
      const instancedMesh = new THREE.InstancedMesh(
        Chunk.sharedBoxGeometry!,
        material,
        positions.length
      );
      instancedMesh.castShadow = false;
      instancedMesh.receiveShadow = false;
      
      for (let i = 0; i < positions.length; i++) {
        const pos = positions[i];
        matrix.setPosition(pos.x + 0.5, pos.y + 0.5, pos.z + 0.5);
        instancedMesh.setMatrixAt(i, matrix);
      }
      
      instancedMesh.instanceMatrix.needsUpdate = true;
      this.mesh.add(instancedMesh);
    });
    
    // Render special shaped blocks as individual meshes
    for (const block of specialBlocks) {
      if (!Chunk.materialCache.has(block.type)) {
        const texture = BlockTextures.getTexture(block.type);
        const mat = new THREE.MeshLambertMaterial({ map: texture });
        Chunk.materialCache.set(block.type, mat);
      }
      const material = Chunk.materialCache.get(block.type)!;
      
      if (block.type === 8) {
        // Bed: half-height, spans 2 blocks in Z (counted as 1 block but looks like 2)
        const bedMesh = new THREE.Mesh(Chunk.bedGeometry!, material);
        bedMesh.position.set(block.x + 0.5, block.y + 0.175, block.z);
        this.mesh.add(bedMesh);
      } else {
        // Chest: slightly smaller, sitting on ground
        const chestMesh = new THREE.Mesh(Chunk.chestGeometry!, material);
        chestMesh.position.set(block.x + 0.5, block.y + 0.375, block.z + 0.5);
        this.mesh.add(chestMesh);
      }
    }
  }
  
  getBlock(x: number, y: number, z: number): number {
    if (x < 0 || x >= Chunk.SIZE || y < 0 || y >= Chunk.HEIGHT || z < 0 || z >= Chunk.SIZE) {
      return 0;
    }
    
    const index = x + z * Chunk.SIZE + y * Chunk.SIZE * Chunk.SIZE;
    return this.blocks[index];
  }
  
  setBlock(x: number, y: number, z: number, blockType: number): void {
    if (x < 0 || x >= Chunk.SIZE || y < 0 || y >= Chunk.HEIGHT || z < 0 || z >= Chunk.SIZE) {
      return;
    }
    
    const index = x + z * Chunk.SIZE + y * Chunk.SIZE * Chunk.SIZE;
    this.blocks[index] = blockType;
  }
  
  getMesh(): THREE.Group {
    return this.mesh;
  }
  
  dispose(): void {
    this.mesh.traverse((child) => {
      if (child instanceof THREE.InstancedMesh) {
        // Don't dispose shared geometry or cached materials
        child.dispose();
      } else if (child instanceof THREE.Mesh) {
        child.geometry.dispose();
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose());
        } else {
          child.material.dispose();
        }
      }
    });
  }
}
