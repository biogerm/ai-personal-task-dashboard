const assert = require('assert');
const { filterFocusTasks, focusHasData, getGridLayout } = require('../static/js/focus.js');

function testFilterFocusTasks() {
    const projects = [
        { id: 1, title: 'Task 1', urgency: 'upcoming', priority_label: 'Low', due_date: '2026-08-01' },
        { id: 2, title: 'Task 2', urgency: 'today', priority_label: 'High', due_date: '2026-07-07' },
        { id: 3, title: 'Task 3', urgency: 'overdue', priority_label: 'High', due_date: '2026-07-01' },
        { id: 4, title: 'Task 4', urgency: 'today', priority_label: 'Low', due_date: '2026-07-07' },
        { id: 5, title: 'Task 5', urgency: 'no-date', priority_label: 'Medium' },
    ];

    const result = filterFocusTasks(projects);
    assert.strictEqual(result.length, 3, 'Should return 3 tasks (high priority + today non-high)');
    
    // Check order
    assert.strictEqual(result[0].id, 3, 'First should be overdue high priority');
    assert.strictEqual(result[1].id, 2, 'Second should be today high priority');
    assert.strictEqual(result[2].id, 4, 'Third should be today non-high priority');
}

function testFocusHasData() {
    assert.strictEqual(focusHasData(null), false, 'Null data should return false');
    assert.strictEqual(focusHasData({ projects: [] }), false, 'Empty projects should return false');
    assert.strictEqual(focusHasData({ projects: [{ urgency: 'upcoming', priority_label: 'Low' }] }), false, 'No focus tasks should return false');
    assert.strictEqual(focusHasData({ projects: [{ urgency: 'today', priority_label: 'Low' }] }), true, 'Has focus tasks should return true');
}

function testGetGridLayout() {
    assert.deepStrictEqual(getGridLayout(1), { cols: 1, rows: 1, fillScreen: false });
    assert.deepStrictEqual(getGridLayout(2), { cols: 2, rows: 1, fillScreen: false });
    assert.deepStrictEqual(getGridLayout(3), { cols: 3, rows: 1, fillScreen: false });
    assert.deepStrictEqual(getGridLayout(4), { cols: 2, rows: 2, fillScreen: true });
    assert.deepStrictEqual(getGridLayout(6), { cols: 2, rows: 3, fillScreen: true });
    assert.deepStrictEqual(getGridLayout(8), { cols: 3, rows: 3, fillScreen: true });
    assert.deepStrictEqual(getGridLayout(12), { cols: 4, rows: 3, fillScreen: true });
}

console.log('Running Focus View tests...');
testFilterFocusTasks();
testFocusHasData();
testGetGridLayout();
console.log('All tests passed!');
