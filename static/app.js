/* ============================================
   Wiki Frontend – app.js
   ============================================ */

// ─── State ────────────────────────────────────

const state = {
  token:         localStorage.getItem('wiki_token') || null,
  user:          null,
  pages:         [],
  currentPageId: null,
  editingPageId: null,
  sidebarOpen:   true,
};

// ─── API helpers ──────────────────────────────

async function apiRequest(method, path, body = null, isForm = false) {
  const opts = { method };

  if (isForm) {
    opts.headers = {};
    if (state.token) opts.headers['Authorization'] = `Bearer ${state.token}`;
    opts.body = body;
  } else {
    opts.headers = { 'Content-Type': 'application/json' };
    if (state.token) opts.headers['Authorization'] = `Bearer ${state.token}`;
    if (body !== null) opts.body = JSON.stringify(body);
  }

  const res = await fetch(path, opts);
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    if (data?.detail) {
      msg = Array.isArray(data.detail)
        ? data.detail.map(e => e.msg || String(e)).join(', ')
        : String(data.detail);
    }
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

// ─── Utilities ────────────────────────────────

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDate(iso) {
  if (!iso) return '–';
  return new Date(iso).toLocaleString('ko-KR', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function setLoading(on) {
  document.getElementById('loading').classList.toggle('visible', on);
}

function showToast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ─── Modal management ─────────────────────────

function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

function switchModal(fromId, toId) {
  closeModal(fromId);
  openModal(toId);
}

document.querySelectorAll('.modal').forEach(modal => {
  modal.addEventListener('click', e => {
    if (e.target === modal) modal.classList.remove('open');
  });
});

document.addEventListener('click', e => {
  const closeTarget = e.target.closest('[data-close]');
  if (closeTarget) closeModal(closeTarget.dataset.close);

  const switchFrom = e.target.closest('[data-switch-from]');
  if (switchFrom) {
    e.preventDefault();
    switchModal(switchFrom.dataset.switchFrom, switchFrom.dataset.switchTo);
  }

  const wikiLink = e.target.closest('.wiki-link[data-page-id]');
  if (wikiLink) {
    e.preventDefault();
    viewPage(Number(wikiLink.dataset.pageId));
  }
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => m.classList.remove('open'));
  }
});

// ─── Markdown renderer ────────────────────────

marked.use({
  gfm: true,
  breaks: true,
  renderer: {
    code({ text, lang }) {
      const validLang = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
      const highlighted = hljs.highlight(text, { language: validLang, ignoreIllegals: true }).value;
      return `<pre><code class="hljs language-${validLang}">${highlighted}</code></pre>`;
    },
  },
});

// GitHub Alerts: > [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING], > [!CAUTION]
const ALERT_MAP = {
  NOTE:      ['ℹ️', '정보',  'note'],
  TIP:       ['💡', '팁',    'tip'],
  IMPORTANT: ['❗', '중요',  'important'],
  WARNING:   ['⚠️', '경고',  'warning'],
  CAUTION:   ['🔴', '주의',  'caution'],
};

function processAlerts(html) {
  return html.replace(/<blockquote>([\s\S]*?)<\/blockquote>/gi, (match, inner) => {
    const m = inner.match(/\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i);
    if (!m) return match;
    const t = m[1].toUpperCase();
    const [icon, label, cls] = ALERT_MAP[t];
    const body = inner
      .replace(/\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\](<br\s*\/?>)?\n?/i, '')
      .trim();
    return `<div class="gh-alert gh-alert-${cls}"><div class="gh-alert-header">${icon} ${label}</div><div class="gh-alert-body">${body}</div></div>`;
  });
}

// [[페이지 제목]] 또는 [[페이지 제목|표시 텍스트]] → 위키 링크 HTML
function processWikiLinks(markdown) {
  return markdown.replace(/\[\[([^\]\n|]+?)(?:\|([^\]\n]+?))?\]\]/g, (match, title, display) => {
    const t = title.trim();
    const d = (display || title).trim();
    const page = state.pages.find(p => p.title.toLowerCase() === t.toLowerCase());
    if (page) {
      return `<a class="wiki-link" data-page-id="${page.id}" href="#">${d}</a>`;
    }
    return `<span class="wiki-link-missing" title="존재하지 않는 페이지: ${escapeHtml(t)}">${d}</span>`;
  });
}

