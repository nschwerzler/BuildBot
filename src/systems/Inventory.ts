import { MetalRegistry } from './MetalRegistry';

/**
 * Inventory System - Manages player's items and hotbar
 */
export class Inventory {
  private hotbar: (InventorySlot | null)[];
  private selectedSlot: number = 0;
  
  constructor() {
    // 9 hotbar slots - start empty
    this.hotbar = new Array(9).fill(null);
    
    // Start with a pickaxe in first slot
    this.hotbar[0] = { blockType: -1, count: 1, name: 'Pickaxe' };
  }
  
  /**
   * Add item to inventory
   */
  addItem(blockType: number, count: number = 1): boolean {
    const blockName = this.getBlockName(blockType);
    
    // Try to stack with existing item
    for (let i = 0; i < this.hotbar.length; i++) {
      const slot = this.hotbar[i];
      if (slot && slot.blockType === blockType && slot.count < 64) {
        const addCount = Math.min(count, 64 - slot.count);
        slot.count += addCount;
        count -= addCount;
        
        if (count === 0) {
          this.updateUI();
          return true;
        }
      }
    }
    
    // Try to find empty slot
    for (let i = 0; i < this.hotbar.length; i++) {
      if (!this.hotbar[i]) {
        this.hotbar[i] = {
          blockType,
          count: Math.min(count, 64),
          name: blockName
        };
        count -= Math.min(count, 64);
        
        if (count === 0) {
          this.updateUI();
          return true;
        }
      }
    }
    
    this.updateUI();
    return count === 0;
  }
  
  /**
   * Remove item from selected slot
   */
  removeSelectedItem(count: number = 1): boolean {
    const slot = this.hotbar[this.selectedSlot];
    
    if (!slot || slot.count < count) {
      return false;
    }
    
    slot.count -= count;
    
    if (slot.count === 0) {
      this.hotbar[this.selectedSlot] = null;
    }
    
    this.updateUI();
    return true;
  }
  
  /**
   * Get the block type in selected slot
   */
  getSelectedBlockType(): number | null {
    const slot = this.hotbar[this.selectedSlot];
    return slot ? slot.blockType : null;
  }
  
  /**
   * Check if selected slot has items
   */
  hasSelectedItem(): boolean {
    const slot = this.hotbar[this.selectedSlot];
    return slot !== null && slot.count > 0;
  }
  
  /**
   * Select hotbar slot (0-8)
   */
  selectSlot(index: number): void {
    if (index >= 0 && index < 9) {
      this.selectedSlot = index;
      this.updateUI();
    }
  }
  
  /**
   * Get currently selected slot index
   */
  getSelectedSlot(): number {
    return this.selectedSlot;
  }
  
  /**
   * Get block name from type
   */
  private getBlockName(blockType: number): string {
    // Pickaxe
    if (blockType === -1) {
      return 'Pickaxe';
    }
    
    // Check if it's a metal
    const metal = MetalRegistry.getMetal(blockType);
    if (metal) {
      return metal.name;
    }
    
    const names: { [key: number]: string } = {
      1: 'Grass',
      2: 'Dirt',
      3: 'Stone',
      4: 'Wood',
      5: 'Leaves',
      6: 'Sand',
      7: 'Water',
      8: 'Bed',
      9: 'Chest',
      10: 'Growth Potion',
      11: 'Netherrack',
      12: 'Lava',
      13: 'Planks'
    };
    
    return names[blockType] || 'Unknown';
  }
  
  /**
   * Get block color for UI display
   */
  private getBlockColor(blockType: number): string {
    // Pickaxe
    if (blockType === -1) {
      return '#8b4513';
    }
    
    // Check if it's a metal - use its color
    const metal = MetalRegistry.getMetal(blockType);
    if (metal) {
      return metal.color;
    }
    
    const colors: { [key: number]: string } = {
      1: '#3cb371',
      2: '#8b6343',
      3: '#808080',
      4: '#8b5a2b',
      5: '#228b22',
      6: '#eedd82',
      7: '#4a90e2',
      8: '#cc3333',
      9: '#aa8844',
      10: '#ff44ff',
      11: '#6b2020',
      12: '#dd6600',
      13: '#c09660'
    };
    
    return colors[blockType] || '#ffffff';
  }
  
  /**
   * Update hotbar UI
   */
  private updateUI(): void {
    const slots = document.querySelectorAll('.toolbar-slot');
    
    slots.forEach((slotElement, index) => {
      const slot = this.hotbar[index];
      
      // Clear slot
      slotElement.innerHTML = '';
      
      // Update selected state
      if (index === this.selectedSlot) {
        slotElement.classList.add('selected');
      } else {
        slotElement.classList.remove('selected');
      }
      
      // Add item if present
      if (slot) {
        const itemDiv = document.createElement('div');
        itemDiv.style.width = '100%';
        itemDiv.style.height = '100%';
        itemDiv.style.display = 'flex';
        itemDiv.style.flexDirection = 'column';
        itemDiv.style.alignItems = 'center';
        itemDiv.style.justifyContent = 'center';
        itemDiv.title = slot.name; // Add tooltip with item name
        
        // Item icon (colored square)
        const icon = document.createElement('div');
        icon.style.width = '30px';
        icon.style.height = '30px';
        icon.style.backgroundColor = this.getBlockColor(slot.blockType);
        icon.style.border = '1px solid rgba(255, 255, 255, 0.3)';
        icon.style.imageRendering = 'pixelated';
        icon.style.boxShadow = '0 0 5px ' + this.getBlockColor(slot.blockType);
        
        // Add pickaxe symbol if it's a tool
        if (slot.blockType === -1) {
          icon.textContent = '⛏️';
          icon.style.display = 'flex';
          icon.style.alignItems = 'center';
          icon.style.justifyContent = 'center';
          icon.style.fontSize = '24px';
          icon.style.backgroundColor = 'transparent';
        }
        
        // Item count (don't show count for pickaxe)
        itemDiv.appendChild(icon);
        
        if (slot.blockType !== -1) {
          const count = document.createElement('div');
          count.textContent = slot.count.toString();
          count.style.color = 'white';
          count.style.fontSize = '12px';
          count.style.fontWeight = 'bold';
          count.style.textShadow = '1px 1px 2px black';
          count.style.marginTop = '2px';
          itemDiv.appendChild(count);
        }
        
        slotElement.appendChild(itemDiv);
      }
    });
  }
  
  /**
   * Initialize inventory UI
   */
  init(): void {
    this.updateUI();
  }
}

export interface InventorySlot {
  blockType: number;
  count: number;
  name: string;
}
