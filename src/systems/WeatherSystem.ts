import * as THREE from 'three';

/**
 * Weather System - Manages rain, snow, fog, and other weather effects
 */

export type WeatherType = 'clear' | 'rain' | 'snow' | 'storm' | 'fog' | 'sandstorm';

export interface WeatherState {
  type: WeatherType;
  intensity: number; // 0 to 1
  duration: number; // seconds remaining
  transition: number; // transition progress 0 to 1
}

export class WeatherSystem {
  private currentWeather: WeatherState;
  private nextWeather: WeatherType = 'clear';
  private transitionSpeed: number = 0.1;
  private weatherChangeInterval: number = 300; // seconds
  private timeSinceLastChange: number = 0;
  
  private rainParticles: THREE.Points | null = null;
  private scene: THREE.Scene;
  
  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.currentWeather = {
      type: 'clear',
      intensity: 0,
      duration: 300,
      transition: 1
    };
    
    this.initializeWeatherEffects();
  }
  
  private initializeWeatherEffects(): void {
    // Create rain particle system
    const particleCount = 1000;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    
    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 100;
      positions[i * 3 + 1] = Math.random() * 100;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 100;
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const material = new THREE.PointsMaterial({
      color: 0x8888ff,
      size: 0.1,
      transparent: true,
      opacity: 0
    });
    
    this.rainParticles = new THREE.Points(geometry, material);
    this.scene.add(this.rainParticles);
  }
  
  update(deltaTime: number, playerPosition: THREE.Vector3): void {
    this.timeSinceLastChange += deltaTime;
    
    // Check if it's time to change weather
    if (this.timeSinceLastChange >= this.weatherChangeInterval) {
      this.changeWeather();
      this.timeSinceLastChange = 0;
    }
    
    // Update transition
    if (this.currentWeather.transition < 1) {
      this.currentWeather.transition = Math.min(
        1,
        this.currentWeather.transition + deltaTime * this.transitionSpeed
      );
    }
    
    // Update weather effects
    this.updateWeatherEffects(deltaTime, playerPosition);
  }
  
  private updateWeatherEffects(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.rainParticles) return;
    
    const material = this.rainParticles.material as THREE.PointsMaterial;
    
    switch (this.currentWeather.type) {
      case 'rain':
      case 'storm':
        material.opacity = this.currentWeather.intensity * this.currentWeather.transition;
        material.color.setHex(0x8888ff);
        this.updateRainParticles(deltaTime, playerPosition);
        break;
        
      case 'snow':
        material.opacity = this.currentWeather.intensity * this.currentWeather.transition * 0.8;
        material.color.setHex(0xffffff);
        this.updateSnowParticles(deltaTime, playerPosition);
        break;
        
      case 'sandstorm':
        material.opacity = this.currentWeather.intensity * this.currentWeather.transition * 0.6;
        material.color.setHex(0xccaa66);
        this.updateSandstormParticles(deltaTime, playerPosition);
        break;
        
      default:
        material.opacity = 0;
        break;
    }
  }
  
  private updateRainParticles(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.rainParticles) return;
    
    const positions = this.rainParticles.geometry.attributes.position.array as Float32Array;
    const speed = this.currentWeather.type === 'storm' ? 40 : 25;
    
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] -= speed * deltaTime;
      
      if (positions[i + 1] < 0) {
        positions[i] = playerPosition.x + (Math.random() - 0.5) * 100;
        positions[i + 1] = 100;
        positions[i + 2] = playerPosition.z + (Math.random() - 0.5) * 100;
      }
    }
    
    this.rainParticles.geometry.attributes.position.needsUpdate = true;
  }
  
  private updateSnowParticles(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.rainParticles) return;
    
    const positions = this.rainParticles.geometry.attributes.position.array as Float32Array;
    const speed = 8;
    
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] -= speed * deltaTime;
      positions[i] += Math.sin(positions[i + 1] * 0.5) * deltaTime;
      
      if (positions[i + 1] < 0) {
        positions[i] = playerPosition.x + (Math.random() - 0.5) * 100;
        positions[i + 1] = 100;
        positions[i + 2] = playerPosition.z + (Math.random() - 0.5) * 100;
      }
    }
    
    this.rainParticles.geometry.attributes.position.needsUpdate = true;
  }
  
  private updateSandstormParticles(deltaTime: number, playerPosition: THREE.Vector3): void {
    if (!this.rainParticles) return;
    
    const positions = this.rainParticles.geometry.attributes.position.array as Float32Array;
    const speed = 15;
    
    for (let i = 0; i < positions.length; i += 3) {
      positions[i] += speed * deltaTime;
      positions[i + 1] += Math.sin(positions[i] * 0.3) * deltaTime * 2;
      
      if (positions[i] > playerPosition.x + 50) {
        positions[i] = playerPosition.x - 50;
        positions[i + 1] = Math.random() * 50;
        positions[i + 2] = playerPosition.z + (Math.random() - 0.5) * 100;
      }
    }
    
    this.rainParticles.geometry.attributes.position.needsUpdate = true;
  }
  
  private changeWeather(): void {
    // Randomly select new weather
    const weatherTypes: WeatherType[] = ['clear', 'clear', 'clear', 'rain', 'snow', 'fog', 'storm'];
    const randomType = weatherTypes[Math.floor(Math.random() * weatherTypes.length)];
    
    this.setWeather(randomType, Math.random() * 0.5 + 0.5);
  }
  
  setWeather(type: WeatherType, intensity: number = 1): void {
    this.currentWeather = {
      type,
      intensity: Math.max(0, Math.min(1, intensity)),
      duration: 180 + Math.random() * 240,
      transition: 0
    };
    
    console.log(`☁️ Weather changed to: ${type} (intensity: ${intensity.toFixed(2)})`);
  }
  
  getCurrentWeather(): WeatherState {
    return { ...this.currentWeather };
  }
  
  getWeatherType(): WeatherType {
    return this.currentWeather.type;
  }
  
  getIntensity(): number {
    return this.currentWeather.intensity * this.currentWeather.transition;
  }
  
  isRaining(): boolean {
    return this.currentWeather.type === 'rain' || this.currentWeather.type === 'storm';
  }
  
  isSnowing(): boolean {
    return this.currentWeather.type === 'snow';
  }
  
  isClear(): boolean {
    return this.currentWeather.type === 'clear';
  }
}
