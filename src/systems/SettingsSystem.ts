/**
 * Settings System - Manages game configuration and preferences
 */

export interface GraphicsSettings {
  renderDistance: number;
  shadows: boolean;
  particles: boolean;
  antialiasing: boolean;
  fov: number;
  maxFps: number;
}

export interface AudioSettings {
  masterVolume: number;
  musicVolume: number;
  sfxVolume: number;
  muted: boolean;
}

export interface GameplaySettings {
  difficulty: 'peaceful' | 'easy' | 'normal' | 'hard';
  autoSave: boolean;
  autoSaveInterval: number;
  showCoordinates: boolean;
  showFPS: boolean;
  mouseSensitivity: number;
  invertY: boolean;
  sprintToggle: boolean;
}

export interface ControlSettings {
  forward: string;
  backward: string;
  left: string;
  right: string;
  jump: string;
  sprint: string;
  crouch: string;
  inventory: string;
  crafting: string;
  drop: string;
  interact: string;
  attack: string;
}

export interface Settings {
  graphics: GraphicsSettings;
  audio: AudioSettings;
  gameplay: GameplaySettings;
  controls: ControlSettings;
}

export class SettingsSystem {
  private settings: Settings;
  private readonly STORAGE_KEY = 'game_settings';
  private listeners: Array<(settings: Settings) => void> = [];
  
  constructor() {
    this.settings = this.getDefaultSettings();
    this.loadSettings();
    console.log('Settings System initialized');
  }
  
  private getDefaultSettings(): Settings {
    return {
      graphics: {
        renderDistance: 2,
        shadows: false,
        particles: true,
        antialiasing: false,
        fov: 75,
        maxFps: 60
      },
      audio: {
        masterVolume: 1.0,
        musicVolume: 0.7,
        sfxVolume: 0.8,
        muted: false
      },
      gameplay: {
        difficulty: 'normal',
        autoSave: true,
        autoSaveInterval: 300,
        showCoordinates: true,
        showFPS: true,
        mouseSensitivity: 0.5,
        invertY: false,
        sprintToggle: false
      },
      controls: {
        forward: 'w',
        backward: 's',
        left: 'a',
        right: 'd',
        jump: ' ',
        sprint: 'Shift',
        crouch: 'Control',
        inventory: 'e',
        crafting: 'c',
        drop: 'q',
        interact: 'f',
        attack: 'Mouse0'
      }
    };
  }
  
  getSettings(): Settings {
    return JSON.parse(JSON.stringify(this.settings));
  }
  
  getGraphicsSettings(): GraphicsSettings {
    return { ...this.settings.graphics };
  }
  
  getAudioSettings(): AudioSettings {
    return { ...this.settings.audio };
  }
  
  getGameplaySettings(): GameplaySettings {
    return { ...this.settings.gameplay };
  }
  
  getControlSettings(): ControlSettings {
    return { ...this.settings.controls };
  }
  
  updateGraphicsSettings(updates: Partial<GraphicsSettings>): void {
    this.settings.graphics = { ...this.settings.graphics, ...updates };
    this.notifyListeners();
    this.saveSettings();
    console.log('Graphics settings updated');
  }
  
  updateAudioSettings(updates: Partial<AudioSettings>): void {
    this.settings.audio = { ...this.settings.audio, ...updates };
    this.notifyListeners();
    this.saveSettings();
    console.log('Audio settings updated');
  }
  
  updateGameplaySettings(updates: Partial<GameplaySettings>): void {
    this.settings.gameplay = { ...this.settings.gameplay, ...updates };
    this.notifyListeners();
    this.saveSettings();
    console.log('Gameplay settings updated');
  }
  
  updateControlSettings(updates: Partial<ControlSettings>): void {
    this.settings.controls = { ...this.settings.controls, ...updates };
    this.notifyListeners();
    this.saveSettings();
    console.log('Control settings updated');
  }
  
  setRenderDistance(distance: number): void {
    this.settings.graphics.renderDistance = Math.max(1, Math.min(10, distance));
    this.notifyListeners();
    this.saveSettings();
  }
  
