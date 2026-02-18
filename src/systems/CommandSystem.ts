/**
 * Command System - Handles debug and admin commands
 */

export type CommandExecutor = (args: string[]) => string;

export interface Command {
  name: string;
  description: string;
  usage: string;
  aliases: string[];
  execute: CommandExecutor;
}

export class CommandSystem {
  private commands: Map<string, Command> = new Map();
  private commandHistory: string[] = [];
  private maxHistory: number = 50;
  private historyIndex: number = -1;
  
  constructor() {
    this.registerDefaultCommands();
    console.log('Command System initialized');
  }
  
  private registerDefaultCommands(): void {
    // Help command
    this.registerCommand({
      name: 'help',
      description: 'Shows list of available commands',
      usage: '/help [command]',
      aliases: ['h', '?'],
      execute: (args) => {
        if (args.length > 0) {
          const cmd = this.commands.get(args[0].toLowerCase());
          if (cmd) {
            return `${cmd.name}: ${cmd.description}\nUsage: ${cmd.usage}\nAliases: ${cmd.aliases.join(', ')}`;
          }
          return `Command not found: ${args[0]}`;
        }
        
        const cmdList = Array.from(this.commands.values())
          .map(cmd => `  /${cmd.name} - ${cmd.description}`)
          .join('\n');
        return `Available commands:\n${cmdList}`;
      }
    });
    
    // Teleport command
    this.registerCommand({
      name: 'tp',
      description: 'Teleport to coordinates',
      usage: '/tp <x> <y> <z>',
      aliases: ['teleport'],
      execute: (args) => {
        if (args.length < 3) {
          return 'Usage: /tp <x> <y> <z>';
        }
        const x = parseFloat(args[0]);
        const y = parseFloat(args[1]);
        const z = parseFloat(args[2]);
        
        if (isNaN(x) || isNaN(y) || isNaN(z)) {
          return 'Invalid coordinates';
        }
        
        return `Teleported to ${x}, ${y}, ${z}`;
      }
    });
    
    // Give item command
    this.registerCommand({
      name: 'give',
      description: 'Give yourself items',
      usage: '/give <item> [count]',
      aliases: ['item'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /give <item> [count]';
        }
        
        const item = args[0];
        const count = args.length > 1 ? parseInt(args[1]) : 1;
        
        if (isNaN(count) || count < 1) {
          return 'Invalid count';
        }
        
        return `Gave ${count}x ${item}`;
      }
    });
    
    // Time command
    this.registerCommand({
      name: 'time',
      description: 'Set or display time',
      usage: '/time [set <hour>|day|night]',
      aliases: ['t'],
      execute: (args) => {
        if (args.length === 0) {
          return 'Current time: 12:00 PM';
        }
        
        if (args[0] === 'set') {
          if (args.length < 2) {
            return 'Usage: /time set <hour>';
          }
          
          if (args[1] === 'day') {
            return 'Time set to day (12:00 PM)';
          } else if (args[1] === 'night') {
            return 'Time set to night (00:00 AM)';
          }
          
          const hour = parseInt(args[1]);
          if (isNaN(hour) || hour < 0 || hour >= 24) {
            return 'Invalid hour (0-23)';
          }
          
          return `Time set to ${hour}:00`;
        }
        
        return 'Usage: /time [set <hour>|day|night]';
      }
    });
    
