/* ── State ─────────────────────────────────────────────────────── */
let currentMode = 'hybrid';
let debounceTimer = null;

/* ── DOM refs ──────────────────────────────────────────────────── */
const textInput        = document.getElementById('textInput');
const predictionList   = document.getElementById('predictionList');
const probabilityChart = document.getElementById('probabilityChart');
const generateBtn      = document.getElementById('generateBtn');
const clearBtn         = document.getElementById('clearBtn');
const continuationBox  = document.getElementById('continuationBox');
const continuationText = document.getElementById('continuationText');
const acceptCont       = document.getElementById('acceptCont');
const sourceBadge      = document.getElementById('sourceBadge');
const sourceLabel      = document.getElementById('sourceLabel');
const dictInput        = document.getElementById('dictInput');
const addDictBtn       = document.getElementById('addDictBtn');
const wordsList        = document.getElementById('wordsList');
const phrasesList      = document.getElementById('phrasesList');
const trainInput       = document.getElementById('trainInput');
const trainBtn         = document.getElementById('trainBtn');
const trainStatus      = document.getElementById('trainStatus');
const vocabCount       = document.getElementById('vocabCount');
const contextCount     = document.getElementById('contextCount');
const footerMode       = document.getElementById('footerMode');

/* ── Mode switcher ─────────────────────────────────────────────── */
document.querySelectorAll('.mode-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentMode = btn.dataset.mode;
    footerMode.textContent = `MODE: ${currentMode.toUpperCase()}`;
    if (textInput.value.trim()) triggerPredict();
  });
});

/* ── Text input handler ────────────────────────────────────────── */
textInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(triggerPredict, 300);
  continuationBox.style.display = 'none';
});

textInput.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    // Accept first prediction on Tab
    const first = predictionList.querySelector('.pred-item');
    if (first) first.click();
  }
});

/* ── Predict ───────────────────────────────────────────────────── */
async function triggerPredict() {
  const text = textInput.value.trim();
  if (!text) {
    showEmptyState();
    sourceBadge.style.opacity = '0';
    return;
  }
  try {
    const res  = await fetch('/predict', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text, mode: currentMode }),
    });
    const data = await res.json();
    renderPredictions(data.predictions || []);
    renderChart(data.predictions || []);
    sourceLabel.textContent = data.source?.toUpperCase() || '—';
    sourceBadge.style.opacity = '1';
  } catch (err) {
    console.error('Predict error:', err);
  }
}

/* ── Render predictions ────────────────────────────────────────── */
function renderPredictions(preds) {
  if (!preds.length) { showEmptyState(); return; }
  predictionList.innerHTML = '';
  preds.forEach(([word, score], i) => {
    const item = document.createElement('div');
    item.className = 'pred-item';
    item.style.setProperty('--prob-width', `${Math.round(score * 100)}%`);
    item.innerHTML = `
      <span class="pred-rank">${i + 1}</span>
      <span class="pred-word">${word}</span>
      <span class="pred-score">${(score * 100).toFixed(1)}%</span>
    `;
    item.addEventListener('click', () => insertWord(word));
    predictionList.appendChild(item);
  });
}

/* ── Render bar chart ──────────────────────────────────────────── */
function renderChart(preds) {
  probabilityChart.innerHTML = '';
  if (!preds.length) return;
  const max = preds[0][1];
  preds.forEach(([word, score]) => {
    const pct = max > 0 ? (score / max) * 100 : 0;
    const row = document.createElement('div');
    row.className = 'chart-bar-wrap';
    row.innerHTML = `
      <span class="chart-bar-label">${word}</span>
      <div class="chart-bar-outer">
        <div class="chart-bar-inner" style="width:${pct}%"></div>
      </div>
      <span class="chart-bar-val">${(score * 100).toFixed(1)}%</span>
    `;
    probabilityChart.appendChild(row);
  });
}

/* ── Insert word into textarea ─────────────────────────────────── */
function insertWord(word) {
  const val = textInput.value;
  const endsWithSpace = val.endsWith(' ') || val === '';
  textInput.value = val + (endsWithSpace ? '' : ' ') + word + ' ';
  textInput.focus();
  textInput.setSelectionRange(textInput.value.length, textInput.value.length);
  triggerPredict();
}

