"use strict";
// Comparison page: loads every clip of one test into Web Audio, plays them all
// in sync and switches by gain, so a switch keeps the playback position.

const $ = id => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, "");
    else node.setAttribute(k, v);
  }
  for (const c of children) if (c !== null && c !== undefined) node.append(c);
  return node;
}

const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem("listening." + key); return v === null ? fallback : JSON.parse(v); }
    catch { return fallback; }
  },
  set(key, value) { try { localStorage.setItem("listening." + key, JSON.stringify(value)); } catch { /* ignore */ } },
};

function fmt(t) {
  if (!isFinite(t) || t < 0) t = 0;
  const m = Math.floor(t / 60), s = t - m * 60;
  return `${m}:${s.toFixed(1).padStart(4, "0")}`;
}
function shortTime(iso) { return iso ? iso.replace("T", " ").slice(0, 16) : ""; }

// ---------------------------------------------------------------- state

const params = new URLSearchParams(location.search);
const SET_PATH = params.get("set") || "";
let SET = null, TEST = null, ENTRIES = [], ANSWERS_MD = "";

let ctx = null, bus = null, master = null;
let clips = [];          // {spec, buffer, gain, source, peaks}
let order = [];          // display order: indexes into clips
let current = 0;         // index into clips
let ready = false;
let playing = false, startCtx = 0, startOffset = 0, pausedAt = 0, playLoop = null;
let duration = 0;
const loop = { on: false, a: 0, b: 0 };

let blind = store.get("blind", false);
let letterOf = {};       // condition -> letter (blind)
let revealed = false;

// ---------------------------------------------------------------- loading

async function init() {
  let data;
  try {
    const r = await fetch(`/api/set?path=${encodeURIComponent(SET_PATH)}`, { cache: "no-store" });
    data = await r.json();
    if (!data.ok) throw new Error(data.error);
  } catch (e) {
    $("title").textContent = "Can't load this test";
    $("question").textContent = String(e.message || e);
    return;
  }
  SET = data.set;
  ANSWERS_MD = data.answers_md;
  if (SET.error) {
    $("title").textContent = SET.title;
    $("question").textContent = "Manifest problem: " + SET.error;
    return;
  }
  const wanted = params.get("test");
  const idx = Math.max(0, SET.tests.findIndex(t => t.id === wanted));
  TEST = SET.tests[idx];
  ENTRIES = data.answers[TEST.id] || [];

  document.title = `${TEST.id} · Listening Test`;
  $("where").textContent = `renders/${SET.path} · ${SET.title}`;
  $("title").textContent = TEST.title === TEST.id ? TEST.id : `${TEST.id}: ${TEST.title}`;
  $("question").textContent = TEST.question;
  $("notes").textContent = TEST.notes;
  if (SET.intro) { $("intro").textContent = SET.intro; $("intro-box").hidden = false; }
  const link = (a, t) => {
    if (!t) return;
    a.href = `/test.html?set=${encodeURIComponent(SET.path)}&test=${encodeURIComponent(t.id)}`;
    a.textContent = a.id === "prev" ? `← ${t.id}` : `${t.id} →`;
    a.hidden = false;
  };
  link($("prev"), SET.tests[idx - 1]);
  link($("next"), SET.tests[idx + 1]);

  clips = TEST.clips.map(spec => ({ spec, buffer: null, gain: null, source: null, peaks: null }));
  if (TEST.blind === false) {
    blind = false;                         // this test's question needs the names
    $("blind").disabled = true;
    $("blind").parentElement.title = "Blind mode is off for this test: its question needs the clip names.";
    $("blind").parentElement.classList.add("muted");
  }
  $("blind").checked = blind;
  if (blind) shuffle();
  buildOrder();
  current = order.find(i => !clips[i].spec.missing) ?? 0;
  renderClips();
  renderQuestions();
  renderPrevious();
  renderFiles();
  updateBlindUi();
  draw();
  await loadAudio();
}