function renderMarkdown(content) {
  const preprocessed = (content || '').replace(/^(#{1,6})([^\s#\n])/gm, '$1 $2');
  const withLinks = processWikiLinks(preprocessed);
  const raw = marked.parse(withLinks);
  return DOMPurify.sanitize(processAlerts(raw), {
    ADD_TAGS: ['input'],
    ADD_ATTR: ['checked', 'disabled', 'type', 'data-page-id'],
  });
}

function applyHighlight(container) {
  container.querySelectorAll('pre code:not(.hljs)').forEach(b => hljs.highlightElement(b));
}

// ─── TOC (Table of Contents) ─────────────────

function buildTOC(contentEl) {
  const headings = [...contentEl.querySelectorAll('h1,h2,h3,h4')];
  if (headings.length < 2) return null;

  const minLevel = Math.min(...headings.map(h => parseInt(h.tagName[1])));
  const counters  = [0, 0, 0, 0];
  const items     = [];

  headings.forEach(h => {
    const text = h.textContent.trim();
    const lvl  = parseInt(h.tagName[1]) - minLevel;
    counters[lvl]++;
    for (let i = lvl + 1; i <= 3; i++) counters[i] = 0;

    const numStr   = counters.slice(0, lvl + 1).join('.');
    const anchorId = `hs-${numStr}`;
    h.id = anchorId;

    const numEl = document.createElement('span');
    numEl.className = 'heading-num';
    numEl.setAttribute('aria-hidden', 'true');
    numEl.textContent = numStr;
    h.prepend(numEl);

    items.push({ lvl, numStr, text, id: anchorId });
  });

  return items;
}

function renderTOCHtml(items) {
  return `
    <nav class="toc-box">
      <div class="toc-header">
        <div class="toc-header-left">
          <span class="toc-icon">§</span>
          <span class="toc-title">목차</span>
          <span class="toc-count">${items.length}개 항목</span>
        </div>
        <button class="toc-toggle" id="toc-toggle-btn" title="목차 접기/펼치기" aria-expanded="true">
          <span class="toc-toggle-icon">▾</span>
        </button>
      </div>
      <div class="toc-body" id="toc-body">
        <ol class="toc-list">
          ${items.map(item => `
            <li class="toc-item toc-lvl-${item.lvl}" data-toc-id="${item.id}">
              <a href="#${item.id}" class="toc-link">
                <span class="toc-num">${item.numStr}</span>
                <span class="toc-text">${escapeHtml(item.text)}</span>
              </a>
            </li>
          `).join('')}
        </ol>
      </div>
    </nav>
  `;
}

function initTOC(contentEl) {
  const toggleBtn = document.getElementById('toc-toggle-btn');
  const tocBody   = document.getElementById('toc-body');
  if (!toggleBtn || !tocBody) return;

  const scrollEl = document.getElementById('content');

  toggleBtn.addEventListener('click', () => {
    const isCollapsed = tocBody.classList.toggle('collapsed');
    toggleBtn.querySelector('.toc-toggle-icon').textContent = isCollapsed ? '▸' : '▾';
    toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
  });

  document.querySelectorAll('.toc-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const targetId = link.getAttribute('href').slice(1);
      const target   = document.getElementById(targetId);
      if (!target || !scrollEl) return;

      // Expand collapsed ancestor sections so the target is visible
      let anc = target.parentElement?.closest('.section-body');
      while (anc) {
        if (anc.classList.contains('collapsed')) {
          anc.classList.remove('collapsed');
          const ph = anc.previousElementSibling;
          ph?.querySelector('.section-toggle')?.setAttribute('aria-expanded', 'true');
          const icon = ph?.querySelector('.section-toggle-icon');
          if (icon) icon.textContent = '▾';
        }
        anc = anc.parentElement?.closest('.section-body');
      }
      // Expand the heading's own section if collapsed
      const own = target.nextElementSibling;
      if (own?.classList.contains('section-body') && own.classList.contains('collapsed')) {
        own.classList.remove('collapsed');
        target.querySelector('.section-toggle')?.setAttribute('aria-expanded', 'true');
        const icon = target.querySelector('.section-toggle-icon');
        if (icon) icon.textContent = '▾';
      }

      const targetRect = target.getBoundingClientRect();
      const scrollRect = scrollEl.getBoundingClientRect();
      const newTop     = scrollEl.scrollTop + targetRect.top - scrollRect.top - 24;
      scrollEl.scrollTo({ top: Math.max(0, newTop), behavior: 'smooth' });
    });
  });

  const tocItems   = [...document.querySelectorAll('.toc-item')];
  const headingEls = [...contentEl.querySelectorAll('[id^="hs-"]')];
  if (!headingEls.length || !scrollEl) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        tocItems.forEach(li => li.classList.remove('active'));
        const active = document.querySelector(`.toc-item[data-toc-id="${entry.target.id}"]`);
        active?.classList.add('active');
      }
    });
  }, { root: scrollEl, rootMargin: '-5% 0px -80% 0px', threshold: 0 });

  headingEls.forEach(h => observer.observe(h));
}

