/**
 * TimeMeshin Universal Time Stone & AI Ingestor (Manifest V3)
 * Captures AI conversations + Form Inputs + Scroll Positions for Abrupt Crash Recovery.
 */

console.log('[TimeMeshin Time Stone] Active on:', window.location.hostname);

const SERVER_URL = 'http://localhost:8765/api/ingest_chat';
const seenMessageHashes = new Set();
let inputDebounceTimer = null;
let aiDebounceTimer = null;

// ==========================================
// 1. TIME STONE: TAB STATE & INPUT CAPTURE
// ==========================================

function gatherFormInputs() {
    const inputs = {};
    const elements = document.querySelectorAll('input, textarea, [contenteditable=\"true\"]');
    
    elements.forEach((el, idx) => {
        // Skip passwords for security and privacy
        if (el.type === 'password' || el.autocomplete === 'current-password') return;
        
        const key = el.id || el.name || ield__;
        const val = el.isContentEditable ? el.innerText : el.value;
        
        if (val && val.trim().length > 0) {
            inputs[key] = {
                id: el.id || '',
                name: el.name || '',
                tagName: el.tagName,
                isContentEditable: el.isContentEditable,
                value: val.trim()
            };
        }
    });
    return inputs;
}

function captureTabSnapshot() {
    const inputs = gatherFormInputs();
    const payload = {
        type: 'TAB_STATE_SNAPSHOT',
        url: window.location.href,
        title: document.title || 'Web Page',
        scroll_x: window.scrollX,
        scroll_y: window.scrollY,
        inputs: inputs
    };

    try {
        chrome.runtime.sendMessage(payload);
    } catch (e) {
        // Extension reloaded
    }
}

function initInputListeners() {
    // Listen for typing across all inputs/textareas
    document.addEventListener('input', () => {
        clearTimeout(inputDebounceTimer);
        inputDebounceTimer = setTimeout(captureTabSnapshot, 1500);
    }, true);

    // Listen for scrolling
    window.addEventListener('scroll', () => {
        clearTimeout(inputDebounceTimer);
        inputDebounceTimer = setTimeout(captureTabSnapshot, 2000);
    }, { passive: true });

    // Initial snapshot after page load
    setTimeout(captureTabSnapshot, 3000);
}

// ==========================================
// 2. TIME STONE: AUTO-RESTORE INJECTION
// ==========================================

