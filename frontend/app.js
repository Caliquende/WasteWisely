/**
 * WasteWisely Dashboard Application
 * Frontend controller for scan, display, and action operations.
 */

const API = '';
let scanData = null;
let scanRoot = null;
let actionHistory = [];
let donutChart = null;
let treemapChart = null;
let activeFilter = 'all'; // Global state for results filtering

// ── Navigation ──
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Language
    applyLanguage(currentLang);
    const langSelect = document.getElementById('lang-selector');
    if (langSelect) {
        langSelect.value = currentLang;
        langSelect.addEventListener('change', (e) => {
            applyLanguage(e.target.value);
            if (currentResults.length > 0) {
                renderResults(currentResults);
            }
            renderHistory();
            renderCategories();
        });
    }

    const selectFolderBtn = document.getElementById('btn-select-folder');
    if (selectFolderBtn) {
        selectFolderBtn.addEventListener('click', async () => {
            // Priority 1: pywebview native API (Desktop App)
            if (window.pywebview && window.pywebview.api) {
                try {
                    const folder = await window.pywebview.api.select_folder();
                    if (folder) {
                        document.getElementById('scan-path').value = folder;
                    }
                    return; // Done
                } catch (err) {
                    console.error("Native folder selection failed:", err);
                }
            }
            
            // Priority 2: Fallback to Backend API (Browser/Serve mode)
            try {
                const response = await fetch('/api/select-directory');
                const data = await response.json();
                if (data.path) {
                    document.getElementById('scan-path').value = data.path;
                }
            } catch (err) {
                console.error("Backend folder selection failed:", err);
            }
        });
    }

    // Initialize UI
    switchView('dashboard');
});

document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        switchView(view);
    });
});

function switchView(viewName) {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const navBtn = document.querySelector(`[data-view="${viewName}"]`);
    const viewEl = document.getElementById(`view-${viewName}`);
    if (navBtn) navBtn.classList.add('active');
    if (viewEl) viewEl.classList.add('active');
    const titles = { dashboard: 'Dashboard', scan: 'Tarama', results: 'Sonuçlar', history: 'Geçmiş' };
    document.getElementById('page-title').textContent = titles[viewName] || viewName;
}

// ── Sidebar Toggle (Mobile) ──
document.getElementById('menu-toggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});

// ── Start Scan Buttons ──
document.getElementById('btn-start-scan').addEventListener('click', () => switchView('scan'));
document.getElementById('btn-rescan')?.addEventListener('click', () => {
    if (scanRoot) startScan(scanRoot);
});

document.getElementById('btn-scan').addEventListener('click', () => {
    const path = document.getElementById('scan-path').value.trim() || '.';
    startScan(path);
});

// Quick paths
document.querySelectorAll('.quick-path-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const path = btn.dataset.path;
        document.getElementById('scan-path').value = path;
        startScan(path);
    });
});

