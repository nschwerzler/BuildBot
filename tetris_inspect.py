"""Inspect the Tetris N-Blox game's JavaScript internals"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(viewport={'width': 900, 'height': 750}).new_page()
    page.goto('https://www.freetetris.org/', wait_until='domcontentloaded')
    time.sleep(3)
    
    # Wait for the iframe to appear and load
    try:
        page.wait_for_selector('#gameIFrame', timeout=10000)
        print('iframe element found, waiting for it to load...')
        time.sleep(5)
    except:
        print('No iframe element found')

    # Try clicking it to ensure it loads
    try:
        page.click('#gameIFrame', timeout=3000)
        time.sleep(2)
    except:
        pass

    # List all frames first
    print('=== ALL FRAMES ===')
    for i, frame in enumerate(page.frames):
        print(f'  Frame {i}: name="{frame.name}" url={frame.url[:120]}')

    # Find the game frame
    game_frame = None
    for frame in page.frames:
        if frame.name == 'gameIFrame':
            game_frame = frame
            break
    if not game_frame:
        for frame in page.frames:
            if 'game' in frame.url.lower():
                game_frame = frame
                break

    if not game_frame:
        print('No game frame found!')
        browser.close()
        exit()

    print(f'Game frame URL: {game_frame.url}')

    # Get all window keys
    print('\n=== ALL WINDOW KEYS ===')
    all_keys = game_frame.evaluate('Object.keys(window).join(", ")')
    print(all_keys[:3000])

    # Get all global functions
    print('\n=== GLOBAL FUNCTIONS ===')
    funcs = game_frame.evaluate('Object.keys(window).filter(k => typeof window[k] === "function").join(", ")')
    print(funcs[:3000])

    # Check common game-related names
    print('\n=== CHECKING GAME OBJECTS ===')
    checks = ['game', 'Game', 'tetris', 'Tetris', 'board', 'Board', 'piece', 'Piece',
              'grid', 'Grid', 'state', 'State', 'score', 'Score', 'level', 'Level',
              'arena', 'matrix', 'field', 'blocks', 'nblox', 'NBlox', 'app', 'App',
              'stage', 'Stage', 'scene', 'Scene', 'engine', 'Engine', 'GAME', 'TETRIS',
              'ctx', 'canvas', 'Canvas', 'gameState', 'gameBoard', 'currentPiece',
              'nextPiece', 'gameOver', 'paused', 'lines', 'rows', 'cols', 'cells',
              'playfield', 'player', 'Player', 'controller', 'Controller',
              'createjs', 'PIXI', 'Phaser', 'cc', 'Cocos', 'Unity', 'gdjs',
              'runtimeScene', 'RuntimeGame', 'gdevelopGame']
    for name in checks:
        try:
            exists = game_frame.evaluate(f'typeof window["{name}"]')
            if exists != 'undefined':
                try:
                    val = game_frame.evaluate(f'JSON.stringify(window["{name}"]).substring(0, 300)')
                except:
                    val = f'[{exists} - not serializable]'
                print(f'  {name}: type={exists}, value={val}')
        except:
            pass

    # Look for game-related keys using regex-like filtering
    print('\n=== GAME-RELATED KEYS ===')
    related = game_frame.evaluate("""
        Object.keys(window).filter(k => {
            var kl = k.toLowerCase();
            return kl.includes('game') || kl.includes('tetris') || kl.includes('board') 
                || kl.includes('piece') || kl.includes('block') || kl.includes('score')
                || kl.includes('level') || kl.includes('grid') || kl.includes('field')
                || kl.includes('play') || kl.includes('pause') || kl.includes('start')
                || kl.includes('new') || kl.includes('reset') || kl.includes('init');
        }).map(k => k + '(' + typeof window[k] + ')').join(', ')
    """)
    print(related[:3000])

    # Check for GDevelop (common HTML5 game engine)
    print('\n=== GDEVELOP CHECK ===')
    gd_check = game_frame.evaluate("""
        var result = [];
        if (typeof gdjs !== 'undefined') result.push('gdjs found');
        if (typeof runtimeScene !== 'undefined') result.push('runtimeScene found');
        if (typeof runtimeGame !== 'undefined') result.push('runtimeGame found');
        // Check for any object with lots of properties (likely game engine)
        Object.keys(window).forEach(k => {
            try {
                var v = window[k];
                if (v && typeof v === 'object' && !Array.isArray(v)) {
                    var keys = Object.keys(v);
                    if (keys.length > 10) {
                        result.push(k + ' has ' + keys.length + ' keys: ' + keys.slice(0, 15).join(','));
                    }
                }
            } catch(e) {}
        });
        result.join('\\n')
    """)
    print(gd_check[:3000])

    # Check all script sources
    print('\n=== SCRIPT SOURCES ===')
    scripts = game_frame.evaluate("""
        Array.from(document.querySelectorAll('script')).map(s => {
            return (s.src || '[inline:' + (s.textContent || '').substring(0, 200) + ']');
        }).join('\\n')
    """)
    print(scripts[:3000])

    # Check the DOM structure
    print('\n=== DOM CHILDREN OF BODY ===')
    dom = game_frame.evaluate("""
        var body = document.body;
        if (!body) 'no body';
        else {
            Array.from(body.children).map(el => {
                return el.tagName + '#' + el.id + '.' + el.className + 
                    ' [' + el.offsetWidth + 'x' + el.offsetHeight + ' at ' + el.offsetLeft + ',' + el.offsetTop + ']' +
                    ' children=' + el.children.length;
            }).join('\\n')
        }
    """)
    print(dom[:3000])

    # Deep dive into Cocos Creator (cc) engine
    print('\n=== COCOS CREATOR (cc) DETAILS ===')
    cc_keys = game_frame.evaluate('Object.keys(cc).join(", ")')
    print(f'cc keys: {cc_keys[:2000]}')

    # Check cc.director (scene manager)
    print('\n=== cc.director ===')
    director_info = game_frame.evaluate("""
        var d = cc.director;
        if (!d) 'no director';
        else {
            var result = 'director keys: ' + Object.keys(d).slice(0, 30).join(', ');
            try {
                var scene = d.getScene();
                if (scene) {
                    result += '\\nScene name: ' + scene.name;
                    result += '\\nScene children count: ' + scene.children.length;
                    result += '\\nScene children names: ' + scene.children.map(c => c.name).join(', ');
                }
            } catch(e) { result += '\\nScene error: ' + e; }
            result;
        }
    """)
    print(director_info[:3000])

    # Explore the scene tree
    print('\n=== SCENE TREE (depth 3) ===')
    tree = game_frame.evaluate("""
        function dumpNode(node, depth, maxDepth) {
            if (depth > maxDepth) return '';
            var indent = '  '.repeat(depth);
            var line = indent + node.name + ' [active=' + node.active + ' children=' + node.children.length;
            if (node._components && node._components.length > 0) {
                line += ' components=' + node._components.map(c => c.__classname__ || c.constructor.name).join(',');
            }
            line += ']';
            var result = line + '\\n';
            for (var i = 0; i < node.children.length; i++) {
                result += dumpNode(node.children[i], depth + 1, maxDepth);
            }
            return result;
        }
        var scene = cc.director.getScene();
        if (!scene) 'No scene';
        else dumpNode(scene, 0, 3);
    """)
    print(tree[:5000])

    # Look for game-specific scripts/components
    print('\n=== SEARCH FOR GAME COMPONENTS ===')
    components = game_frame.evaluate("""
        function findComponents(node, results, depth) {
            if (depth > 10) return;
            if (node._components) {
                for (var c of node._components) {
                    var name = c.__classname__ || c.constructor.name;
                    if (name && !name.startsWith('cc.') && !name.startsWith('cc_')) {
                        var props = Object.keys(c).filter(k => !k.startsWith('_')).slice(0, 20);
                        results.push(node.name + ' -> ' + name + ': ' + props.join(', '));
                    }
                }
            }
            for (var child of node.children) {
                findComponents(child, results, depth + 1);
            }
        }
        var scene = cc.director.getScene();
        var results = [];
        if (scene) findComponents(scene, results, 0);
        results.join('\\n');
    """)
    print(components[:5000])

    # Look specifically for board/grid/game state
    print('\n=== SEARCH FOR GAME STATE VARIABLES ===')
    game_state = game_frame.evaluate("""
        function findGameState(node, results, depth) {
            if (depth > 10) return;
            if (node._components) {
                for (var c of node._components) {
                    var keys = Object.keys(c).filter(k => !k.startsWith('__'));
                    for (var k of keys) {
                        var kl = k.toLowerCase();
                        if (kl.includes('board') || kl.includes('grid') || kl.includes('piece') ||
                            kl.includes('score') || kl.includes('level') || kl.includes('game') ||
                            kl.includes('block') || kl.includes('row') || kl.includes('col') ||
                            kl.includes('field') || kl.includes('cell') || kl.includes('line') ||
                            kl.includes('tetri') || kl.includes('matrix') || kl.includes('next') ||
                            kl.includes('state') || kl.includes('play') || kl.includes('pause') ||
                            kl.includes('start') || kl.includes('new') || kl.includes('reset')) {
                            try {
                                var val = JSON.stringify(c[k]).substring(0, 200);
                                results.push(node.name + '.' + (c.__classname__ || '') + '.' + k + ' = ' + val);
                            } catch(e) {
                                results.push(node.name + '.' + (c.__classname__ || '') + '.' + k + ' = [not serializable]');
                            }
                        }
                    }
                }
            }
            for (var child of node.children) {
                findGameState(child, results, depth + 1);
            }
        }
        var scene = cc.director.getScene();
        var results = [];
        if (scene) findGameState(scene, results, 0);
        results.join('\\n');
    """)
    print(game_state[:8000])

    # Check mBPSApp for game state
    print('\n=== mBPSApp DETAILS ===')
    bps = game_frame.evaluate("""
        var app = window.mBPSApp || window.self.mBPSApp;
        if (!app) 'no mBPSApp';
        else {
            var keys = Object.keys(app);
            var result = 'keys: ' + keys.join(', ') + '\\n';
            for (var k of keys) {
                try {
                    var val = JSON.stringify(app[k]).substring(0, 200);
                    result += k + ' = ' + val + '\\n';
                } catch(e) {
                    result += k + ' = [not serializable]\\n';
                }
            }
            result;
        }
    """)
    print(bps[:5000])

    browser.close()
    print('\nDone!')
