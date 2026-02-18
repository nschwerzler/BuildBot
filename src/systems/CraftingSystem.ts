import { MetalRegistry } from './MetalRegistry';

/**
 * Crafting System - Allows players to combine resources into new items
 */

export interface CraftingRecipe {
  id: string;
  name: string;
  inputs: { blockType: number; count: number }[];
  output: { blockType: number; count: number };
  category: string;
  unlocked: boolean;
}

export class CraftingSystem {
  private recipes: Map<string, CraftingRecipe> = new Map();
  private unlockedRecipes: Set<string> = new Set();
  
  constructor() {
    this.initializeRecipes();
  }
  
  private initializeRecipes(): void {
    // Basic crafting recipes
    this.addRecipe({
      id: 'stone_pickaxe',
      name: 'Stone Pickaxe',
      inputs: [
        { blockType: 3, count: 3 }, // Stone
        { blockType: 4, count: 2 }  // Wood
      ],
      output: { blockType: -2, count: 1 },
      category: 'tools',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'stone_axe',
      name: 'Stone Axe',
      inputs: [
        { blockType: 3, count: 3 }, // Stone
        { blockType: 4, count: 2 }  // Wood
      ],
      output: { blockType: -3, count: 1 },
      category: 'tools',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'stone_shovel',
      name: 'Stone Shovel',
      inputs: [
        { blockType: 3, count: 1 }, // Stone
        { blockType: 4, count: 2 }  // Wood
      ],
      output: { blockType: -4, count: 1 },
      category: 'tools',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'torch',
      name: 'Torch',
      inputs: [
        { blockType: 4, count: 1 }, // Wood
        { blockType: 3, count: 1 }  // Stone
      ],
      output: { blockType: -5, count: 4 },
      category: 'lighting',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'wooden_planks',
      name: 'Wooden Planks',
      inputs: [
        { blockType: 4, count: 1 }  // Wood
      ],
      output: { blockType: -6, count: 4 },
      category: 'building',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'crafting_table',
      name: 'Crafting Table',
      inputs: [
        { blockType: -6, count: 4 }  // Wooden Planks
      ],
      output: { blockType: -7, count: 1 },
      category: 'utility',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'furnace',
      name: 'Furnace',
      inputs: [
        { blockType: 3, count: 8 }  // Stone
      ],
      output: { blockType: -8, count: 1 },
      category: 'utility',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'chest',
      name: 'Chest',
      inputs: [
        { blockType: -6, count: 8 }  // Wooden Planks
      ],
      output: { blockType: -9, count: 1 },
      category: 'storage',
      unlocked: true
    });
    
    // Metal tool recipes
    this.addRecipe({
      id: 'iron_pickaxe',
      name: 'Iron Pickaxe',
      inputs: [
        { blockType: 100, count: 3 }, // Iron (first metal)
        { blockType: 4, count: 2 }    // Wood
      ],
      output: { blockType: -10, count: 1 },
      category: 'tools',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'iron_sword',
      name: 'Iron Sword',
      inputs: [
        { blockType: 100, count: 2 }, // Iron
        { blockType: 4, count: 1 }    // Wood
      ],
      output: { blockType: -11, count: 1 },
      category: 'weapons',
      unlocked: true
    });
    
    // Building blocks
    this.addRecipe({
      id: 'stone_bricks',
      name: 'Stone Bricks',
      inputs: [
        { blockType: 3, count: 4 }    // Stone
      ],
      output: { blockType: -12, count: 4 },
      category: 'building',
      unlocked: true
    });
    
    this.addRecipe({
      id: 'glass',
      name: 'Glass',
      inputs: [
        { blockType: 6, count: 1 }    // Sand
      ],
      output: { blockType: -13, count: 1 },
      category: 'building',
      unlocked: true
    });
    
    // Advanced recipes
    this.addRecipe({
      id: 'metal_alloy',
      name: 'Metal Alloy',
      inputs: [
        { blockType: 100, count: 1 }, // Iron
        { blockType: 101, count: 1 }  // Copper
      ],
      output: { blockType: -14, count: 2 },
      category: 'materials',
      unlocked: false
    });
    
    console.log(`Loaded ${this.recipes.size} crafting recipes`);
  }
  
  private addRecipe(recipe: CraftingRecipe): void {
    this.recipes.set(recipe.id, recipe);
    if (recipe.unlocked) {
      this.unlockedRecipes.add(recipe.id);
    }
  }
  
  canCraft(recipeId: string, inventory: Map<number, number>): boolean {
    const recipe = this.recipes.get(recipeId);
    if (!recipe) return false;
    
    // Check if recipe is unlocked
    if (!this.unlockedRecipes.has(recipeId)) return false;
    
    // Check if player has all required materials
    for (const input of recipe.inputs) {
      const available = inventory.get(input.blockType) || 0;
      if (available < input.count) {
        return false;
      }
    }
    
    return true;
  }
  
  craft(recipeId: string, inventory: Map<number, number>): boolean {
    if (!this.canCraft(recipeId, inventory)) {
      return false;
    }
    
    const recipe = this.recipes.get(recipeId)!;
    
    // Remove input materials
    for (const input of recipe.inputs) {
      const current = inventory.get(input.blockType)!;
      inventory.set(input.blockType, current - input.count);
    }
    
    // Add output
    const currentOutput = inventory.get(recipe.output.blockType) || 0;
    inventory.set(recipe.output.blockType, currentOutput + recipe.output.count);
    
    return true;
  }
  
  getRecipesByCategory(category: string): CraftingRecipe[] {
    return Array.from(this.recipes.values()).filter(
      recipe => recipe.category === category && this.unlockedRecipes.has(recipe.id)
    );
  }
  
  getAllRecipes(): CraftingRecipe[] {
    return Array.from(this.recipes.values()).filter(
      recipe => this.unlockedRecipes.has(recipe.id)
    );
  }
  
  unlockRecipe(recipeId: string): void {
    if (this.recipes.has(recipeId)) {
      this.unlockedRecipes.add(recipeId);
    }
  }
  
  getCategories(): string[] {
    const categories = new Set<string>();
    this.recipes.forEach(recipe => {
      if (this.unlockedRecipes.has(recipe.id)) {
        categories.add(recipe.category);
      }
    });
    return Array.from(categories);
  }
}