/* ── Empty state ───────────────────────────────────────────────── */
function showEmptyState() {
  predictionList.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">◌</div>
      <p>Start typing to see word predictions appear here in real-time.</p>
    </div>`;
  probabilityChart.innerHTML = '';
}

/* ── Generate continuation ─────────────────────────────────────── */
generateBtn.addEventListener('click', async () => {
  const text = textInput.value.trim();
  if (!text) return;
  generateBtn.textContent = '⟳ GENERATING...';
  generateBtn.disabled = true;
  try {
    const res  = await fetch('/generate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ text, length: 10 }),
    });
    const data = await res.json();
    if (data.continuation) {
      continuationText.textContent = data.continuation;
      continuationBox.style.display = 'block';
    }
  } catch (err) { console.error(err); }
  finally {
    generateBtn.innerHTML = '<span class="btn-icon">⟳</span> GENERATE CONTINUATION';
    generateBtn.disabled = false;
  }
});

acceptCont.addEventListener('click', () => {
  const cur  = textInput.value.trim();
  const cont = continuationText.textContent;
  textInput.value = cur + ' ' + cont + ' ';
  continuationBox.style.display = 'none';
  textInput.focus();
  triggerPredict();
});

clearBtn.addEventListener('click', () => {
  textInput.value = '';
  continuationBox.style.display = 'none';
  showEmptyState();
  sourceBadge.style.opacity = '0';
});

/* ── Dictionary ────────────────────────────────────────────────── */
addDictBtn.addEventListener('click', addToDict);
dictInput.addEventListener('keydown', e => { if (e.key === 'Enter') addToDict(); });

async function addToDict() {
  const word  = dictInput.value.trim();
  const type  = document.querySelector('input[name="dictType"]:checked').value;
  if (!word) return;
  const res  = await fetch('/custom_dict', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ word, type }),
  });
  const data = await res.json();
  if (data.success) {
    dictInput.value = '';
    renderDict(data.dict);
  }
}

async function deleteFromDict(word, type) {
  const res  = await fetch('/custom_dict/delete', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ word, type }),
  });
  const data = await res.json();
  if (data.success) renderDict(data.dict);
}

function renderDict(dict) {
  renderDictList(wordsList,   dict.words,   'word');
  renderDictList(phrasesList, dict.phrases, 'phrase');
}

function renderDictList(container, items, type) {
  container.innerHTML = '';
  if (!items.length) {
    container.innerHTML = `<span style="color:var(--text-dim);font-size:.7rem">None yet</span>`;
    return;
  }
  items.forEach(w => {
    const tag = document.createElement('div');
    tag.className = 'dict-tag';
    tag.innerHTML = `${w}<button class="dict-tag-del" title="Remove">×</button>`;
    tag.querySelector('.dict-tag-del').addEventListener('click', () => deleteFromDict(w, type));
    container.appendChild(tag);
  });
}

async function loadDict() {
  const res  = await fetch('/custom_dict');
  const data = await res.json();
  renderDict(data);
}

/* ── Train ─────────────────────────────────────────────────────── */
trainBtn.addEventListener('click', async () => {
  const text = trainInput.value.trim();
  if (!text) return;
  trainBtn.textContent = '⬆ TRAINING...';
  trainBtn.disabled = true;
  const res  = await fetch('/train', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ text }),
  });
  const data = await res.json();
  trainBtn.textContent = '⬆ TRAIN ON THIS TEXT';
  trainBtn.disabled = false;
  if (data.success) {
    trainStatus.textContent = '✓ MODEL RETRAINED SUCCESSFULLY';
    trainInput.value = '';
    setTimeout(() => { trainStatus.textContent = ''; }, 3000);
    loadStats();
  }
});

/* ── Stats ─────────────────────────────────────────────────────── */
async function loadStats() {
  const res  = await fetch('/stats');
  const data = await res.json();
  vocabCount.textContent   = data.unigram_vocab?.toLocaleString() || '—';
  contextCount.textContent = (data.ngram_contexts + data.bigram_contexts)?.toLocaleString() || '—';
}

/* ── Init ──────────────────────────────────────────────────────── */
loadDict();
loadStats();
