/**
 * UI Manager - Manages all game UI elements and screens
 */

export type UIScreen = 'game' | 'inventory' | 'crafting' | 'settings' | 'achievements' | 'quests' | 'pause';

export interface UIElement {
  id: string;
  type: 'text' | 'button' | 'panel' | 'image' | 'progressBar' | 'list';
  element: HTMLElement;
  visible: boolean;
  parent?: string;
}

export class UIManager {
  private elements: Map<string, UIElement> = new Map();
  private currentScreen: UIScreen = 'game';
  private screens: Map<UIScreen, Set<string>> = new Map();
  
  constructor() {
    this.initializeScreens();
    this.setupBaseUI();
  }
  
  private initializeScreens(): void {
    this.screens.set('game', new Set(['hotbar', 'crosshair', 'health', 'hunger', 'time']));
    this.screens.set('inventory', new Set(['inventory_panel', 'close_button']));
    this.screens.set('crafting', new Set(['crafting_panel', 'recipe_list', 'close_button']));
    this.screens.set('settings', new Set(['settings_panel', 'close_button']));
    this.screens.set('achievements', new Set(['achievement_panel', 'close_button']));
    this.screens.set('quests', new Set(['quest_panel', 'close_button']));
    this.screens.set('pause', new Set(['pause_menu', 'resume_button', 'settings_button', 'quit_button']));
  }
  
  private setupBaseUI(): void {
    // Crosshair
    this.createElement('crosshair', 'text', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.color = 'white';
      el.style.fontSize = '24px';
      el.style.pointerEvents = 'none';
      el.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
      el.textContent = '+';
    });
    
    // Health bar
    this.createElement('health', 'progressBar', (el) => {
      el.style.position = 'fixed';
      el.style.bottom = '80px';
      el.style.left = '20px';
      el.style.width = '200px';
      el.style.height = '20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.5)';
      el.style.border = '2px solid #fff';
      el.innerHTML = '<div style="width: 100%; height: 100%; background-color: #ff0000;"></div>';
    });
    
    // Hunger bar
    this.createElement('hunger', 'progressBar', (el) => {
      el.style.position = 'fixed';
      el.style.bottom = '50px';
      el.style.left = '20px';
      el.style.width = '200px';
      el.style.height = '20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.5)';
      el.style.border = '2px solid #fff';
      el.innerHTML = '<div style="width: 100%; height: 100%; background-color: #ffa500;"></div>';
    });
    
    // Time display
    this.createElement('time', 'text', (el) => {
      el.style.position = 'fixed';
      el.style.top = '20px';
      el.style.right = '20px';
      el.style.color = 'white';
      el.style.fontSize = '18px';
      el.style.fontFamily = 'monospace';
      el.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
      el.style.padding = '10px';
      el.style.backgroundColor = 'rgba(0,0,0,0.3)';
      el.textContent = 'Day 1 - 12:00 PM';
    });
    
    // Inventory button
    this.createElement('inventory_button', 'button', (el) => {
      el.style.position = 'fixed';
      el.style.top = '20px';
      el.style.left = '20px';
      el.style.padding = '10px 20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.7)';
      el.style.color = 'white';
      el.style.border = '2px solid #fff';
      el.style.cursor = 'pointer';
      el.style.fontSize = '16px';
      el.textContent = 'Inventory (E)';
      el.addEventListener('click', () => this.switchScreen('inventory'));
    });
    
    // Crafting button
    this.createElement('crafting_button', 'button', (el) => {
      el.style.position = 'fixed';
      el.style.top = '70px';
      el.style.left = '20px';
      el.style.padding = '10px 20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.7)';
      el.style.color = 'white';
      el.style.border = '2px solid #fff';
      el.style.cursor = 'pointer';
      el.style.fontSize = '16px';
      el.textContent = 'Crafting (C)';
      el.addEventListener('click', () => this.switchScreen('crafting'));
    });
    