  toggleShadows(): void {
    this.settings.graphics.shadows = !this.settings.graphics.shadows;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Shadows: ${this.settings.graphics.shadows ? 'ON' : 'OFF'}`);
  }
  
  toggleParticles(): void {
    this.settings.graphics.particles = !this.settings.graphics.particles;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Particles: ${this.settings.graphics.particles ? 'ON' : 'OFF'}`);
  }
  
  setMasterVolume(volume: number): void {
    this.settings.audio.masterVolume = Math.max(0, Math.min(1, volume));
    this.notifyListeners();
    this.saveSettings();
  }
  
  setMusicVolume(volume: number): void {
    this.settings.audio.musicVolume = Math.max(0, Math.min(1, volume));
    this.notifyListeners();
    this.saveSettings();
  }
  
  setSfxVolume(volume: number): void {
    this.settings.audio.sfxVolume = Math.max(0, Math.min(1, volume));
    this.notifyListeners();
    this.saveSettings();
  }
  
  toggleMute(): void {
    this.settings.audio.muted = !this.settings.audio.muted;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Audio: ${this.settings.audio.muted ? 'MUTED' : 'UNMUTED'}`);
  }
  
  setDifficulty(difficulty: GameplaySettings['difficulty']): void {
    this.settings.gameplay.difficulty = difficulty;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Difficulty set to: ${difficulty}`);
  }
  
  setMouseSensitivity(sensitivity: number): void {
    this.settings.gameplay.mouseSensitivity = Math.max(0.1, Math.min(2.0, sensitivity));
    this.notifyListeners();
    this.saveSettings();
  }
  
  setFOV(fov: number): void {
    this.settings.graphics.fov = Math.max(60, Math.min(120, fov));
    this.notifyListeners();
    this.saveSettings();
    console.log(`FOV: ${this.settings.graphics.fov}`);
  }
  
  toggleAutoSave(): void {
    this.settings.gameplay.autoSave = !this.settings.gameplay.autoSave;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Auto-save: ${this.settings.gameplay.autoSave ? 'ON' : 'OFF'}`);
  }
  
  toggleCoordinatesDisplay(): void {
    this.settings.gameplay.showCoordinates = !this.settings.gameplay.showCoordinates;
    this.notifyListeners();
    this.saveSettings();
  }
  
  toggleFPSDisplay(): void {
    this.settings.gameplay.showFPS = !this.settings.gameplay.showFPS;
    this.notifyListeners();
    this.saveSettings();
  }
  
  rebindKey(action: keyof ControlSettings, newKey: string): void {
    this.settings.controls[action] = newKey;
    this.notifyListeners();
    this.saveSettings();
    console.log(`Rebound ${action} to ${newKey}`);
  }
  
  resetToDefaults(): void {
    this.settings = this.getDefaultSettings();
    this.notifyListeners();
    this.saveSettings();
    console.log('Settings reset to defaults');
  }
  
  resetGraphics(): void {
    this.settings.graphics = this.getDefaultSettings().graphics;
    this.notifyListeners();
    this.saveSettings();
  }
  
  resetAudio(): void {
    this.settings.audio = this.getDefaultSettings().audio;
    this.notifyListeners();
    this.saveSettings();
  }
  
  resetGameplay(): void {
    this.settings.gameplay = this.getDefaultSettings().gameplay;
    this.notifyListeners();
    this.saveSettings();
  }
  
  resetControls(): void {
    this.settings.controls = this.getDefaultSettings().controls;
    this.notifyListeners();
    this.saveSettings();
  }
  
  saveSettings(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.settings));
      console.log('💾 Settings saved');
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  }
  
  loadSettings(): void {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) {
        const loadedSettings = JSON.parse(saved);
        
        // Merge with defaults to add any new settings
        this.settings = {
          graphics: { ...this.settings.graphics, ...loadedSettings.graphics },
          audio: { ...this.settings.audio, ...loadedSettings.audio },
          gameplay: { ...this.settings.gameplay, ...loadedSettings.gameplay },
          controls: { ...this.settings.controls, ...loadedSettings.controls }
        };
        
        console.log('⬆️ Settings loaded');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  }
  
  exportSettings(): string {
    return JSON.stringify(this.settings, null, 2);
  }
  
  importSettings(json: string): boolean {
    try {
      const imported = JSON.parse(json);
      this.settings = {
        graphics: { ...this.settings.graphics, ...imported.graphics },
        audio: { ...this.settings.audio, ...imported.audio },
        gameplay: { ...this.settings.gameplay, ...imported.gameplay },
        controls: { ...this.settings.controls, ...imported.controls }
      };
      this.notifyListeners();
      this.saveSettings();
      console.log('⬇️ Settings imported');
      return true;
    } catch (error) {
      console.error('Failed to import settings:', error);
      return false;
    }
  }
  
  onSettingsChange(callback: (settings: Settings) => void): void {
    this.listeners.push(callback);
  }
  
  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.getSettings()));
  }
  
  getKeyBinding(action: keyof ControlSettings): string {
    return this.settings.controls[action];
  }
  
  isKeyBound(key: string): keyof ControlSettings | null {
    for (const [action, boundKey] of Object.entries(this.settings.controls)) {
      if (boundKey === key) {
        return action as keyof ControlSettings;
      }
    }
    return null;
  }
}
