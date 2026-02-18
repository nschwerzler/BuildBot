import * as THREE from 'three';
import { BlockTextures } from './PixelTexture';

/**
 * Voxel definition for creating detailed models
 */
export interface Voxel {
  position: [number, number, number];
  size: [number, number, number];
  texture?: THREE.Texture;
  color?: THREE.Color;
}

/**
 * VoxelModel - Create detailed voxel-based models
 * These are NOT simple cubes, but detailed models made of smaller voxels
 */
export class VoxelModel {
  /**
   * Create a basic block (1x1x1 cube)
   */
  static createBlock(blockType: number, x: number, y: number, z: number): THREE.Mesh {
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const texture = BlockTextures.getTexture(blockType);
    
    const material = new THREE.MeshLambertMaterial({
      map: texture,
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, y, z);
    mesh.castShadow = false; // Disable shadows
    mesh.receiveShadow = false;
    
    return mesh;
  }
  
  /**
   * Create a detailed tree model (not just log + leaves)
   */
  static createTree(x: number, y: number, z: number): THREE.Group {
    const tree = new THREE.Group();
    
    // Tree trunk - tapered for realism
    const trunkHeight = 5 + Math.floor(Math.random() * 3);
    for (let i = 0; i < trunkHeight; i++) {
      const scale = 1 - (i / trunkHeight) * 0.2;
      const trunk = this.createVoxel(
        [0, i, 0],
        [scale, 1, scale],
        BlockTextures.wood
      );
      tree.add(trunk);
    }
    
    // Foliage - organic rounded shape
    const foliageY = trunkHeight;
    const foliageRadius = 2 + Math.random();
    
    for (let dy = -2; dy <= 2; dy++) {
      for (let dx = -2; dx <= 2; dx++) {
        for (let dz = -2; dz <= 2; dz++) {
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          const threshold = foliageRadius - Math.abs(dy) * 0.3;
          
          if (dist < threshold && Math.random() > 0.3) {
            const leaf = this.createVoxel(
              [dx, foliageY + dy, dz],
              [0.9, 0.9, 0.9],
              BlockTextures.leaves
            );
            tree.add(leaf);
          }
        }
      }
    }
    
    // Top cluster
    const top = this.createVoxel([0, foliageY + 2, 0], [0.9, 0.9, 0.9], BlockTextures.leaves);
    tree.add(top);
    
    tree.position.set(x, y, z);
    return tree;
  }
  
  /**
   * Create a rock formation (detailed, not just a cube)
   */
  static createRock(x: number, y: number, z: number, size: number = 1): THREE.Group {
    const rock = new THREE.Group();
    
    const voxels = Math.floor(3 + size * 3);
    for (let i = 0; i < voxels; i++) {
      const offsetX = (Math.random() - 0.5) * size;
      const offsetY = (Math.random() - 0.5) * size * 0.5;
      const offsetZ = (Math.random() - 0.5) * size;
      
      const voxelSize = 0.3 + Math.random() * 0.4;
      const voxel = this.createVoxel(
        [offsetX, offsetY, offsetZ],
        [voxelSize, voxelSize, voxelSize],
        BlockTextures.stone
      );
      
      voxel.rotation.set(
        Math.random() * 0.5,
        Math.random() * Math.PI,
        Math.random() * 0.5
      );
      
      rock.add(voxel);
    }
    
    rock.position.set(x, y, z);
    return rock;
  }
  
  /**
   * Create a grass tuft (decorative detail)
   */
  static createGrassTuft(x: number, y: number, z: number): THREE.Group {
    const tuft = new THREE.Group();
    
    const blades = 3 + Math.floor(Math.random() * 3);
    for (let i = 0; i < blades; i++) {
      const blade = this.createVoxel(
        [
          (Math.random() - 0.5) * 0.3,
          Math.random() * 0.3,
          (Math.random() - 0.5) * 0.3
        ],
        [0.05, 0.3 + Math.random() * 0.2, 0.05],
        BlockTextures.grass
      );
      
      blade.rotation.z = (Math.random() - 0.5) * 0.3;
      tuft.add(blade);
    }
    
    tuft.position.set(x, y, z);
    return tuft;
  }
  
  /**
   * Create a single voxel with given parameters
   */
  private static createVoxel(
    position: [number, number, number],
    size: [number, number, number],
    texture: THREE.Texture,
    color?: THREE.Color
  ): THREE.Mesh {
    const geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
    const material = new THREE.MeshLambertMaterial({
      map: texture,
      color: color || 0xffffff,
    });
    
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(position[0], position[1], position[2]);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    
    return mesh;
  }
  
  /**
   * Create a flower (detailed multi-voxel model)
   */
  static createFlower(x: number, y: number, z: number, type: number = 0): THREE.Group {
    const flower = new THREE.Group();
    
    // Stem
    const stem = this.createVoxel(
      [0, 0.2, 0],
      [0.05, 0.4, 0.05],
      BlockTextures.grass
    );
    flower.add(stem);
    
    // Petals
    const petalColors = [
      new THREE.Color(0xff6b6b), // Red
      new THREE.Color(0xffd93d), // Yellow
      new THREE.Color(0x6bcbff), // Blue
      new THREE.Color(0xff6bff), // Pink
    ];
    
    const color = petalColors[type % petalColors.length];
    
    const petalPositions = [
      [0.15, 0.4, 0],
      [-0.15, 0.4, 0],
      [0, 0.4, 0.15],
      [0, 0.4, -0.15],
    ];
    
    petalPositions.forEach(pos => {
      const petal = this.createVoxel(
        pos as [number, number, number],
        [0.1, 0.1, 0.1],
        BlockTextures.grass,
        color
      );
      flower.add(petal);
    });
    
    // Center
    const center = this.createVoxel(
      [0, 0.4, 0],
      [0.1, 0.1, 0.1],
      BlockTextures.grass,
      new THREE.Color(0xffd93d)
    );
    flower.add(center);
    
    flower.position.set(x, y, z);
    return flower;
  }
}