function wavRate(buf) {
  // RIFF/WAVE header: the sample rate is at byte 24 of a canonical fmt chunk.
  const v = new DataView(buf);
  if (buf.byteLength < 28 || v.getUint32(0, false) !== 0x52494646) return null;
  let p = 12;
  while (p + 8 <= buf.byteLength) {
    const id = v.getUint32(p, false), size = v.getUint32(p + 4, true);
    if (id === 0x666d7420) return v.getUint32(p + 12, true); // "fmt "
    p += 8 + size + (size & 1);
  }
  return null;
}

async function loadAudio() {
  const files = [...new Set(clips.filter(c => !c.spec.missing).map(c => c.spec.file))];
  const status = $("load-status");
  if (!files.length) { status.textContent = "No audio files found for this test."; return; }
  let done = 0;
  status.textContent = `Loading audio 0/${files.length}…`;
  const raw = await Promise.all(files.map(async f => {
    const r = await fetch("/renders/" + f.split("/").map(encodeURIComponent).join("/"), { cache: "no-store" });
    if (!r.ok) throw new Error(`${f}: HTTP ${r.status}`);
    const b = await r.arrayBuffer();
    status.textContent = `Loading audio ${++done}/${files.length}…`;
    return b;
  })).catch(e => { status.textContent = "Loading failed: " + e.message; return null; });
  if (!raw) return;

  const rate = wavRate(raw[0]);
  try { ctx = new AudioContext(rate ? { sampleRate: rate, latencyHint: "interactive" } : {}); }
  catch { ctx = new AudioContext(); }
  master = ctx.createGain();
  bus = ctx.createGain();
  bus.connect(master);
  master.connect(ctx.destination);
  setVolume(store.get("volume", 1));

  status.textContent = "Decoding…";
  const decoded = new Map();
  try {
    for (let i = 0; i < files.length; i++) decoded.set(files[i], await ctx.decodeAudioData(raw[i]));
  } catch (e) {
    status.textContent = "Decoding failed: " + e.message;
    return;
  }

  // Cut segments, then pad every clip to the longest so loops stay in sync.
  const pieces = clips.map(c => {
    if (c.spec.missing) return null;
    const src = decoded.get(c.spec.file);
    const a = Math.min(src.length, Math.round((c.spec.start || 0) * src.sampleRate));
    const b = c.spec.end == null ? src.length : Math.min(src.length, Math.round(c.spec.end * src.sampleRate));
    return { src, a, b: Math.max(a + 1, b) };
  });
  const len = Math.max(...pieces.filter(Boolean).map(p => p.b - p.a));
  pieces.forEach((p, i) => {
    if (!p) return;
    const whole = p.a === 0 && p.b === p.src.length && p.src.length === len;
    let buf = p.src;
    if (!whole) {
      buf = ctx.createBuffer(p.src.numberOfChannels, len, p.src.sampleRate);
      for (let ch = 0; ch < p.src.numberOfChannels; ch++) {
        buf.copyToChannel(p.src.getChannelData(ch).subarray(p.a, p.b), ch);
      }
    }
    const c = clips[i];
    c.buffer = buf;
    c.active = (p.b - p.a) / p.src.sampleRate;
    c.gain = ctx.createGain();
    c.gain.gain.value = i === current ? 1 : 0;
    c.gain.connect(bus);
  });
  duration = len / ctx.sampleRate;
  ready = true;
  $("play").disabled = false;
  const rateNote = ctx.sampleRate === rate ? `${rate / 1000} kHz` : `${rate / 1000} kHz files, ${ctx.sampleRate / 1000} kHz output`;
  status.textContent = `${clips.filter(c => c.buffer).length} clips loaded (${rateNote}).`;
  updateTransport();
  draw();
}

// ---------------------------------------------------------------- playback

