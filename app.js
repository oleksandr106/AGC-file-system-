/* ============================================
   AGC Technowizz 2027 — Premium DMS Application
   ============================================ */
const API_URL = window.location.protocol === 'file:' ? 'http://localhost:8000' : window.location.origin;
let token = localStorage.getItem('dms_token') || '';
let currentUser = null;
let searchDebounceTimer = null;
let currentSearchPage = 1;
let currentCategoryFilter = '';
let currentStatusFilter = '';
// ============================================
// TOAST NOTIFICATION SYSTEM
// ============================================
function showToast(type, title, message, duration = 4000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icons = {
        success: 'ph-fill ph-check-circle',
        error: 'ph-fill ph-x-circle',
        info: 'ph-fill ph-info',
        warning: 'ph-fill ph-warning',
    };
    toast.innerHTML = `
        <i class="toast-icon ${icons[type] || icons.info}"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-message">${message}</div>` : ''}
        </div>
        <button class="toast-close" onclick="dismissToast(this)">
            <i class="ph-bold ph-x"></i>
        </button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        dismissToast(toast.querySelector('.toast-close'));
    }, duration);
}
function dismissToast(btn) {
    const toast = btn.closest ? btn.closest('.toast') : btn;
    if (!toast || toast.classList.contains('hiding'))
        return;
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
}
// ============================================
// THEME TOGGLE
// ============================================
function initTheme() {
    const saved = localStorage.getItem('dms_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('dms_theme', next);
    updateThemeIcon(next);
}
function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggle');
    const btn2 = document.getElementById('themeToggleSidebar');
    const icon = theme === 'dark' ? 'ph-sun' : 'ph-moon';
    if (btn)
        btn.innerHTML = `<i class="ph-duotone ${icon}"></i>`;
    if (btn2)
        btn2.innerHTML = `<i class="ph-duotone ${icon}"></i>`;
}
// ============================================
// AUTH SYSTEM
// ============================================
async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
async function fetchWithAuth(endpoint, options = {}) {
    options.headers = options.headers || {};
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    return fetch(`${API_URL}${endpoint}`, options);
}
function checkAuth() {
    if (token) {
        try {
            let base64Url = token.split('.')[1];
            let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            // Add padding to base64 string to prevent atob DOMException
            while (base64.length % 4) {
                base64 += '=';
            }
            const payload = JSON.parse(window.atob(base64));
            // Check token expiration
            if (payload.exp && payload.exp * 1000 < Date.now()) {
                handleLogout();
                return;
            }
            currentUser = {
                username: payload.sub,
                role: payload.role || (payload.sub === 'admin' ? 'admin' : 'user'),
            };
            showApp();
        }
        catch (e) {
            console.error('checkAuth failed:', e);
            alert('Chyba při přihlášení (checkAuth): ' + e.message);
            handleLogout();
        }
    }
    else {
        showLogin();
    }
}
function showLogin() {
    document.getElementById('loginScreen').style.display = 'flex';
    document.getElementById('appScreen').style.display = 'none';
}
function showApp() {
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('appScreen').style.display = 'flex';
    // User info
    document.getElementById('displayUsername').innerText = currentUser.username;
    document.getElementById('displayRole').innerText =
        currentUser.role === 'admin' ? 'Administrátor' : 'Uživatel';
    document.getElementById('userAvatar').innerText =
        currentUser.username.charAt(0).toUpperCase();
    // Admin menu visibility
    const adminMenu = document.getElementById('menu-admin');
    if (currentUser.role === 'admin') {
        adminMenu.style.display = 'block';
    }
    else {
        adminMenu.style.display = 'none';
    }
    switchView('dashboard');
}
async function handleLogin(e) {
    e.preventDefault();
    const btn = document.querySelector('.login-btn');
    const errDiv = document.getElementById('loginError');
    errDiv.style.display = 'none';
    btn.classList.add('loading');
    btn.innerHTML = '<span class="spinner"></span> Přihlašování...';
    const rawPassword = document.getElementById('password').value;
    const hashedPassword = await hashPassword(rawPassword);
    const formData = new FormData();
    formData.append('username', document.getElementById('username').value);
    formData.append('password', hashedPassword);
    try {
        const res = await fetch(`${API_URL}/api/token`, {
            method: 'POST',
            body: formData,
        });
        if (res.ok) {
            const data = await res.json();
            token = data.access_token;
            localStorage.setItem('dms_token', token);
            showToast('success', 'Přihlášení úspěšné', `Vítejte zpět, ${document.getElementById('username').value}!`);
            document.getElementById('loginForm').reset();
            checkAuth();
        }
        else {
            errDiv.style.display = 'block';
            errDiv.textContent = 'Nesprávné přihlašovací údaje. Zkuste to znovu.';
        }
    }
    catch (err) {
        showToast('error', 'Chyba připojení', 'Nepodařilo se spojit s API serverem.');
    }
    finally {
        btn.classList.remove('loading');
        btn.innerHTML = 'Přihlásit se';
    }
}
function handleLogout() {
    token = '';
    currentUser = null;
    localStorage.removeItem('dms_token');
    showLogin();
}
// ============================================
// NAVIGATION
// ============================================
function switchView(viewName) {
    document.querySelectorAll('.view-section').forEach((v) => v.classList.remove('active'));
    document.querySelectorAll('.nav-menu li').forEach((m) => m.classList.remove('active'));
    const viewEl = document.getElementById(`view-${viewName}`);
    if (viewEl)
        viewEl.classList.add('active');
    const menuMap = {
        dashboard: 'menu-dash',
        documents: 'menu-docs',
        upload: 'menu-upload',
        admin: 'menu-admin',
        info: 'menu-info',
    };
    const menuEl = document.getElementById(menuMap[viewName]);
    if (menuEl)
        menuEl.classList.add('active');
    const title = document.getElementById('viewTitle');
    const sub = document.getElementById('viewSubtitle');
    const views = {
        dashboard: {
            title: 'Přehled',
            sub: 'Vítejte v systému pro správu řízené dokumentace.',
            init: loadDashboard,
        },
        documents: {
            title: 'Správa dokumentů',
            sub: 'Procházejte, stahujte a hledejte napříč databází.',
            init: () => { currentSearchPage = 1; executeSearch(false); },
        },
        upload: {
            title: 'Nahrát dokument',
            sub: 'Vložte nový soubor nebo vytvořte novou verzi stávajícího dokumentu.',
        },
        admin: {
            title: 'Správa systému',
            sub: 'Administrátorské nástroje, správa uživatelů a zálohování.',
            init: loadAdminPanel,
        },
        info: {
            title: 'Informace',
            sub: 'Informace o projektu a systému.',
        },
    };
    const view = views[viewName];
    if (view) {
        title.innerText = view.title;
        if (sub) sub.innerText = view.sub;
        if (view.init)
            view.init();
    }
    // Close mobile sidebar
    closeMobileSidebar();
}
// ============================================
// MOBILE SIDEBAR
// ============================================
function openMobileSidebar() {
    document.querySelector('.sidebar').classList.add('open');
    document.getElementById('sidebarOverlay').classList.add('active');
}
function closeMobileSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('active');
}
// ============================================
// DASHBOARD
// ============================================
async function loadDashboard() {
    await Promise.all([loadStats(), loadRecentDocuments()]);
}
async function loadStats() {
    try {
        const res = await fetchWithAuth('/api/stats');
        if (res.ok) {
            const data = await res.json();
            animateNumber('statDocs', data.total_documents);
            animateNumber('statVersions', data.total_versions);
            animateNumber('statUsers', data.total_users);
            renderCategoryChart(data.categories);
        }
    }
    catch (err) {
        console.error('Chyba při načítání statistik:', err);
    }
}
function animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el)
        return;
    const duration = 600;
    const start = parseInt(el.innerText) || 0;
    const diff = target - start;
    const startTime = performance.now();
    function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.innerText = Math.round(start + diff * eased).toString();
        if (progress < 1)
            requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}