    // Achievements button
    this.createElement('achievements_button', 'button', (el) => {
      el.style.position = 'fixed';
      el.style.top = '120px';
      el.style.left = '20px';
      el.style.padding = '10px 20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.7)';
      el.style.color = 'white';
      el.style.border = '2px solid #fff';
      el.style.cursor = 'pointer';
      el.style.fontSize = '16px';
      el.textContent = 'Achievements (A)';
      el.addEventListener('click', () => this.switchScreen('achievements'));
    });
    
    // Quests button
    this.createElement('quests_button', 'button', (el) => {
      el.style.position = 'fixed';
      el.style.top = '170px';
      el.style.left = '20px';
      el.style.padding = '10px 20px';
      el.style.backgroundColor = 'rgba(0,0,0,0.7)';
      el.style.color = 'white';
      el.style.border = '2px solid #fff';
      el.style.cursor = 'pointer';
      el.style.fontSize = '16px';
      el.textContent = 'Quests (Q)';
      el.addEventListener('click', () => this.switchScreen('quests'));
    });
    
    // FPS counter
    this.createElement('fps', 'text', (el) => {
      el.style.position = 'fixed';
      el.style.top = '60px';
      el.style.right = '20px';
      el.style.color = '#00ff00';
      el.style.fontSize = '14px';
      el.style.fontFamily = 'monospace';
      el.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
      el.textContent = 'FPS: 60';
    });
    
