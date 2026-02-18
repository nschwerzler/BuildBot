import * as THREE from 'three';
import { InputManager } from '../systems/InputManager';

export class Player {
  public position: THREE.Vector3;
  public velocity: THREE.Vector3;
  public onGround: boolean = false;
  public boundingBox: THREE.Box3;
  
  private camera: THREE.PerspectiveCamera;
  private inputManager: InputManager;
  
  private pitch: number = 0;
  private yaw: number = 0;
  
  private moveSpeed: number = 4.3; // Similar to Minecraft
  private sprintSpeed: number = 5.6;
  private jumpForce: number = 8;
  private mouseSensitivity: number = 0.002;
  private speedMultiplier: number = 1.0;
  
  // Player dimensions - slightly larger for better collision
  private readonly width: number = 0.7;
  private height: number = 1.8;
  private eyeOffset: number = 1.6;
  
  constructor(camera: THREE.PerspectiveCamera, inputManager: InputManager) {
    this.camera = camera;
    this.inputManager = inputManager;
    this.position = new THREE.Vector3(0.5, 65, 0.5);
    this.velocity = new THREE.Vector3(0, 0, 0);
    this.onGround = true;
    
    // Bounding box relative to position
    this.boundingBox = new THREE.Box3(
      new THREE.Vector3(-this.width / 2, 0, -this.width / 2),
      new THREE.Vector3(this.width / 2, this.height, this.width / 2)
    );
    
    this.setupControls();
  }
  
  private setupControls(): void {
    // Mouse movement
    this.inputManager.onMouseMove((movementX: number, movementY: number) => {
      this.yaw -= movementX * this.mouseSensitivity;
      this.pitch -= movementY * this.mouseSensitivity;
      
      // Clamp pitch
      this.pitch = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, this.pitch));
    });
  }
  
  update(deltaTime: number): void {
    // Update camera rotation
    this.camera.rotation.order = 'YXZ';
    this.camera.rotation.y = this.yaw;
    this.camera.rotation.x = this.pitch;
    
    // Calculate movement direction
    const forward = new THREE.Vector3(0, 0, -1);
    const right = new THREE.Vector3(1, 0, 0);
    
    forward.applyQuaternion(this.camera.quaternion);
    forward.y = 0;
    forward.normalize();
    
    right.applyQuaternion(this.camera.quaternion);
    right.y = 0;
    right.normalize();
    
    // Get input
    const moveDirection = new THREE.Vector3();
    
    if (this.inputManager.isKeyHeld('KeyW')) {
      moveDirection.add(forward);
    }
    if (this.inputManager.isKeyHeld('KeyS')) {
      moveDirection.sub(forward);
    }
    if (this.inputManager.isKeyHeld('KeyD')) {
      moveDirection.add(right);
    }
    if (this.inputManager.isKeyHeld('KeyA')) {
      moveDirection.sub(right);
    }
    
    // Normalize diagonal movement
    if (moveDirection.length() > 0) {
      moveDirection.normalize();
    }
    
    // Apply speed
    const speed = this.inputManager.isKeyHeld('ShiftLeft') ? this.sprintSpeed : this.moveSpeed;
    moveDirection.multiplyScalar(speed * this.speedMultiplier);
    
    // Apply movement
    this.position.x += moveDirection.x * deltaTime;
    this.position.z += moveDirection.z * deltaTime;
    
    // Jumping
    if (this.inputManager.isKeyHeld('Space') && this.onGround) {
      this.velocity.y = this.jumpForce;
      this.onGround = false;
    }
    
    // Don't apply vertical velocity here - let Game.ts handle it with collision
    // Don't sync camera here - Game.ts will call syncCamera() after collision
  }

  /** Sync camera to position (call after collision resolution) */
  syncCamera(): void {
    this.camera.position.copy(this.position);
    this.camera.position.y += this.eyeOffset;
  }

  getHeight(): number {
    return this.height;
  }
  
  getBoundingBox(): THREE.Box3 {
    return this.boundingBox.clone().translate(this.position);
  }

  setSpeedMultiplier(mult: number): void {
    this.speedMultiplier = mult;
  }

  setMobSize(mobType: string): void {
    switch (mobType) {
      case 'cat':
        this.height = 0.35;
        this.eyeOffset = 0.28;
        break;
      case 'wolf':
        this.height = 0.45;
        this.eyeOffset = 0.38;
        break;
      case 'bunny':
        this.height = 0.25;
        this.eyeOffset = 0.2;
        break;
      case 'human':
        this.height = 1.0;
        this.eyeOffset = 0.85;
        break;
      default:
        this.height = 1.0;
        this.eyeOffset = 0.85;
    }
    // Update bounding box for new height
    this.boundingBox = new THREE.Box3(
      new THREE.Vector3(-this.width / 2, 0, -this.width / 2),
      new THREE.Vector3(this.width / 2, this.height, this.width / 2)
    );
  }
}
