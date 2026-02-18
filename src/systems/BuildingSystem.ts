import * as THREE from 'three';

/**
 * Building System - Manages structures and blueprints
 */

export interface BlockPlacement {
  position: THREE.Vector3;
  blockType: string;
  metadata?: Record<string, any>;
}

export interface Structure {
  id: string;
  name: string;
  description: string;
  blocks: BlockPlacement[];
  size: THREE.Vector3;
  category: 'house' | 'farm' | 'utility' | 'decoration' | 'custom';
  cost: Array<{ type: string; count: number }>;
}

export interface Blueprint {
  structure: Structure;
  rotation: number;
  preview: boolean;
}

export class BuildingSystem {
  private structures: Map<string, Structure> = new Map();
  private placedStructures: Array<{
    structure: Structure;
    position: THREE.Vector3;
    rotation: number;
  }> = [];
  
  constructor() {
    this.initializeStructures();
  }
  
  private initializeStructures(): void {
    // Simple house
    this.addStructure({
      id: 'simple_house',
      name: 'Simple House',
      description: 'A basic wooden house',
      blocks: this.generateHouseBlocks(5, 4, 5),
      size: new THREE.Vector3(5, 4, 5),
      category: 'house',
      cost: [
        { type: 'wood', count: 100 },
        { type: 'stone', count: 50 }
      ]
    });
    
    // Watch tower
    this.addStructure({
      id: 'watch_tower',
      name: 'Watch Tower',
      description: 'A tall tower for surveillance',
      blocks: this.generateTowerBlocks(3, 12, 3),
      size: new THREE.Vector3(3, 12, 3),
      category: 'utility',
      cost: [
        { type: 'stone', count: 150 },
        { type: 'wood', count: 50 }
      ]
    });
    
    // Farm plot
    this.addStructure({
      id: 'farm_plot',
      name: 'Farm Plot',
      description: 'A prepared farming area',
      blocks: this.generateFarmBlocks(7, 7),
      size: new THREE.Vector3(7, 1, 7),
      category: 'farm',
      cost: [
        { type: 'dirt', count: 49 },
        { type: 'wood', count: 28 }
      ]
    });
    
    // Storage shed
    this.addStructure({
      id: 'storage_shed',
      name: 'Storage Shed',
      description: 'A small building for storage',
      blocks: this.generateShedBlocks(4, 3, 3),
      size: new THREE.Vector3(4, 3, 3),
      category: 'utility',
      cost: [
        { type: 'wood', count: 60 },
        { type: 'stone', count: 20 }
      ]
    });
    
    // Fountain
    this.addStructure({
      id: 'fountain',
      name: 'Fountain',
      description: 'A decorative fountain',
      blocks: this.generateFountainBlocks(),
      size: new THREE.Vector3(5, 3, 5),
      category: 'decoration',
      cost: [
        { type: 'stone', count: 50 },
        { type: 'water', count: 10 }
      ]
    });
    
    // Bridge
    this.addStructure({
      id: 'bridge',
      name: 'Bridge',
      description: 'A wooden bridge',
      blocks: this.generateBridgeBlocks(10),
      size: new THREE.Vector3(10, 2, 3),
      category: 'utility',
      cost: [
        { type: 'wood', count: 80 }
      ]
    });
    
    // Wall segment
    this.addStructure({
      id: 'wall',
      name: 'Wall Segment',
      description: 'A defensive wall',
      blocks: this.generateWallBlocks(10, 5),
      size: new THREE.Vector3(10, 5, 1),
      category: 'utility',
      cost: [
        { type: 'stone', count: 50 }
      ]
    });
    
    console.log(`Loaded ${this.structures.size} building structures`);
  }
  