    // Debug info
    this.createElement('debug', 'text', (el) => {
      el.style.position = 'fixed';
      el.style.bottom = '20px';
      el.style.right = '20px';
      el.style.color = 'white';
      el.style.fontSize = '12px';
      el.style.fontFamily = 'monospace';
      el.style.textShadow = '2px 2px 4px rgba(0,0,0,0.8)';
      el.style.textAlign = 'right';
      el.style.lineHeight = '1.5';
      el.textContent = 'Position: 0, 0, 0';
    });
  }
  
  createElement(
    id: string,
    type: UIElement['type'],
    setup: (element: HTMLElement) => void
  ): UIElement {
    const element = document.createElement('div');
    element.id = id;
    setup(element);
    document.body.appendChild(element);
    
    const uiElement: UIElement = {
      id,
      type,
      element,
      visible: true
    };
    
    this.elements.set(id, uiElement);
    return uiElement;
  }
  
  createInventoryPanel(): void {
    this.createElement('inventory_panel', 'panel', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.width = '600px';
      el.style.height = '400px';
      el.style.backgroundColor = 'rgba(0,0,0,0.9)';
      el.style.border = '4px solid #fff';
      el.style.padding = '20px';
      el.style.color = 'white';
      el.style.display = 'none';
      el.style.overflowY = 'auto';
      el.innerHTML = '<h2>Inventory</h2><div id="inventory_grid"></div>';
    });
  }
  
  createCraftingPanel(): void {
    this.createElement('crafting_panel', 'panel', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.width = '700px';
      el.style.height = '500px';
      el.style.backgroundColor = 'rgba(0,0,0,0.9)';
      el.style.border = '4px solid #fff';
      el.style.padding = '20px';
      el.style.color = 'white';
      el.style.display = 'none';
      el.style.overflowY = 'auto';
      el.innerHTML = '<h2>Crafting</h2><div id="recipe_list"></div>';
    });
  }
  
  createAchievementPanel(): void {
    this.createElement('achievement_panel', 'panel', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.width = '600px';
      el.style.height = '500px';
      el.style.backgroundColor = 'rgba(0,0,0,0.9)';
      el.style.border = '4px solid #fff';
      el.style.padding = '20px';
      el.style.color = 'white';
      el.style.display = 'none';
      el.style.overflowY = 'auto';
      el.innerHTML = '<h2>Achievements</h2><div id="achievement_list"></div>';
    });
  }
  
  createQuestPanel(): void {
    this.createElement('quest_panel', 'panel', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.width = '600px';
      el.style.height = '500px';
      el.style.backgroundColor = 'rgba(0,0,0,0.9)';
      el.style.border = '4px solid #fff';
      el.style.padding = '20px';
      el.style.color = 'white';
      el.style.display = 'none';
      el.style.overflowY = 'auto';
      el.innerHTML = '<h2>Quests</h2><div id="quest_list"></div>';
    });
  }
  
  createSettingsPanel(): void {
    this.createElement('settings_panel', 'panel', (el) => {
      el.style.position = 'fixed';
      el.style.top = '50%';
      el.style.left = '50%';
      el.style.transform = 'translate(-50%, -50%)';
      el.style.width = '500px';
      el.style.height = '400px';
      el.style.backgroundColor = 'rgba(0,0,0,0.9)';
      el.style.border = '4px solid #fff';
      el.style.padding = '20px';
      el.style.color = 'white';
      el.style.display = 'none';
      el.innerHTML = '<h2>Settings</h2><div id="settings_content"></div>';
    });
  }
  
  switchScreen(screen: UIScreen): void {
    // Hide all screens first
    this.screens.forEach((elementIds, screenName) => {
      elementIds.forEach(id => {
        const element = this.elements.get(id);
        if (element) {
          this.hide(id);
        }
      });
    });
    
    // Show requested screen
    this.currentScreen = screen;
    const elementIds = this.screens.get(screen);
    if (elementIds) {
      elementIds.forEach(id => {
        const element = this.elements.get(id);
        if (element) {
          this.show(id);
        }
      });
    }
  }
  
  show(elementId: string): void {
    const element = this.elements.get(elementId);
    if (element) {
      element.visible = true;
      element.element.style.display = 'block';
    }
  }
  
  hide(elementId: string): void {
    const element = this.elements.get(elementId);
    if (element) {
      element.visible = false;
      element.element.style.display = 'none';
    }
  }
  
  toggle(elementId: string): void {
    const element = this.elements.get(elementId);
    if (element) {
      if (element.visible) {
        this.hide(elementId);
      } else {
        this.show(elementId);
      }
    }
  }
  
  updateText(elementId: string, text: string): void {
    const element = this.elements.get(elementId);
    if (element && element.element) {
      element.element.textContent = text;
    }
  }
  
  updateHTML(elementId: string, html: string): void {
    const element = this.elements.get(elementId);
    if (element && element.element) {
      element.element.innerHTML = html;
    }
  }
  
  updateProgressBar(elementId: string, percent: number): void {
    const element = this.elements.get(elementId);
    if (element && element.element) {
      const bar = element.element.querySelector('div');
      if (bar) {
        (bar as HTMLElement).style.width = `${Math.max(0, Math.min(100, percent))}%`;
      }
    }
  }
  
  showNotification(message: string, duration: number = 3000): void {
    const notification = document.createElement('div');
    notification.style.position = 'fixed';
    notification.style.top = '100px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.padding = '15px 30px';
    notification.style.backgroundColor = 'rgba(0,0,0,0.8)';
    notification.style.color = 'white';
    notification.style.border = '2px solid #fff';
    notification.style.fontSize = '18px';
    notification.style.zIndex = '10000';
    notification.style.textAlign = 'center';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.opacity = '0';
      notification.style.transition = 'opacity 0.5s';
      setTimeout(() => document.body.removeChild(notification), 500);
    }, duration);
  }
  
  getCurrentScreen(): UIScreen {
    return this.currentScreen;
  }
  
  isScreenOpen(screen: UIScreen): boolean {
    return this.currentScreen === screen;
  }
  
  getElement(id: string): UIElement | undefined {
    return this.elements.get(id);
  }
  
  removeElement(id: string): boolean {
    const element = this.elements.get(id);
    if (element) {
      document.body.removeChild(element.element);
      this.elements.delete(id);
      return true;
    }
    return false;
  }
}