function pos() {
  if (!playing) return pausedAt;
  let p = startOffset + Math.max(0, ctx.currentTime - startCtx);
  if (playLoop && p >= playLoop.b) p = playLoop.a + ((p - playLoop.b) % (playLoop.b - playLoop.a));
  return Math.min(p, duration);
}

function stopSources() {
  if (!ctx) return;
  const now = ctx.currentTime;
  bus.gain.cancelScheduledValues(now);
  bus.gain.setValueAtTime(bus.gain.value, now);
  bus.gain.linearRampToValueAtTime(0, now + 0.01);   // short fade: no click
  for (const c of clips) {
    if (c.source) { try { c.source.stop(now + 0.012); } catch { /* already stopped */ } c.source = null; }
  }
}

async function play(offset = pausedAt) {
  if (!ready) return;
  if (ctx.state !== "running") await ctx.resume();
  stopSources();
  const useLoop = loop.on && loop.b - loop.a >= 0.05;
  if (useLoop && (offset < loop.a || offset >= loop.b)) offset = loop.a;
  if (offset >= duration - 0.01) offset = 0;
  const t0 = ctx.currentTime + 0.03;
  bus.gain.setValueAtTime(0, t0);
  bus.gain.linearRampToValueAtTime(1, t0 + 0.006);
  for (const c of clips) {
    if (!c.buffer) continue;
    const s = ctx.createBufferSource();
    s.buffer = c.buffer;
    if (useLoop) { s.loop = true; s.loopStart = loop.a; s.loopEnd = loop.b; }
    s.connect(c.gain);
    s.start(t0, offset);
    c.source = s;
  }
  playing = true;
  startCtx = t0;
  startOffset = offset;
  playLoop = useLoop ? { a: loop.a, b: loop.b } : null;
  updateTransport();
  requestAnimationFrame(tick);
}

function pause() {
  if (!playing) return;
  pausedAt = pos();
  stopSources();
  playing = false;
  updateTransport();
  draw();
}

function toggle() { playing ? pause() : play(); }

function seek(t) {
  t = Math.max(0, Math.min(duration, t));
  if (playing) play(t);
  else { pausedAt = t; updateTransport(); draw(); }
}

function restartIfPlaying() { if (playing) play(pos()); else { updateTransport(); draw(); } }

function tick() {
  if (!playing) return;
  if (!playLoop && pos() >= duration) {
    stopSources();
    playing = false;
    pausedAt = 0;
    updateTransport();
    draw();
    return;
  }
  updateTime();
  draw();
  requestAnimationFrame(tick);
}

function select(i, autoplay = true) {
  if (i == null || i < 0 || i >= clips.length || clips[i].spec.missing) return;
  current = i;
  if (ctx) {
    const now = ctx.currentTime;
    clips.forEach((c, k) => {
      if (!c.gain) return;
      c.gain.gain.cancelScheduledValues(now);
      c.gain.gain.setValueAtTime(c.gain.gain.value, now);
      c.gain.gain.linearRampToValueAtTime(k === i ? 1 : 0, now + 0.008);
    });
  }
  for (const b of document.querySelectorAll(".clip")) b.classList.toggle("active", +b.dataset.index === i);
  draw();
  if (autoplay && ready && !playing) play();
}

function selectByPosition(n) { if (n < order.length) select(order[n]); }

function step(delta) {
  const usable = order.filter(i => !clips[i].spec.missing);
  const at = usable.indexOf(current);
  select(usable[(at + delta + usable.length) % usable.length], false);
}

function setVolume(v) {
  v = Math.max(0, Math.min(1, +v));
  $("volume").value = v;
  store.set("volume", v);
  if (master) master.gain.value = v * v;
}

// ---------------------------------------------------------------- transport UI

function updateTime() { $("time").textContent = `${fmt(pos())} / ${fmt(duration)}`; }

function updateTransport() {
  $("play").textContent = playing ? "❚❚ Pause" : "▶ Play";
  $("loop").checked = loop.on;
  $("loop-info").textContent = loop.on ? `${fmt(loop.a)}–${fmt(loop.b)}` : "";
  updateTime();
}

