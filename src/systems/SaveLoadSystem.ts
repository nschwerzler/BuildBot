import * as THREE from 'three';
import type { Inventory } from './Inventory';
import type { MetalRegistry } from './MetalRegistry';

/**
 * Save/Load System - Manages game state persistence
 */

export interface PlayerData {
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number };
  health: number;
  hunger: number;
  inventory: any[];
  achievements: string[];
  completedQuests: string[];
  statistics: Record<string, number>;
}

export interface WorldData {
  seed: number;
  spawnPosition: { x: number; y: number; z: number };
  timeOfDay: number;
  weather: string;
  placedBlocks: Array<{
    position: { x: number; y: number; z: number };
    type: string;
  }>;
  removedBlocks: Array<{
    position: { x: number; y: number; z: number };
  }>;
  structures: Array<{
    id: string;
    position: { x: number; y: number; z: number };
    rotation: number;
  }>;
}

export interface GameSave {
  version: string;
  timestamp: number;
  saveName: string;
  playTime: number;
  player: PlayerData;
  world: WorldData;
  settings: any;
}

export class SaveLoadSystem {
  private readonly VERSION = '1.0.0';
  private readonly SAVE_PREFIX = 'game_save_';
  private currentSave: GameSave | null = null;
  private autoSaveInterval: number = 300000; // 5 minutes
  private lastAutoSave: number = 0;
  
  constructor() {
    console.log('Save/Load System initialized');
  }
  
  createNewSave(saveName: string): GameSave {
    return {
      version: this.VERSION,
      timestamp: Date.now(),
      saveName,
      playTime: 0,
      player: {
        position: { x: 0, y: 65, z: 0 },
        rotation: { x: 0, y: 0 },
        health: 20,
        hunger: 20,
        inventory: [],
        achievements: [],
        completedQuests: [],
        statistics: {
          blocksMin ed: 0,
          blocksPlaced: 0,
          distanceWalked: 0,
          itemsCrafted: 0,
          mobsKilled: 0,
          deaths: 0,
          playTime: 0
        }
      },
      world: {
        seed: Math.floor(Math.random() * 1000000),
        spawnPosition: { x: 0, y: 65, z: 0 },
        timeOfDay: 6,
        weather: 'clear',
        placedBlocks: [],
        removedBlocks: [],
        structures: []
      },
      settings: {}
    };
  }
  
  saveGame(saveData: GameSave): boolean {
    try {
      saveData.timestamp = Date.now();
      
      const saveKey = this.SAVE_PREFIX + this.sanitizeSaveName(saveData.saveName);
      const serialized = JSON.stringify(saveData);
      
      localStorage.setItem(saveKey, serialized);
      
      // Update save list
      this.updateSaveList(saveData.saveName);
      
      this.currentSave = saveData;
      console.log(`💾 Game saved: ${saveData.saveName}`);
      return true;
    } catch (error) {
      console.error('Failed to save game:', error);
      return false;
    }
  }
  
  loadGame(saveName: string): GameSave | null {
    try {
      const saveKey = this.SAVE_PREFIX + this.sanitizeSaveName(saveName);
      const serialized = localStorage.getItem(saveKey);
      
      if (!serialized) {
        console.error(`Save not found: ${saveName}`);
        return null;
      }
      
      const saveData: GameSave = JSON.parse(serialized);
      
      // Validate version
      if (saveData.version !== this.VERSION) {
        console.warn(`Save version mismatch: ${saveData.version} vs ${this.VERSION}`);
        // Could implement migration here
      }
      
      this.currentSave = saveData;
      console.log(`📂 Game loaded: ${saveName}`);
      return saveData;
    } catch (error) {
      console.error('Failed to load game:', error);
      return null;
    }
  }
  
