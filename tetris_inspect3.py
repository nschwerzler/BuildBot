"""Inspect Tetris N-Blox menu items and game state machine"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(viewport={'width': 900, 'height': 750}).new_page()
    page.goto('https://www.freetetris.org/', wait_until='domcontentloaded')
    time.sleep(3)
    try:
        page.wait_for_selector('#gameIFrame', timeout=10000)
        time.sleep(5)
    except:
        pass
    try:
        page.click('#gameIFrame', timeout=3000)
        time.sleep(2)
    except:
        pass

    game_frame = None
    for frame in page.frames:
        if frame.name == 'gameIFrame':
            game_frame = frame
            break

    if not game_frame:
        print('No game frame!')
        browser.close()
        exit()

    # Explore panelContent children (menu buttons)
    print('=== MENU PANEL CONTENT ===')
    menu = game_frame.evaluate("""
        (function() {
            var scene = cc.director.getScene();
            var canvas = scene.children[0];
            // Navigate: Canvas -> mainMenu-rootView -> menu -> internalChildrenContainer -> content -> panelContent
            function findByName(node, name) {
                if (node.name === name) return node;
                for (var i = 0; i < node.children.length; i++) {
                    var result = findByName(node.children[i], name);
                    if (result) return result;
                }
                return null;
            }
            var panel = findByName(canvas, 'panelContent');
            if (!panel) return 'panelContent not found';
            
            var result = 'panelContent has ' + panel.children.length + ' children:\\n';
            for (var i = 0; i < panel.children.length; i++) {
                var child = panel.children[i];
                result += '  [' + i + '] ' + child.name + ' active=' + child.active + ' ch=' + child.children.length;
                // Get component info
                if (child._components) {
                    for (var j = 0; j < child._components.length; j++) {
                        var c = child._components[j];
                        var cn = c.__classname__ || c.constructor.name;
                        result += ' comp=' + cn;
                    }
                }
                result += '\\n';
                
                // Check grandchildren for labels/text
                for (var k = 0; k < child.children.length; k++) {
                    var gc = child.children[k];
                    result += '    [' + k + '] ' + gc.name + ' active=' + gc.active;
                    if (gc._components) {
                        for (var j = 0; j < gc._components.length; j++) {
                            var c = gc._components[j];
                            var cn = c.__classname__ || '';
                            result += ' comp=' + cn;
                            if (cn === 'cc.Label' || cn === 'cc.RichText') {
                                result += ' text="' + (c.string || c._string || '') + '"';
                            }
                        }
                    }
                    result += '\\n';
                    
                    // Even deeper
                    for (var m = 0; m < gc.children.length; m++) {
                        var ggc = gc.children[m];
                        result += '      [' + m + '] ' + ggc.name + ' active=' + ggc.active;
                        if (ggc._components) {
                            for (var j = 0; j < ggc._components.length; j++) {
                                var c = ggc._components[j];
                                var cn = c.__classname__ || '';
                                result += ' comp=' + cn;
                                if (cn === 'cc.Label' || cn === 'cc.RichText') {
                                    result += ' text="' + (c.string || c._string || '') + '"';
                                }
                            }
                        }
                        result += '\\n';
                    }
                }
            }
            return result;
        })()
    """)
    print(menu[:5000])

    # Explore the state machine
    print('\n=== STATE MACHINE ===')
    sm = game_frame.evaluate("""
        (function() {
            var app = window.mBPSApp || (window.self && window.self.mBPSApp);
            if (!app) return 'no mBPSApp';
            var sm = app.mStateMachine;
            if (!sm) return 'no state machine';
            var result = 'StateMachine keys: ' + Object.keys(sm).join(', ') + '\\n';
            try {
                result += 'Current state: ' + JSON.stringify(sm.mCurrentState || sm.currentState || sm._currentState).substring(0, 200) + '\\n';
            } catch(e) { result += 'Current state: [err]\\n'; }
            try {
                var states = sm.mStates || sm.states || sm._states;
                if (states) {
                    result += 'States keys: ' + Object.keys(states).join(', ') + '\\n';
                }
            } catch(e) {}
            // Dump all sm props
            var keys = Object.keys(sm);
            for (var i = 0; i < keys.length; i++) {
                var k = keys[i];
                try {
                    var v = sm[k];
                    if (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') {
                        result += k + ' = ' + v + '\\n';
                    } else if (Array.isArray(v)) {
                        result += k + ' = [Array(' + v.length + ')]\\n';
                    } else if (typeof v === 'object' && v) {
                        result += k + ' = {' + Object.keys(v).slice(0, 10).join(',') + '}\\n';
                    }
                } catch(e) {}
            }
            return result;
        })()
    """)
    print(sm[:5000])

    # Deep scan: find ALL scene nodes with full depth
    print('\n=== FULL SCENE TREE (depth 10) ===')
    tree = game_frame.evaluate("""
        (function() {
            function dump(node, depth, maxD) {
                if (depth > maxD || !node) return '';
                var pad = '';
                for (var i = 0; i < depth; i++) pad += '  ';
                var comps = '';
                if (node._components) {
                    var names = [];
                    for (var j = 0; j < node._components.length; j++) {
                        var c = node._components[j];
                        var cn = c.__classname__ || c.constructor.name || '?';
                        names.push(cn);
                        // Add label text
                        if ((cn === 'cc.Label' || cn === 'cc.RichText') && (c.string || c._string)) {
                            names[names.length-1] += ':"' + (c.string || c._string) + '"';
                        }
                    }
                    comps = ' [' + names.join(', ') + ']';
                }
                var line = pad + node.name + (node.active ? '' : ' (INACTIVE)') + comps + '\\n';
                for (var k = 0; k < node.children.length; k++) {
                    line += dump(node.children[k], depth + 1, maxD);
                }
                return line;
            }
            var scene = cc.director.getScene();
            return scene ? dump(scene, 0, 10) : 'no scene';
        })()
    """)
    print(tree[:10000])

    browser.close()
    print('\nDone!')
