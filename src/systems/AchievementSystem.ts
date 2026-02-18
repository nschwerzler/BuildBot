/**
 * Achievement System - Tracks player progress and rewards
 */

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  requirement: number;
  progress: number;
  unlocked: boolean;
  reward?: { type: string; value: any };
}

export class AchievementSystem {
  private achievements: Map<string, Achievement> = new Map();
  private listeners: Array<(achievement: Achievement) => void> = [];
  
  constructor() {
    this.initializeAchievements();
  }
  
  private initializeAchievements(): void {
    // Mining achievements
    this.addAchievement({
      id: 'first_block',
      name: 'Getting Wood',
      description: 'Mine your first block',
      icon: '🪓',
      category: 'mining',
      requirement: 1,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'miner',
      name: 'Miner',
      description: 'Mine 100 blocks',
      icon: '⛏️',
      category: 'mining',
      requirement: 100,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'master_miner',
      name: 'Master Miner',
      description: 'Mine 1000 blocks',
      icon: '💎',
      category: 'mining',
      requirement: 1000,
      progress: 0,
      unlocked: false
    });
    
    // Building achievements
    this.addAchievement({
      id: 'first_place',
      name: 'Builder',
      description: 'Place your first block',
      icon: '🧱',
      category: 'building',
      requirement: 1,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'architect',
      name: 'Architect',
      description: 'Place 500 blocks',
      icon: '🏗️',
      category: 'building',
      requirement: 500,
      progress: 0,
      unlocked: false
    });
    
    // Exploration achievements
    this.addAchievement({
      id: 'explorer',
      name: 'Explorer',
      description: 'Walk 1000 blocks',
      icon: '🗺️',
      category: 'exploration',
      requirement: 1000,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'adventurer',
      name: 'Adventurer',
      description: 'Walk 10000 blocks',
      icon: '🧭',
      category: 'exploration',
      requirement: 10000,
      progress: 0,
      unlocked: false
    });
    
    // Collection achievements
    this.addAchievement({
      id: 'metal_collector',
      name: 'Metal Collector',
      description: 'Collect 10 different metals',
      icon: '⚙️',
      category: 'collection',
      requirement: 10,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'metal_master',
      name: 'Metal Master',
      description: 'Collect 50 different metals',
      icon: '🏆',
      category: 'collection',
      requirement: 50,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'metal_legend',
      name: 'Metal Legend',
      description: 'Collect 100 different metals',
      icon: '👑',
      category: 'collection',
      requirement: 100,
      progress: 0,
      unlocked: false
    });
    
    // Crafting achievements
    this.addAchievement({
      id: 'first_craft',
      name: 'Craftsman',
      description: 'Craft your first item',
      icon: '🔨',
      category: 'crafting',
      requirement: 1,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'master_crafter',
      name: 'Master Crafter',
      description: 'Craft 50 items',
      icon: '⚒️',
      category: 'crafting',
      requirement: 50,
      progress: 0,
      unlocked: false
    });
    
    // Special achievements
    this.addAchievement({
      id: 'first_jump',
      name: 'Up We Go',
      description: 'Jump for the first time',
      icon: '⬆️',
      category: 'special',
      requirement: 1,
      progress: 0,
      unlocked: false
    });
    
    this.addAchievement({
      id: 'speedrunner',
      name: 'Speedrunner',
      description: 'Sprint for 100 blocks',
      icon: '💨',
      category: 'special',
      requirement: 100,
      progress: 0,
      unlocked: false
    });
    
    console.log(`Loaded ${this.achievements.size} achievements`);
  }
  
  private addAchievement(achievement: Achievement): void {
    this.achievements.set(achievement.id, achievement);
  }
  
  updateProgress(achievementId: string, amount: number = 1): boolean {
    const achievement = this.achievements.get(achievementId);
    if (!achievement || achievement.unlocked) return false;
    
    achievement.progress += amount;
    
    if (achievement.progress >= achievement.requirement) {
      achievement.unlocked = true;
      achievement.progress = achievement.requirement;
      this.notifyUnlock(achievement);
      return true;
    }
    
    return false;
  }
  
  setProgress(achievementId: string, progress: number): boolean {
    const achievement = this.achievements.get(achievementId);
    if (!achievement || achievement.unlocked) return false;
    
    achievement.progress = Math.min(progress, achievement.requirement);
    
    if (achievement.progress >= achievement.requirement) {
      achievement.unlocked = true;
      this.notifyUnlock(achievement);
      return true;
    }
    
    return false;
  }
  
  private notifyUnlock(achievement: Achievement): void {
    console.log(`🏆 Achievement Unlocked: ${achievement.name}`);
    this.listeners.forEach(listener => listener(achievement));
  }
  
  onAchievementUnlocked(callback: (achievement: Achievement) => void): void {
    this.listeners.push(callback);
  }
  
  getAchievement(id: string): Achievement | undefined {
    return this.achievements.get(id);
  }
  
  getAllAchievements(): Achievement[] {
    return Array.from(this.achievements.values());
  }
  
  getAchievementsByCategory(category: string): Achievement[] {
    return Array.from(this.achievements.values()).filter(
      a => a.category === category
    );
  }
  
  getUnlockedCount(): number {
    return Array.from(this.achievements.values()).filter(a => a.unlocked).length;
  }
  
  getTotalCount(): number {
    return this.achievements.size;
  }
  
  getCompletionPercentage(): number {
    const total = this.getTotalCount();
    const unlocked = this.getUnlockedCount();
    return total > 0 ? (unlocked / total) * 100 : 0;
  }
}
