function renderHistory() {
    chrome.storage.local.get(['timemeshin_history'], (res) => {
        const history = res.timemeshin_history || [];
        const list = document.getElementById('history-list');
        const count = document.getElementById('tab-count');
        
        count.innerText = `${history.length} tabs`;

        if (history.length === 0) {
            list.innerHTML = '<div class="empty-text">Monitoring tabs... Closed windows will appear here.</div>';
            return;
        }

        list.innerHTML = history.map((item, idx) => {
            const inputCount = item.inputs ? Object.keys(item.inputs).length : 0;
            const timeStr = item.last_updated ? new Date(item.last_updated).toLocaleTimeString() : 'Recent';
            const badgeHtml = inputCount > 0 ? `<span class="badge-inputs">?? ${inputCount} inputs saved</span>` : '<span style="color:#64748b;">0 inputs</span>';
            
            return `
                <div class="history-card">
                    <div class="card-header">
                        <div class="tab-title" title="${item.title || item.url}">${item.title || 'Untitled Tab'}</div>
                        <div class="tab-time">${timeStr}</div>
                    </div>
                    <div class="tab-meta">
                        ${badgeHtml}
                        <span>?? Scroll: ${item.scroll_y || 0}px</span>
                    </div>
                    <button class="btn-restore" data-idx="${idx}">
                        <span>??</span> Time Travel & Restore
                    </button>
                </div>
            `;
        }).join('');

        document.querySelectorAll('.btn-restore').forEach(btn => {
            btn.onclick = () => {
                const idx = parseInt(btn.getAttribute('data-idx'));
                restoreTab(idx);
            };
        });
    });
}

function restoreTab(idx) {
    chrome.storage.local.get(['timemeshin_history'], (res) => {
        const history = res.timemeshin_history || [];
        const item = history[idx];
        if (item) {
            chrome.runtime.sendMessage({
                type: 'RESTORE_TAB_REQUEST',
                url: item.url,
                title: item.title,
                scroll_x: item.scroll_x,
                scroll_y: item.scroll_y,
                inputs: item.inputs
            });
            window.close();
        }
    });
}

document.addEventListener('DOMContentLoaded', renderHistory);
