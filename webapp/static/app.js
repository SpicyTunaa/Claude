/* Domain Hunter Mini App */
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── State ────────────────────────────────────────────────
const state = {
  view: 'list',
  huntId: null,
  detail: null,
  domains: [],
  domainsTotal: 0,
  domainsOffset: 0,
  domainsLoading: false,
  domainsFilter: { search: '', live: '', sort: 'confidence_score', excludeSource: '' },
  progressFeed: [],
  progressSse: null,
};

// ── Router ───────────────────────────────────────────────
function navigate(view, params = {}) {
  Object.assign(state, params);
  state.view = view;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(`view-${view}`).classList.add('active');

  if (view === 'list') {
    tg?.BackButton?.hide();
    tg?.MainButton?.hide();
    renderList();
  } else if (view === 'detail') {
    tg?.BackButton?.show();
    tg?.BackButton?.onClick(() => navigate('list'));
    tg?.MainButton?.hide();
    state.domains = [];
    state.domainsOffset = 0;
    state.progressFeed = [];
    state.progressSse?.close();
    state.progressSse = null;
    renderDetail();
  } else if (view === 'new') {
    tg?.BackButton?.show();
    tg?.BackButton?.onClick(() => navigate('list'));
    renderNew();
  }
}

// ── API ──────────────────────────────────────────────────
async function api(path, opts = {}) {
  const r = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(msg);
  }
  return r.json();
}