function enableLoop() {
  if (loop.b - loop.a < 0.05) { loop.a = 0; loop.b = duration; }
  loop.on = true;
}

const canvas = $("wave");
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function peaks(c, width) {
  if (c.peaks && c.peaks.width === width) return c.peaks;
  const buf = c.buffer, n = buf.length, chans = [];
  for (let ch = 0; ch < buf.numberOfChannels; ch++) chans.push(buf.getChannelData(ch));
  const lo = new Float32Array(width), hi = new Float32Array(width);
  for (let x = 0; x < width; x++) {
    const a = Math.floor(x * n / width), b = Math.max(a + 1, Math.floor((x + 1) * n / width));
    let mn = 0, mx = 0;
    for (const d of chans) for (let i = a; i < b; i++) { const s = d[i]; if (s < mn) mn = s; else if (s > mx) mx = s; }
    lo[x] = mn; hi[x] = mx;
  }
  c.peaks = { width, lo, hi };
  return c.peaks;
}

function draw() {
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  const g = canvas.getContext("2d");
  g.fillStyle = css("--panel");
  g.fillRect(0, 0, w, h);
  if (!ready || !duration) return;
  const x = t => (t / duration) * w;
  if (loop.on) { g.fillStyle = css("--loop"); g.fillRect(x(loop.a), 0, Math.max(1, x(loop.b) - x(loop.a)), h); }
  // seconds ticks
  g.fillStyle = css("--line");
  for (let s = 1; s < duration; s++) g.fillRect(Math.round(x(s)), h - (s % 5 ? 5 : 10) * dpr, dpr, (s % 5 ? 5 : 10) * dpr);
  const c = clips[current];
  if (c && c.buffer) {
    const p = peaks(c, w), mid = h / 2, amp = h / 2 - 4 * dpr;
    g.fillStyle = css("--wave-active");
    for (let i = 0; i < w; i++) {
      const top = mid - p.hi[i] * amp, bot = mid - p.lo[i] * amp;
      g.fillRect(i, top, 1, Math.max(1, bot - top));
    }
  }
  if (loop.on) {
    g.fillStyle = css("--accent");
    g.fillRect(x(loop.a), 0, dpr, h);
    g.fillRect(x(loop.b) - dpr, 0, dpr, h);
  }
  g.fillStyle = css("--text");
  g.fillRect(Math.round(x(pos())), 0, Math.max(1, Math.round(1.5 * dpr)), h);
}

let drag = null;
canvas.addEventListener("pointerdown", e => {
  if (!ready) return;
  canvas.setPointerCapture(e.pointerId);
  drag = { x: e.offsetX, t: e.offsetX / canvas.clientWidth * duration, moved: false };
});
canvas.addEventListener("pointermove", e => {
  if (!drag) return;
  if (Math.abs(e.offsetX - drag.x) > 4) drag.moved = true;
  if (drag.moved) {
    const t = Math.max(0, Math.min(duration, e.offsetX / canvas.clientWidth * duration));
    loop.a = Math.min(drag.t, t); loop.b = Math.max(drag.t, t); loop.on = true;
    updateTransport(); draw();
  }
});
canvas.addEventListener("pointerup", e => {
  if (!drag) return;
  const d = drag; drag = null;
  if (d.moved) {
    if (loop.b - loop.a < 0.05) { loop.on = false; }
    if (playing) play(loop.on ? loop.a : pos()); else { pausedAt = loop.on ? loop.a : pausedAt; updateTransport(); draw(); }
  } else {
    seek(e.offsetX / canvas.clientWidth * duration);
  }
});
window.addEventListener("resize", draw);

