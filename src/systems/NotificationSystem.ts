/**
 * Notification System - Handles in-game notifications and messages
 */

export type NotificationType = 'info' | 'success' | 'warning' | 'error' | 'achievement' | 'quest';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: number;
  duration: number;
  icon?: string;
  sound?: boolean;
  persistent?: boolean;
}

export class NotificationSystem {
  private notifications: Map<string, Notification> = new Map();
  private notificationQueue: Notification[] = [];
  private nextId: number = 0;
  private maxNotifications: number = 5;
  private defaultDuration: number = 3000;
  
  private listeners: Array<(notification: Notification) => void> = [];
  
  constructor() {
    console.log('Notification System initialized');
  }
  
  notify(
    title: string,
    message: string,
    type: NotificationType = 'info',
    duration?: number
  ): string {
    const notification: Notification = {
      id: `notification_${this.nextId++}`,
      type,
      title,
      message,
      timestamp: Date.now(),
      duration: duration || this.defaultDuration,
      sound: true
    };
    
    this.addNotification(notification);
    return notification.id;
  }
  
  info(title: string, message: string, duration?: number): string {
    return this.notify(title, message, 'info', duration);
  }
  
  success(title: string, message: string, duration?: number): string {
    return this.notify(title, message, 'success', duration);
  }
  
  warning(title: string, message: string, duration?: number): string {
    return this.notify(title, message, 'warning', duration);
  }
  
  error(title: string, message: string, duration?: number): string {
    return this.notify(title, message, 'error', duration);
  }
  
  achievement(title: string, message: string, icon?: string): string {
    const notification: Notification = {
      id: `notification_${this.nextId++}`,
      type: 'achievement',
      title,
      message,
      timestamp: Date.now(),
      duration: 5000,
      icon,
      sound: true
    };
    
    this.addNotification(notification);
    console.log(`🏆 Achievement: ${title}`);
    return notification.id;
  }
  
  quest(title: string, message: string): string {
    const notification: Notification = {
      id: `notification_${this.nextId++}`,
      type: 'quest',
      title,
      message,
      timestamp: Date.now(),
      duration: 4000,
      icon: '📜',
      sound: true
    };
    
    this.addNotification(notification);
    return notification.id;
  }
  
  persistent(title: string, message: string, type: NotificationType = 'info'): string {
    const notification: Notification = {
      id: `notification_${this.nextId++}`,
      type,
      title,
      message,
      timestamp: Date.now(),
      duration: -1,
      persistent: true,
      sound: false
    };
    
    this.addNotification(notification);
    return notification.id;
  }
  
  private addNotification(notification: Notification): void {
    // Add to queue if at max capacity
    if (this.notifications.size >= this.maxNotifications) {
      this.notificationQueue.push(notification);
      return;
    }
    
    this.notifications.set(notification.id, notification);
    this.notifyListeners(notification);
    
    // Auto-remove after duration (if not persistent)
    if (notification.duration > 0 && !notification.persistent) {
      setTimeout(() => {
        this.remove(notification.id);
      }, notification.duration);
    }
  }
  
  remove(notificationId: string): boolean {
    const removed = this.notifications.delete(notificationId);
    
    if (removed) {
      // Process queue
      if (this.notificationQueue.length > 0) {
        const next = this.notificationQueue.shift();
        if (next) {
          this.addNotification(next);
        }
      }
    }
    
    return removed;
  }
  
  clear(): void {
    this.notifications.clear();
    this.notificationQueue = [];
  }
  
  clearType(type: NotificationType): void {
    const toRemove: string[] = [];
    
    this.notifications.forEach((notification, id) => {
      if (notification.type === type) {
        toRemove.push(id);
      }
    });
    
    toRemove.forEach(id => this.remove(id));
  }
  
  getNotification(id: string): Notification | undefined {
    return this.notifications.get(id);
  }
  
  getAllNotifications(): Notification[] {
    return Array.from(this.notifications.values());
  }
  
  getNotificationsByType(type: NotificationType): Notification[] {
    return Array.from(this.notifications.values()).filter(n => n.type === type);
  }
  
  getActiveCount(): number {
    return this.notifications.size;
  }
  
  getQueuedCount(): number {
    return this.notificationQueue.length;
  }
  
  hasNotification(id: string): boolean {
    return this.notifications.has(id);
  }
  
  onNotification(callback: (notification: Notification) => void): void {
    this.listeners.push(callback);
  }
  
  private notifyListeners(notification: Notification): void {
    this.listeners.forEach(listener => listener(notification));
  }
  
  // Specific notification shortcuts
  itemPickedUp(itemName: string, count: number): void {
    this.info('Item Picked Up', `+${count}x ${itemName}`, 2000);
  }
  
  itemCrafted(itemName: string, count: number): void {
    this.success('Item Crafted', `Created ${count}x ${itemName}`, 2500);
  }
  
  blockMined(blockType: string): void {
    if (Math.random() < 0.2) { // Only show 20% of the time to avoid spam
      this.info('Block Mined', blockType, 1500);
    }
  }
  
  toolBroken(toolName: string): void {
    this.warning('Tool Broken', `Your ${toolName} broke!`, 3000);
  }
  
  playerDied(cause: string): void {
    this.error('You Died!', `Cause: ${cause}`, 5000);
  }
  
  questStarted(questName: string): void {
    this.quest('Quest Started', questName);
  }
  
  questCompleted(questName: string): void {
    this.success('Quest Completed', questName, 4000);
  }
  
  achievementUnlocked(achievementName: string, icon?: string): void {
    this.achievement(achievementName, 'Achievement Unlocked!', icon);
  }
  
  levelUp(newLevel: number): void {
    this.success('Level Up!', `You are now level ${newLevel}`, 4000);
  }
  
  healthLow(): void {
    this.warning('Low Health', 'Find food or heal!', 3000);
  }
  
  hungerLow(): void {
    this.warning('Low Hunger', 'You need to eat soon!', 3000);
  }
  
  enemyNearby(enemyName: string): void {
    this.warning('Enemy Nearby', `${enemyName} is approaching!`, 2500);
  }
  
  treasureFound(): void {
    this.success('Treasure Found!', 'You discovered something valuable!', 3500);
  }
  
  biomeEntered(biomeName: string): void {
    this.info('Biome', `Entered ${biomeName}`, 3000);
  }
  
  weatherChanged(weatherType: string): void {
    this.info('Weather', `Weather changed to ${weatherType}`, 2500);
  }
  
  dayNightTransition(timeOfDay: string): void {
    const messages = {
      dawn: 'The sun is rising',
      day: 'It is now daytime',
      dusk: 'The sun is setting',
      night: 'Night has fallen'
    };
    
    const message = messages[timeOfDay as keyof typeof messages] || timeOfDay;
    this.info('Time', message, 2000);
  }
  
  commandExecuted(command: string, result: string): void {
    this.info('Command', result, 2500);
  }
  
  serverMessage(message: string): void {
    this.info('Server', message, 3000);
  }
  
  debugMessage(message: string): void {
    this.info('Debug', message, 2000);
  }
}
