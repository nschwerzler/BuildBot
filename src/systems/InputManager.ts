export class InputManager {
  private keys: Map<string, boolean> = new Map();
  private keysPressed: Map<string, boolean> = new Map(); // For single-press detection
  private mouseButtons: Map<number, boolean> = new Map();
  private mouseMoveCallbacks: Array<(movementX: number, movementY: number) => void> = [];
  
  private canvas: HTMLCanvasElement;
  
  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    this.setupEventListeners();
  }
  
  private setupEventListeners(): void {
    // Keyboard events
    window.addEventListener('keydown', (e) => {
      const wasPressed = this.keys.get(e.code);
      this.keys.set(e.code, true);
      
      // Only set keysPressed if this is a new press (not held)
      if (!wasPressed) {
        this.keysPressed.set(e.code, true);
      }
      
      // ESC to unlock pointer
      if (e.code === 'Escape') {
        if (document.pointerLockElement) {
          document.exitPointerLock();
        }
      }
      
      // Prevent default for game controls
      if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'Space'].includes(e.code)) {
        e.preventDefault();
      }
    });
    
    window.addEventListener('keyup', (e) => {
      this.keys.set(e.code, false);
      this.keysPressed.set(e.code, false);
    });
    
    // Mouse events
    this.canvas.addEventListener('mousedown', (e) => {
      this.mouseButtons.set(e.button, true);
    });
    
    this.canvas.addEventListener('mouseup', (e) => {
      this.mouseButtons.set(e.button, false);
    });
    
    // Mouse movement (when pointer is locked)
    document.addEventListener('mousemove', (e) => {
      if (document.pointerLockElement === this.canvas) {
        const movementX = e.movementX || 0;
        const movementY = e.movementY || 0;
        
        this.mouseMoveCallbacks.forEach(callback => {
          callback(movementX, movementY);
        });
      }
    });
    
    // Pointer lock change
    document.addEventListener('pointerlockchange', () => {
      if (document.pointerLockElement !== this.canvas) {
        console.log('Pointer unlocked - press ESC was pressed or click canvas to resume');
      }
    });
    
    // Re-lock on canvas click if unlocked
    this.canvas.addEventListener('click', () => {
      if (!document.pointerLockElement) {
        this.canvas.requestPointerLock();
      }
    });
  }
  
  isKeyPressed(code: string): boolean {
    const pressed = this.keysPressed.get(code) || false;
    
    // Reset after checking (for single-press actions like number keys)
    if (pressed) {
      this.keysPressed.set(code, false);
    }
    
    return pressed;
  }
  
  isKeyHeld(code: string): boolean {
    return this.keys.get(code) || false;
  }
  
  isMouseButtonPressed(button: number): boolean {
    const isPressed = this.mouseButtons.get(button) || false;
    
    // Reset after checking (for single-click actions)
    if (isPressed) {
      this.mouseButtons.set(button, false);
    }
    
    return isPressed;
  }
  
  onMouseMove(callback: (movementX: number, movementY: number) => void): void {
    this.mouseMoveCallbacks.push(callback);
  }
}
