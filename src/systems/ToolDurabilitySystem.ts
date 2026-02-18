/**
 * Tool Durability System - Manages tool wear and breakage
 */

export interface Tool {
  id: string;
  name: string;
  type: 'pickaxe' | 'axe' | 'shovel' | 'sword' | 'hoe';
  material: 'wood' | 'stone' | 'iron' | 'gold' | 'diamond' | 'metal';
  maxDurability: number;
  currentDurability: number;
  miningSpeed: number;
  miningLevel: number; // 0=wood, 1=stone, 2=iron, 3=diamond
  efficiency: number;
}

export class Tool DurabilitySystem {
  private tools: Map<string, Tool> = new Map();
  
  // Durability values for different materials
  private readonly durabilityValues = {
    wood: 59,
    stone: 131,
    iron: 250,
    gold: 32,
    diamond: 1561,
    metal: 500
  };
  
  // Mining speed multipliers
  private readonly speedMultipliers = {
    wood: 1.0,
    stone: 1.5,
    iron: 2.0,
    gold: 3.0,
    diamond: 2.5,
    metal: 2.2
  };
  
  constructor() {
    console.log('Tool Durability System initialized');
  }
  
  createTool(
    id: string,
    name: string,
    type: Tool['type'],
    material: Tool['material']
  ): Tool {
    const maxDurability = this.durabilityValues[material];
    const miningSpeed = this.speedMultipliers[material];
    const miningLevel = this.getMiningLevel(material);
    
    const tool: Tool = {
      id,
      name,
      type,
      material,
      maxDurability,
      currentDurability: maxDurability,
      miningSpeed,
      miningLevel,
      efficiency: 1.0
    };
    
    this.tools.set(id, tool);
    return tool;
  }
  
  private getMiningLevel(material: Tool['material']): number {
    switch (material) {
      case 'wood': return 0;
      case 'stone': return 1;
      case 'iron': return 2;
      case 'gold': return 2;
      case 'diamond': return 3;
      case 'metal': return 2;
      default: return 0;
    }
  }
  
  useTool(toolId: string, damage: number = 1): boolean {
    const tool = this.tools.get(toolId);
    if (!tool) return false;
    
    tool.currentDurability -= damage;
    
    // Tool breaks
    if (tool.currentDurability <= 0) {
      tool.currentDurability = 0;
      console.log(`💔 ${tool.name} broke!`);
      return false;
    }
    
    // Warn when low durability
    const durabilityPercent = (tool.currentDurability / tool.maxDurability) * 100;
    if (durabilityPercent <= 10 && Math.random() < 0.3) {
      console.log(`⚠️ ${tool.name} is about to break! (${Math.floor(durabilityPercent)}%)`);
    }
    
    return true;
  }
  
  repairTool(toolId: string, amount: number): boolean {
    const tool = this.tools.get(toolId);
    if (!tool) return false;
    
    const oldDurability = tool.currentDurability;
    tool.currentDurability = Math.min(tool.maxDurability, tool.currentDurability + amount);
    
    const repaired = tool.currentDurability - oldDurability;
    if (repaired > 0) {
      console.log(`🔧 Repaired ${tool.name} by ${repaired} durability`);
      return true;
    }
    
    return false;
  }
  
  repairToolFull(toolId: string): boolean {
    const tool = this.tools.get(toolId);
    if (!tool) return false;
    
    tool.currentDurability = tool.maxDurability;
    console.log(`✨ ${tool.name} fully repaired!`);
    return true;
  }
  
  getTool(toolId: string): Tool | undefined {
    return this.tools.get(toolId);
  }
  
  getDurabilityPercent(toolId: string): number {
    const tool = this.tools.get(toolId);
    if (!tool) return 0;
    
    return (tool.currentDurability / tool.maxDurability) * 100;
  }
  
  isBroken(toolId: string): boolean {
    const tool = this.tools.get(toolId);
    return !tool || tool.currentDurability <= 0;
  }
  
  canMineBlock(toolId: string, blockHardness: number): boolean {
    const tool = this.tools.get(toolId);
    if (!tool || tool.currentDurability <= 0) return false;
    
    return tool.miningLevel >= blockHardness;
  }
  
  getMiningTime(toolId: string, blockHardness: number): number {
    const tool = this.tools.get(toolId);
    if (!tool) return 5.0; // Default bare hands
    
    if (tool.currentDurability <= 0) return 5.0;
    
    const baseTime = (blockHardness + 1) * 1.5;
    const toolSpeed = tool.miningSpeed * tool.efficiency;
    
    return baseTime / toolSpeed;
  }
  
  getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }
  
  removeTool(toolId: string): boolean {
    return this.tools.delete(toolId);
  }
  
  getToolCount(): number {
    return this.tools.size;
  }
  
  enhanceTool(toolId: string, efficiencyBonus: number): boolean {
    const tool = this.tools.get(toolId);
    if (!tool) return false;
    
    tool.efficiency += efficiencyBonus;
    console.log(`⬆️ ${tool.name} efficiency increased to ${tool.efficiency.toFixed(2)}x`);
    return true;
  }
}
