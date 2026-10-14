const fmt = new Intl.NumberFormat('es-AR');
const BASE = 'https://pindec.pages.dev';
let history = [];
let builderData = {};   // index.json data keyed by indicator name
let currentMode = 'guide';

function fetchJSON(url) {
  return fetch(url, { headers: { Accept: 'application/json' } }).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.text().then(body => ({ data: JSON.parse(body), bytes: body.length }));
  });
}

const indexFetches = {};
function fetchIndex(ind) {
  if (!indexFetches[ind]) {
    indexFetches[ind] = fetchJSON('/v1/' + ind + '/index.json').then(
      idx => { builderData[ind] = idx; indexFetches[ind] = idx; return idx; },
      err => { indexFetches[ind] = null; throw err; }
    );
  }
  return indexFetches[ind];
}

const resourceFetches = {};
function fetchResource(url) {
  if (!resourceFetches[url]) {
    resourceFetches[url] = fetchJSON(url).then(
      data => { resourceFetches[url] = data; return data; },
      err => { resourceFetches[url] = null; throw err; }
    );
  }
  return resourceFetches[url];
}

/* ---------- URL building ---------- */
function esc(s) { return encodeURIComponent(String(s).replace(/ /g, '_')); }

function buildUrl() {
  const ind = document.getElementById('pg-ind').value;
  const f1 = document.getElementById('pg-f1').value;
  const f2 = document.getElementById('pg-f2').value;
  const f3 = document.getElementById('pg-f3').value;
  const year = document.getElementById('pg-year').value.trim();
  let path = '/v1/' + ind + '/';
  if (f1) path += esc(f1) + '/';
  if (f2) path += esc(f2) + '/';
  if (f3) path += esc(f3) + '/';
  if (year) path += year + '/';
  return path;
}

function updateUrlBar() {
  document.getElementById('pg-url').textContent = buildUrl();
}

/* ---------- Builder options from API ---------- */
function setField(id, options, selected) {
  const el = document.getElementById(id);
  const wrap = document.getElementById(id + '-wrap');
  el.innerHTML = '';
  el.appendChild(new Option('—', ''));
  options.forEach(o => el.appendChild(new Option(o, o, false, o === selected)));
  el.disabled = false;
  wrap.style.display = 'flex';
}

function hideField(id) {
  document.getElementById(id).disabled = true;
  document.getElementById(id).innerHTML = '<option value="">—</option>';
  document.getElementById(id + '-wrap').style.display = 'none';
}

function setLabel(id, text) {
  const label = document.querySelector('label[for="' + id + '"]');
  if (label) label.textContent = text;
}

/* ---------- Indicator metadata (lightweight, per-directory indexes) ---------- */
const builderMeta = {};

const META_SPEC = {
  ipc: {
    nivel1Label: 'Región',
    nivel2Label: 'Clasificación',
    nivel3Label: 'Código',
    load: async () => {
      const idx = await fetchIndex('ipc');
      const years = Object.keys(idx.datos || {}).filter(k => /^\d{4}$/.test(k)).sort();
      const regions = [];
      if (years.length) {
        for (const region of Object.keys(idx.datos[years[years.length - 1]] || {})) {
          regions.push(region);
        }
      }
      return {
        years,
        subcategorias: regions.sort(),
        detail: region => {
          const clasifs = new Set();
          for (const year of years) {
            for (const c of Object.keys((idx.datos[year] || {})[region] || {})) clasifs.add(c);
          }
          const list = Array.from(clasifs).sort();
          return {
            codigos: list,
            nivel3: clasif => {
              const codes = new Set();
              for (const year of years) {
                const clasifData = ((idx.datos[year] || {})[region] || {})[clasif] || [];
                for (const c of clasifData) codes.add(String(c.codigo));
              }
              return Array.from(codes);
            }
          };
        }
      };
    }
  },
  'cba-cbt': {
    subcategoriaLabel: 'Subcategoría',
    load: async () => {
      const idx = await fetchIndex('cba-cbt');
      const years = Object.keys(idx.datos || {}).filter(k => /^\d{4}$/.test(k)).sort();
      const subs = [];
      if (years.length) {
        const last = idx.datos[years[years.length - 1]] || {};
        if (last.adulto_equivalente) subs.push('adulto-equivalente');
        if (last.hogares) subs.push('hogares');
      }
      return { years, subcategorias: subs, detail: () => ({}) };
    }
  },
  emae: {
    subcategoriaLabel: 'Subcategoría',
    nivel2Label: 'Sector',
    load: async () => {
      const idx = await fetchIndex('emae');
      const years = Object.keys(idx.datos || {}).filter(k => /^\d{4}$/.test(k)).sort();
      const subs = [];
      let sectorIdx = null;
      if (years.length) {
        const last = idx.datos[years[years.length - 1]] || {};
        if (last.nivel_general) subs.push('nivel-general');
        if (last.sectores) subs.push('sectores');
        if (last.impuestos_netos_subsidios) subs.push('impuestos');
      }
      if (subs.includes('sectores')) {
        try {
          sectorIdx = await fetchResource('/v1/emae/sectores/index.json');
        } catch (e) { sectorIdx = null; }
      }
      return {
        years,
        subcategorias: subs,
        detail: sub => (sub === 'sectores' && sectorIdx
          ? { codigos: sectorIdx.codigos || [] }
          : {})
      };
    }
  },
  ica: {
    load: async () => {
      const idx = await fetchIndex('ica');
      const years = Object.keys(idx.datos || {}).filter(k => /^\d{4}$/.test(k)).sort();
      return { years, subcategorias: [], detail: () => ({}) };
    }
  }
};