// ─── Section collapse ─────────────────────────

function wrapSections(contentEl) {
  // Process in reverse so inner sections are wrapped before outer ones,
  // enabling correct nesting when outer sections collect their children.
  const headings = [...contentEl.querySelectorAll('[id^="hs-"]')].reverse();

  headings.forEach(h => {
    const hLevel = parseInt(h.tagName[1]);
    const toMove = [];
    let node = h.nextSibling;

    while (node) {
      if (
        node.nodeType === Node.ELEMENT_NODE &&
        /^H[1-6]$/.test(node.tagName) &&
        parseInt(node.tagName[1]) <= hLevel
      ) break;
      toMove.push(node);
      node = node.nextSibling;
    }

    const btn = document.createElement('button');
    btn.className = 'section-toggle';
    btn.setAttribute('aria-expanded', 'true');
    btn.setAttribute('title', '섹션 접기/펼치기');
    btn.innerHTML = '<span class="section-toggle-icon">▾</span>';
    h.appendChild(btn);

    if (!toMove.length) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'section-body';
    h.after(wrapper);
    toMove.forEach(n => wrapper.appendChild(n));

    btn.addEventListener('click', e => {
      e.stopPropagation();
      const isCollapsed = wrapper.classList.toggle('collapsed');
      btn.querySelector('.section-toggle-icon').textContent = isCollapsed ? '▸' : '▾';
      btn.setAttribute('aria-expanded', String(!isCollapsed));
    });
  });
}

// ─── Auth ─────────────────────────────────────

async function loadCurrentUser() {
  if (!state.token) return;
  try {
    state.user = await apiRequest('GET', '/users/me');
  } catch {
    state.token = null;
    state.user = null;
    localStorage.removeItem('wiki_token');
  }
}

async function doLogin(username, password) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  const data = await apiRequest('POST', '/auth/login', form, true);
  state.token = data.access_token;
  localStorage.setItem('wiki_token', state.token);
  await loadCurrentUser();
  renderAuthArea();
  closeModal('login-modal');
  showToast(`${state.user?.username || username}님, 환영합니다!`);
  await loadPages();
  renderWelcomeView();
}

async function doRegister(username, email, password) {
  await apiRequest('POST', '/auth/register', { username, email, password });
  showToast('회원가입 완료! 로그인하세요.');
  closeModal('register-modal');
  openModal('login-modal');
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = '';
}

function doLogout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('wiki_token');
  renderAuthArea();
  showToast('로그아웃되었습니다.', 'info');
}

// ─── Render: Auth area ────────────────────────

