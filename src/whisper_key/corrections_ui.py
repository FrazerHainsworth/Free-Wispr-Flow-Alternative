# corrections_ui.py
# Browser page for the learned word replacements in user_settings.yaml.
# Binds to 127.0.0.1 only. Edits go through corrections.py, so the running
# app picks them up on the next dictation.

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .corrections import find_conflicts, list_replacements, save_replacements
from .text_postprocess import _apply_replacements

HOST = '127.0.0.1'
PORT = 8770
_MAX_BODY = 2_000_000
_write_lock = threading.Lock()


def _payload(rules) -> dict:
    return {'rules': rules, 'conflicts': find_conflicts(rules)}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path in ('/', '/index.html'):
            body = _PAGE.encode('utf-8')
            self._send(200, 'text/html; charset=utf-8', body)
            return
        if path == '/api/rules':
            with _write_lock:
                rules = list_replacements()
            self._send_json(200, _payload(rules))
            return
        self._send(404, 'text/plain; charset=utf-8', b'Not found')

    def do_PUT(self):
        if self.path.split('?', 1)[0] != '/api/rules':
            self._send(404, 'text/plain; charset=utf-8', b'Not found')
            return
        try:
            data = self._read_json()
            with _write_lock:
                saved = save_replacements(data.get('rules'))
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {'error': str(e)})
            return
        except Exception as e:
            self._send_json(500, {'error': str(e)})
            return
        self._send_json(200, _payload(saved))

    def do_POST(self):
        if self.path.split('?', 1)[0] != '/api/preview':
            self._send(404, 'text/plain; charset=utf-8', b'Not found')
            return
        try:
            data = self._read_json()
            text = str(data.get('text') or '')
            rules = data.get('rules')
            if not isinstance(rules, list):
                with _write_lock:
                    rules = list_replacements()
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {'error': str(e)})
            return
        self._send_json(200, {'text': _apply_replacements(text, rules)})

    def _read_json(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        if length < 0 or length > _MAX_BODY:
            raise ValueError('request body is too large')
        raw = self.rfile.read(length) if length else b'{}'
        data = json.loads(raw.decode('utf-8'))
        if not isinstance(data, dict):
            raise ValueError('expected a JSON object')
        return data

    def _send_json(self, status: int, payload: dict):
        self._send(status, 'application/json; charset=utf-8',
                   json.dumps(payload).encode('utf-8'))

    def _send(self, status: int, content_type: str, body: bytes):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # The page polls itself. A console line per request just adds noise.
        return


def serve(open_browser: bool = True) -> None:
    url = f'http://{HOST}:{PORT}/'
    try:
        httpd = ThreadingHTTPServer((HOST, PORT), _Handler)
    except OSError:
        print(f'Corrections page is already open at {url}', flush=True)
        if open_browser:
            webbrowser.open(url)
        return
    print(f'Learned corrections: {url}', flush=True)
    print('Close this window when you are done.', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free Wispr Flow — learned corrections</title>
<style>
  :root { color-scheme: light; }
  body { margin: 0; font: 15px/1.45 Segoe UI, sans-serif; background: #f4f5f7; color: #1c1e21; }
  main { max-width: 920px; margin: 0 auto; padding: 28px 20px 64px; }
  h1 { font-size: 22px; font-weight: 650; margin: 0 0 6px; }
  p.lead { margin: 0 0 18px; color: #4b5160; }
  section { background: #fff; border: 1px solid #e2e4e8; border-radius: 10px; padding: 14px 16px; margin: 0 0 14px; }
  label { display: block; font-size: 12px; color: #5c6370; margin-bottom: 4px; }
  input[type="text"], input[type="search"] { width: 100%; box-sizing: border-box; font: inherit; padding: 8px 10px; border: 1px solid #cfd3da; border-radius: 8px; background: #fff; }
  input:focus { outline: 2px solid #2563eb; border-color: #2563eb; }
  .preview-out { margin: 10px 0 0; min-height: 1.4em; font-weight: 650; }
  .preview-out.changed { color: #9a3412; }
  .problem { border-color: #fdba74; background: #fff7ed; }
  .problem h2 { font-size: 14px; margin: 0 0 8px; }
  .problem p { margin: 0 0 8px; }
  .toolbar { display: flex; gap: 10px; align-items: center; margin: 0 0 10px; }
  .toolbar input { flex: 1; }
  button { font: inherit; border: 1px solid #d0d4dc; background: #fff; border-radius: 8px; padding: 7px 12px; cursor: pointer; }
  button:hover { background: #f3f4f6; }
  button.danger { color: #9f1239; }
  button.primary { background: #1d4ed8; color: #fff; border-color: #1d4ed8; }
  .rule { display: grid; grid-template-columns: 1fr 28px 1fr auto; gap: 8px; align-items: center; padding: 8px 0; border-top: 1px solid #eceef2; }
  .rule.bad { background: #fff7ed; margin: 0 -8px; padding: 8px; border-radius: 8px; }
  .arrow { text-align: center; color: #6b7280; }
  .status { color: #5c6370; font-size: 13px; min-height: 1.2em; }
  .empty { color: #6b7280; margin: 8px 0; }
</style>
</head>
<body>
<main>
  <h1>Learned corrections</h1>
  <p class="lead">After you fix a word by hand, Whisper Local remembers it and rewrites that word on later dictations. Rules run from top to bottom, so a later rule can change what an earlier rule just wrote. Edits here are saved to your settings and apply on the next dictation.</p>

  <section>
    <label for="sample">Try a sentence</label>
    <input id="sample" type="text" value="please send this" autocomplete="off">
    <div id="preview" class="preview-out"></div>
  </section>

  <div id="problems"></div>

  <section>
    <div class="toolbar">
      <input id="q" type="search" placeholder="Search heard or written words" autocomplete="off">
      <label style="display:flex;align-items:center;gap:6px;margin:0;white-space:nowrap;">
        <input id="problemsOnly" type="checkbox"> Problems only
      </label>
      <button id="add" class="primary" type="button">Add rule</button>
    </div>
    <div id="status" class="status"></div>
    <div id="rows"></div>
  </section>
</main>
<script>
let rules = [];
let conflicts = [];
let saveTimer = null;
let previewTimer = null;

const rowsEl = document.getElementById('rows');
const problemsEl = document.getElementById('problems');
const statusEl = document.getElementById('status');
const previewEl = document.getElementById('preview');

function problemIndexes() {
  const set = new Set();
  conflicts.forEach(function (item) {
    set.add(item.earlier);
    set.add(item.later);
  });
  return set;
}

function setStatus(text) { statusEl.textContent = text; }

async function load() {
  const res = await fetch('/api/rules');
  const data = await res.json();
  rules = data.rules || [];
  conflicts = data.conflicts || [];
  render();
  schedulePreview();
}

function render() {
  renderProblems();
  renderRows();
  setStatus(rules.length + ' saved rules');
}

function renderProblems() {
  problemsEl.innerHTML = '';
  conflicts.forEach(function (item) {
    const box = document.createElement('section');
    box.className = 'problem';
    const title = document.createElement('h2');
    title.textContent = item.kind === 'swap' ? 'These two rules undo each other' : 'One rule rewrites another';
    const copy = document.createElement('p');
    copy.textContent = item.message;
    box.appendChild(title);
    box.appendChild(copy);
    if (item.later_from) {
      const button = document.createElement('button');
      button.className = 'danger';
      button.type = 'button';
      button.textContent = 'Delete "' + item.later_from + '" to "' + item.later_to + '"';
      button.addEventListener('click', function () {
        removeMatch(item.later_from, item.later_to);
      });
      box.appendChild(button);
    }
    problemsEl.appendChild(box);
  });
}

function renderRows() {
  const q = document.getElementById('q').value.trim().toLowerCase();
  const onlyProblems = document.getElementById('problemsOnly').checked;
  const bad = problemIndexes();
  rowsEl.innerHTML = '';
  let shown = 0;
  rules.forEach(function (rule, index) {
    const hay = ((rule.from || '') + ' ' + (rule.to || '')).toLowerCase();
    if (q && hay.indexOf(q) === -1) return;
    if (onlyProblems && !bad.has(index)) return;
    shown += 1;
    const row = document.createElement('div');
    row.className = 'rule' + (bad.has(index) ? ' bad' : '');
    row.appendChild(field(rule, index, 'from', 'Heard'));
    const arrow = document.createElement('div');
    arrow.className = 'arrow';
    arrow.textContent = '\\u2192';
    row.appendChild(arrow);
    row.appendChild(field(rule, index, 'to', 'Written'));
    const del = document.createElement('button');
    del.className = 'danger';
    del.type = 'button';
    del.textContent = 'Delete';
    del.addEventListener('click', function () { removeRule(index); });
    row.appendChild(del);
    rowsEl.appendChild(row);
  });
  if (!shown) {
    const empty = document.createElement('p');
    empty.className = 'empty';
    empty.textContent = rules.length ? 'Nothing matches that search.' : 'No learned corrections yet.';
    rowsEl.appendChild(empty);
  }
}

function field(rule, index, key, name) {
  const input = document.createElement('input');
  input.type = 'text';
  input.value = rule[key] || '';
  input.setAttribute('aria-label', name + ' ' + (index + 1));
  input.addEventListener('input', function () {
    rules[index][key] = input.value;
    scheduleSave();
    schedulePreview();
  });
  return input;
}

function removeMatch(fromText, toText) {
  const index = rules.findIndex(function (rule) {
    return (rule.from || '') === fromText && (rule.to || '') === toText;
  });
  if (index >= 0) removeRule(index);
}

function removeRule(index) {
  rules.splice(index, 1);
  render();
  schedulePreview();
  saveNow();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  setStatus('Saving...');
  saveTimer = setTimeout(saveNow, 400);
}

let saveChain = Promise.resolve();

function saveNow() {
  clearTimeout(saveTimer);
  const snapshot = rules.map(function (rule) { return Object.assign({}, rule); });
  setStatus('Saving...');
  saveChain = saveChain.then(function () { return postRules(snapshot); });
}

async function postRules(snapshot) {
  try {
    const res = await fetch('/api/rules', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rules: snapshot })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Save failed');
    conflicts = data.conflicts || [];
    const editing = document.activeElement && document.activeElement.closest
      && document.activeElement.closest('#rows');
    if (editing) renderProblems();
    else render();
    setStatus('Saved ' + (data.rules || []).length + ' rules. They apply on the next dictation.');
  } catch (err) {
    setStatus(err.message || 'Could not save');
  }
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(runPreview, 200);
}

async function runPreview() {
  const sample = document.getElementById('sample').value;
  if (!sample) { previewEl.textContent = ''; previewEl.className = 'preview-out'; return; }
  const res = await fetch('/api/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: sample, rules: rules })
  });
  const data = await res.json();
  previewEl.textContent = data.text || '';
  previewEl.className = 'preview-out' + (data.text !== sample ? ' changed' : '');
}

document.getElementById('q').addEventListener('input', renderRows);
document.getElementById('problemsOnly').addEventListener('change', renderRows);
document.getElementById('sample').addEventListener('input', schedulePreview);
document.getElementById('add').addEventListener('click', function () {
  rules.unshift({ from: '', to: '' });
  render();
  const first = rowsEl.querySelector('input');
  if (first) first.focus();
});

load().catch(function (err) { setStatus(err.message || 'Could not load corrections'); });
</script>
</body>
</html>
"""