  private generateHouseBlocks(width: number, height: number, depth: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    // Floor
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({
          position: new THREE.Vector3(x, 0, z),
          blockType: 'wood_planks'
        });
      }
    }
    
    // Walls
    for (let y = 1; y < height; y++) {
      for (let x = 0; x < width; x++) {
        for (let z = 0; z < depth; z++) {
          if (x === 0 || x === width - 1 || z === 0 || z === depth - 1) {
            // Leave door space
            if (!(z === 0 && x === Math.floor(width / 2) && y === 1)) {
              blocks.push({
                position: new THREE.Vector3(x, y, z),
                blockType: 'wood_planks'
              });
            }
          }
        }
      }
    }
    
    // Roof
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({
          position: new THREE.Vector3(x, height, z),
          blockType: 'wood'
        });
      }
    }
    
    return blocks;
  }
  
  private generateTowerBlocks(width: number, height: number, depth: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        for (let z = 0; z < depth; z++) {
          // Hollow tower with walls
          if (x === 0 || x === width - 1 || z === 0 || z === depth - 1 || y === 0) {
            blocks.push({
              position: new THREE.Vector3(x, y, z),
              blockType: 'stone'
            });
          }
        }
      }
    }
    
    // Top platform
    for (let x = -1; x <= width; x++) {
      for (let z = -1; z <= depth; z++) {
        if (x === -1 || x === width || z === -1 || z === depth) {
          blocks.push({
            position: new THREE.Vector3(x, height, z),
            blockType: 'stone'
          });
        }
      }
    }
    
    return blocks;
  }
  
  private generateFarmBlocks(width: number, depth: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    // Farmland
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({
          position: new THREE.Vector3(x, 0, z),
          blockType: 'farmland'
        });
      }
    }
    
    // Fence border
    for (let x = -1; x <= width; x++) {
      blocks.push({
        position: new THREE.Vector3(x, 1, -1),
        blockType: 'fence'
      });
      blocks.push({
        position: new THREE.Vector3(x, 1, depth),
        blockType: 'fence'
      });
    }
    
    for (let z = 0; z < depth; z++) {
      blocks.push({
        position: new THREE.Vector3(-1, 1, z),
        blockType: 'fence'
      });
      blocks.push({
        position: new THREE.Vector3(width, 1, z),
        blockType: 'fence'
      });
    }
    
    return blocks;
  }
  
  private generateShedBlocks(width: number, height: number, depth: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    // Similar to house but smaller and simpler
    for (let y = 0; y <= height; y++) {
      for (let x = 0; x < width; x++) {
        for (let z = 0; z < depth; z++) {
          if (y === 0 || y === height || x === 0 || x === width - 1 || z === 0 || z === depth - 1) {
            blocks.push({
              position: new THREE.Vector3(x, y, z),
              blockType: y === 0 || y === height ? 'wood' : 'wood_planks'
            });
          }
        }
      }
    }
    
    return blocks;
  }
  
  private generateFountainBlocks(): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    const center = 2;
    
    // Base ring
    for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 4) {
      const x = Math.round(center + Math.cos(angle) * 2);
      const z = Math.round(center + Math.sin(angle) * 2);
      blocks.push({
        position: new THREE.Vector3(x, 0, z),
        blockType: 'stone'
      });
    }
    
    // Center pillar
    for (let y = 0; y < 3; y++) {
      blocks.push({
        position: new THREE.Vector3(center, y, center),
        blockType: 'stone'
      });
    }
    
    // Water
    blocks.push({
      position: new THREE.Vector3(center, 3, center),
      blockType: 'water'
    });
    
    return blocks;
  }
  
  private generateBridgeBlocks(length: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    // Floor
    for (let x = 0; x < length; x++) {
      for (let z = 0; z < 3; z++) {
        blocks.push({
          position: new THREE.Vector3(x, 0, z),
          blockType: 'wood_planks'
        });
      }
    }
    
    // Railings
    for (let x = 0; x < length; x++) {
      blocks.push({
        position: new THREE.Vector3(x, 1, 0),
        blockType: 'fence'
      });
      blocks.push({
        position: new THREE.Vector3(x, 1, 2),
        blockType: 'fence'
      });
    }
    
    return blocks;
  }
  
  private generateWallBlocks(length: number, height: number): BlockPlacement[] {
    const blocks: BlockPlacement[] = [];
    
    for (let x = 0; x < length; x++) {
      for (let y = 0; y < height; y++) {
        blocks.push({
          position: new THREE.Vector3(x, y, 0),
          blockType: 'stone_bricks'
        });
        
        // Battlements
        if (y === height - 1 && x % 2 === 0) {
          blocks.push({
            position: new THREE.Vector3(x, y + 1, 0),
            blockType: 'stone_bricks'
          });
        }
      }
    }
    
    return blocks;
  }
  
  private addStructure(structure: Structure): void {
    this.structures.set(structure.id, structure);
  }
  
  getStructure(id: string): Structure | undefined {
    return this.structures.get(id);
  }
  
  getAllStructures(): Structure[] {
    return Array.from(this.structures.values());
  }
  
  getStructuresByCategory(category: Structure['category']): Structure[] {
    return Array.from(this.structures.values()).filter(s => s.category === category);
  }
  
  placeStructure(
    structureId: string,
    position: THREE.Vector3,
    rotation: number = 0
  ): BlockPlacement[] | null {
    const structure = this.structures.get(structureId);
    if (!structure) return null;
    
    const rotatedBlocks = this.rotateStructure(structure.blocks, rotation);
    const worldBlocks = rotatedBlocks.map(block => ({
      position: block.position.clone().add(position),
      blockType: block.blockType,
      metadata: block.metadata
    }));
    
    this.placedStructures.push({
      structure,
      position: position.clone(),
      rotation
    });
    
    console.log(`🏗️ Placed ${structure.name} at ${position.toArray().join(', ')}`);
    
    return worldBlocks;
  }
  
  private rotateStructure(blocks: BlockPlacement[], rotation: number): BlockPlacement[] {
    if (rotation === 0) return blocks;
    
    const rotations = Math.floor(rotation / 90) % 4;
    if (rotations === 0) return blocks;
    
    return blocks.map(block => {
      let pos = block.position.clone();
      
      for (let i = 0; i < rotations; i++) {
        const temp = pos.x;
        pos.x = -pos.z;
        pos.z = temp;
      }
      
      return {
        position: pos,
        blockType: block.blockType,
        metadata: block.metadata
      };
    });
  }
  
  getPlacedStructures(): Array<{ structure: Structure; position: THREE.Vector3; rotation: number }> {
    return [...this.placedStructures];
  }
  
  clearPlacedStructures(): void {
    this.placedStructures = [];
  }
}
