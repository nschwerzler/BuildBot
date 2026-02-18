/**
 * Sound Manager - Handles all audio in the game
 */

export interface Sound {
  name: string;
  volume: number;
  loop: boolean;
  audio: HTMLAudioElement | null;
}

export class SoundManager {
  private sounds: Map<string, Sound> = new Map();
  private masterVolume: number = 1.0;
  private musicVolume: number = 0.7;
  private sfxVolume: number = 0.8;
  private muted: boolean = false;
  
  constructor() {
    this.initializeSounds();
  }
  
  private initializeSounds(): void {
    // Note: In a real game, these would be actual audio files
    // For now, we'll create placeholder sound definitions
    
    // SFX sounds
    this.registerSound('block_break', 0.6, false);
    this.registerSound('block_place', 0.5, false);
    this.registerSound('footstep', 0.3, false);
    this.registerSound('jump', 0.4, false);
    this.registerSound('land', 0.5, false);
    this.registerSound('pickup', 0.6, false);
    this.registerSound('craft', 0.5, false);
    this.registerSound('tool_break', 0.7, false);
    this.registerSound('hit', 0.5, false);
    this.registerSound('hurt', 0.6, false);
    this.registerSound('explosion', 0.8, false);
    this.registerSound('water_splash', 0.5, false);
    this.registerSound('button_click', 0.4, false);
    this.registerSound('achievement', 0.7, false);
    
    // Music
    this.registerSound('menu_music', 0.3, true);
    this.registerSound('game_music', 0.3, true);
    this.registerSound('cave_ambience', 0.2, true);
    
    console.log('Sound system initialized');
  }
  
  private registerSound(name: string, volume: number, loop: boolean): void {
    this.sounds.set(name, {
      name,
      volume,
      loop,
      audio: null
    });
  }
  
  playSound(name: string, volumeMultiplier: number = 1.0): void {
    if (this.muted) return;
    
    const sound = this.sounds.get(name);
    if (!sound) {
      console.warn(`Sound not found: ${name}`);
      return;
    }
    
    // In a real implementation, this would create and play an actual audio element
    // For now, we just log it
    const finalVolume = sound.volume * volumeMultiplier * this.sfxVolume * this.masterVolume;
    
    if (finalVolume > 0) {
      console.log(`🔊 Playing sound: ${name} (volume: ${finalVolume.toFixed(2)})`);
    }
  }
  
  playMusic(name: string): void {
    if (this.muted) return;
    
    const sound = this.sounds.get(name);
    if (!sound) {
      console.warn(`Music not found: ${name}`);
      return;
    }
    
    // Stop all other music
    this.stopAllMusic();
    
    const finalVolume = sound.volume * this.musicVolume * this.masterVolume;
    console.log(`🎵 Playing music: ${name} (volume: ${finalVolume.toFixed(2)})`);
  }
  
  stopSound(name: string): void {
    const sound = this.sounds.get(name);
    if (sound?.audio) {
      sound.audio.pause();
      sound.audio.currentTime = 0;
    }
  }
  
  stopAllMusic(): void {
    this.sounds.forEach((sound) => {
      if (sound.loop && sound.audio) {
        sound.audio.pause();
        sound.audio.currentTime = 0;
      }
    });
  }
  
  stopAllSounds(): void {
    this.sounds.forEach((sound) => {
      if (sound.audio) {
        sound.audio.pause();
        sound.audio.currentTime = 0;
      }
    });
  }
  
  setMasterVolume(volume: number): void {
    this.masterVolume = Math.max(0, Math.min(1, volume));
  }
  
  setMusicVolume(volume: number): void {
    this.musicVolume = Math.max(0, Math.min(1, volume));
  }
  
  setSfxVolume(volume: number): void {
    this.sfxVolume = Math.max(0, Math.min(1, volume));
  }
  
  getMasterVolume(): number {
    return this.masterVolume;
  }
  
  getMusicVolume(): number {
    return this.musicVolume;
  }
  
  getSfxVolume(): number {
    return this.sfxVolume;
  }
  
  toggleMute(): void {
    this.muted = !this.muted;
    if (this.muted) {
      this.stopAllSounds();
      console.log('🔇 Muted');
    } else {
      console.log('🔊 Unmuted');
    }
  }
  
  isMuted(): boolean {
    return this.muted;
  }
  
  playFootstep(): void {
    // Random variation
    const pitch = 0.9 + Math.random() * 0.2;
    this.playSound('footstep', pitch);
  }
  
  playBlockBreak(): void {
    const pitch = 0.8 + Math.random() * 0.4;
    this.playSound('block_break', pitch);
  }
  
  playBlockPlace(): void {
    const pitch = 0.9 + Math.random() * 0.2;
    this.playSound('block_place', pitch);
  }
}
