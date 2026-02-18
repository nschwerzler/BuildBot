/**
 * AI Bug Tester System - Automatically detects and reports bugs
 */

export interface BugReport {
  id: string;
  timestamp: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: 'crash' | 'performance' | 'logic' | 'rendering' | 'memory' | 'null' | 'warning';
  message: string;
  details: string;
  stackTrace?: string;
  fixed: boolean;
}

export class AIBugTester {
  private bugs: Map<string, BugReport> = new Map();
  private nextBugId: number = 1;
  private isRunning: boolean = false;
  private checkInterval: number = 2000; // Check every 2 seconds
  private lastCheck: number = 0;
  
  // Performance monitoring
  private frameTimings: number[] = [];
  private maxFrameTimings: number = 60;
  private memorySnapshots: number[] = [];
  
  // Error tracking
  private consoleErrors: string[] = [];
  private consoleWarnings: string[] = [];
  
  // Game state validation
  private lastPlayerPosition: { x: number; y: number; z: number } | null = null;
  private stuckTimer: number = 0;
  
  private uiPanel: HTMLDivElement | null = null;
  
  constructor() {
    this.setupErrorHandlers();
    this.createUI();
    console.log('🤖 AI Bug Tester initialized - Monitoring for issues...');
  }
  
  private setupErrorHandlers(): void {
    // Capture console errors
    const originalError = console.error;
    console.error = (...args: any[]) => {
      this.consoleErrors.push(args.join(' '));
      if (this.consoleErrors.length > 50) this.consoleErrors.shift();
      originalError.apply(console, args);
    };
    
    // Capture console warnings
    const originalWarn = console.warn;
    console.warn = (...args: any[]) => {
      this.consoleWarnings.push(args.join(' '));
      if (this.consoleWarnings.length > 50) this.consoleWarnings.shift();
      originalWarn.apply(console, args);
    };
    
    // Capture unhandled errors
    window.addEventListener('error', (event) => {
      this.reportBug({
        severity: 'critical',
        category: 'crash',
        message: 'Unhandled Error Detected',
        details: event.message,
        stackTrace: event.error?.stack
      });
    });
    
    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.reportBug({
        severity: 'high',
        category: 'crash',
        message: 'Unhandled Promise Rejection',
        details: String(event.reason),
        stackTrace: event.reason?.stack
      });
    });
  }
  
  private createUI(): void {
    this.uiPanel = document.createElement('div');
    this.uiPanel.id = 'bug-tester-panel';
    this.uiPanel.style.position = 'fixed';
    this.uiPanel.style.top = '10px';
    this.uiPanel.style.right = '10px';
    this.uiPanel.style.width = '320px';
    this.uiPanel.style.maxHeight = '600px';
    this.uiPanel.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    this.uiPanel.style.border = '2px solid #ff4444';
    this.uiPanel.style.borderRadius = '8px';
    this.uiPanel.style.padding = '12px';
    this.uiPanel.style.color = '#fff';
    this.uiPanel.style.fontFamily = 'monospace';
    this.uiPanel.style.fontSize = '11px';
    this.uiPanel.style.overflowY = 'auto';
    this.uiPanel.style.zIndex = '10000';
    this.uiPanel.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';
    
    this.uiPanel.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div>
          <span style="color: #ff4444; font-weight: bold;">🤖 AI BUG TESTER</span>
          <span id="bug-status" style="color: #4ade80; margin-left: 8px;">ACTIVE</span>
        </div>
        <button id="clear-bugs" style="background: #333; border: 1px solid #666; color: #fff; padding: 2px 8px; cursor: pointer; border-radius: 4px; font-size: 10px;">Clear</button>
      </div>
      <div style="border-top: 1px solid #444; padding-top: 8px; margin-top: 8px;">
        <div style="color: #888; margin-bottom: 4px; font-size: 10px;">FOUND ISSUES: <span id="bug-count" style="color: #ff4444; font-weight: bold;">0</span></div>
        <div id="bug-list" style="max-height: 500px; overflow-y: auto;"></div>
      </div>
    `;
    
    document.body.appendChild(this.uiPanel);
    
    // Clear button handler
    const clearBtn = document.getElementById('clear-bugs');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => this.clearAllBugs());
    }
  }
  
  start(): void {
    this.isRunning = true;
    console.log('🤖 AI Bug Tester started monitoring');
  }
  
  stop(): void {
    this.isRunning = false;
  }
  
  update(deltaTime: number, gameState: any): void {
    if (!this.isRunning) return;
    
    this.lastCheck += deltaTime;
    
    if (this.lastCheck >= this.checkInterval / 1000) {
      this.runChecks(gameState);
      this.lastCheck = 0;
    }
    
    // Track frame timing for performance analysis
    this.frameTimings.push(deltaTime * 1000);
    if (this.frameTimings.length > this.maxFrameTimings) {
      this.frameTimings.shift();
    }
  }
  
  private runChecks(gameState: any): void {
    this.checkPerformance();
    this.checkMemory();
    this.checkConsoleErrors();
    this.checkGameState(gameState);
    this.checkNullReferences(gameState);
  }
  
  private checkPerformance(): void {
    if (this.frameTimings.length < 30) return;
    
    const avgFrameTime = this.frameTimings.reduce((a, b) => a + b, 0) / this.frameTimings.length;
    const fps = 1000 / avgFrameTime;
    
    // Check for low FPS
    if (fps < 30 && !this.hasBug('low_fps')) {
      this.reportBug({
        severity: 'high',
        category: 'performance',
        message: 'Low FPS Detected',
        details: `Average FPS: ${fps.toFixed(1)} (below 30)`
      }, 'low_fps');
    } else if (fps >= 30 && this.hasBug('low_fps')) {
      this.fixBug('low_fps');
    }
    
    // Check for frame drops
    const maxFrameTime = Math.max(...this.frameTimings);
    if (maxFrameTime > 100 && !this.hasBug('frame_drop')) {
      this.reportBug({
        severity: 'medium',
        category: 'performance',
        message: 'Frame Drop Detected',
        details: `Frame took ${maxFrameTime.toFixed(1)}ms (>100ms spike)`
      }, 'frame_drop');
    }
  }
  
  private checkMemory(): void {
    if ((performance as any).memory) {
      const memory = (performance as any).memory;
      const usedMB = memory.usedJSHeapSize / 1024 / 1024;
      const limitMB = memory.jsHeapSizeLimit / 1024 / 1024;
      const usage = (usedMB / limitMB) * 100;
      
      this.memorySnapshots.push(usedMB);
      if (this.memorySnapshots.length > 10) this.memorySnapshots.shift();
      
      // Check for high memory usage
      if (usage > 80 && !this.hasBug('high_memory')) {
        this.reportBug({
          severity: 'high',
          category: 'memory',
          message: 'High Memory Usage',
          details: `Using ${usedMB.toFixed(1)}MB (${usage.toFixed(1)}% of limit)`
        }, 'high_memory');
      }
      
      // Check for memory leak (continuously growing)
      if (this.memorySnapshots.length >= 10) {
        const trend = this.memorySnapshots[9] - this.memorySnapshots[0];
        if (trend > 50 && !this.hasBug('memory_leak')) {
          this.reportBug({
            severity: 'critical',
            category: 'memory',
            message: 'Possible Memory Leak',
            details: `Memory increased by ${trend.toFixed(1)}MB in last 20 seconds`
          }, 'memory_leak');
        }
      }
    }
  }
  
  private checkConsoleErrors(): void {
    // Check for new console errors
    if (this.consoleErrors.length > 0) {
      const latestError = this.consoleErrors[this.consoleErrors.length - 1];
      const errorHash = this.hashString(latestError);
      
      if (!this.hasBug(`error_${errorHash}`)) {
        this.reportBug({
          severity: 'high',
          category: 'crash',
          message: 'Console Error Detected',
          details: latestError.substring(0, 100)
        }, `error_${errorHash}`);
      }
    }
    
    // Check for repeated warnings
    if (this.consoleWarnings.length > 10) {
      const recentWarnings = this.consoleWarnings.slice(-10);
      const duplicates = recentWarnings.filter(w => w === recentWarnings[0]).length;
      
      if (duplicates >= 5 && !this.hasBug('repeated_warning')) {
        this.reportBug({
          severity: 'medium',
          category: 'warning',
          message: 'Repeated Console Warning',
          details: `Warning repeated ${duplicates} times: ${recentWarnings[0].substring(0, 80)}`
        }, 'repeated_warning');
      }
    }
  }
  
  private checkGameState(gameState: any): void {
    if (!gameState || !gameState.player) return;
    
    const player = gameState.player;
    
    // Check if player is stuck
    if (this.lastPlayerPosition) {
      const dx = player.position.x - this.lastPlayerPosition.x;
      const dy = player.position.y - this.lastPlayerPosition.y;
      const dz = player.position.z - this.lastPlayerPosition.z;
      const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);
      
      if (distance < 0.01) {
        this.stuckTimer += this.checkInterval / 1000;
        
        if (this.stuckTimer > 10 && !this.hasBug('player_stuck')) {
          this.reportBug({
            severity: 'medium',
            category: 'logic',
            message: 'Player May Be Stuck',
            details: `No movement detected for ${this.stuckTimer.toFixed(0)} seconds`
          }, 'player_stuck');
        }
      } else {
        this.stuckTimer = 0;
        if (this.hasBug('player_stuck')) {
          this.fixBug('player_stuck');
        }
      }
    }
    
    this.lastPlayerPosition = { ...player.position };
    
    // Check for player falling through world
    if (player.position.y < 0 && !this.hasBug('player_falling')) {
      this.reportBug({
        severity: 'critical',
        category: 'logic',
        message: 'Player Falling Through World',
        details: `Player Y position: ${player.position.y.toFixed(2)} (below 0)`
      }, 'player_falling');
    }
    
    // Check for extreme positions
    const maxDist = 10000;
    const dist = Math.sqrt(player.position.x ** 2 + player.position.z ** 2);
    if (dist > maxDist && !this.hasBug('extreme_position')) {
      this.reportBug({
        severity: 'medium',
        category: 'logic',
        message: 'Player at Extreme Position',
        details: `Distance from spawn: ${dist.toFixed(0)} blocks`
      }, 'extreme_position');
    }
  }
  
  private checkNullReferences(gameState: any): void {
    const checks = [
      { obj: gameState, name: 'gameState' },
      { obj: gameState?.player, name: 'player' },
      { obj: gameState?.world, name: 'world' },
      { obj: gameState?.renderer, name: 'renderer' }
    ];
    
    checks.forEach(check => {
      if (!check.obj && !this.hasBug(`null_${check.name}`)) {
        this.reportBug({
          severity: 'critical',
          category: 'null',
          message: 'Null Reference Detected',
          details: `${check.name} is null or undefined`
        }, `null_${check.name}`);
      }
    });
  }
  
  private reportBug(bug: Omit<BugReport, 'id' | 'timestamp' | 'fixed'>, customId?: string): void {
    const id = customId || `bug_${this.nextBugId++}`;
    
    if (this.bugs.has(id)) return; // Don't duplicate
    
    const fullBug: BugReport = {
      id,
      timestamp: Date.now(),
      fixed: false,
      ...bug
    };
    
    this.bugs.set(id, fullBug);
    this.updateUI();
    
    console.warn(`🐛 Bug detected: ${bug.message} - ${bug.details}`);
  }
  
  private fixBug(id: string): void {
    const bug = this.bugs.get(id);
    if (bug) {
      bug.fixed = true;
      console.log(`✅ Bug fixed: ${bug.message}`);
      this.updateUI();
    }
  }
  
  private hasBug(id: string): boolean {
    const bug = this.bugs.get(id);
    return bug !== undefined && !bug.fixed;
  }
  
  private clearAllBugs(): void {
    this.bugs.clear();
    this.consoleErrors = [];
    this.consoleWarnings = [];
    this.updateUI();
    console.log('🧹 Bug list cleared');
  }
  
  private updateUI(): void {
    const bugList = document.getElementById('bug-list');
    const bugCount = document.getElementById('bug-count');
    
    if (!bugList || !bugCount) return;
    
    const activeBugs = Array.from(this.bugs.values()).filter(b => !b.fixed);
    bugCount.textContent = activeBugs.length.toString();
    
    if (activeBugs.length === 0) {
      bugList.innerHTML = '<div style="color: #4ade80; padding: 8px; text-align: center;">✓ No issues detected</div>';
      return;
    }
    
    bugList.innerHTML = activeBugs
      .sort((a, b) => this.getSeverityOrder(a.severity) - this.getSeverityOrder(b.severity))
      .map(bug => {
        const color = this.getSeverityColor(bug.severity);
        const icon = this.getCategoryIcon(bug.category);
        const time = this.getTimeAgo(bug.timestamp);
        
        return `
          <div style="background: #1a1a1a; border-left: 3px solid ${color}; padding: 8px; margin-bottom: 6px; border-radius: 4px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${color}; font-weight: bold;">${icon} ${bug.severity.toUpperCase()}</span>
              <span style="color: #666; font-size: 9px;">${time}</span>
            </div>
            <div style="color: #fff; margin-bottom: 2px; font-weight: bold;">${bug.message}</div>
            <div style="color: #aaa; font-size: 10px;">${bug.details}</div>
            <div style="color: #666; font-size: 9px; margin-top: 4px;">[${bug.category}]</div>
          </div>
        `;
      })
      .join('');
  }
  
  private getSeverityOrder(severity: string): number {
    const order: Record<string, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3
    };
    return order[severity] || 4;
  }
  
  private getSeverityColor(severity: string): string {
    const colors: Record<string, string> = {
      critical: '#ff0000',
      high: '#ff4444',
      medium: '#ffaa00',
      low: '#ffff00'
    };
    return colors[severity] || '#888';
  }
  
  private getCategoryIcon(category: string): string {
    const icons: Record<string, string> = {
      crash: '💥',
      performance: '🐌',
      logic: '❌',
      rendering: '🎨',
      memory: '💾',
      null: '⚠️',
      warning: '⚡'
    };
    return icons[category] || '🐛';
  }
  
  private getTimeAgo(timestamp: number): string {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  }
  
  private hashString(str: string): string {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(36);
  }
  
  getBugCount(): number {
    return Array.from(this.bugs.values()).filter(b => !b.fixed).length;
  }
  
  getAllBugs(): BugReport[] {
    return Array.from(this.bugs.values());
  }
  
  getActiveBugs(): BugReport[] {
    return Array.from(this.bugs.values()).filter(b => !b.fixed);
  }
}