function renderAuthArea() {
  const area = document.getElementById('auth-area');
  const newBtn = document.getElementById('new-page-btn');

  if (state.user) {
    area.innerHTML = `
      <span style="font-size:14px;color:var(--text-secondary);max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
        ${escapeHtml(state.user.username)}${state.user.is_admin ? ' 👑' : ''}
      </span>
      <button class="btn btn-secondary btn-sm" id="logout-btn">로그아웃</button>
    `;
    document.getElementById('logout-btn').addEventListener('click', doLogout);
    if (newBtn) newBtn.style.display = 'flex';
  } else {
    area.innerHTML = `
      <button class="btn btn-ghost btn-sm" id="header-login-btn">로그인</button>
      <button class="btn btn-primary btn-sm" id="header-register-btn">회원가입</button>
    `;
    document.getElementById('header-login-btn').addEventListener('click', () => openModal('login-modal'));
    document.getElementById('header-register-btn').addEventListener('click', () => openModal('register-modal'));
    if (newBtn) newBtn.style.display = 'none';
  }
}

// ─── Pages: load & list ───────────────────────

async function loadPages() {
  try {
    state.pages = await apiRequest('GET', '/pages/?limit=200') || [];
  } catch {
    state.pages = [];
  }
  renderPageList(state.pages);
}

function renderPageList(pages) {
  const ul = document.getElementById('page-list');
  const sorted = [...pages].sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

  if (!sorted.length) {
    ul.innerHTML = '<li class="page-list-empty">페이지가 없습니다</li>';
    return;
  }

  ul.innerHTML = sorted.map(p => `
    <li class="page-list-item${p.id === state.currentPageId ? ' active' : ''}"
        data-page-id="${p.id}"
        title="${escapeHtml(p.title)}">
      📄 ${escapeHtml(p.title)}
    </li>
  `).join('');

  ul.querySelectorAll('.page-list-item').forEach(li => {
    li.addEventListener('click', () => viewPage(Number(li.dataset.pageId)));
  });
}

// ─── Page view ────────────────────────────────

async function viewPage(id) {
  setLoading(true);
  try {
    const page = await apiRequest('GET', `/pages/${id}`);
    state.currentPageId = id;
    renderPageList(state.pages);
    renderPageView(page);
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    setLoading(false);
  }
}