// ── Utils ─────────────────────────────────────────────────
const fmt = {
  date(s) {
    if (!s) return '—';
    return new Date(s).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  },
  elapsed(start, end) {
    if (!start || !end) return '';
    const toUtc = s => /[Z+]/.test(s.slice(-6)) ? new Date(s) : new Date(s + 'Z');
    const s = Math.round((toUtc(end) - toUtc(start)) / 1000);
    if (s < 0 || s > 86400) return '';
    return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`;
  },
  score(n) { return n ? n.toFixed(2) : '—'; },
  esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
    else el.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null) continue;
    el.append(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return el;
}

function mount(id, ...nodes) {
  const el = document.getElementById(id);
  el.innerHTML = '';
  el.append(...nodes.flat().filter(Boolean));
}

// ── View: List ───────────────────────────────────────────
async function renderList() {
  mount('view-list',
    h('div', { class: 'header' },
      h('h1', {}, '🔍 Domain Hunter'),
      h('button', { class: 'btn btn-icon', onClick: () => navigate('new') }, '+'),
    ),
    h('div', { class: 'scroll-area', id: 'list-scroll' },
      h('div', { class: 'center' }, h('div', { class: 'loader' })),
    ),
  );

  try {
    const [statsData, huntsData] = await Promise.all([
      api('/api/stats'),
      api('/api/hunts?limit=30'),
    ]);
    renderListContent(statsData, huntsData.items);
  } catch (e) {
    mount('list-scroll', h('div', { class: 'center' }, `Error: ${e.message}`));
  }
}

function renderListContent(stats, hunts) {
  const items = hunts.map(hunt => {
    const card = h('div', { class: 'hunt-card', onClick: () => navigate('detail', { huntId: hunt.id }) },
      h('div', { class: 'hunt-card-top' },
        h('strong', {}, hunt.seed_domain),
        h('span', { class: `badge badge-${hunt.status}` }, hunt.status),
      ),
      h('div', { class: 'hunt-card-meta' },
        h('span', {}, hunt.vertical),
        h('span', {}, `${hunt.total} domains`),
        hunt.live ? h('span', {}, `${hunt.live} live`) : null,
        h('span', {}, fmt.date(hunt.started_at)),
      ),
    );
    return card;
  });

  mount('list-scroll',
    h('div', { class: 'stats-bar' },
      h('div', { class: 'stat-card' }, h('div', { class: 'num' }, stats.hunts || 0), h('div', { class: 'lbl' }, 'Hunts')),
      h('div', { class: 'stat-card' }, h('div', { class: 'num' }, stats.domains || 0), h('div', { class: 'lbl' }, 'Domains')),
      h('div', { class: 'stat-card' }, h('div', { class: 'num' }, stats.live || 0), h('div', { class: 'lbl' }, 'Live')),
    ),
    hunts.length
      ? h('div', { class: 'hunt-list' }, ...items)
      : h('div', { class: 'center' }, '🔎', h('p', {}, 'No hunts yet.'), h('p', {}, 'Tap + to start one.')),
  );
}

// ── View: Detail ─────────────────────────────────────────
async function renderDetail() {
  if (!state.huntId) return navigate('list');

  mount('view-detail',
    h('div', { class: 'center', id: 'detail-loading' }, h('div', { class: 'loader' })),
  );

  try {
    const hunt = await api(`/api/hunts/${state.huntId}`);
    state.detail = hunt;
    renderDetailFull(hunt);
  } catch (e) {
    mount('view-detail', h('div', { class: 'center' }, `Error: ${e.message}`));
  }
}

function renderDetailFull(hunt) {
  const isRunning = hunt.status === 'running';
  const sources = hunt.sources ? hunt.sources.split('|') : [];

  mount('view-detail',
    // Sticky header
    h('div', { class: 'detail-header', id: 'detail-hdr' },
      h('h2', {}, hunt.seed_domain),
      h('div', { class: 'sub' }, hunt.vertical + (hunt.error ? ` • ⚠ ${hunt.error}` : '')),
      h('div', { class: 'detail-stats' },
        h('span', {}, h('strong', { id: 'detail-total' }, hunt.total || '…'), ' domains'),
        h('span', {}, h('strong', { id: 'detail-live' }, hunt.live || 0), ' live'),
        hunt.finished_at
          ? h('span', {}, fmt.elapsed(hunt.started_at, hunt.finished_at))
          : null,
      ),
    ),

    // Filter bar
    h('div', { class: 'filter-bar' },
      h('input', {
        class: 'search-input', type: 'search', placeholder: 'Search domains…',
        value: state.domainsFilter.search,
        onInput: debounce(e => { state.domainsFilter.search = e.target.value; reloadDomains(); }, 350),
      }),
      h('label', { class: 'live-toggle' },
        h('input', {
          type: 'checkbox',
          checked: state.domainsFilter.live === 'true',
          onChange: e => { state.domainsFilter.live = e.target.checked ? 'true' : ''; reloadDomains(); },
        }),
        'Live',
      ),
      h('label', { class: 'live-toggle', title: 'Hide domains found only via shared hosting (dns_expander)' },
        h('input', {
          type: 'checkbox',
          checked: state.domainsFilter.excludeSource === 'dns_expander',
          onChange: e => { state.domainsFilter.excludeSource = e.target.checked ? 'dns_expander' : ''; reloadDomains(); },
        }),
        'Hide hosting',
      ),
      h('select', {
        class: 'filter-select',
        onChange: e => { state.domainsFilter.sort = e.target.value; reloadDomains(); },
      },
        h('option', { value: 'confidence_score', selected: state.domainsFilter.sort === 'confidence_score' }, 'Score'),
        h('option', { value: 'domain', selected: state.domainsFilter.sort === 'domain' }, 'Domain'),
        h('option', { value: 'status_code', selected: state.domainsFilter.sort === 'status_code' }, 'Status'),
      ),
    ),

    // Progress feed (only when running)
    isRunning ? h('div', { class: 'scroll-area' },
      h('div', { class: 'progress-feed', id: 'progress-feed' },
        h('div', { class: 'feed-title' }, h('div', { class: 'spinner' }), 'Hunt in progress…'),
      ),
      domainTableContainer(),
    ) : h('div', { class: 'scroll-area' }, domainTableContainer()),
  );

  loadMoreDomains();
  if (isRunning) startSSE(hunt.id);
}

function domainTableContainer() {
  return h('div', { id: 'domain-wrap' },
    h('table', { class: 'domain-table' },
      h('thead', {},
        h('tr', {},
          h('th', { class: 'col-domain' }, 'Domain'),
          h('th', { class: 'col-live' }, '●'),
          h('th', { class: 'col-score' }, 'Score'),
          h('th', { class: 'col-code' }, 'HTTP'),
          h('th', { class: 'col-sources' }, 'Sources'),
        ),
      ),
      h('tbody', { id: 'domain-tbody' }),
    ),
    h('div', { class: 'sentinel', id: 'sentinel' }),
    h('div', { id: 'domain-status', class: 'center', style: 'padding:20px' }),
  );
}

async function loadMoreDomains() {
  if (state.domainsLoading) return;
  if (state.domainsTotal > 0 && state.domainsOffset >= state.domainsTotal) return;

  state.domainsLoading = true;
  const { search, live, sort } = state.domainsFilter;

  try {
    const { excludeSource } = state.domainsFilter;
    const params = new URLSearchParams({
      limit: 50, offset: state.domainsOffset,
      sort, order: 'desc',
      ...(search && { search }),
      ...(live && { live }),
      ...(excludeSource && { exclude_source: excludeSource }),
    });
    const data = await api(`/api/hunts/${state.huntId}/domains?${params}`);
    state.domainsTotal = data.total;
    state.domainsOffset += data.items.length;
    appendDomainRows(data.items);
    updateDomainStatus();
  } catch (e) {
    const el = document.getElementById('domain-status');
    if (el) el.textContent = `Error: ${e.message}`;
  } finally {
    state.domainsLoading = false;
  }
}

function appendDomainRows(rows) {
  const tbody = document.getElementById('domain-tbody');
  if (!tbody) return;
  for (const r of rows) {
    const tr = h('tr', {},
      h('td', { class: 'col-domain' },
        h('a', { href: `https://${r.domain}`, target: '_blank', rel: 'noopener' }, r.domain),
      ),
      h('td', { class: 'col-live' },
        r.is_live === 1 ? h('span', { class: 'dot-live' }, '●')
        : r.is_live === 0 ? h('span', { class: 'dot-dead' }, '○')
        : h('span', { class: 'dot-dead' }, '?'),
      ),
      h('td', { class: 'col-score' }, fmt.score(r.confidence_score)),
      h('td', { class: 'col-code' }, r.status_code || '—'),
      h('td', { class: 'col-sources' }, r.sources ? r.sources.replace(/\|/g, ' ') : ''),
    );
    tbody.append(tr);
  }
}

