document.documentElement.classList.add('js');

const fmt = new Intl.NumberFormat('es-AR');
const BASE = 'https://pindec.pages.dev';
let history = [];
let builderData = {};   // { ipc: {estructura, años}, cba-cbt: {subcategorias}, emae: {...} }
let currentMode = 'guide';

function fetchJSON(url) {
  return fetch(url, { headers: { Accept: 'application/json' } }).then(r => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  });
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
  el.innerHTML = '<option value="">—</option>' + options.map(o =>
    '<option value="' + o + '"' + (o === selected ? ' selected' : '') + '>' + o + '</option>'
  ).join('');
  el.disabled = false;
  wrap.style.display = 'flex';
}

function hideField(id) {
  document.getElementById(id).disabled = true;
  document.getElementById(id).innerHTML = '<option value="">—</option>';
  document.getElementById(id + '-wrap').style.display = 'none';
}

async function loadBuilder() {
  const ind = document.getElementById('pg-ind').value;
  const f1 = document.getElementById('pg-f1');
  const f2 = document.getElementById('pg-f2');
  const f3 = document.getElementById('pg-f3');

  if (!builderData[ind]) {
    try {
      const index = await fetchJSON('/v1/' + ind + '/index.json');
      builderData[ind] = index;
    } catch (e) {
      builderData[ind] = null;
    }
  }
  const data = builderData[ind];

  f1.value = ''; f2.value = ''; f3.value = '';
  hideField('pg-f1'); hideField('pg-f2'); hideField('pg-f3');

  if (!data) return;

  if (ind === 'ipc') {
    const regions = data.regiones || [];
    if (regions.length) setField('pg-f1', regions, f1.dataset.last);
  } else if (ind === 'cba-cbt') {
    const subs = data.subcategorias || [];
    if (subs.length) setField('pg-f1', subs, f1.dataset.last);
  } else if (ind === 'emae') {
    const subs = data.subcategorias || [];
    if (subs.length) setField('pg-f1', subs, f1.dataset.last);
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
  if (!f1) return;

  const data = builderData[ind];
  if (!data) return;

  if (ind === 'ipc') {
    const estructura = data.estructura || {};
    const clasifs = estructura[f1] ? Object.keys(estructura[f1]) : [];
    if (clasifs.length) setField('pg-f2', clasifs, f2.dataset.last);
  } else if (ind === 'emae') {
    if (f1 === 'sectores') {
      const codes = data.sectores || [];
      if (codes.length) setField('pg-f2', codes, f2.dataset.last);
    }
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
  if (!f2) return;

  const data = builderData[ind];
  if (!data) return;

  if (ind === 'ipc') {
    const estructura = data.estructura || {};
    const codes = (estructura[f1] || {})[f2] || [];
    if (codes.length) setField('pg-f3', codes, f3.dataset.last);
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
    const data = await fetchJSON(url);
    const ms = Math.round(performance.now() - start);
    out.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));
    status.className = 'status-line';
    status.textContent = '200 OK · ' + ms + ' ms · ' + out.textContent.length + ' bytes';
    pushHistory(url);
  } catch (err) {
    out.innerHTML = '<span class="err">Error: ' + escapeHtml(err.message) + '</span>';
    status.className = 'status-line fail';
    status.textContent = 'Solicitud fallida';
  } finally {
    btn.disabled = false; btn.textContent = 'Ejecutar';
  }
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
  try {
    const years = await fetchJSON('/v1/ipc/index.json');
    const lastYear = Math.max(...years.anos_disponibles);
    const ipc = await fetchJSON('/v1/ipc/Nacional/' + lastYear + '/');
    const nivel = ipc.datos.COICOP.find(c => c.codigo === '0');
    if (nivel && nivel.historico.length) {
      const last = nivel.historico[nivel.historico.length - 1];
      animateValue(document.getElementById('stat-ipc'), last.indice, { decimals: 2 });
      document.getElementById('stat-ipc-hint').textContent = last.periodo;
      document.getElementById('foot-update').textContent = last.periodo;
    }
  } catch (e) {}
  try {
    const years = await fetchJSON('/v1/cba-cbt/index.json');
    const lastYear = Math.max(...years.anos_disponibles);
    const cba = await fetchJSON('/v1/cba-cbt/' + lastYear + '/');
    const last = cba.adulto_equivalente[cba.adulto_equivalente.length - 1];
    if (last) animateValue(document.getElementById('stat-cba'), last.cba.indice, { prefix: '$', decimals: 2 });
  } catch (e) {}
  try {
    const years = await fetchJSON('/v1/emae/index.json');
    const lastYear = Math.max(...years.anos_disponibles);
    const emae = await fetchJSON('/v1/emae/' + lastYear + '/');
    const nivel = emae.datos.nivel_general[emae.datos.nivel_general.length - 1];
    if (nivel) {
      animateValue(document.getElementById('stat-emae'), nivel.original.indice, { decimals: 2 });
      document.getElementById('stat-emae-hint').textContent = nivel.periodo;
    }
  } catch (e) {}
  try {
    const years = await fetchJSON('/v1/ica/index.json');
    const lastYear = Math.max(...years.anos_disponibles);
    const ica = await fetchJSON('/v1/ica/' + lastYear + '/');
    const last = ica.datos[ica.datos.length - 1];
    if (last) animateValue(document.getElementById('stat-ica'), last.saldo, { decimals: 1 });
  } catch (e) {}
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