function renderCategoryChart(categories) {
    const container = document.getElementById('categoryChart');
    if (!container || !categories || categories.length === 0) {
        if (container)
            container.innerHTML = '<p style="color: var(--text-muted); font-size: 0.9rem; text-align: center; padding: 1rem;">Zatím žádné kategorie.</p>';
        return;
    }
    const max = Math.max(...categories.map((c) => c.count));
    container.innerHTML = categories
        .map((cat) => `
        <div class="chart-bar-row">
            <span class="chart-bar-label">${cat.name}</span>
            <div class="chart-bar-track">
                <div class="chart-bar-fill" style="width: ${Math.max((cat.count / max) * 100, 8)}%;">
                    <span class="chart-bar-value">${cat.count}</span>
                </div>
            </div>
        </div>
    `)
        .join('');
}
async function loadRecentDocuments() {
    const container = document.getElementById('recentDocuments');
    if (!container)
        return;
    try {
        const res = await fetchWithAuth('/api/recent');
        if (!res.ok)
            throw new Error();
        const docs = await res.json();
        if (docs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="ph-duotone ph-folder-simple-dashed"></i>
                    <h3>Žádné dokumenty</h3>
                    <p>Zatím nebyly nahrány žádné dokumenty.</p>
                </div>
            `;
            return;
        }
        container.innerHTML = docs
            .map((doc) => {
            const dateStr = new Date(doc.uploaded_at).toLocaleString('cs-CZ', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
            return `
                <div class="recent-item">
                    <div class="recent-icon"><i class="ph-duotone ph-file-pdf"></i></div>
                    <div class="recent-info">
                        <div class="recent-title">${doc.title}</div>
                        <div class="recent-meta">v${doc.version_number.toFixed(1)} · ${dateStr} · ${doc.uploaded_by}</div>
                    </div>
                    <div class="recent-action">
                        <button class="action-btn" title="Stáhnout" onclick="downloadDoc(${doc.version_id}, '${doc.title}_v${doc.version_number.toFixed(1)}')">
                            <i class="ph-bold ph-download-simple"></i> Stáhnout
                        </button>
                    </div>
                </div>
            `;
        })
            .join('');
    }
    catch (err) {
        container.innerHTML = '<p style="color: var(--text-muted); padding: 1rem;">Nepodařilo se načíst nedávné dokumenty.</p>';
    }
}
// ============================================
// DOCUMENTS — SEARCH & TABLE
// ============================================
function debounceSearch() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        currentSearchPage = 1;
        executeSearch(false);
    }, 300);
}
function onCategoryFilterChange() {
    currentCategoryFilter = document.getElementById('categoryFilter').value;
    currentSearchPage = 1;
    executeSearch(false);
}
function onStatusFilterChange() {
    currentStatusFilter = document.getElementById('statusFilter').value;
    currentSearchPage = 1;
    executeSearch(false);
}
// Mapování stavů na barevné badge
function getStatusBadge(status) {
    const statusMap = {
        'APPROVED': { label: 'Schváleno', class: 'status-approved' },
        'PENDING_APPROVAL': { label: 'Čeká na schválení', class: 'status-pending' },
        'DRAFT': { label: 'Koncept', class: 'status-draft' },
        'ARCHIVED': { label: 'Archivováno', class: 'status-archived' },
    };
    const s = statusMap[status] || statusMap['APPROVED'];
    return `<span class="status-badge ${s.class}">${s.label}</span>`;
}
async function executeSearch(page) {
    if (page)
        currentSearchPage = page;
    const query = document.getElementById('searchQuery').value;
    const tbody = document.getElementById('documentsTableBody');
    // Skeleton loader
    tbody.innerHTML = Array(3)
        .fill(0)
        .map(() => `
        <tr class="skeleton-row">
            <td><div class="skeleton skeleton-cell w-40" style="height:16px;"></div></td>
            <td><div class="skeleton skeleton-cell w-20" style="height:16px;"></div></td>
            <td><div class="skeleton skeleton-cell w-15" style="height:16px;"></div></td>
            <td><div class="skeleton skeleton-cell w-20" style="height:16px;"></div></td>
            <td><div class="skeleton skeleton-cell w-10" style="height:16px;"></div></td>
            <td><div class="skeleton skeleton-cell w-10" style="height:16px;"></div></td>
        </tr>
    `)
        .join('');
    try {
        const params = new URLSearchParams({
            q: query,
            page: String(page || currentSearchPage),
            per_page: String(10)
        });
        if (currentCategoryFilter)
            params.append('category', currentCategoryFilter);
        if (currentStatusFilter)
            params.append('doc_status', currentStatusFilter);
        const res = await fetchWithAuth(`/api/search?${params}`);
        if (!res.ok)
            throw new Error('Chyba API');
        const data = await res.json();
        tbody.innerHTML = '';
        if (data.documents.length === 0) {
            tbody.innerHTML = `
                <tr><td colspan="6">
                    <div class="empty-state">
                        <i class="ph-duotone ph-magnifying-glass"></i>
                        <h3>Žádné výsledky</h3>
                        <p>${query ? `Pro hledaný výraz "${query}" nebyly nalezeny žádné dokumenty.` : 'Zatím nejsou v systému žádné dokumenty.'}</p>
                        ${!query ? '<button class="btn-primary" onclick="switchView(\'upload\')"><i class="ph-bold ph-plus"></i> Nahrát první dokument</button>' : ''}
                    </div>
                </td></tr>
            `;
            document.getElementById('paginationContainer').innerHTML = '';
            return;
        }
        data.documents.forEach((doc) => {
            const tr = document.createElement('tr');
            const dateStr = new Date(doc.uploaded_at).toLocaleString('cs-CZ', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
            const isAdmin = currentUser && currentUser.role === 'admin';
            tr.innerHTML = `
                <td>
                    <div class="doc-title" onclick="previewDoc(${doc.version_id}, '${doc.title}')" style="cursor: pointer;" title="Klikněte pro náhled">
                        <i class="ph-duotone ph-file-pdf doc-icon"></i>
                        <span style="text-decoration: underline; text-underline-offset: 3px; color: var(--accent-blue);">${doc.title}</span>
                    </div>
                </td>
                <td><span class="badge">${doc.category}</span></td>
                <td>${getStatusBadge(doc.status)}</td>
                <td style="color: var(--text-muted); font-size: 0.85rem;">${dateStr}</td>
                <td><span class="v-badge">v${doc.latest_version.toFixed(1)}</span></td>
                <td>
                    <div class="actions-cell">
                        <button class="action-btn" title="Stáhnout" onclick="downloadDoc(${doc.version_id}, '${doc.title}_v${doc.latest_version.toFixed(1)}')">
                            <i class="ph-bold ph-download-simple"></i> Stáhnout
                        </button>
                        <button class="action-btn" title="Historie verzí" onclick="showVersionHistory(${doc.document_id}, '${doc.title}')">
                            <i class="ph-bold ph-clock-counter-clockwise"></i> Historie
                        </button>
                        ${isAdmin ? `
                        <button class="action-btn delete" title="Smazat dokument" onclick="confirmDeleteDocument(${doc.document_id}, '${doc.title}')">
                            <i class="ph-bold ph-trash"></i> Smazat
                        </button>
                        ` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
        renderPagination(data);
    }
    catch (error) {
        console.error('Search error:', error);
        tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><i class="ph-duotone ph-warning-circle"></i><h3>Chyba načítání</h3><p>Nepodařilo se načíst dokumenty ze serveru.</p></div></td></tr>`;
    }
}
function renderPagination(data) {
    const container = document.getElementById('paginationContainer');
    if (!container || data.total_pages <= 1) {
        if (container)
            container.innerHTML = '';
        return;
    }
    let html = `<div class="pagination">`;
    html += `<button class="pagination-btn" ${data.page <= 1 ? 'disabled' : ''} onclick="executeSearch(${data.page - 1})">
        <i class="ph-bold ph-caret-left"></i>
    </button>`;
    for (let i = 1; i <= data.total_pages; i++) {
        if (i === 1 ||
            i === data.total_pages ||
            (i >= data.page - 1 && i <= data.page + 1)) {
            html += `<button class="pagination-btn ${i === data.page ? 'active' : ''}" onclick="executeSearch(${i})">${i}</button>`;
        }
        else if (i === data.page - 2 || i === data.page + 2) {
            html += `<span class="pagination-info">…</span>`;
        }
    }
    html += `<button class="pagination-btn" ${data.page >= data.total_pages ? 'disabled' : ''} onclick="executeSearch(${data.page + 1})">
        <i class="ph-bold ph-caret-right"></i>
    </button>`;
    html += `</div>`;
    container.innerHTML = html;
}
// ============================================
// DOCUMENT ACTIONS
// ============================================
async function previewDoc(versionId, title) {
    try {
        const res = await fetchWithAuth(`/api/download/${versionId}`);
        if (res.ok) {
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            let content = '';
            if (blob.type.startsWith('image/')) {
                content = `<img src="${url}" style="max-width:100%; max-height:60vh; object-fit:contain; border-radius:4px;">`;
            }
            else if (blob.type === 'application/pdf') {
                content = `<iframe src="${url}" width="100%" height="600px" style="border:none; border-radius:4px;"></iframe>`;
            }
            else if (blob.type === 'text/plain' || blob.type === 'text/csv') {
                const text = await blob.text();
                content = `<pre style="text-align: left; background: var(--bg-glass); padding: 1rem; overflow: auto; max-height: 500px;">${text}</pre>`;
            }
            else {
                content = `<div style="padding: 2rem; text-align: center; color: var(--text-muted);">
                    <i class="ph-duotone ph-file-text" style="font-size: 4rem; margin-bottom: 1rem; color: var(--accent-blue);"></i>
                    <p>Tento typ souboru nelze zobrazit v náhledu.</p>
                    <button class="btn-primary" style="margin-top: 1rem;" onclick="downloadDoc(${versionId}, '${title}')">Stáhnout místo náhledu</button>
                </div>`;
            }
            showModal(`Náhled: ${title}`, content, [
                { text: 'Zavřít', class: 'btn-secondary', action: 'closeModal()' },
                { text: 'Stáhnout', class: 'btn-primary', action: `downloadDoc(${versionId}, '${title}')` }
            ]);
        }
        else {
            showToast('error', 'Chyba', 'Soubor se nepodařilo načíst pro náhled.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se spojit se serverem.');
    }
}
async function downloadDoc(versionId, filename) {
    try {
        const res = await fetchWithAuth(`/api/download/${versionId}`);
        if (res.ok) {
            let finalFilename = filename;
            const disposition = res.headers.get('Content-Disposition');
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (matches != null && matches[1]) {
                    finalFilename = matches[1].replace(/['"]/g, '');
                }
            }
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = finalFilename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            showToast('success', 'Stahování zahájeno', `Soubor "${finalFilename}" se stahuje.`);
        }
        else {
            showToast('error', 'Chyba stahování', 'Soubor se nepodařilo stáhnout.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se spojit se serverem.');
    }
}
function confirmDeleteDocument(docId, title) {
    showModal('Smazat dokument', `Opravdu chcete trvale smazat dokument "<strong>${title}</strong>" a všechny jeho verze? Tato akce je nevratná.`, [
        { text: 'Zrušit', class: 'btn-secondary', action: 'closeModal()' },
        {
            text: 'Smazat',
            class: 'btn-danger',
            action: `deleteDocument(${docId})`,
        },
    ]);
}
async function deleteDocument(docId) {
    closeModal();
    try {
        const res = await fetchWithAuth(`/api/documents/${docId}`, {
            method: 'DELETE',
        });
        const data = await res.json();
        if (res.ok) {
            showToast('success', 'Dokument smazán', data.message);
            executeSearch(false);
        }
        else {
            showToast('error', 'Chyba', data.detail || 'Mazání selhalo.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se spojit se serverem.');
    }
}
async function showVersionHistory(docId, title) {
    try {
        const res = await fetchWithAuth(`/api/documents/${docId}/versions`);
        if (!res.ok)
            throw new Error();
        const data = await res.json();
        let content = `<div style="max-height: 400px; overflow-y: auto;">`;
        content += `<table class="dms-table" style="font-size: 0.85rem;">
            <thead><tr>
                <th>Verze</th>
                <th>Nahráno</th>
                <th>Nahrál</th>
                <th style="width:60px;">Akce</th>
            </tr></thead><tbody>`;
        data.versions.forEach((v) => {
            const dateStr = new Date(v.uploaded_at).toLocaleString('cs-CZ', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            });
            content += `<tr>
                <td><span class="v-badge">v${v.version_number.toFixed(1)}</span></td>
                <td style="color: var(--text-muted);">${dateStr}</td>
                <td style="color: var(--text-secondary);">${v.uploaded_by}</td>
                <td><button class="action-btn" onclick="downloadDoc(${v.id}, '${title}_v${v.version_number.toFixed(1)}')"><i class="ph-bold ph-download-simple"></i> Stáhnout</button></td>
            </tr>`;
        });
        content += `</tbody></table></div>`;
        showModal(`Historie verzí — ${title}`, content, [
            { text: 'Zavřít', class: 'btn-secondary', action: 'closeModal()' },
        ]);
    }
    catch (err) {
        showToast('error', 'Chyba', 'Nepodařilo se načíst historii verzí.');
    }
}
// ============================================
// UPLOAD
// ============================================
function updateFileLabel() {
    const input = document.getElementById('fileInput');
    const label = document.getElementById('fileLabel');
    const hint = document.getElementById('fileHint');
    const previewContainer = document.getElementById('filePreviewContainer');
    const previewContent = document.getElementById('filePreviewContent');
    if (input.files && input.files.length > 0) {
        const file = input.files[0];
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        label.innerText = file.name;
        label.style.color = 'var(--accent-blue)';
        if (hint)
            hint.innerText = `${sizeMB} MB`;
        // Generate Preview
        previewContainer.style.display = 'block';
        previewContent.innerHTML = '<span class="spinner"></span> Načítání náhledu...';
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewContent.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; max-height: 350px; object-fit: contain;">`;
            };
            reader.readAsDataURL(file);
        }
        else if (file.type === 'application/pdf') {
            const url = URL.createObjectURL(file);
            previewContent.innerHTML = `<iframe src="${url}" width="100%" height="400px" style="border: none;"></iframe>`;
        }
        else if (file.type === 'text/plain' || file.type === 'text/csv') {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewContent.innerHTML = `<pre style="text-align: left; background: var(--bg-glass); padding: 1rem; overflow: auto; max-height: 350px;">${e.target.result}</pre>`;
            };
            reader.readAsText(file);
        }
        else {
            previewContent.innerHTML = `<p style="color: var(--text-muted);">Náhled pro tento typ souboru není podporován.</p><i class="ph-duotone ph-file" style="font-size: 3rem; color: var(--accent-blue);"></i>`;
        }
    }
    else {
        label.innerText = 'Klikněte nebo přetáhněte soubor';
        label.style.color = 'var(--text-muted)';
        if (hint)
            hint.innerText = 'PDF, DOCX, XLSX, PPTX, TXT, CSV, obrázky';
        previewContainer.style.display = 'none';
        previewContent.innerHTML = '';
    }
}
function initDragDrop() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone)
        return;
    ['dragenter', 'dragover'].forEach((evt) => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });
    ['dragleave', 'drop'].forEach((evt) => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            document.getElementById('fileInput').files = files;
            updateFileLabel();
        }
    });
}
async function handleUpload(e) {
    e.preventDefault();
    const title = document.getElementById('uploadTitle').value;
    const category = document.getElementById('uploadCategory').value;
    const version = document.getElementById('uploadVersion').value;
    const fileInput = document.getElementById('fileInput');
    if (fileInput.files.length === 0) {
        showToast('warning', 'Chybí soubor', 'Vyberte soubor k nahrání.');
        return;
    }
    const btn = document.getElementById('uploadBtn');
    btn.classList.add('loading');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Nahrávání...';
    btn.disabled = true;
    const formData = new FormData();
    formData.append('title', title);
    formData.append('category', category);
    formData.append('version_number', version);
    formData.append('doc_status', document.getElementById('uploadStatus').value);
    formData.append('file', fileInput.files[0]);
    try {
        const res = await fetchWithAuth('/api/upload', {
            method: 'POST',
            body: formData,
        });
        if (res.ok) {
            showToast('success', 'Dokument uložen', `"${title}" verze ${version} byl úspěšně nahrán.`);
            document.getElementById('uploadForm').reset();
            updateFileLabel();
            setTimeout(() => switchView('documents'), 800);
        }
        else {
            const errData = await res.json();
            showToast('error', 'Chyba nahrávání', errData.detail || 'Nahrávání selhalo.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se nahrát soubor na server.');
    }
    finally {
        btn.classList.remove('loading');
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
// ============================================
// ADMIN PANEL
// ============================================
async function loadAdminPanel() {
    await loadUsers();
}
async function loadUsers() {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody)
        return;
    try {
        const res = await fetchWithAuth('/api/users');
        if (!res.ok)
            throw new Error();
        const users = await res.json();
        tbody.innerHTML = '';
        users.forEach((u) => {
            const dateStr = u.created_at
                ? new Date(u.created_at).toLocaleString('cs-CZ', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                })
                : '–';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight: 600;">${u.username}</td>
                <td><span class="role-badge ${u.role}">${u.role === 'admin' ? '⚡ Admin' : '👤 User'}</span></td>
                <td style="color: var(--text-muted); font-size: 0.85rem;">${dateStr}</td>
                <td>
                    ${u.username !== 'admin' ? `
                        <button class="action-btn delete" title="Smazat uživatele" onclick="confirmDeleteUser(${u.id}, '${u.username}')">
                            <i class="ph-bold ph-trash"></i>
                        </button>
                    ` : '<span style="color: var(--text-muted); font-size: 0.78rem;">Chráněný</span>'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    catch (err) {
        showToast('error', 'Chyba', 'Nepodařilo se načíst seznam uživatelů.');
    }
}
function confirmDeleteUser(userId, username) {
    showModal('Smazat uživatele', `Opravdu chcete smazat uživatele "<strong>${username}</strong>"? Tato akce je nevratná.`, [
        { text: 'Zrušit', class: 'btn-secondary', action: 'closeModal()' },
        {
            text: 'Smazat',
            class: 'btn-danger',
            action: `deleteUser(${userId})`,
        },
    ]);
}
async function deleteUser(userId) {
    closeModal();
    try {
        const res = await fetchWithAuth(`/api/users/${userId}`, {
            method: 'DELETE',
        });
        const data = await res.json();
        if (res.ok) {
            showToast('success', 'Uživatel smazán', data.message);
            loadUsers();
        }
        else {
            showToast('error', 'Chyba', data.detail || 'Mazání selhalo.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se spojit se serverem.');
    }
}
async function createBackup() {
    const btn = document.getElementById('backupBtn');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Vytvářím zálohu...';
    btn.disabled = true;
    try {
        const res = await fetchWithAuth('/api/backup', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            showToast('success', 'Záloha vytvořena', `${data.message} (${data.file})`);
        }
        else {
            showToast('error', 'Chyba zálohy', data.detail || 'Nepodařilo se vytvořit zálohu.');
        }
    }
    catch (err) {
        showToast('error', 'Chyba sítě', 'Nepodařilo se spojit se zálohovacím modulem.');
    }
    finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}
// ============================================
// MODAL SYSTEM
// ============================================
function showModal(title, content, actions = []) {
    const overlay = document.getElementById('modalOverlay');
    document.getElementById('modalTitle').innerHTML = title;
    document.getElementById('modalDesc').innerHTML = content;
    const actionsContainer = document.getElementById('modalActions');
    actionsContainer.innerHTML = actions
        .map((a) => `<button class="${a.class}" onclick="${a.action}">${a.text}</button>`)
        .join('');
    overlay.classList.add('active');
}
function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}
// ============================================
// INIT
// ============================================
window.addEventListener('DOMContentLoaded', () => {
    initTheme();
    checkAuth();
    initDragDrop();
    // Close modal on overlay click
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget)
            closeModal();
    });
    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeMobileSidebar();
        }
    });
});
