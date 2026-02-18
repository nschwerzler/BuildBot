import * as THREE from 'three';

export class Renderer {
  public scene: THREE.Scene;
  public camera: THREE.PerspectiveCamera;
  public sunLight!: THREE.DirectionalLight;
  public ambientLight!: THREE.AmbientLight;
  private threeRenderer: THREE.WebGLRenderer;
  private canvas: HTMLCanvasElement;
  
  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    
    // Create scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x87CEEB); // Sky blue
    this.scene.fog = new THREE.Fog(0x87CEEB, 30, 80); // Adjusted for closer render distance
    
    // Create camera
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.set(0, 70, 0);
    
    // Create renderer with pixel art settings
    this.threeRenderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: false, // Disable AA for pixel art
      powerPreference: 'high-performance'
    });
    
    this.threeRenderer.setSize(window.innerWidth, window.innerHeight);
    this.threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1)); // Limit pixel ratio
    this.threeRenderer.shadowMap.enabled = false; // Disable shadows for performance
    
    // Setup lighting
    this.setupLighting();
  }
  
  private setupLighting(): void {
    // Ambient light
    this.ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    this.scene.add(this.ambientLight);
    
    // Directional light (sun)
    this.sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
    this.sunLight.position.set(50, 100, 50);
    this.sunLight.castShadow = false; // Disable shadow casting
    
    this.scene.add(this.sunLight);
  }
  
  render(): void {
    this.threeRenderer.render(this.scene, this.camera);
  }
  
  onResize(): void {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    
    this.threeRenderer.setSize(width, height);
  }
  
  getRenderer(): THREE.WebGLRenderer {
    return this.threeRenderer;
  }
}