function checkAndRestorePendingState() {
    chrome.storage.local.get(['pending_restores'], (res) => {
        const pending = res.pending_restores || {};
        // Match current URL
        let matchedKey = null;
        let restoreData = null;

        for (const [key, data] of Object.entries(pending)) {
            if (data.url === window.location.href) {
                matchedKey = key;
                restoreData = data;
                break;
            }
        }

        if (restoreData) {
            console.log('[TimeMeshin Time Stone] Restoring state from previous session:', restoreData);
            
            // Restore scroll position
            if (restoreData.scroll_y !== undefined) {
                setTimeout(() => {
                    window.scrollTo({
                        left: restoreData.scroll_x || 0,
                        top: restoreData.scroll_y,
                        behavior: 'smooth'
                    });
                }, 800);
            }

            // Restore form inputs
            if (restoreData.inputs) {
                setTimeout(() => {
                    let restoredCount = 0;
                    for (const [fieldKey, field] of Object.entries(restoreData.inputs)) {
                        let el = null;
                        if (field.id) el = document.getElementById(field.id);
                        if (!el && field.name) el = document.querySelector([name=\"\"]);
                        
                        if (el) {
                            if (field.isContentEditable) {
                                el.innerText = field.value;
                            } else {
                                el.value = field.value;
                            }
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            restoredCount++;
                        }
                    }
                    if (restoredCount > 0) {
                        showHUDNotification(🟢 Time Stone: Restored  input field(s)!);
                    }
                }, 1000);
            }

            // Cleanup pending restore
            delete pending[matchedKey];
            chrome.storage.local.set({ pending_restores: pending });
        }
    });
}

// ==========================================
// 3. FLOATING HUD BADGE
// ==========================================

function injectFloatingBadge() {
    if (document.getElementById('timemeshin-hud-badge')) return;
    
    const badge = document.createElement('div');
    badge.id = 'timemeshin-hud-badge';
    badge.style.cssText = 
        position: fixed;
        bottom: 18px;
        right: 18px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 7px 13px;
        background: rgba(10, 13, 20, 0.94);
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
        font-size: 11px;
        font-weight: 600;
        border-radius: 20px;
        border: 1px solid rgba(0, 229, 255, 0.35);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5), 0 0 12px rgba(0, 229, 255, 0.2);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
        cursor: pointer;
        user-select: none;
    ;
    badge.innerHTML = 
        <span style=\"font-size: 13px;\">🟢</span>
        <span id=\"tm-hud-text\">Time Stone Active</span>
    ;
    badge.onclick = () => {
        captureTabSnapshot();
        showHUDNotification('⚡ Time Stone: State Keyframe Captured!');
    };
    document.body.appendChild(badge);
}

function showHUDNotification(msg) {
    const text = document.getElementById('tm-hud-text');
    if (!text) return;
    
    text.innerText = msg;
    text.style.color = '#10b981';
    
    setTimeout(() => {
        text.innerText = 'Time Stone Active';
        text.style.color = '#f8fafc';
    }, 3500);
}

// ==========================================
// 4. AI CHAT PARSING (Gemini, ChatGPT, Claude)
// ==========================================

function hashText(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return hash.toString();
}

function parseActiveConversation() {
    const host = window.location.hostname;
    let provider = 'AI Chat';
    let pairs = [];

    if (host.includes('gemini.google.com')) {
        provider = 'Gemini Web';
        const queries = Array.from(document.querySelectorAll('.user-query-container, user-query, [data-message-author-role=\"user\"]'));
        const responses = Array.from(document.querySelectorAll('.model-response-text, model-response, [data-message-author-role=\"model\"]'));
        const count = Math.min(queries.length, responses.length);
        for (let i = 0; i < count; i++) {
            const q = queries[i]?.innerText?.trim();
            const r = responses[i]?.innerText?.trim();
            if (q && r) pairs.push({ prompt: q, response: r });
        }
    } else if (host.includes('chatgpt.com')) {
        provider = 'ChatGPT Web';
        const articles = Array.from(document.querySelectorAll('article'));
        for (let i = 0; i < articles.length; i += 2) {
            const q = articles[i]?.innerText?.trim();
            const r = articles[i+1]?.innerText?.trim();
            if (q && r) pairs.push({ prompt: q, response: r });
        }
    } else if (host.includes('claude.ai')) {
        provider = 'Claude Web';
        const humanMsgs = Array.from(document.querySelectorAll('[data-testid=\"user-message\"]'));
        const assistantMsgs = Array.from(document.querySelectorAll('.font-claude-message'));
        const count = Math.min(humanMsgs.length, assistantMsgs.length);
        for (let i = 0; i < count; i++) {
            const q = humanMsgs[i]?.innerText?.trim();
            const r = assistantMsgs[i]?.innerText?.trim();
            if (q && r) pairs.push({ prompt: q, response: r });
        }
    }

    return { provider, pairs };
}

async function syncLatestAITurns() {
    const { provider, pairs } = parseActiveConversation();
    if (pairs.length === 0) return;

    const latest = pairs[pairs.length - 1];
    const turnKey = hashText(latest.prompt + ':::' + latest.response.substring(0, 100));

    if (seenMessageHashes.has(turnKey)) return;

    try {
        const payload = {
            provider: provider,
            url: window.location.href,
            title: document.title || 'AI Chat Session',
            prompt: latest.prompt,
            response: latest.response,
            timestamp: new Date().toISOString()
        };

        const res = await fetch(SERVER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            seenMessageHashes.add(turnKey);
            showHUDNotification('⚡ Synced to TimeMeshin!');
        }
    } catch (err) {}
}

function initAIOptions() {
    const observer = new MutationObserver(() => {
        clearTimeout(aiDebounceTimer);
        aiDebounceTimer = setTimeout(syncLatestAITurns, 2000);
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
}

// ==========================================
// 5. INITIALIZATION
// ==========================================

function init() {
    injectFloatingBadge();
    initInputListeners();
    checkAndRestorePendingState();
    if (window.location.hostname.match(/gemini\.google|chatgpt|claude\.ai/)) {
        initAIOptions();
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