$("play").addEventListener("click", e => { e.currentTarget.blur(); toggle(); });
$("loop").addEventListener("change", e => { e.target.blur(); if (e.target.checked) enableLoop(); else loop.on = false; restartIfPlaying(); });
$("loop-a").addEventListener("click", e => { e.currentTarget.blur(); setLoopStart(); });
$("loop-b").addEventListener("click", e => { e.currentTarget.blur(); setLoopEnd(); });
$("loop-clear").addEventListener("click", e => { e.currentTarget.blur(); loop.on = false; loop.a = loop.b = 0; restartIfPlaying(); });
$("volume").addEventListener("input", e => setVolume(e.target.value));
$("volume").addEventListener("change", e => e.target.blur());

function setLoopStart() {
  const p = pos();
  loop.a = p;
  if (loop.b <= p + 0.05) loop.b = duration;
  loop.on = true;
  restartIfPlaying();
}
function setLoopEnd() {
  const p = pos();
  loop.b = p;
  if (loop.a >= p - 0.05) loop.a = 0;
  loop.on = true;
  if (playing) play(loop.a); else { pausedAt = loop.a; updateTransport(); draw(); }
}

document.addEventListener("keydown", e => {
  if (e.ctrlKey || e.altKey || e.metaKey) return;
  const t = e.target;
  const typing = t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable ||
    (t.tagName === "INPUT" && !["radio", "checkbox", "button"].includes(t.type));
  if (typing) return;
  const k = e.key;
  if (/^[1-9]$/.test(k)) selectByPosition(+k - 1);
  else if (k === "0") selectByPosition(9);
  else if (k === " ") { if (!e.repeat) toggle(); }
  else if (k === "ArrowUp") step(-1);
  else if (k === "ArrowDown") step(1);
  else if (k === "ArrowLeft") seek(pos() - (e.shiftKey ? 0.5 : 2));
  else if (k === "ArrowRight") seek(pos() + (e.shiftKey ? 0.5 : 2));
  else if (k === "Home") seek(loop.on ? loop.a : 0);
  else if (k === "l" || k === "L") { if (loop.on) loop.on = false; else enableLoop(); restartIfPlaying(); }
  else if (k === "[") setLoopStart();
  else if (k === "]") setLoopEnd();
  else return;
  e.preventDefault();
});
document.addEventListener("keyup", e => {
  const t = e.target;
  if (e.key === " " && t.tagName !== "TEXTAREA" && !(t.tagName === "INPUT" && t.type === "text")) e.preventDefault();
});

// ---------------------------------------------------------------- blind mode

function isBlind() { return blind && !revealed; }

function shuffle() {
  const conds = TEST.conditions.filter(c => !c.reference).map(c => c.id);
  for (let i = conds.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [conds[i], conds[j]] = [conds[j], conds[i]];
  }
  letterOf = {};
  conds.forEach((c, i) => { letterOf[c] = String.fromCharCode(65 + i); });
  revealed = false;
}

function lettersPayload() {
  const out = {};
  for (const [cond, letter] of Object.entries(letterOf)) out[letter] = cond;
  return out;
}

function buildOrder() {
  const groups = [];
  clips.forEach((c, i) => {
    let g = groups.find(x => x.name === c.spec.group);
    if (!g) groups.push(g = { name: c.spec.group, items: [] });
    g.items.push(i);
  });
  order = [];
  for (const g of groups) {
    let items = g.items;
    if (blind) {
      const key = i => {
        const spec = clips[i].spec, letter = letterOf[spec.condition];
        return spec.reference ? -1 : letter ? letter.charCodeAt(0) : 1000;
      };
      items = [...items].sort((a, b) => key(a) - key(b) || a - b);
    }
    order.push(...items);
  }
}

function clipName(spec) {
  if (!blind) return spec.label;
  if (spec.reference) return spec.label;
  const letter = letterOf[spec.condition];
  return revealed ? `${letter} = ${spec.label}` : letter;
}