function reloadDomains() {
  state.domains = [];
  state.domainsOffset = 0;
  state.domainsTotal = 0;
  const tbody = document.getElementById('domain-tbody');
  if (tbody) tbody.innerHTML = '';
  loadMoreDomains();
}

function updateDomainStatus() {
  const el = document.getElementById('domain-status');
  if (!el) return;
  if (state.domainsOffset >= state.domainsTotal && state.domainsTotal > 0) {
    el.textContent = `${state.domainsTotal} domains total`;
  } else if (state.domainsTotal === 0 && !state.domainsLoading) {
    el.textContent = 'No domains found.';
  } else {
    el.innerHTML = '';
  }
}

// Infinite scroll
function setupIntersectionObserver() {
  const sentinel = document.getElementById('sentinel');
  if (!sentinel) return;
  const obs = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) loadMoreDomains();
  }, { rootMargin: '200px' });
  obs.observe(sentinel);
}
setTimeout(setupIntersectionObserver, 300);

// ── SSE progress ─────────────────────────────────────────
function startSSE(huntId) {
  if (state.progressSse) state.progressSse.close();

  const sse = new EventSource(`/api/sse/${huntId}`);
  state.progressSse = sse;

  sse.addEventListener('progress', e => {
    const ev = JSON.parse(e.data);
    addFeedItem(ev);
    if (ev.total_so_far) {
      const el = document.getElementById('detail-total');
      if (el) el.textContent = ev.total_so_far;
    }
  });

  sse.addEventListener('done', () => {
    sse.close();
    state.progressSse = null;
    // Refresh hunt detail to get final counts
    api(`/api/hunts/${huntId}`).then(hunt => {
      const tot = document.getElementById('detail-total');
      const liv = document.getElementById('detail-live');
      if (tot) tot.textContent = hunt.total || 0;
      if (liv) liv.textContent = hunt.live || 0;
    }).catch(() => {});
  });
}