// ── Scan Logic ──
async function startScan(path, options = {}) {
    const viewAfterScan = options.viewAfterScan || 'dashboard';
    const progressEl = document.getElementById('scan-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');

    progressEl.classList.remove('hidden');
    progressFill.style.width = '20%';
    progressText.textContent = 'Tarama başlatılıyor...';
    statusDot.style.background = 'var(--yellow)';
    statusText.textContent = 'Taranıyor...';

    // Simulate progress
    let progress = 20;
    const progressInterval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 15, 90);
        progressFill.style.width = progress + '%';
        const msgs = ['Dosyalar taranıyor...', 'Bağımlılıklar analiz ediliyor...', 'Hassas dosyalar kontrol ediliyor...', 'Sınıflandırma yapılıyor...'];
        progressText.textContent = msgs[Math.floor(Math.random() * msgs.length)];
    }, 400);

    try {
        const resp = await fetch(`${API}/api/scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path }),
        });

        clearInterval(progressInterval);

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Tarama başarısız');
        }

        const data = await resp.json();
        scanData = data.summary;
        scanRoot = data.scan_root;

        progressFill.style.width = '100%';
        progressText.textContent = 'Tarama tamamlandı!';
        statusDot.style.background = 'var(--green)';
        statusText.textContent = 'Hazır';

        setTimeout(() => {
            progressEl.classList.add('hidden');
            renderDashboard();
            renderResults();
            switchView(viewAfterScan);
            showToast('success', `Tarama tamamlandı: ${scanData.total_waste_count} atık bulundu.`);
        }, 500);

    } catch (err) {
        clearInterval(progressInterval);
        progressFill.style.width = '0%';
        progressEl.classList.add('hidden');
        statusDot.style.background = 'var(--red)';
        statusText.textContent = 'Hata';
        showToast('error', err.message);
    }
}

// ── Dashboard Render ──
function renderDashboard() {
    if (!scanData) return;
    document.getElementById('dashboard-empty').classList.add('hidden');
    document.getElementById('dashboard-content').classList.remove('hidden');

    // Stats
    document.getElementById('stat-scanned').textContent = scanData.total_items_scanned.toLocaleString();
    document.getElementById('stat-waste-count').textContent = scanData.total_waste_count.toLocaleString();
    document.getElementById('stat-waste-size').textContent = scanData.total_waste_size_human;

    const criticalCount = (scanData.categories.sensitive_leaks?.count || 0);
    document.getElementById('stat-critical').textContent = criticalCount;

    renderCharts();
    renderCategories();
}

// ── Charts ──
function renderCharts() {
    const cats = scanData.categories;
    const labels = [], counts = [], sizes = [], colors = [];
    const colorMap = {
        heavy_dependencies: '#6366f1',
        sensitive_leaks: '#ef4444',
        ghost_files: '#a855f7',
        forgotten_projects: '#eab308',
        large_files: '#06b6d4',
    };

    for (const [key, cat] of Object.entries(cats)) {
        if (cat.count === 0) continue;
        labels.push(cat.name);
        counts.push(cat.count);
        sizes.push(+(cat.total_size / (1024 * 1024)).toFixed(2));
        colors.push(colorMap[key] || '#6366f1');
    }

    const chartDefaults = {
        color: '#94a3b8',
        font: { family: 'Inter' },
    };
    Chart.defaults.color = chartDefaults.color;
    Chart.defaults.font.family = chartDefaults.font.family;

    // Donut
    if (donutChart) donutChart.destroy();
    const donutCtx = document.getElementById('chart-categories').getContext('2d');
    donutChart = new Chart(donutCtx, {
        type: 'doughnut',
        data: { labels, datasets: [{ data: counts, backgroundColor: colors, borderWidth: 0, hoverOffset: 8 }] },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: '65%',
            plugins: {
                legend: { position: 'right', labels: { padding: 16, usePointStyle: true, pointStyleWidth: 12 } },
            },
        },
    });

    // Treemap
    if (treemapChart) treemapChart.destroy();
    const treemapCtx = document.getElementById('chart-treemap')?.getContext('2d');
    if (treemapCtx) {
        const treeData = [];
        for (const [key, cat] of Object.entries(scanData.categories)) {
            for (const item of cat.items) {
                if (item.size > 0) {
                    treeData.push({
                        categoryKey: key,
                        name: item.name,
                        value: item.size
                    });
                }
            }
        }
        
        treemapChart = new Chart(treemapCtx, {
            type: 'treemap',
            data: {
                datasets: [{
                    tree: treeData,
                    key: 'value',
                    groups: ['categoryKey', 'name'],
                    backgroundColor: (ctx) => {
                        if (ctx.type !== 'data') return 'transparent';
                        const item = ctx.raw;
                        if (!item || !item._data) return '#334155';
                        const cat = item._data.categoryKey;
                        const col = colorMap[cat] || '#334155';
                        return col + '80'; // 50% opacity
                    },
                    borderColor: '#0f172a',
                    borderWidth: 1,
                    labels: {
                        display: true,
                        color: '#f8fafc',
                        formatter: (ctx) => {
                            if (ctx.type !== 'data') return [];
                            return [ctx.raw._data.name];
                        }
                    }
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const v = ctx.raw.v;
                                return `${ctx.raw._data.name}: ${(v / (1024*1024)).toFixed(2)} MB`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// ── Category Cards ──
function renderCategories() {
    const container = document.getElementById('categories-list');
    container.innerHTML = '';
    for (const [key, cat] of Object.entries(scanData.categories)) {
        const riskClass = `risk-${cat.risk}`;
        container.innerHTML += `
            <div class="category-item">
                <div class="cat-left">
                    <div class="cat-icon">${cat.icon}</div>
                    <div><div class="cat-name">${cat.name}</div><div class="cat-count">${cat.count} öğe</div></div>
                </div>
                <div class="cat-right">
                    <div class="cat-size">${cat.total_size_human}</div>
                    <span class="risk-badge ${riskClass}">${cat.risk}</span>
                </div>
            </div>`;
    }
}

// ── Results Render ──
function renderResults() {
    if (!scanData) return;
    document.getElementById('results-empty')?.classList.add('hidden');
    document.getElementById('results-container')?.classList.remove('hidden');
    const container = document.getElementById('results-list');
    container.innerHTML = '';

    const allItems = [];
    for (const [key, cat] of Object.entries(scanData.categories)) {
        for (const item of cat.items) {
            allItems.push(item);
        }
    }

    allItems.sort((a, b) => b.size - a.size);

    for (const item of allItems) {
        container.appendChild(createResultItem(item));
    }

    // Filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            activeFilter = btn.dataset.filter;
            applyFilter();
        });
    });

    function applyFilter() {
        document.querySelectorAll('.filter-btn').forEach(b => {
            b.classList.remove('active');
            if (b.dataset.filter === activeFilter) b.classList.add('active');
        });
        
        document.querySelectorAll('.result-item').forEach(el => {
            if (activeFilter === 'all' || el.dataset.category === activeFilter) {
                el.style.display = '';
            } else {
                el.style.display = 'none';
            }
        });
    }

    // Initial apply
    applyFilter();

    // Bulk Action Handler
    document.getElementById('btn-bulk-clean')?.addEventListener('click', () => {
        if (allItems.length > 0) {
            openActionModal('bulk_delete', 'all', `${allItems.length} Adet Atık Öğe`);
        } else {
            showToast('info', 'Temizlenecek atık yok.');
        }
    });
}

function createResultItem(item) {
    const el = document.createElement('div');
    el.className = 'result-item';
    el.dataset.category = item.category;

    const iconMap = {
        heavy_dependencies: '📦', sensitive_leaks: '🔑',
        ghost_files: '👻', forgotten_projects: '🕸️', large_files: '💾',
    };

    el.innerHTML = `
        <div class="result-left">
            <div class="result-icon">${iconMap[item.category] || '📄'}</div>
            <div class="result-info">
                <div class="result-name">${item.name}</div>
                <div class="result-path" title="${item.path}">${item.relative_path || item.path}</div>
            </div>
        </div>
        <div class="result-right">
            <span class="risk-badge risk-${item.risk}">${item.risk}</span>
            <div class="result-size">${item.size_human}</div>
            <div class="result-actions">
                <button class="btn btn-archive btn-sm" onclick="openActionModal('archive', '${escPath(item.action_path)}', '${esc(item.name)}')">📁 Arşivle</button>
                <button class="btn btn-danger btn-sm" onclick="openActionModal('delete', '${escPath(item.action_path)}', '${esc(item.name)}')">🗑️ Sil</button>
            </div>
        </div>`;
    return el;
}

function esc(s) { return s.replace(/'/g, "\\'").replace(/"/g, '&quot;'); }
function escPath(s) { return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }

// ── Action Modal ──
let pendingAction = null;

function openActionModal(action, targetPath, name) {
    pendingAction = { action, targetPath };
    const actionName = action.includes('delete') ? 'Silme' : 'Arşivleme';
    const actionVerb = action.includes('delete') ? 'silinecek' : 'arşivlenip silinecek';
    const warningColor = action.includes('delete') ? 'var(--red)' : 'var(--cyan)';

    document.getElementById('modal-title').textContent = `${actionName} Onayı`;
    document.getElementById('modal-body').innerHTML = `
        <p><strong style="color:${warningColor}">${name}</strong> kalıcı olarak ${actionVerb}.</p>
        <p>${action.includes('delete') ? '⚠️ Bu işlem geri alınamaz!' : '📁 Dosyalar zip olarak arşive kaldırılacak.'}</p>
        <div class="path-display">${targetPath === 'all' ? 'Tüm tespit edilen atıklar' : targetPath}</div>`;

    const confirmBtn = document.getElementById('modal-confirm');
    confirmBtn.className = action.includes('delete') ? 'btn btn-danger' : 'btn btn-archive';
    confirmBtn.textContent = action.includes('delete') ? '🗑️ Sil' : '📁 Arşivle';

    document.getElementById('modal-overlay').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    pendingAction = null;
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.getElementById('modal-cancel').addEventListener('click', closeModal);
document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'modal-overlay') closeModal();
});

document.getElementById('modal-confirm').addEventListener('click', async () => {
    if (!pendingAction) return;
    const { action, targetPath } = pendingAction;
    closeModal();

    if (action === 'bulk_delete') {
        let successCount = 0;
        document.getElementById('btn-bulk-clean').textContent = 'Temizleniyor...';
        
        for (const [key, cat] of Object.entries(scanData.categories)) {
            for (const item of cat.items) {
                try {
                    await fetch(`${API}/api/action`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'delete', target_path: item.action_path, root_path: scanRoot }),
                    });
                    successCount++;
                } catch(e) {}
            }
        }
        
        showToast('success', `Toplu temizlik tamamlandı: ${successCount} öğe silindi.`);
        document.getElementById('btn-bulk-clean').innerHTML = '💥 Tüm Atıkları Temizle';
        if (scanRoot) startScan(scanRoot, { viewAfterScan: 'results' });
        return;
    }

    try {
        const resp = await fetch(`${API}/api/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, target_path: targetPath, root_path: scanRoot }),
        });

        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'İşlem başarısız');

        const actionLabel = action === 'delete' ? 'Silindi' : 'Arşivlendi';
        showToast('success', `${actionLabel}: ${targetPath.split(/[/\\]/).pop()}`);

        actionHistory.unshift({
            action, path: targetPath,
            time: new Date().toLocaleTimeString('tr-TR'),
            date: new Date().toLocaleDateString('tr-TR'),
        });
        renderHistory();

        // Re-scan
        if (scanRoot) startScan(scanRoot, { viewAfterScan: 'results' });

    } catch (err) {
        showToast('error', err.message);
    }
});

// ── History ──
function renderHistory() {
    const container = document.getElementById('history-list');
    if (actionHistory.length === 0) {
        container.innerHTML = '<p class="text-muted">Henüz işlem yapılmadı.</p>';
        return;
    }
    container.innerHTML = actionHistory.map(h => `
        <div class="history-item">
            <div class="history-icon">${h.action === 'delete' ? '🗑️' : '📁'}</div>
            <div class="history-info">
                <div class="history-action">${h.action === 'delete' ? 'Silindi' : 'Arşivlendi'}</div>
                <div class="history-path">${h.path}</div>
            </div>
            <div class="history-time">${h.date} ${h.time}</div>
        </div>`).join('');
}

// ── Toast ──
function showToast(type, message) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; setTimeout(() => toast.remove(), 300); }, 4000);
}

// ── Init ──
renderHistory();
