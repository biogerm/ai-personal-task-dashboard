const assert = require('assert');
const carousel = require('../static/js/carousel.js');

function createMockElement() {
    return {
        style: { display: '', opacity: '' },
        classList: {
            add: function(cls) {},
            remove: function(cls) {},
            contains: function(cls) { return false; }
        },
        offsetHeight: 100
    };
}

// Override setTimeout to run synchronously for testing
const originalSetTimeout = global.setTimeout;
global.setTimeout = (fn, ms) => {
    fn();
    return 1;
};

try {
    // Test 1: registerView
    carousel._reset();
    const el1 = createMockElement();
    const el2 = createMockElement();
    
    carousel.registerView(0, 'view1', el1, (data) => true, () => {}, () => {});
    carousel.registerView(1, 'view2', el2, (data) => data && data.showView2, () => {}, () => {});
    
    assert.strictEqual(carousel.views.length, 2, 'Should have 2 registered views');

    // Test 2: initCarousel
    carousel.initCarousel({ intervalSeconds: 5 }, { showView2: false });
    assert.strictEqual(carousel.currentIndex, 0, 'Should start at view1 since view2 hasDataFn returns false');
    assert.strictEqual(el1.style.display, 'flex', 'View1 should be visible');
    assert.strictEqual(el2.style.display, 'none', 'View2 should be hidden');
    assert.ok(carousel.timerId !== null, 'Timer should be started');

    // Test 3: switchToNext skipping views without data
    carousel.switchToNext();
    assert.strictEqual(carousel.currentIndex, 0, 'Should not switch since view2 has no data');

    // Test 4: updateData and switch
    carousel.updateData({ showView2: true });
    carousel.switchToNext();
    assert.strictEqual(carousel.currentIndex, 1, 'Should switch to view2 now that it has data');
    assert.strictEqual(el1.style.opacity, '0', 'View1 should fade out');
    assert.strictEqual(el2.style.display, 'flex', 'View2 should become visible');
    
    // Cleanup
    carousel.stopTimer();
    
    console.log('All carousel logic tests passed successfully!');
} catch (e) {
    console.error('Test failed:', e);
    process.exit(1);
} finally {
    global.setTimeout = originalSetTimeout;
}
