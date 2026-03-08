"""Inspect Tetris N-Blox Cocos Creator scene tree and game state"""
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

    # Dump scene tree safely
    print('=== SCENE TREE ===')
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
                        names.push(c.__classname__ || c.constructor.name || '?');
                    }
                    comps = ' comps=[' + names.join(',') + ']';
                }
                var line = pad + node.name + ' active=' + node.active + ' ch=' + node.children.length + comps + '\\n';
                for (var k = 0; k < node.children.length; k++) {
                    line += dump(node.children[k], depth + 1, maxD);
                }
                return line;
            }
            var scene = cc.director.getScene();
            return scene ? dump(scene, 0, 6) : 'no scene';
        })()
    """)
    print(tree[:8000])

    # Find all custom (non-cc) components and their properties
    print('\n=== CUSTOM COMPONENTS ===')
    comps = game_frame.evaluate("""
        (function() {
            var results = [];
            function scan(node, depth) {
                if (depth > 10 || !node) return;
                if (node._components) {
                    for (var j = 0; j < node._components.length; j++) {
                        var c = node._components[j];
                        var cname = c.__classname__ || c.constructor.name || '?';
                        if (cname.indexOf('cc_') !== 0 && cname.indexOf('cc.') !== 0) {
                            var keys = Object.keys(c);
                            var props = [];
                            for (var ki = 0; ki < keys.length; ki++) {
                                var k = keys[ki];
                                if (k.charAt(0) !== '_') {
                                    try {
                                        var v = c[k];
                                        var t = typeof v;
                                        if (t === 'number' || t === 'string' || t === 'boolean' || v === null) {
                                            props.push(k + '=' + String(v).substring(0, 80));
                                        } else if (Array.isArray(v)) {
                                            props.push(k + '=[Array(' + v.length + ')]');
                                        } else if (t === 'object' && v) {
                                            props.push(k + '={' + Object.keys(v).slice(0, 5).join(',') + '}');
                                        }
                                    } catch(e) {}
                                }
                            }
                            results.push(node.name + ' -> ' + cname + ': ' + props.join(', '));
                        }
                    }
                }
                for (var ci = 0; ci < node.children.length; ci++) {
                    scan(node.children[ci], depth + 1);
                }
            }
            var scene = cc.director.getScene();
            if (scene) scan(scene, 0);
            return results.join('\\n');
        })()
    """)
    print(comps[:10000])

    # Try to find board array or game state
    print('\n=== SEARCHING FOR ARRAYS (BOARD DATA) ===')
    arrays = game_frame.evaluate("""
        (function() {
            var results = [];
            function scan(node, depth) {
                if (depth > 10 || !node) return;
                if (node._components) {
                    for (var j = 0; j < node._components.length; j++) {
                        var c = node._components[j];
                        var cname = c.__classname__ || '';
                        var keys = Object.keys(c);
                        for (var ki = 0; ki < keys.length; ki++) {
                            var k = keys[ki];
                            var v = c[k];
                            if (Array.isArray(v) && v.length > 0) {
                                var preview = '';
                                try { preview = JSON.stringify(v).substring(0, 300); } catch(e) { preview = '[err]'; }
                                results.push(node.name + '.' + cname + '.' + k + ' len=' + v.length + ' => ' + preview);
                            }
                        }
                    }
                }
                for (var ci = 0; ci < node.children.length; ci++) {
                    scan(node.children[ci], depth + 1);
                }
            }
            var scene = cc.director.getScene();
            if (scene) scan(scene, 0);
            return results.join('\\n');
        })()
    """)
    print(arrays[:10000])

    browser.close()
    print('\nDone!')