function addFeedItem(ev) {
  const feed = document.getElementById('progress-feed');
  if (!feed) return;
  let text = '';
  let cls = 'feed-item';

  if (ev.event === 'hunter_done') {
    if (ev.message) { text = `${ev.hunter_name}: ${ev.message}`; cls += ' err'; }
    else { text = `${ev.hunter_name}: ${ev.domains_found} domains`; cls += ' ok'; }
  } else if (ev.event === 'filter_done') { text = `Filter: ${ev.total_so_far} valid`; }
  else if (ev.event === 'dedup_done') { text = `Dedup: ${ev.total_so_far} unique`; }
  else if (ev.event === 'validation_start') { text = `Validating ${ev.total_so_far} domains…`; }
  else if (ev.event === 'validation_done') { text = `Done — ${ev.message}`; cls += ' ok'; }
  else if (ev.event === 'complete') { text = `✓ ${ev.message}`; cls += ' ok'; }
  else if (ev.event === 'error') { text = `✗ ${ev.message}`; cls += ' err'; }

  if (text) feed.append(h('div', { class: cls }, text));
  feed.scrollTop = feed.scrollHeight;
}

// ── View: New Hunt ────────────────────────────────────────
function renderNew() {
  let err = '';

  function getValues() {
    return {
      seed_domain: document.getElementById('f-domain')?.value?.trim() || '',
      vertical: document.getElementById('f-vertical')?.value?.trim() || '',
      validate_domains: document.getElementById('f-validate')?.checked ?? true,
    };
  }

  async function submit() {
    const vals = getValues();
    const errEl = document.getElementById('form-err');
    if (errEl) errEl.textContent = '';

    if (!vals.seed_domain) { if (errEl) errEl.textContent = 'Domain is required.'; return; }
    if (!vals.vertical) { if (errEl) errEl.textContent = 'Vertical is required.'; return; }

    tg?.MainButton?.showProgress(false);
    tg?.MainButton?.disable();

    try {
      const data = await api('/api/hunts', {
        method: 'POST',
        body: JSON.stringify(vals),
      });
      navigate('detail', { huntId: data.hunt_id });
    } catch (e) {
      const errEl2 = document.getElementById('form-err');
      if (errEl2) errEl2.textContent = `Error: ${e.message}`;
      tg?.MainButton?.hideProgress();
      tg?.MainButton?.enable();
    }
  }

  // Telegram Main Button
  if (tg?.MainButton) {
    tg.MainButton.setText('Start Hunt');
    tg.MainButton.show();
    tg.MainButton.onClick(submit);
  }

  mount('view-new',
    h('div', { class: 'header' }, h('h1', {}, 'New Hunt')),
    h('div', { class: 'form-wrap' },
      h('div', { class: 'form-group' },
        h('label', { for: 'f-domain' }, 'Seed Domain'),
        h('input', { class: 'form-input', id: 'f-domain', type: 'text', placeholder: 'example.com', autocapitalize: 'none', autocorrect: 'off' }),
      ),
      h('div', { class: 'form-group' },
        h('label', { for: 'f-vertical' }, 'Vertical'),
        h('input', { class: 'form-input', id: 'f-vertical', type: 'text', placeholder: 'adtech, gaming, …' }),
      ),
      h('label', { class: 'form-check' },
        h('input', { type: 'checkbox', id: 'f-validate', checked: true }),
        'Validate HTTP (slower, recommended)',
      ),
      h('p', { class: 'form-hint' }, 'Hunt runs in the background. Results appear when complete.'),
      h('p', { class: 'form-error', id: 'form-err' }),
      // Fallback button for non-Telegram browsers
      tg ? null : h('button', { class: 'btn btn-primary', style: 'width:100%', onClick: submit }, 'Start Hunt'),
    ),
  );
}

// ── Helpers ──────────────────────────────────────────────
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── Boot ─────────────────────────────────────────────────
window.addEventListener('error', e => {
  document.body.innerHTML = `<div style="color:red;padding:20px;word-break:break-all">JS Error: ${e.message} @ ${e.filename}:${e.lineno}</div>`;
});
window.addEventListener('unhandledrejection', e => {
  document.body.innerHTML = `<div style="color:red;padding:20px;word-break:break-all">Unhandled rejection: ${e.reason}</div>`;
});

try {
  const initHuntId = new URLSearchParams(window.location.search).get('hunt');
  if (initHuntId) {
    navigate('detail', { huntId: initHuntId });
  } else {
    navigate('list');
  }
} catch (e) {
  document.body.innerHTML = `<div style="color:red;padding:20px">Boot error: ${e.message}</div>`;
}
