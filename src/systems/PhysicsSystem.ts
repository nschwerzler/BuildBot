import * as THREE from 'three';
import { Player } from '../entities/Player';

export class PhysicsSystem {
  private gravity: number = -25; // Stronger gravity for better ground detection
  
  applyGravity(player: Player, deltaTime: number): void {
    if (!player.onGround) {
      player.velocity.y += this.gravity * deltaTime;
      
      // Terminal velocity
      player.velocity.y = Math.max(player.velocity.y, -50);
    }
  }
  
  checkAABBCollision(box1: THREE.Box3, box2: THREE.Box3): boolean {
    return box1.intersectsBox(box2);
  }
  
  resolveCollision(
    entity: THREE.Vector3,
    entityBox: THREE.Box3,
    obstacleBox: THREE.Box3
  ): THREE.Vector3 {
    const testBox = entityBox.clone().translate(entity);
    
    if (!testBox.intersectsBox(obstacleBox)) {
      return entity;
    }
    
    // Calculate overlap on each axis
    const overlapX = Math.min(
      testBox.max.x - obstacleBox.min.x,
      obstacleBox.max.x - testBox.min.x
    );
    
    const overlapY = Math.min(
      testBox.max.y - obstacleBox.min.y,
      obstacleBox.max.y - testBox.min.y
    );
    
    const overlapZ = Math.min(
      testBox.max.z - obstacleBox.min.z,
      obstacleBox.max.z - testBox.min.z
    );
    
    // Resolve on the axis with minimum overlap
    const corrected = entity.clone();
    const minOverlap = Math.min(overlapX, overlapY, overlapZ);
    
    if (minOverlap === overlapX) {
      if (testBox.min.x < obstacleBox.min.x) {
        corrected.x -= overlapX;
      } else {
        corrected.x += overlapX;
      }
    } else if (minOverlap === overlapY) {
      if (testBox.min.y < obstacleBox.min.y) {
        corrected.y -= overlapY;
      } else {
        corrected.y += overlapY;
      }
    } else {
      if (testBox.min.z < obstacleBox.min.z) {
        corrected.z -= overlapZ;
      } else {
        corrected.z += overlapZ;
      }
    }
    
    return corrected;
  }
}
