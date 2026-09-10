/**
 * TimeMeshin Time Stone - Background Service Worker
 * Manages tab lifecycles, abrupt window closure recovery, and state synchronization.
 */

const SERVER_URL = 'http://localhost:8765/api/tab_state';
const tabRegistry = new Map();

// Helper: Save tab state to local storage & TimeMeshin server
async function persistTabState(tabState, eventType = 'UPDATE') {
    tabState.last_updated = new Date().toISOString();
    tabState.status = eventType;

    // 1. Save in chrome.storage.local
    chrome.storage.local.get(['timemeshin_history'], (result) => {
        let history = result.timemeshin_history || [];
        // Deduplicate or replace
        history = history.filter(item => item.url !== tabState.url);
        history.unshift(tabState);
        history = history.slice(0, 50); // Keep last 50 closed/active states
        chrome.storage.local.set({ timemeshin_history: history });
    });

    // 2. Post to TimeMeshin Desktop Server if active
    try {
        await fetch(SERVER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tabState)
        });
    } catch (e) {
        // Quiet if desktop server is paused
    }
}

// Listen for messages from content.js (Form inputs, scroll positions, DOM snapshots)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TAB_STATE_SNAPSHOT') {
        const tabId = sender.tab ? sender.tab.id : message.tab_id;
        const tabState = {
            tab_id: tabId,
            window_id: sender.tab ? sender.tab.windowId : null,
            url: message.url,
            title: message.title,
            scroll_x: message.scroll_x,
            scroll_y: message.scroll_y,
            inputs: message.inputs,
            timestamp: new Date().toISOString()
        };
        tabRegistry.set(tabId, tabState);
        persistTabState(tabState, 'ACTIVE_I_FRAME');
        sendResponse({ status: 'ACK' });
    } else if (message.type === 'RESTORE_TAB_REQUEST') {
        // Reopen closed tab
        chrome.tabs.create({ url: message.url }, (newTab) => {
            // Save state to pending restore queue for new tab
            chrome.storage.local.get(['pending_restores'], (res) => {
                const pending = res.pending_restores || {};
                pending[newTab.id] = message;
                chrome.storage.local.set({ pending_restores: pending });
            });
        });
        sendResponse({ status: 'REOPENED' });
    }
    return true;
});

// Detect when a tab is closed abruptly
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    if (tabRegistry.has(tabId)) {
        const lastState = tabRegistry.get(tabId);
        lastState.closed_at = new Date().toISOString();
        lastState.is_window_closing = removeInfo.isWindowClosing;
        persistTabState(lastState, removeInfo.isWindowClosing ? 'WINDOW_CLOSED_ABRUPT' : 'TAB_CLOSED');
        tabRegistry.delete(tabId);
    }
});
