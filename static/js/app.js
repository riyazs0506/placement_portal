/**
 * app.js — University Placement Portal
 * Global: auth, sidebar nav, toast, API helpers, notification badge.
 */

// ── Role → Nav links map ─────────────────────────────────────
const NAV_LINKS = {
    student: [
        { href: '/dashboard',          icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/exams',              icon: 'fas fa-pencil-alt',  label: 'My Exams' },
        { href: '/campus-drives',      icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/placement-results',  icon: 'fas fa-trophy',      label: 'My Placements' },
        { href: '/profile',            icon: 'fas fa-user-circle', label: 'My Profile' },
        { href: '/notifications',      icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    staff: [
        { href: '/dashboard',     icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/exams',         icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/exams/create',  icon: 'fas fa-plus-circle', label: 'Create Exam' },
        { href: '/questions',     icon: 'fas fa-database',    label: 'Question Bank' },
        { href: '/campus-drives', icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/placement-results', icon: 'fas fa-trophy',  label: 'Placement' },
        { href: '/notifications', icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    senior_staff: [
        { href: '/dashboard',     icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/exams',         icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/exams/create',  icon: 'fas fa-plus-circle', label: 'Create Exam' },
        { href: '/questions',     icon: 'fas fa-database',    label: 'Question Bank' },
        { href: '/campus-drives', icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/notifications', icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    junior_staff: [
        { href: '/dashboard',     icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/exams',         icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/campus-drives', icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/notifications', icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    head_admin: [
        { href: '/dashboard',          icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/exams',              icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/exams/create',       icon: 'fas fa-plus-circle', label: 'Create Exam' },
        { href: '/questions',          icon: 'fas fa-database',    label: 'Question Bank' },
        { href: '/campus-drives',      icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/placement-results',  icon: 'fas fa-trophy',      label: 'Placement' },
        { href: '/notifications',      icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    placement_officer: [
        { href: '/dashboard',          icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives',      icon: 'fas fa-building',    label: 'Campus Drives' },
        { href: '/exams',              icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/placement-results',  icon: 'fas fa-trophy',      label: 'Placement' },
        { href: '/notifications',      icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company_hr_manager: [
        { href: '/dashboard',           icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives/create',icon: 'fas fa-plus-circle', label: 'New Drive' },
        { href: '/campus-drives',       icon: 'fas fa-building',    label: 'My Drives' },
        { href: '/exams',               icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/exams/create',        icon: 'fas fa-plus',        label: 'Create Exam' },
        { href: '/questions',           icon: 'fas fa-database',    label: 'Question Bank' },
        { href: '/placement-results',   icon: 'fas fa-trophy',      label: 'Placement' },
        { href: '/notifications',       icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company_tech_interviewer: [
        { href: '/dashboard',     icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives', icon: 'fas fa-building',    label: 'Drives' },
        { href: '/notifications', icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company_recruitment_mgr: [
        { href: '/dashboard',           icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives/create',icon: 'fas fa-plus-circle', label: 'New Drive' },
        { href: '/campus-drives',       icon: 'fas fa-building',    label: 'My Drives' },
        { href: '/exams',               icon: 'fas fa-pencil-alt',  label: 'Exams' },
        { href: '/exams/create',        icon: 'fas fa-plus',        label: 'Create Exam' },
        { href: '/placement-results',   icon: 'fas fa-trophy',      label: 'Placement' },
        { href: '/notifications',       icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company_team_leader: [
        { href: '/dashboard',     icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives', icon: 'fas fa-building',    label: 'Drives' },
        { href: '/notifications', icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company_officer: [
        { href: '/dashboard',           icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives/create',icon: 'fas fa-plus-circle', label: 'New Drive' },
        { href: '/campus-drives',       icon: 'fas fa-building',    label: 'My Drives' },
        { href: '/notifications',       icon: 'fas fa-bell',        label: 'Notifications' },
    ],
    company: [
        { href: '/dashboard',           icon: 'fas fa-th-large',    label: 'Dashboard' },
        { href: '/campus-drives/create',icon: 'fas fa-plus-circle', label: 'New Drive' },
        { href: '/campus-drives',       icon: 'fas fa-building',    label: 'My Drives' },
        { href: '/notifications',       icon: 'fas fa-bell',        label: 'Notifications' },
    ],
};

const ROLE_LABELS = {
    student:                  '🎓 Student',
    staff:                    '📋 Staff',
    senior_staff:             '📋 Senior Staff',
    junior_staff:             '📋 Junior Staff',
    head_admin:               '👑 Head Admin',
    placement_officer:        '🏛️ Placement Officer',
    company_hr_manager:       '💼 HR Manager',
    company_tech_interviewer: '💻 Tech Interviewer',
    company_recruitment_mgr:  '🔍 Recruitment Manager',
    company_team_leader:      '👥 Team Leader',
    company_officer:          '🏢 Company Officer',
    company:                  '🏢 Company',
};

// ── Init ─────────────────────────────────────────────────────
function initApp() {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) {
        if (!location.pathname.startsWith('/login') &&
            !location.pathname.startsWith('/register')) {
            window.location.href = '/login';
        }
        return;
    }

    const user = JSON.parse(userStr);
    const role = user.role || 'student';

    // Set topbar user info
    const nameEl = document.getElementById('topbarUserName');
    const roleEl = document.getElementById('topbarUserRole');
    const badgeEl = document.getElementById('userRoleBadge');

    if (nameEl) nameEl.textContent = user.name || '';
    if (roleEl) roleEl.textContent = ROLE_LABELS[role] || role;
    if (badgeEl) badgeEl.textContent = ROLE_LABELS[role] || role;

    // Render sidebar nav
    buildNav(role);

    // Load notification badge count
    loadNotifBadge();
}

function buildNav(role) {
    const navEl = document.getElementById('sidebarNav');
    if (!navEl) return;

    const links = NAV_LINKS[role] || NAV_LINKS['student'];
    const currentPath = location.pathname;

    navEl.innerHTML = links.map(link => `
        <a href="${link.href}" class="nav-link ${currentPath === link.href || currentPath.startsWith(link.href + '/') ? 'active' : ''}">
            <i class="${link.icon}"></i>
            ${link.label}
        </a>
    `).join('');
}

async function loadNotifBadge() {
    try {
        const resp = await apiGet('/api/campus-drive/notifications/unread-count');
        if (!resp.ok) return;
        const data = await resp.json();
        const badge = document.getElementById('notifBadge');
        if (badge && data.count > 0) {
            badge.style.display = 'inline';
            badge.textContent = data.count;
        }
    } catch(e) { /* silent */ }
}

// ── Auth ─────────────────────────────────────────────────────
async function logout() {
    try { await fetch('/api/users/logout', { method: 'POST' }); } catch(e) {}
    localStorage.clear();
    window.location.href = '/login';
}

// ── API Helpers ──────────────────────────────────────────────
async function apiGet(url) {
    const token = localStorage.getItem('token');
    const resp = await fetch(url, {
        headers: { 'Authorization': 'Bearer ' + token }
    });
    if (resp.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return resp;
}

async function apiPost(url, body) {
    const token = localStorage.getItem('token');
    const resp = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify(body)
    });
    if (resp.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }
    return resp;
}

async function apiPut(url, body) {
    const token = localStorage.getItem('token');
    return fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify(body)
    });
}

async function apiDelete(url) {
    const token = localStorage.getItem('token');
    return fetch(url, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + token }
    });
}

// ── Authenticated file download ───────────────────────────────
async function apiDownload(url, btnEl) {
    if (btnEl) {
        btnEl.classList.add('loading');
        const icon = btnEl.querySelector('.dl-icon i');
        if (icon) { icon._origClass = icon.className; icon.className = 'fas fa-spinner'; }
    }
    try {
        const token = localStorage.getItem('token');
        const r = await fetch(url, { headers: { 'Authorization': 'Bearer ' + token } });
        if (!r.ok) throw new Error(r.status === 403 ? 'Access denied' : `Error ${r.status}`);
        // Extract filename from Content-Disposition
        const cd = r.headers.get('Content-Disposition') || '';
        const m  = cd.match(/filename[^;=\n]*=["']?([^"';\n]+)/i);
        const filename = m ? m[1].trim() : url.split('/').pop() + '.csv';
        const blob = await r.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(a.href);
        showToast('Downloaded: ' + filename, 'success');
    } catch(e) {
        showToast('Download failed — ' + e.message, 'error');
    } finally {
        if (btnEl) {
            btnEl.classList.remove('loading');
            const icon = btnEl.querySelector('.dl-icon i');
            if (icon && icon._origClass) icon.className = icon._origClass;
        }
    }
}

// ── Toast ─────────────────────────────────────────────────────
function showToast(message, type = 'success', duration = 3500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        document.body.appendChild(container);
    }
    const icons = { success:'<i class="fas fa-check-circle"></i>', error:'<i class="fas fa-times-circle"></i>', warning:'<i class="fas fa-exclamation-triangle"></i>', info:'<i class="fas fa-info-circle"></i>' };
    const el = document.createElement('div');
    el.className = `toast-msg ${type}`;
    el.innerHTML = `${icons[type]||icons.info} <span>${message}</span>`;
    container.appendChild(el);
    const remove = () => {
        el.classList.add('hiding');
        setTimeout(() => el.remove(), 250);
    };
    const t = setTimeout(remove, duration);
    el.addEventListener('click', () => { clearTimeout(t); remove(); });
}

// ── Utilities ────────────────────────────────────────────────
function formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${pad(h)}:${pad(m)}:${pad(s)}`;
    return `${pad(m)}:${pad(s)}`;
}

function pad(n) { return String(n).padStart(2, '0'); }