function renderClips() {
  const box = $("clips");
  box.replaceChildren();
  let group = null, list = null;
  order.forEach((i, n) => {
    const spec = clips[i].spec;
    if (!list || spec.group !== group) {
      group = spec.group;
      if (group) box.append(el("div", { class: "group-title", text: group }));
      list = el("div", { class: "clips" });
      box.append(list);
    }
    const key = n < 9 ? String(n + 1) : n === 9 ? "0" : "";
    const showDesc = !isBlind() || spec.reference;
    const btn = el("button", {
      type: "button", class: "clip" + (i === current ? " active" : "") + (spec.missing ? " missing" : ""),
      "data-index": i, disabled: spec.missing || null,
      title: spec.missing ? `missing: ${spec.file}` : null,
    },
      el("span", { class: "key" }, key ? el("kbd", { text: key }) : null),
      el("span", { class: "name" + (isBlind() && !spec.reference ? " letter" : "") },
        clipName(spec), spec.reference ? el("span", { class: "badge ref", text: "reference" }) : null),
      el("span", { class: "desc", text: spec.missing ? `File missing: ${spec.file}` : (showDesc ? spec.desc : "") }));
    btn.querySelector(".badge")?.style.setProperty("margin-left", "8px");
    btn.addEventListener("click", () => { btn.blur(); select(i); });
    list.append(btn);
  });
}

function renderFiles() {
  const files = [...new Set(clips.map(c => c.spec.file))];
  const box = $("files");
  if (isBlind()) { box.replaceChildren(); return; }
  box.replaceChildren("Files: ", ...files.flatMap((f, k) => [
    k ? ", " : "",
    el("a", { href: "/renders/" + f.split("/").map(encodeURIComponent).join("/"), target: "_blank", text: f.split("/").pop() }),
  ]));
}

function updateBlindUi() {
  $("blind-note").hidden = !blind;
  $("reshuffle").hidden = !(blind && revealed);
}

function rerenderAll() {
  const keep = readForm();
  buildOrder();
  renderClips();
  renderQuestions();
  fillForm(keep);
  renderPrevious();
  renderFiles();
  updateBlindUi();
}

$("blind").addEventListener("change", e => {
  e.target.blur();
  blind = e.target.checked;
  store.set("blind", blind);
  if (blind) shuffle(); else { letterOf = {}; revealed = false; }
  rerenderAll();
  clearForm();
  setStatus("");
});

$("reshuffle").addEventListener("click", () => {
  shuffle();
  rerenderAll();
  clearForm();
  setStatus("New blind round: clips reshuffled.");
});

// ---------------------------------------------------------------- answers

function choiceLabel(ch) {
  if (!blind || !ch.condition) return ch.label;
  const letter = letterOf[ch.condition];
  if (!letter) return ch.label;            // the reference keeps its name
  return revealed ? `${letter}: ${ch.label}` : letter;
}

function choicesInOrder(q) {
  if (!blind) return q.choices;
  const lettered = q.choices.filter(c => c.condition && letterOf[c.condition]);
  const rest = q.choices.filter(c => !(c.condition && letterOf[c.condition]));
  lettered.sort((a, b) => letterOf[a.condition].localeCompare(letterOf[b.condition]));
  return [...lettered, ...rest];
}

function renderQuestions() {
  const box = $("questions");
  box.replaceChildren(...TEST.questions.map(q => {
    const fs = el("fieldset", {}, el("legend", { text: q.text + (q.multi ? " (tick all that apply)" : "") }));
    const row = el("div", { class: "choices" });
    for (const ch of choicesInOrder(q)) {
      row.append(el("label", { class: "choice" },
        el("input", { type: q.multi ? "checkbox" : "radio", name: "q:" + q.id, value: ch.id }),
        " " + choiceLabel(ch)));
    }
    fs.append(row);
    return fs;
  }));
}

function readForm() {
  const answers = {};
  for (const q of TEST.questions) {
    const picked = [...document.querySelectorAll(`input[name="q:${CSS.escape(q.id)}"]:checked`)].map(i => i.value);
    answers[q.id] = q.multi ? picked : (picked[0] ?? null);
  }
  const conf = document.querySelector('input[name="confidence"]:checked');
  return { answers, confidence: conf ? conf.value : null, note: $("note").value };
}