async function loadIndicatorMeta(ind) {
  const spec = META_SPEC[ind];
  if (!spec) return null;
  try {
    builderMeta[ind] = await spec.load();
  } catch (e) {
    builderMeta[ind] = null;
  }
  return builderMeta[ind];
}

async function loadBuilder() {
  const ind = document.getElementById('pg-ind').value;
  const f1 = document.getElementById('pg-f1');
  const f2 = document.getElementById('pg-f2');
  const f3 = document.getElementById('pg-f3');
  const yearInput = document.getElementById('pg-year');
  const yearWrap = document.getElementById('pg-year').parentElement;

  f1.value = ''; f2.value = ''; f3.value = '';
  hideField('pg-f1'); hideField('pg-f2'); hideField('pg-f3');
  builderMeta[ind] = null;

  const meta = await loadIndicatorMeta(ind);
  if (!meta) { updateUrlBar(); return; }

  if (meta.subcategorias) {
    setLabel('pg-f1', meta.subcategoriaLabel || 'Subcategoría');
    if (meta.subcategorias.length) setField('pg-f1', meta.subcategorias, f1.value);
  }

  if (meta.years.length) {
    yearWrap.style.display = 'flex';
    yearInput.disabled = false;
    yearInput.value = '';
    yearInput.placeholder = meta.years[0] + '–' + meta.years[meta.years.length - 1];
  } else {
    yearWrap.style.display = 'none';
  }

  updateUrlBar();
}

async function onF1Change() {
  const ind = document.getElementById('pg-ind').value;
  const f1 = document.getElementById('pg-f1').value;
  const f2 = document.getElementById('pg-f2');
  const f3 = document.getElementById('pg-f3');
  f2.value = ''; f3.value = '';
  hideField('pg-f2'); hideField('pg-f3');

  const meta = builderMeta[ind];
  if (!f1 || !meta) { updateUrlBar(); return; }

  const detail = meta.detail(f1);
  if (!detail) { updateUrlBar(); return; }

  if (detail.codigos) {
    setLabel('pg-f2', meta.nivel2Label || 'Clasificación');
    setField('pg-f2', detail.codigos, f2.value);
  }

  updateUrlBar();
}

async function onF2Change() {
  const ind = document.getElementById('pg-ind').value;
  const f1 = document.getElementById('pg-f1').value;
  const f2 = document.getElementById('pg-f2').value;
  const f3 = document.getElementById('pg-f3');
  f3.value = '';
  hideField('pg-f3');
  if (!f2) { updateUrlBar(); return; }

  const meta = builderMeta[ind];
  if (!meta) { updateUrlBar(); return; }

  const detail = meta.detail(f1);
  if (detail && detail.nivel3) {
    setLabel('pg-f3', meta.nivel3Label || 'Código');
    setField('pg-f3', detail.nivel3(f2), f3.value);
  }

  updateUrlBar();
}