    // Weather command
    this.registerCommand({
      name: 'weather',
      description: 'Change weather',
      usage: '/weather <clear|rain|storm|snow>',
      aliases: ['w'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /weather <clear|rain|storm|snow>';
        }
        
        const weather = args[0].toLowerCase();
        const validWeather = ['clear', 'rain', 'storm', 'snow', 'fog', 'sandstorm'];
        
        if (!validWeather.includes(weather)) {
          return `Invalid weather. Options: ${validWeather.join(', ')}`;
        }
        
        return `Weather set to ${weather}`;
      }
    });
    
    // Gamemode command
    this.registerCommand({
      name: 'gamemode',
      description: 'Change game mode',
      usage: '/gamemode <survival|creative|adventure>',
      aliases: ['gm'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /gamemode <survival|creative|adventure>';
        }
        
        const mode = args[0].toLowerCase();
        const validModes = ['survival', 'creative', 'adventure'];
        
        if (!validModes.includes(mode)) {
          return `Invalid mode. Options: ${validModes.join(', ')}`;
        }
        
        return `Game mode set to ${mode}`;
      }
    });
    
    // Difficulty command
    this.registerCommand({
      name: 'difficulty',
      description: 'Change difficulty',
      usage: '/difficulty <peaceful|easy|normal|hard>',
      aliases: ['diff'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /difficulty <peaceful|easy|normal|hard>';
        }
        
        const diff = args[0].toLowerCase();
        const validDiffs = ['peaceful', 'easy', 'normal', 'hard'];
        
        if (!validDiffs.includes(diff)) {
          return `Invalid difficulty. Options: ${validDiffs.join(', ')}`;
        }
        
        return `Difficulty set to ${diff}`;
      }
    });
    
    // Clear inventory
    this.registerCommand({
      name: 'clear',
      description: 'Clear inventory',
      usage: '/clear',
      aliases: ['clearinv'],
      execute: () => {
        return 'Inventory cleared';
      }
    });
    
    // Kill command
    this.registerCommand({
      name: 'kill',
      description: 'Kill yourself or mobs',
      usage: '/kill [all|hostile|passive]',
      aliases: ['suicide'],
      execute: (args) => {
        if (args.length === 0) {
          return 'You died';
        }
        
        const target = args[0].toLowerCase();
        if (target === 'all') {
          return 'Killed all mobs';
        } else if (target === 'hostile') {
          return 'Killed all hostile mobs';
        } else if (target === 'passive') {
          return 'Killed all passive mobs';
        }
        
        return 'Usage: /kill [all|hostile|passive]';
      }
    });
    
    // Heal command
    this.registerCommand({
      name: 'heal',
      description: 'Restore health and hunger',
      usage: '/heal',
      aliases: ['restore'],
      execute: () => {
        return 'Health and hunger restored';
      }
    });
    
    // Speed command
    this.registerCommand({
      name: 'speed',
      description: 'Change movement speed',
      usage: '/speed <multiplier>',
      aliases: ['spd'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /speed <multiplier>';
        }
        
        const speed = parseFloat(args[0]);
        if (isNaN(speed) || speed < 0.1 || speed > 10) {
          return 'Invalid speed (0.1-10)';
        }
        
        return `Speed set to ${speed}x`;
      }
    });
    
    // Spawn command
    this.registerCommand({
      name: 'spawn',
      description: 'Spawn a mob',
      usage: '/spawn <mob> [count]',
      aliases: ['summon'],
      execute: (args) => {
        if (args.length < 1) {
          return 'Usage: /spawn <mob> [count]';
        }
        
        const mob = args[0];
        const count = args.length > 1 ? parseInt(args[1]) : 1;
        
        if (isNaN(count) || count < 1 || count > 100) {
          return 'Invalid count (1-100)';
        }
        
        return `Spawned ${count}x ${mob}`;
      }
    });
    
    // FPS command
    this.registerCommand({
      name: 'fps',
      description: 'Toggle FPS display',
      usage: '/fps',
      aliases: ['showfps'],
      execute: () => {
        return 'FPS display toggled';
      }
    });
    
    // Debug command
    this.registerCommand({
      name: 'debug',
      description: 'Toggle debug info',
      usage: '/debug',
      aliases: ['dbg'],
      execute: () => {
        return 'Debug info toggled';
      }
    });
    
    // Seed command
    this.registerCommand({
      name: 'seed',
      description: 'Display world seed',
      usage: '/seed',
      aliases: [],
      execute: () => {
        return 'World seed: 123456';
      }
    });
  }
  
  registerCommand(command: Command): void {
    this.commands.set(command.name.toLowerCase(), command);
    
    // Register aliases
    command.aliases.forEach(alias => {
      this.commands.set(alias.toLowerCase(), command);
    });
    
    console.log(`Registered command: /${command.name}`);
  }
  
  executeCommand(input: string): string {
    // Remove leading slash
    if (input.startsWith('/')) {
      input = input.substring(1);
    }
    
    // Parse command and arguments
    const parts = input.trim().split(/\s+/);
    const commandName = parts[0].toLowerCase();
    const args = parts.slice(1);
    
    // Add to history
    this.addToHistory(input);
    
    // Find and execute command
    const command = this.commands.get(commandName);
    if (!command) {
      return `Unknown command: ${commandName}. Type /help for a list of commands.`;
    }
    
    try {
      return command.execute(args);
    } catch (error) {
      return `Error executing command: ${error}`;
    }
  }
  
  getCommand(name: string): Command | undefined {
    return this.commands.get(name.toLowerCase());
  }
  
  getAllCommands(): Command[] {
    // Return unique commands (not aliases)
    const unique = new Map<string, Command>();
    this.commands.forEach(cmd => {
      unique.set(cmd.name, cmd);
    });
    return Array.from(unique.values());
  }
  
  hasCommand(name: string): boolean {
    return this.commands.has(name.toLowerCase());
  }
  
  addToHistory(command: string): void {
    this.commandHistory.push(command);
    if (this.commandHistory.length > this.maxHistory) {
      this.commandHistory.shift();
    }
    this.historyIndex = this.commandHistory.length;
  }
  
  getHistory(): string[] {
    return [...this.commandHistory];
  }
  
  getPreviousCommand(): string | null {
    if (this.commandHistory.length === 0) return null;
    
    this.historyIndex = Math.max(0, this.historyIndex - 1);
    return this.commandHistory[this.historyIndex];
  }
  
  getNextCommand(): string | null {
    if (this.commandHistory.length === 0) return null;
    
    this.historyIndex = Math.min(this.commandHistory.length, this.historyIndex + 1);
    
    if (this.historyIndex >= this.commandHistory.length) {
      return '';
    }
    
    return this.commandHistory[this.historyIndex];
  }
  
  clearHistory(): void {
    this.commandHistory = [];
    this.historyIndex = -1;
  }
  
  autoComplete(partial: string): string[] {
    if (!partial || partial.length === 0) return [];
    
    const lower = partial.toLowerCase();
    return Array.from(this.commands.keys())
      .filter(cmd => cmd.startsWith(lower))
      .slice(0, 10);
  }
}