function fillForm(state) {
  for (const q of TEST.questions) {
    const v = state.answers[q.id];
    const want = Array.isArray(v) ? v : v == null ? [] : [v];
    for (const input of document.querySelectorAll(`input[name="q:${CSS.escape(q.id)}"]`)) input.checked = want.includes(input.value);
  }
  for (const input of document.querySelectorAll('input[name="confidence"]')) input.checked = input.value === state.confidence;
  $("note").value = state.note || "";
}

function clearForm() { fillForm({ answers: {}, confidence: null, note: "" }); }

function setStatus(msg, kind = "") { const s = $("status"); s.textContent = msg; s.className = kind; }

async function submit(status) {
  const form = readForm();
  if (status === "answered") {
    const any = Object.values(form.answers).some(v => Array.isArray(v) ? v.length : v);
    if (!any && !form.note.trim()) { setStatus("Pick an answer (or press Skip).", "bad"); return; }
  }
  // A re-save after the reveal is no longer blind.
  const body = { set: SET.path, test: TEST.id, status, blind: isBlind(), letters: isBlind() ? lettersPayload() : {}, ...form };
  $("save").disabled = $("skip").disabled = true;
  try {
    const r = await fetch("/api/answer", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await r.json();
    if (!data.ok) throw new Error(data.error);
    ENTRIES = data.entries;
    const when = shortTime(ENTRIES[ENTRIES.length - 1].saved).slice(11);
    setStatus(`${status === "skipped" ? "Skipped" : "Saved"} at ${when} → ${ANSWERS_MD.replace(/answers\.md$/, "answers.json")}`, "ok");
    if (blind) { revealed = true; rerenderAll(); } else renderPrevious();
  } catch (e) {
    setStatus("Not saved: " + (e.message || e), "bad");
  } finally {
    $("save").disabled = $("skip").disabled = false;
  }
}

$("form").addEventListener("submit", e => { e.preventDefault(); submit("answered"); });
$("skip").addEventListener("click", () => submit("skipped"));

function entryItem(e) {
  const head = `${shortTime(e.saved)} · ${e.blind ? "blind" : "sighted"}` + (e.confidence ? ` · confidence ${e.confidence}` : "");
  const li = el("li", {}, el("div", { class: "small muted", text: head }));
  if (e.status === "skipped") li.append(el("div", {}, el("span", { class: "badge skipped", text: "skipped" })));
  else {
    for (const a of e.answers) {
      let label = a.label;
      if (Array.isArray(label)) label = label.length ? label.map((l, k) => a.letter && a.letter[k] ? `${l} [${a.letter[k]}]` : l).join(", ") : "(none ticked)";
      else if (label == null) label = "(not answered)";
      else if (a.letter) label += ` [${a.letter}]`;
      li.append(el("div", {}, `${a.text} `, el("b", { text: label })));
    }
  }
  if (e.note) li.append(el("div", { class: "small", text: "Note: " + e.note }));
  return li;
}

function renderPrevious() {
  const box = $("previous");
  if (!ENTRIES.length) {
    box.replaceChildren(el("p", { class: "small muted", text: `No answers yet. They go to ${ANSWERS_MD.replace(/answers\.md$/, "answers.json")} and answers.md.` }));
    return;
  }
  const list = el("ol", { class: "history", reversed: true }, ...[...ENTRIES].reverse().map(entryItem));
  const hidden = isBlind();
  const details = el("details", { open: hidden ? null : true },
    el("summary", { text: `Previous answers (${ENTRIES.length})` + (hidden ? ": hidden until you answer this blind round" : "") }),
    list,
    el("p", { class: "small muted", text: `Summary: ${ANSWERS_MD}` }));
  box.replaceChildren(el("h3", { text: "Saved so far" }), details);
}

init();