function renderPageView(page) {
  const canEdit   = !!state.user;
  const canDelete = state.user && (state.user.id === page.author_id || state.user.is_admin);

  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-view">
      <div class="page-header">
        <h1>${escapeHtml(page.title)}</h1>
        <div class="page-meta">
          <span class="version-badge">v${page.version}</span>
          <span>수정: ${formatDate(page.updated_at)}</span>
          <span>생성: ${formatDate(page.created_at)}</span>
        </div>
        <div class="page-actions">
          ${canEdit   ? `<button class="btn btn-secondary btn-sm" id="btn-edit">✏️ 편집</button>` : ''}
          ${canDelete ? `<button class="btn btn-danger btn-sm"   id="btn-del">🗑️ 삭제</button>` : ''}
          <button class="btn btn-ghost btn-sm" id="btn-hist">📋 히스토리</button>
        </div>
      </div>
      <div id="toc-container"></div>
      <div class="wiki-content" id="page-body">
        ${page.content ? renderMarkdown(page.content) : '<p style="color:var(--text-muted)">내용이 없습니다.</p>'}
      </div>
    </div>
  `;

  const pageBody = document.getElementById('page-body');
  applyHighlight(pageBody);

  const tocItems = buildTOC(pageBody);
  if (tocItems) {
    document.getElementById('toc-container').innerHTML = renderTOCHtml(tocItems);
    initTOC(pageBody);
  }
  wrapSections(pageBody);

  if (canEdit)   document.getElementById('btn-edit').addEventListener('click', () => openEditModal(page.id));
  if (canDelete) document.getElementById('btn-del').addEventListener('click',  () => confirmDeletePage(page.id, page.title));
  document.getElementById('btn-hist').addEventListener('click', () => viewHistory(page.id));
}

// ─── Welcome view ──────────────────────────────

function renderWelcomeView() {
  state.currentPageId = null;
  renderPageList(state.pages);

  const recent = [...state.pages]
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    .slice(0, 6);

  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="welcome-view">
      <span class="welcome-icon">📚</span>
      <h1>Wiki</h1>
      <p class="subtitle">지식을 기록하고, 함께 편집하고, 쉽게 찾아보세요</p>
      ${state.user
        ? `<button class="btn btn-primary" id="welcome-new-btn">+ 새 페이지 만들기</button>`
        : `<button class="btn btn-primary" id="welcome-login-btn">로그인하여 시작하기</button>`
      }
      ${recent.length ? `
        <div class="recent-pages">
          <h3>최근 페이지</h3>
          ${recent.map(p => `
            <div class="recent-page-card" data-page-id="${p.id}">
              <div class="title">📄 ${escapeHtml(p.title)}</div>
              <div class="meta">최종 수정 ${formatDate(p.updated_at)} · v${p.version}</div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;

  if (state.user) {
    document.getElementById('welcome-new-btn')?.addEventListener('click', openCreateModal);
  } else {
    document.getElementById('welcome-login-btn')?.addEventListener('click', () => openModal('login-modal'));
  }

  content.querySelectorAll('.recent-page-card').forEach(card => {
    card.addEventListener('click', () => viewPage(Number(card.dataset.pageId)));
  });
}

// ─── History view ──────────────────────────────

async function viewHistory(pageId) {
  if (!state.user) { openModal('login-modal'); return; }
  setLoading(true);
  try {
    const [archives, page] = await Promise.all([
      apiRequest('GET', `/pages/${pageId}/archives/?limit=100`),
      apiRequest('GET', `/pages/${pageId}`),
    ]);
    renderHistoryView(pageId, archives || [], page.title);
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    setLoading(false);
  }
}

function renderHistoryView(pageId, archives, pageTitle) {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="history-view">
      <button class="btn btn-ghost back-btn" id="hist-back">← 페이지로 돌아가기</button>
      <h2>📋 "${escapeHtml(pageTitle)}" 히스토리</h2>
      ${archives.length === 0
        ? '<p style="color:var(--text-muted);margin-top:16px">이전 버전이 없습니다.</p>'
        : `<ul class="archive-list">
            ${archives.map(a => `
              <li class="archive-item" data-page-id="${pageId}" data-archive-id="${a.id}">
                <div>
                  <div class="archive-version">v${a.version}</div>
                  <div class="archive-meta">${escapeHtml(a.title)}</div>
                </div>
                <div style="text-align:right">
                  <div class="archive-meta">${formatDate(a.archived_at)}</div>
                  <div class="archive-meta" style="margin-top:2px">편집자 #${a.editor_id}</div>
                </div>
              </li>
            `).join('')}
          </ul>`
      }
    </div>
  `;

  document.getElementById('hist-back').addEventListener('click', () => viewPage(pageId));

  content.querySelectorAll('.archive-item').forEach(li => {
    li.addEventListener('click', () => viewArchive(Number(li.dataset.pageId), Number(li.dataset.archiveId)));
  });
}

async function viewArchive(pageId, archiveId) {
  setLoading(true);
  try {
    const [archive, page] = await Promise.all([
      apiRequest('GET', `/pages/${pageId}/archives/${archiveId}`),
      apiRequest('GET', `/pages/${pageId}`),
    ]);
    renderArchiveView(page, archive, pageId);
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    setLoading(false);
  }
}

function renderArchiveView(page, archive, pageId) {
  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="archive-view">
      <button class="btn btn-ghost back-btn" id="arch-back">← 히스토리로 돌아가기</button>
      <div class="archive-banner">
        <span>⚠️ <strong>v${archive.version}</strong> 이전 버전을 보고 있습니다 (${formatDate(archive.archived_at)})</span>
        <button class="btn btn-secondary btn-sm" id="arch-current">현재 버전 보기</button>
      </div>
      <div class="page-header">
        <h1>${escapeHtml(archive.title)}</h1>
        <div class="page-meta">
          <span class="version-badge">v${archive.version}</span>
          <span>보관 일시: ${formatDate(archive.archived_at)}</span>
        </div>
      </div>
      <div class="wiki-content" id="archive-body">
        ${archive.content ? renderMarkdown(archive.content) : '<p style="color:var(--text-muted)">내용이 없습니다.</p>'}
      </div>
    </div>
  `;

  applyHighlight(document.getElementById('archive-body'));
  document.getElementById('arch-back').addEventListener('click', () => viewHistory(pageId));
  document.getElementById('arch-current').addEventListener('click', () => viewPage(pageId));
}

// ─── Create / Edit page ────────────────────────

function openCreateModal() {
  if (!state.user) { openModal('login-modal'); return; }
  state.editingPageId = null;
  document.getElementById('editor-title-label').textContent = '새 페이지';
  document.getElementById('editor-submit-btn').textContent = '게시';
  document.getElementById('page-title-input').value = '';
  document.getElementById('page-content-input').value = '';
  document.getElementById('editor-error').textContent = '';
  resetPreview();
  openModal('editor-modal');
  setTimeout(() => document.getElementById('page-title-input').focus(), 50);
}

async function openEditModal(id) {
  if (!state.user) { openModal('login-modal'); return; }
  setLoading(true);
  try {
    const page = await apiRequest('GET', `/pages/${id}`);
    state.editingPageId = id;
    document.getElementById('editor-title-label').textContent = '페이지 편집';
    document.getElementById('editor-submit-btn').textContent = '저장';
    document.getElementById('page-title-input').value = page.title;
    document.getElementById('page-content-input').value = page.content || '';
    document.getElementById('editor-error').textContent = '';
    resetPreview();
    openModal('editor-modal');
    setTimeout(() => document.getElementById('page-content-input').focus(), 50);
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    setLoading(false);
  }
}

document.getElementById('editor-form').addEventListener('submit', async e => {
  e.preventDefault();
  const title   = document.getElementById('page-title-input').value.trim();
  const content = document.getElementById('page-content-input').value;
  const errEl   = document.getElementById('editor-error');
  errEl.textContent = '';

  if (!title) { errEl.textContent = '제목을 입력하세요.'; return; }

  const btn = document.getElementById('editor-submit-btn');
  btn.disabled = true;
  setLoading(true);
  try {
    let page;
    if (state.editingPageId) {
      page = await apiRequest('PUT', `/pages/${state.editingPageId}`, { title, content });
      showToast('페이지가 업데이트되었습니다.');
    } else {
      page = await apiRequest('POST', '/pages/', { title, content });
      showToast('페이지가 생성되었습니다.');
    }
    closeModal('editor-modal');
    await loadPages();
    viewPage(page.id);
  } catch (e) {
    errEl.textContent = e.message;
  } finally {
    btn.disabled = false;
    setLoading(false);
  }
});

// ─── Delete page ───────────────────────────────

function confirmDeletePage(id, title) {
  document.getElementById('delete-message').textContent =
    `"${title}" 페이지를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`;
  const btn = document.getElementById('confirm-delete-btn');
  btn.onclick = () => deletePage(id);
  openModal('delete-modal');
}

async function deletePage(id) {
  setLoading(true);
  closeModal('delete-modal');
  try {
    await apiRequest('DELETE', `/pages/${id}`);
    showToast('페이지가 삭제되었습니다.', 'info');
    state.currentPageId = null;
    await loadPages();
    renderWelcomeView();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    setLoading(false);
  }
}

// ─── Editor: toolbar & preview ─────────────────

document.querySelectorAll('.toolbar-btn[data-md-before]').forEach(btn => {
  btn.addEventListener('click', () => insertMd(btn.dataset.mdBefore, btn.dataset.mdAfter));
});

document.querySelector('.toolbar-btn[data-action="table"]')?.addEventListener('click', () => {
  insertMd('| 헤더 1 | 헤더 2 | 헤더 3 |\n| --- | --- | --- |\n| 내용 | 내용 | 내용 |\n', '');
});

function insertMd(before, after) {
  const ta    = document.getElementById('page-content-input');
  const start = ta.selectionStart;
  const end   = ta.selectionEnd;
  const sel   = ta.value.substring(start, end);
  const ins   = before + sel + after;
  ta.value    = ta.value.substring(0, start) + ins + ta.value.substring(end);
  ta.focus();
  ta.selectionStart = start + before.length;
  ta.selectionEnd   = start + before.length + sel.length;
  syncPreview();
}

let previewVisible = false;

function resetPreview() {
  previewVisible = false;
  document.getElementById('editor-preview').classList.add('hidden');
  document.getElementById('editor-preview').innerHTML = '';
  document.getElementById('preview-toggle-btn').textContent = '👁 미리보기';
  document.getElementById('preview-toggle-btn').classList.remove('active');
}

document.getElementById('preview-toggle-btn').addEventListener('click', () => {
  previewVisible = !previewVisible;
  const preview = document.getElementById('editor-preview');
  const btn     = document.getElementById('preview-toggle-btn');
  preview.classList.toggle('hidden', !previewVisible);
  btn.textContent = previewVisible ? '✏️ 편집기' : '👁 미리보기';
  btn.classList.toggle('active', previewVisible);
  if (previewVisible) syncPreview();
});

function syncPreview() {
  if (!previewVisible) return;
  const preview = document.getElementById('editor-preview');
  preview.innerHTML = renderMarkdown(document.getElementById('page-content-input').value);
  applyHighlight(preview);
}

document.getElementById('page-content-input').addEventListener('input', syncPreview);

// ─── Search ────────────────────────────────────

const searchInput   = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

searchInput.addEventListener('input', () => {
  const q = searchInput.value.trim().toLowerCase();
  if (!q) {
    searchResults.classList.remove('visible');
    renderPageList(state.pages);
    return;
  }
  const filtered = state.pages.filter(p => p.title.toLowerCase().includes(q));
  renderPageList(filtered);

  if (!filtered.length) {
    searchResults.innerHTML = '<div class="search-result-item" style="color:var(--text-muted)">검색 결과 없음</div>';
  } else {
    searchResults.innerHTML = filtered.slice(0, 8).map(p => `
      <div class="search-result-item" data-page-id="${p.id}">${escapeHtml(p.title)}</div>
    `).join('');
    searchResults.querySelectorAll('[data-page-id]').forEach(el => {
      el.addEventListener('click', () => {
        searchInput.value = '';
        searchResults.classList.remove('visible');
        renderPageList(state.pages);
        viewPage(Number(el.dataset.pageId));
      });
    });
  }
  searchResults.classList.add('visible');
});

document.addEventListener('click', e => {
  if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
    searchResults.classList.remove('visible');
  }
});

searchInput.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    searchInput.value = '';
    searchResults.classList.remove('visible');
    renderPageList(state.pages);
  }
});

// ─── Sidebar toggle ────────────────────────────

document.getElementById('sidebar-toggle').addEventListener('click', () => {
  state.sidebarOpen = !state.sidebarOpen;
  document.getElementById('sidebar').classList.toggle('collapsed', !state.sidebarOpen);
});

// ─── New page button ───────────────────────────

document.getElementById('new-page-btn').addEventListener('click', openCreateModal);

// ─── Logo click ────────────────────────────────

document.getElementById('logo').addEventListener('click', e => {
  e.preventDefault();
  renderWelcomeView();
});

// ─── Login form ────────────────────────────────

document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  const btn = e.target.querySelector('[type="submit"]');
  btn.disabled = true;
  try {
    await doLogin(
      document.getElementById('login-username').value,
      document.getElementById('login-password').value,
    );
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

// ─── Register form ─────────────────────────────

document.getElementById('register-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errEl = document.getElementById('register-error');
  errEl.textContent = '';
  const btn = e.target.querySelector('[type="submit"]');
  btn.disabled = true;
  try {
    await doRegister(
      document.getElementById('reg-username').value,
      document.getElementById('reg-email').value,
      document.getElementById('reg-password').value,
    );
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

// ─── Init ──────────────────────────────────────

async function init() {
  setLoading(true);
  try {
    await loadCurrentUser();
    renderAuthArea();
    await loadPages();
    renderWelcomeView();
  } catch (e) {
    console.error('init error:', e);
  } finally {
    setLoading(false);
  }
}

window.addEventListener('load', init);
