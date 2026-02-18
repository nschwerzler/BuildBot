/**
 * Quest System - Manages player quests and objectives
 */

export interface QuestObjective {
  id: string;
  description: string;
  type: 'mine' | 'craft' | 'collect' | 'explore' | 'build' | 'kill';
  target: string;
  required: number;
  current: number;
  completed: boolean;
}

export interface Quest {
  id: string;
  title: string;
  description: string;
  objectives: QuestObjective[];
  rewards: {
    items?: Array<{ type: string; count: number }>;
    experience?: number;
  };
  status: 'locked' | 'available' | 'active' | 'completed';
  prerequisites?: string[];
}

export class QuestSystem {
  private quests: Map<string, Quest> = new Map();
  private activeQuests: Set<string> = new Set();
  private completedQuests: Set<string> = new Set();
  private questListeners: Array<(quest: Quest) => void> = [];
  
  constructor() {
    this.initializeQuests();
  }
  
  private initializeQuests(): void {
    // Tutorial quests
    this.addQuest({
      id: 'tutorial_1',
      title: 'Welcome to the World',
      description: 'Learn the basics of survival',
      objectives: [
        {
          id: 'mine_blocks',
          description: 'Mine 5 blocks',
          type: 'mine',
          target: 'any',
          required: 5,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'wood', count: 10 }]
      },
      status: 'available'
    });
    
    this.addQuest({
      id: 'tutorial_2',
      title: 'Getting Started',
      description: 'Craft your first tool',
      objectives: [
        {
          id: 'craft_pickaxe',
          description: 'Craft a pickaxe',
          type: 'craft',
          target: 'stone_pickaxe',
          required: 1,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'stone', count: 20 }],
        experience: 50
      },
      status: 'locked',
      prerequisites: ['tutorial_1']
    });
    
    this.addQuest({
      id: 'tutorial_3',
      title: 'Building Foundations',
      description: 'Start building your base',
      objectives: [
        {
          id: 'place_blocks',
          description: 'Place 20 blocks',
          type: 'build',
          target: 'any',
          required: 20,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'torch', count: 5 }],
        experience: 75
      },
      status: 'locked',
      prerequisites: ['tutorial_2']
    });
    
    // Mining quests
    this.addQuest({
      id: 'mining_1',
      title: 'Deep Digger',
      description: 'Mine deep into the earth',
      objectives: [
        {
          id: 'mine_stone',
          description: 'Mine 50 stone blocks',
          type: 'mine',
          target: 'stone',
          required: 50,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'iron_pickaxe', count: 1 }],
        experience: 100
      },
      status: 'locked',
      prerequisites: ['tutorial_3']
    });
    
    this.addQuest({
      id: 'mining_2',
      title: 'Metal Hunter',
      description: 'Collect various metals',
      objectives: [
        {
          id: 'collect_metals',
          description: 'Collect 5 different metal types',
          type: 'collect',
          target: 'metal',
          required: 5,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        experience: 150
      },
      status: 'locked',
      prerequisites: ['mining_1']
    });
    
    // Exploration quests
    this.addQuest({
      id: 'explore_1',
      title: 'First Steps',
      description: 'Explore the world around you',
      objectives: [
        {
          id: 'walk_distance',
          description: 'Walk 500 blocks',
          type: 'explore',
          target: 'distance',
          required: 500,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'food', count: 10 }],
        experience: 100
      },
      status: 'available'
    });
    
    this.addQuest({
      id: 'explore_2',
      title: 'Far Lands',
      description: 'Venture far from spawn',
      objectives: [
        {
          id: 'reach_distance',
          description: 'Get 200 blocks away from spawn',
          type: 'explore',
          target: 'spawn_distance',
          required: 200,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'compass', count: 1 }],
        experience: 200
      },
      status: 'locked',
      prerequisites: ['explore_1']
    });
    
    // Building quests
    this.addQuest({
      id: 'build_1',
      title: 'Architect',
      description: 'Build a structure',
      objectives: [
        {
          id: 'place_many_blocks',
          description: 'Place 100 blocks',
          type: 'build',
          target: 'any',
          required: 100,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'stone_bricks', count: 50 }],
        experience: 150
      },
      status: 'locked',
      prerequisites: ['tutorial_3']
    });
    
    // Crafting quests
    this.addQuest({
      id: 'craft_1',
      title: 'Master Craftsman',
      description: 'Become skilled at crafting',
      objectives: [
        {
          id: 'craft_items',
          description: 'Craft 20 items',
          type: 'craft',
          target: 'any',
          required: 20,
          current: 0,
          completed: false
        }
      ],
      rewards: {
        items: [{ type: 'crafting_table', count: 1 }],
        experience: 250
      },
      status: 'locked',
      prerequisites: ['tutorial_2']
    });
    
    console.log(`Loaded ${this.quests.size} quests`);
  }
  
  private addQuest(quest: Quest): void {
    this.quests.set(quest.id, quest);
  }
  
  startQuest(questId: string): boolean {
    const quest = this.quests.get(questId);
    if (!quest) return false;
    
    if (quest.status !== 'available') {
      console.warn(`Quest ${questId} is not available`);
      return false;
    }
    
    quest.status = 'active';
    this.activeQuests.add(questId);
    console.log(`📜 Started quest: ${quest.title}`);
    return true;
  }
  
  updateObjective(questId: string, objectiveId: string, amount: number = 1): void {
    const quest = this.quests.get(questId);
    if (!quest || quest.status !== 'active') return;
    
    const objective = quest.objectives.find(o => o.id === objectiveId);
    if (!objective || objective.completed) return;
    
    objective.current = Math.min(objective.current + amount, objective.required);
    
    if (objective.current >= objective.required) {
      objective.completed = true;
      console.log(`✓ Objective completed: ${objective.description}`);
      
      // Check if all objectives are complete
      if (quest.objectives.every(o => o.completed)) {
        this.completeQuest(questId);
      }
    }
  }
  
  private completeQuest(questId: string): void {
    const quest = this.quests.get(questId);
    if (!quest) return;
    
    quest.status = 'completed';
    this.activeQuests.delete(questId);
    this.completedQuests.add(questId);
    
    console.log(`🎊 Quest completed: ${quest.title}`);
    this.questListeners.forEach(listener => listener(quest));
    
    // Unlock dependent quests
    this.quests.forEach(q => {
      if (q.status === 'locked' && q.prerequisites?.includes(questId)) {
        const allPrereqsMet = q.prerequisites.every(pre => this.completedQuests.has(pre));
        if (allPrereqsMet) {
          q.status = 'available';
          console.log(`📜 Quest unlocked: ${q.title}`);
        }
      }
    });
  }
  
  onQuestComplete(callback: (quest: Quest) => void): void {
    this.questListeners.push(callback);
  }
  
  getQuest(id: string): Quest | undefined {
    return this.quests.get(id);
  }
  
  getActiveQuests(): Quest[] {
    return Array.from(this.activeQuests)
      .map(id => this.quests.get(id))
      .filter((q): q is Quest => q !== undefined);
  }
  
  getAvailableQuests(): Quest[] {
    return Array.from(this.quests.values()).filter(q => q.status === 'available');
  }
  
  getCompletedQuests(): Quest[] {
    return Array.from(this.completedQuests)
      .map(id => this.quests.get(id))
      .filter((q): q is Quest => q !== undefined);
  }
  
  getAllQuests(): Quest[] {
    return Array.from(this.quests.values());
  }
}