  deleteSave(saveName: string): boolean {
    try {
      const saveKey = this.SAVE_PREFIX + this.sanitizeSaveName(saveName);
      localStorage.removeItem(saveKey);
      
      // Update save list
      const saves = this.getSaveList();
      const filtered = saves.filter(s => s !== saveName);
      localStorage.setItem('save_list', JSON.stringify(filtered));
      
      console.log(`🗑️ Save deleted: ${saveName}`);
      return true;
    } catch (error) {
      console.error('Failed to delete save:', error);
      return false;
    }
  }
  
  getSaveList(): string[] {
    try {
      const list = localStorage.getItem('save_list');
      return list ? JSON.parse(list) : [];
    } catch (error) {
      console.error('Failed to get save list:', error);
      return [];
    }
  }
  
  getSaveInfo(saveName: string): { name: string; timestamp: number; playTime: number } | null {
    try {
      const saveKey = this.SAVE_PREFIX + this.sanitizeSaveName(saveName);
      const serialized = localStorage.getItem(saveKey);
      
      if (!serialized) return null;
      
      const save: GameSave = JSON.parse(serialized);
      return {
        name: save.saveName,
        timestamp: save.timestamp,
        playTime: save.playTime
      };
    } catch (error) {
      return null;
    }
  }
  
  getAllSaveInfo(): Array<{ name: string; timestamp: number; playTime: number }> {
    const saves = this.getSaveList();
    return saves
      .map(name => this.getSaveInfo(name))
      .filter((info): info is { name: string; timestamp: number; playTime: number } => info !== null);
  }
  
  autoSave(saveData: GameSave): void {
    const now = Date.now();
    if (now - this.lastAutoSave >= this.autoSaveInterval) {
      saveData.saveName = saveData.saveName || 'autosave';
      this.saveGame(saveData);
      this.lastAutoSave = now;
      console.log('🔄 Auto-saved');
    }
  }
  
  exportSave(saveName: string): string | null {
    const saveData = this.loadGame(saveName);
    if (!saveData) return null;
    
    return JSON.stringify(saveData, null, 2);
  }
  
  importSave(jsonData: string, saveName?: string): boolean {
    try {
      const saveData: GameSave = JSON.parse(jsonData);
      
      if (saveName) {
        saveData.saveName = saveName;
      }
      
      return this.saveGame(saveData);
    } catch (error) {
      console.error('Failed to import save:', error);
      return false;
    }
  }
  
  private sanitizeSaveName(name: string): string {
    return name.replace(/[^a-zA-Z0-9_-]/g, '_');
  }
  
  private updateSaveList(saveName: string): void {
    const saves = this.getSaveList();
    if (!saves.includes(saveName)) {
      saves.push(saveName);
      localStorage.setItem('save_list', JSON.stringify(saves));
    }
  }
  
  getCurrentSave(): GameSave | null {
    return this.currentSave;
  }
  
  updatePlayerData(playerData: Partial<PlayerData>): void {
    if (this.currentSave) {
      this.currentSave.player = { ...this.currentSave.player, ...playerData };
    }
  }
  
  updateWorldData(worldData: Partial<WorldData>): void {
    if (this.currentSave) {
      this.currentSave.world = { ...this.currentSave.world, ...worldData };
    }
  }
  
  incrementStatistic(stat: string, amount: number = 1): void {
    if (this.currentSave) {
      if (!this.currentSave.player.statistics[stat]) {
        this.currentSave.player.statistics[stat] = 0;
      }
      this.currentSave.player.statistics[stat] += amount;
    }
  }
  
  getStatistic(stat: string): number {
    return this.currentSave?.player.statistics[stat] || 0;
  }
  
  getAllStatistics(): Record<string, number> {
    return this.currentSave?.player.statistics || {};
  }
  
  clearAllSaves(): boolean {
    try {
      const saves = this.getSaveList();
      saves.forEach(saveName => {
        const saveKey = this.SAVE_PREFIX + this.sanitizeSaveName(saveName);
        localStorage.removeItem(saveKey);
      });
      
      localStorage.removeItem('save_list');
      console.log('🗑️ All saves cleared');
      return true;
    } catch (error) {
      console.error('Failed to clear saves:', error);
      return false;
    }
  }
}