/* ---------- Request execution ---------- */
async function run(url) {
  const out = document.getElementById('pg-output');
  const status = document.getElementById('pg-status');
  const btn = document.getElementById('pg-run');

  btn.disabled = true; btn.textContent = 'Cargando…';
  status.className = 'status-line waiting loading';
  status.textContent = 'Solicitando ' + url + '…';
  const start = performance.now();

  try {
    const res = await fetchJSON(url);
    const ms = Math.round(performance.now() - start);
    out.innerHTML = syntaxHighlight(JSON.stringify(res.data, null, 2));
    status.className = 'status-line';
    status.textContent = '200 OK · ' + ms + ' ms · ' + fmtBytes(res.bytes);
    pushHistory(url);
  } catch (err) {
    out.innerHTML = '<span class="err">Error: ' + escapeHtml(err.message) + '</span>';
    status.className = 'status-line fail';
    status.textContent = 'Solicitud fallida';
  } finally {
    btn.disabled = false; btn.textContent = 'Ejecutar';
  }
}

function fmtBytes(n) {
  if (n < 1024) return n + ' B';
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
  return (n / 1024 / 1024).toFixed(2) + ' MB';
}

function pushHistory(url) {
  history = [url, ...history.filter(u => u !== url)].slice(0, 6);
  renderHistory();
}

function renderHistory() {
  const box = document.getElementById('history');
  if (!history.length) { box.innerHTML = ''; return; }
  box.innerHTML = '<span style="font-size:0.76rem;color:var(--muted);align-self:center">Historial:</span>' +
    history.map(u => '<button class="chip">' + escapeHtml(u) + '</button>').join('');
  box.querySelectorAll('.chip').forEach((chip, i) => {
    chip.addEventListener('click', () => run(history[i]));
  });
}

function syntaxHighlight(json) {
  return json
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g, m => {
      let cls;
      if (/^"/.test(m)) cls = /:$/.test(m) ? 'string' : 'num';
      else if (/true|false/.test(m)) cls = 'bool';
      else if (/null/.test(m)) cls = 'null';
      else cls = 'num';
      return '<span class="' + cls + '">' + m + '</span>';
    });
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ---------- Animated counters ---------- */
function animateValue(el, end, { prefix = '', suffix = '', decimals = 0, duration = 900 } = {}) {
  const start = performance.now();
  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    const val = end * eased;
    el.textContent = prefix + fmt.format(Number(val.toFixed(decimals))) + suffix;
    if (t < 1) requestAnimationFrame(frame);
    else el.textContent = prefix + fmt.format(end) + suffix;
  }
  requestAnimationFrame(frame);
}

/* ---------- Live stats ---------- */
async function loadStats() {
  async function ipcStat() {
    const index = await fetchIndex('ipc');
    const allYears = Object.keys(index.datos || {}).filter(k => /^\d{4}$/.test(k));
    const lastYear = Math.max(...allYears.map(Number));
    const { data: ipc } = await fetchJSON('/v1/ipc/Nacional/' + lastYear + '/');
    const nivel = ipc.datos.COICOP.find(c => c.codigo === '0');
    if (nivel && nivel.historico.length) {
      const last = nivel.historico[nivel.historico.length - 1];
      animateValue(document.getElementById('stat-ipc'), last.indice, { decimals: 2 });
      document.getElementById('stat-ipc-hint').textContent = last.periodo;
      document.getElementById('foot-update').textContent = last.periodo;
    }
  }
  async function cbaStat() {
    const index = await fetchIndex('cba-cbt');
    const allYears = Object.keys(index.datos || {}).filter(k => /^\d{4}$/.test(k));
    const lastYear = Math.max(...allYears.map(Number));
    const { data: cba } = await fetchJSON('/v1/cba-cbt/' + lastYear + '/');
    const last = cba.adulto_equivalente[cba.adulto_equivalente.length - 1];
    if (last) animateValue(document.getElementById('stat-cba'), last.cba.indice, { prefix: '$', decimals: 2 });
  }
  async function emaeStat() {
    const index = await fetchIndex('emae');
    const allYears = Object.keys(index.datos || {}).filter(k => /^\d{4}$/.test(k));
    const lastYear = Math.max(...allYears.map(Number));
    const { data: emae } = await fetchJSON('/v1/emae/' + lastYear + '/');
    const nivel = emae.datos.nivel_general[emae.datos.nivel_general.length - 1];
    if (nivel) {
      animateValue(document.getElementById('stat-emae'), nivel.original.indice, { decimals: 2 });
      document.getElementById('stat-emae-hint').textContent = nivel.periodo;
    }
  }
  async function icaStat() {
    const index = await fetchIndex('ica');
    const allYears = Object.keys(index.datos || {}).filter(k => /^\d{4}$/.test(k));
    const lastYear = Math.max(...allYears.map(Number));
    const { data: ica } = await fetchJSON('/v1/ica/' + lastYear + '/');
    const last = ica.datos[ica.datos.length - 1];
    if (last) animateValue(document.getElementById('stat-ica'), last.saldo, { decimals: 1 });
  }

  const results = await Promise.allSettled([ipcStat(), cbaStat(), emaeStat(), icaStat()]);
  results.forEach((r, i) => {
    if (r.status === 'rejected') console.warn('stats task ' + i + ' failed:', r.reason);
  });
}

