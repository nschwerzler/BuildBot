import * as THREE from 'three';

/**
 * Particle System - Creates visual effects for the game
 */

export interface Particle {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  color: THREE.Color;
  size: number;
  life: number;
  maxLife: number;
  mesh: THREE.Mesh;
}

export class ParticleSystem {
  private particles: Particle[] = [];
  private particleGroup: THREE.Group;
  private maxParticles: number = 500;
  
  constructor(scene: THREE.Scene) {
    this.particleGroup = new THREE.Group();
    scene.add(this.particleGroup);
  }
  
  /**
   * Create block break particles
   */
  createBlockBreakParticles(position: THREE.Vector3, blockColor: THREE.Color): void {
    const particleCount = 8;
    
    for (let i = 0; i < particleCount; i++) {
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 5,
        Math.random() * 8,
        (Math.random() - 0.5) * 5
      );
      
      this.createParticle(
        position.clone(),
        velocity,
        blockColor,
        0.2,
        0.5
      );
    }
  }
  
  /**
   * Create explosion particles
   */
  createExplosion(position: THREE.Vector3, count: number = 20): void {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count;
      const speed = 5 + Math.random() * 3;
      
      const velocity = new THREE.Vector3(
        Math.cos(angle) * speed,
        Math.random() * 8,
        Math.sin(angle) * speed
      );
      
      const color = new THREE.Color().setHSL(
        0.1 + Math.random() * 0.2,
        1,
        0.5
      );
      
      this.createParticle(
        position.clone(),
        velocity,
        color,
        0.3,
        1.0
      );
    }
  }
  
  /**
   * Create sparkle particles (for collecting items)
   */
  createSparkles(position: THREE.Vector3, color: THREE.Color): void {
    for (let i = 0; i < 10; i++) {
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        Math.random() * 4 + 2,
        (Math.random() - 0.5) * 2
      );
      
      this.createParticle(
        position.clone(),
        velocity,
        color,
        0.15,
        0.8
      );
    }
  }
  
  /**
   * Create trail particles (for movement effects)
   */
  createTrail(position: THREE.Vector3): void {
    if (Math.random() > 0.7) {
      const offset = new THREE.Vector3(
        (Math.random() - 0.5) * 0.5,
        0,
        (Math.random() - 0.5) * 0.5
      );
      
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 0.5,
        0.5,
        (Math.random() - 0.5) * 0.5
      );
      
      this.createParticle(
        position.clone().add(offset),
        velocity,
        new THREE.Color(0xcccccc),
        0.1,
        0.3
      );
    }
  }
  
  /**
   * Create smoke particles
   */
  createSmoke(position: THREE.Vector3, count: number = 5): void {
    for (let i = 0; i < count; i++) {
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 1,
        2 + Math.random() * 2,
        (Math.random() - 0.5) * 1
      );
      
      const gray = 0.3 + Math.random() * 0.4;
      const color = new THREE.Color(gray, gray, gray);
      
      this.createParticle(
        position.clone(),
        velocity,
        color,
        0.4,
        2.0
      );
    }
  }
  
  private createParticle(
    position: THREE.Vector3,
    velocity: THREE.Vector3,
    color: THREE.Color,
    size: number,
    life: number
  ): void {
    if (this.particles.length >= this.maxParticles) {
      // Remove oldest particle
      const oldest = this.particles.shift();
      if (oldest) {
        this.particleGroup.remove(oldest.mesh);
        oldest.mesh.geometry.dispose();
        (oldest.mesh.material as THREE.Material).dispose();
      }
    }
    
    const geometry = new THREE.BoxGeometry(size, size, size);
    const material = new THREE.MeshBasicMaterial({ color });
    const mesh = new THREE.Mesh(geometry, material);
    
    mesh.position.copy(position);
    this.particleGroup.add(mesh);
    
    this.particles.push({
      position: position.clone(),
      velocity: velocity.clone(),
      color,
      size,
      life,
      maxLife: life,
      mesh
    });
  }
  
  update(deltaTime: number): void {
    const particlesToRemove: number[] = [];
    
    this.particles.forEach((particle, index) => {
      // Update life
      particle.life -= deltaTime;
      
      if (particle.life <= 0) {
        particlesToRemove.push(index);
        return;
      }
      
      // Update position
      particle.velocity.y -= 15 * deltaTime; // Gravity
      particle.position.add(particle.velocity.clone().multiplyScalar(deltaTime));
      particle.mesh.position.copy(particle.position);
      
      // Fade out
      const alpha = particle.life / particle.maxLife;
      particle.mesh.scale.setScalar(alpha);
      
      // Slow down
      particle.velocity.multiplyScalar(0.98);
    });
    
    // Remove dead particles (in reverse to maintain indices)
    for (let i = particlesToRemove.length - 1; i >= 0; i--) {
      const index = particlesToRemove[i];
      const particle = this.particles[index];
      
      this.particleGroup.remove(particle.mesh);
      particle.mesh.geometry.dispose();
      (particle.mesh.material as THREE.Material).dispose();
      
      this.particles.splice(index, 1);
    }
  }
  
  clear(): void {
    this.particles.forEach(particle => {
      this.particleGroup.remove(particle.mesh);
      particle.mesh.geometry.dispose();
      (particle.mesh.material as THREE.Material).dispose();
    });
    this.particles = [];
  }
  
  getParticleCount(): number {
    return this.particles.length;
  }
}
