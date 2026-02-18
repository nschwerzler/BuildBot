import * as THREE from 'three';

/**
 * Animation System - Handles entity animations and transitions
 */

export type AnimationType = 'idle' | 'walk' | 'run' | 'jump' | 'fall' | 'attack' | 'mine' | 'hurt' | 'death';

export interface AnimationFrame {
  time: number;
  position?: THREE.Vector3;
  rotation?: THREE.Euler;
  scale?: THREE.Vector3;
}

export interface Animation {
  name: AnimationType;
  duration: number;
  loop: boolean;
  frames: AnimationFrame[];
}

export interface AnimationState {
  currentAnimation: AnimationType;
  currentTime: number;
  nextAnimation: AnimationType | null;
  blendTime: number;
  blendDuration: number;
  speed: number;
}

export class AnimationSystem {
  private animations: Map<AnimationType, Animation> = new Map();
  private entityStates: Map<string, AnimationState> = new Map();
  
  constructor() {
    this.initializeAnimations();
    console.log('Animation System initialized');
  }
  
  private initializeAnimations(): void {
    // Idle animation
    this.registerAnimation({
      name: 'idle',
      duration: 2.0,
      loop: true,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 1.0, position: new THREE.Vector3(0, 0.05, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 2.0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Walk animation
    this.registerAnimation({
      name: 'walk',
      duration: 1.0,
      loop: true,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.25, position: new THREE.Vector3(0, 0.1, 0), rotation: new THREE.Euler(0.1, 0, 0.05) },
        { time: 0.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.75, position: new THREE.Vector3(0, 0.1, 0), rotation: new THREE.Euler(-0.1, 0, -0.05) },
        { time: 1.0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Run animation
    this.registerAnimation({
      name: 'run',
      duration: 0.6,
      loop: true,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.15, position: new THREE.Vector3(0, 0.15, 0), rotation: new THREE.Euler(0.2, 0, 0.1) },
        { time: 0.3, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.45, position: new THREE.Vector3(0, 0.15, 0), rotation: new THREE.Euler(-0.2, 0, -0.1) },
        { time: 0.6, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Jump animation
    this.registerAnimation({
      name: 'jump',
      duration: 0.5,
      loop: false,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.1, position: new THREE.Vector3(0, -0.1, 0), rotation: new THREE.Euler(-0.2, 0, 0) },
        { time: 0.3, position: new THREE.Vector3(0, 0.3, 0), rotation: new THREE.Euler(0.3, 0, 0) },
        { time: 0.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Fall animation
    this.registerAnimation({
      name: 'fall',
      duration: 1.0,
      loop: true,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0.3, 0, 0) },
        { time: 0.5, position: new THREE.Vector3(0, -0.1, 0), rotation: new THREE.Euler(0.4, 0, 0) },
        { time: 1.0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0.3, 0, 0) }
      ]
    });
    
    // Attack animation
    this.registerAnimation({
      name: 'attack',
      duration: 0.4,
      loop: false,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.1, position: new THREE.Vector3(0, 0.1, -0.2), rotation: new THREE.Euler(-0.5, 0, 0) },
        { time: 0.2, position: new THREE.Vector3(0, 0, 0.3), rotation: new THREE.Euler(0.8, 0, 0) },
        { time: 0.4, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Mine animation
    this.registerAnimation({
      name: 'mine',
      duration: 0.5,
      loop: true,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
        { time: 0.125, position: new THREE.Vector3(-0.1, 0.2, 0), rotation: new THREE.Euler(-0.5, -0.3, 0) },
        { time: 0.25, position: new THREE.Vector3(0.1, 0.1, 0.2), rotation: new THREE.Euler(0.3, 0.3, 0) },
        { time: 0.375, position: new THREE.Vector3(-0.1, 0.2, 0), rotation: new THREE.Euler(-0.5, -0.3, 0) },
        { time: 0.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
      ]
    });
    
    // Hurt animation
    this.registerAnimation({
      name: 'hurt',
      duration: 0.3,
      loop: false,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0), scale: new THREE.Vector3(1, 1, 1) },
        { time: 0.1, position: new THREE.Vector3(-0.2, 0, 0), rotation: new THREE.Euler(0, 0, 0.3), scale: new THREE.Vector3(0.9, 1.1, 0.9) },
        { time: 0.2, position: new THREE.Vector3(0.1, 0, 0), rotation: new THREE.Euler(0, 0, -0.2), scale: new THREE.Vector3(1.1, 0.9, 1.1) },
        { time: 0.3, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0), scale: new THREE.Vector3(1, 1, 1) }
      ]
    });
    
    // Death animation
    this.registerAnimation({
      name: 'death',
      duration: 1.0,
      loop: false,
      frames: [
        { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0), scale: new THREE.Vector3(1, 1, 1) },
        { time: 0.3, position: new THREE.Vector3(0, 0.2, 0), rotation: new THREE.Euler(0, 0, 0), scale: new THREE.Vector3(1, 1, 1) },
        { time: 0.6, position: new THREE.Vector3(0, -0.5, 0), rotation: new THREE.Euler(Math.PI / 2, 0, 0), scale: new THREE.Vector3(1.2, 0.8, 1) },
        { time: 1.0, position: new THREE.Vector3(0, -1, 0), rotation: new THREE.Euler(Math.PI / 2, 0, 0), scale: new THREE.Vector3(1.5, 0.5, 1) }
      ]
    });
  }
  
  registerAnimation(animation: Animation): void {
    this.animations.set(animation.name, animation);
  }
  
  createEntityState(entityId: string, initialAnimation: AnimationType = 'idle'): AnimationState {
    const state: AnimationState = {
      currentAnimation: initialAnimation,
      currentTime: 0,
      nextAnimation: null,
      blendTime: 0,
      blendDuration: 0.2,
      speed: 1.0
    };
    
    this.entityStates.set(entityId, state);
    return state;
  }
  
  updateEntity(entityId: string, deltaTime: number, mesh: THREE.Mesh): void {
    const state = this.entityStates.get(entityId);
    if (!state) return;
    
    const animation = this.animations.get(state.currentAnimation);
    if (!animation) return;
    
    // Update current time
    state.currentTime += deltaTime * state.speed;
    
    // Handle looping
    if (state.currentTime >= animation.duration) {
      if (animation.loop) {
        state.currentTime %= animation.duration;
      } else {
        state.currentTime = animation.duration;
        
        // Switch to next animation if queued
        if (state.nextAnimation) {
          this.playAnimation(entityId, state.nextAnimation);
        } else {
          // Default back to idle
          this.playAnimation(entityId, 'idle');
        }
      }
    }
    
    // Get current frame data
    const frame = this.interpolateFrames(animation, state.currentTime);
    
    // Apply animation to mesh
    if (frame.position) {
      mesh.position.y += frame.position.y;
    }
    
    if (frame.rotation) {
      mesh.rotation.copy(frame.rotation);
    }
    
    if (frame.scale) {
      mesh.scale.copy(frame.scale);
    }
  }
  
  private interpolateFrames(animation: Animation, time: number): AnimationFrame {
    const frames = animation.frames;
    
    // Find surrounding frames
    let prevFrame = frames[0];
    let nextFrame = frames[frames.length - 1];
    
    for (let i = 0; i < frames.length - 1; i++) {
      if (time >= frames[i].time && time < frames[i + 1].time) {
        prevFrame = frames[i];
        nextFrame = frames[i + 1];
        break;
      }
    }
    
    // Calculate blend factor
    const timeDiff = nextFrame.time - prevFrame.time;
    const t = timeDiff > 0 ? (time - prevFrame.time) / timeDiff : 0;
    
    // Interpolate values
    const result: AnimationFrame = { time };
    
    if (prevFrame.position && nextFrame.position) {
      result.position = new THREE.Vector3().lerpVectors(prevFrame.position, nextFrame.position, t);
    }
    
    if (prevFrame.rotation && nextFrame.rotation) {
      const q1 = new THREE.Quaternion().setFromEuler(prevFrame.rotation);
      const q2 = new THREE.Quaternion().setFromEuler(nextFrame.rotation);
      const qResult = new THREE.Quaternion().slerpQuaternions(q1, q2, t);
      result.rotation = new THREE.Euler().setFromQuaternion(qResult);
    }
    
    if (prevFrame.scale && nextFrame.scale) {
      result.scale = new THREE.Vector3().lerpVectors(prevFrame.scale, nextFrame.scale, t);
    }
    
    return result;
  }
  
  playAnimation(entityId: string, animationType: AnimationType, force: boolean = false): void {
    const state = this.entityStates.get(entityId);
    if (!state) return;
    
    // Don't interrupt unless forced
    if (!force && state.currentAnimation === animationType) return;
    
    const animation = this.animations.get(animationType);
    if (!animation) {
      console.warn(`Animation not found: ${animationType}`);
      return;
    }
    
    state.currentAnimation = animationType;
    state.currentTime = 0;
    state.nextAnimation = null;
  }
  
  queueAnimation(entityId: string, animationType: AnimationType): void {
    const state = this.entityStates.get(entityId);
    if (!state) return;
    
    state.nextAnimation = animationType;
  }
  
  setAnimationSpeed(entityId: string, speed: number): void {
    const state = this.entityStates.get(entityId);
    if (!state) return;
    
    state.speed = Math.max(0.1, Math.min(5.0, speed));
  }
  
  getAnimationSpeed(entityId: string): number {
    const state = this.entityStates.get(entityId);
    return state?.speed || 1.0;
  }
  
  getCurrentAnimation(entityId: string): AnimationType | null {
    const state = this.entityStates.get(entityId);
    return state?.currentAnimation || null;
  }
  
  getAnimationProgress(entityId: string): number {
    const state = this.entityStates.get(entityId);
    if (!state) return 0;
    
    const animation = this.animations.get(state.currentAnimation);
    if (!animation) return 0;
    
    return state.currentTime / animation.duration;
  }
  
  isAnimationPlaying(entityId: string, animationType: AnimationType): boolean {
    const state = this.entityStates.get(entityId);
    return state?.currentAnimation === animationType;
  }
  
  stopAnimation(entityId: string): void {
    this.playAnimation(entityId, 'idle', true);
  }
  
  removeEntity(entityId: string): void {
    this.entityStates.delete(entityId);
  }
  
  getEntityState(entityId: string): AnimationState | undefined {
    return this.entityStates.get(entityId);
  }
  
  getAllAnimations(): Animation[] {
    return Array.from(this.animations.values());
  }
  
  hasEntity(entityId: string): boolean {
    return this.entityStates.has(entityId);
  }
}
