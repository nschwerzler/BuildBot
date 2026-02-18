import * as THREE from 'three';

/**
 * Day/Night Cycle System - Manages time of day and lighting
 */

export type TimeOfDay = 'dawn' | 'day' | 'dusk' | 'night';

export interface DayNightState {
  timeOfDay: TimeOfDay;
  hour: number; // 0-24
  dayProgress: number; // 0-1
  sunPosition: THREE.Vector3;
  moonPosition: THREE.Vector3;
  ambientLight: THREE.Color;
  sunLight: THREE.Color;
}

export class DayNightCycle {
  private currentTime: number = 6; // Start at 6 AM
  private dayDuration: number = 1200; // 20 minutes real time = 24 hours game time
  private scene: THREE.Scene;
  private sunLight: THREE.DirectionalLight;
  private moonLight: THREE.DirectionalLight;
  private ambientLight: THREE.AmbientLight;
  private skybox: THREE.Mesh | null = null;
  
  // Time multipliers
  private timeScale: number = 1.0;
  
  // Colors for different times of day
  private readonly colors = {
    day: {
      sky: new THREE.Color(0x87ceeb),
      ambient: new THREE.Color(0x404040),
      sun: new THREE.Color(0xffffff)
    },
    dawn: {
      sky: new THREE.Color(0xff7f50),
      ambient: new THREE.Color(0x303030),
      sun: new THREE.Color(0xffaa66)
    },
    dusk: {
      sky: new THREE.Color(0xff6347),
      ambient: new THREE.Color(0x303030),
      sun: new THREE.Color(0xff8844)
    },
    night: {
      sky: new THREE.Color(0x001a33),
      ambient: new THREE.Color(0x0a0a15),
      sun: new THREE.Color(0x6688aa)
    }
  };
  
  constructor(scene: THREE.Scene, sunLight: THREE.DirectionalLight, ambientLight: THREE.AmbientLight) {
    this.scene = scene;
    this.sunLight = sunLight;
    this.ambientLight = ambientLight;
    
    // Create moon light
    this.moonLight = new THREE.DirectionalLight(0x6688aa, 0.2);
    this.moonLight.position.set(0, -1, 0);
    this.scene.add(this.moonLight);
    
    this.createSkybox();
    this.updateLighting();
  }
  
  private createSkybox(): void {
    const geometry = new THREE.SphereGeometry(500, 32, 32);
    const material = new THREE.MeshBasicMaterial({
      color: this.colors.day.sky,
      side: THREE.BackSide
    });
    
    this.skybox = new THREE.Mesh(geometry, material);
    this.scene.add(this.skybox);
  }
  
  update(deltaTime: number): void {
    // Update time (24 hours = dayDuration seconds)
    this.currentTime += (24 / this.dayDuration) * deltaTime * this.timeScale;
    
    if (this.currentTime >= 24) {
      this.currentTime -= 24;
      console.log('🌅 New day begins');
    }
    
    this.updateLighting();
  }
  
  private updateLighting(): void {
    const state = this.getCurrentState();
    
    // Update sun position (circular path)
    const sunAngle = (this.currentTime / 24) * Math.PI * 2 - Math.PI / 2;
    this.sunLight.position.set(
      Math.cos(sunAngle) * 100,
      Math.sin(sunAngle) * 100,
      50
    );
    
    // Update moon position (opposite of sun)
    const moonAngle = sunAngle + Math.PI;
    this.moonLight.position.set(
      Math.cos(moonAngle) * 100,
      Math.sin(moonAngle) * 100,
      50
    );
    
    // Update light intensities
    const dayIntensity = Math.max(0, Math.sin(sunAngle));
    const nightIntensity = Math.max(0, -Math.sin(sunAngle));
    
    this.sunLight.intensity = dayIntensity * 0.8;
    this.moonLight.intensity = nightIntensity * 0.2;
    
    // Update ambient light
    this.ambientLight.color.copy(state.ambientLight);
    this.ambientLight.intensity = 0.4 + dayIntensity * 0.2;
    
    // Update sunlight color
    this.sunLight.color.copy(state.sunLight);
    
    // Update skybox color
    if (this.skybox) {
      const material = this.skybox.material as THREE.MeshBasicMaterial;
      material.color.copy(this.getSkyColor());
    }
  }
  
  private getSkyColor(): THREE.Color {
    const timeOfDay = this.getTimeOfDay();
    const hour = this.currentTime;
    
    if (timeOfDay === 'dawn') {
      // Blend from night to day (5-7 AM)
      const t = (hour - 5) / 2;
      return new THREE.Color().lerpColors(this.colors.night.sky, this.colors.dawn.sky, t);
    } else if (timeOfDay === 'day') {
      if (hour < 9) {
        // Blend from dawn to day (7-9 AM)
        const t = (hour - 7) / 2;
        return new THREE.Color().lerpColors(this.colors.dawn.sky, this.colors.day.sky, t);
      } else if (hour > 15) {
        // Blend from day to dusk (15-17)
        const t = (hour - 15) / 2;
        return new THREE.Color().lerpColors(this.colors.day.sky, this.colors.dusk.sky, t);
      }
      return this.colors.day.sky;
    } else if (timeOfDay === 'dusk') {
      // Blend from dusk to night (17-19)
      const t = (hour - 17) / 2;
      return new THREE.Color().lerpColors(this.colors.dusk.sky, this.colors.night.sky, t);
    } else { // night
      return this.colors.night.sky;
    }
  }
  
  getCurrentState(): DayNightState {
    const timeOfDay = this.getTimeOfDay();
    const colorSet = this.colors[timeOfDay];
    
    return {
      timeOfDay,
      hour: this.currentTime,
      dayProgress: this.currentTime / 24,
      sunPosition: this.sunLight.position.clone(),
      moonPosition: this.moonLight.position.clone(),
      ambientLight: colorSet.ambient,
      sunLight: colorSet.sun
    };
  }
  
  getTimeOfDay(): TimeOfDay {
    const hour = this.currentTime;
    
    if (hour >= 5 && hour < 7) return 'dawn';
    if (hour >= 7 && hour < 17) return 'day';
    if (hour >= 17 && hour < 19) return 'dusk';
    return 'night';
  }
  
  getCurrentHour(): number {
    return Math.floor(this.currentTime);
  }
  
  getCurrentMinute(): number {
    return Math.floor((this.currentTime % 1) * 60);
  }
  
  getFormattedTime(): string {
    const hour = this.getCurrentHour();
    const minute = this.getCurrentMinute();
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minute.toString().padStart(2, '0')} ${ampm}`;
  }
  
  setTime(hour: number): void {
    this.currentTime = Math.max(0, Math.min(24, hour));
    this.updateLighting();
  }
  
  setTimeScale(scale: number): void {
    this.timeScale = Math.max(0, scale);
  }
  
  getTimeScale(): number {
    return this.timeScale;
  }
  
  isDaytime(): boolean {
    const timeOfDay = this.getTimeOfDay();
    return timeOfDay === 'day' || timeOfDay === 'dawn';
  }
  
  isNighttime(): boolean {
    const timeOfDay = this.getTimeOfDay();
    return timeOfDay === 'night' || timeOfDay === 'dusk';
  }
  
  skipToDay(): void {
    this.setTime(8);
  }
  
  skipToNight(): void {
    this.setTime(20);
  }
}