/* ---------- Reveal on scroll ---------- */
function initReveal() {
  document.querySelectorAll('[data-stagger]').forEach(group => {
    group.querySelectorAll(':scope > .reveal').forEach((el, i) => {
      el.style.transitionDelay = (i * 70) + 'ms';
    });
  });
  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
}

/* ---------- Docs tabs ---------- */
function initTabs() {
  const tabs = document.querySelectorAll('#doc-tabs .tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
    });
  });
  document.querySelectorAll('#ind-grid .ind-card').forEach(card => {
    card.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      const tab = document.querySelector('#doc-tabs .tab[data-tab="' + card.dataset.tab + '"]');
      tab.classList.add('active');
      document.getElementById('panel-' + card.dataset.tab).classList.add('active');
      document.getElementById('endpoints').scrollIntoView({ behavior: 'smooth' });
    });
  });
}

/* ---------- Copy buttons ---------- */
function initCopy() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const url = BASE + (btn.dataset.copy || '');
      navigator.clipboard.writeText(url).then(() => {
        btn.textContent = '✓ copiado';
        setTimeout(() => btn.textContent = 'copiar', 1500);
      });
    });
  });
}

/* ---------- Modes ---------- */
function setMode(mode) {
  currentMode = mode;
  document.getElementById('mode-guide').classList.toggle('active', mode === 'guide');
  document.getElementById('mode-raw').classList.toggle('active', mode === 'raw');
  document.getElementById('raw-row').style.display = mode === 'raw' ? 'flex' : 'none';
  if (mode === 'raw') {
    document.getElementById('raw-path').value = buildUrl();
    document.getElementById('raw-path').focus();
  } else {
    updateUrlBar();
  }
}

/* ---------- Init ---------- */
function init() {
  document.getElementById('pg-ind').addEventListener('change', () => { loadBuilder(); updateUrlBar(); });
  document.getElementById('pg-f1').addEventListener('change', onF1Change);
  document.getElementById('pg-f2').addEventListener('change', onF2Change);
  document.getElementById('pg-f3').addEventListener('change', updateUrlBar);
  document.getElementById('pg-year').addEventListener('input', updateUrlBar);
  document.getElementById('pg-run').addEventListener('click', () => run(buildUrl()));
  document.getElementById('raw-run').addEventListener('click', () => {
    const raw = document.getElementById('raw-path').value.trim();
    if (!raw) return;
    const url = raw.startsWith('/') ? raw : '/' + raw;
    run(url);
  });
  document.getElementById('raw-path').addEventListener('keydown', e => {
    if (e.key === 'Enter') document.getElementById('raw-run').click();
  });
  document.getElementById('mode-guide').addEventListener('click', () => setMode('guide'));
  document.getElementById('mode-raw').addEventListener('click', () => setMode('raw'));
  document.getElementById('pg-open').addEventListener('click', () => {
    window.open(BASE + buildUrl(), '_blank');
  });
  document.getElementById('pg-copy').addEventListener('click', () => {
    navigator.clipboard.writeText(BASE + buildUrl()).then(() => {
      document.getElementById('pg-copy').textContent = '✓ copiado';
      setTimeout(() => document.getElementById('pg-copy').textContent = '⧉ copiar', 1500);
    });
  });

  initTabs();
  initCopy();
  initReveal();
  loadBuilder();
  loadStats();
}

init();
