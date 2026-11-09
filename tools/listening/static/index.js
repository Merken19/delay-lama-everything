"use strict";

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  for (const c of children) if (c !== null && c !== undefined) node.append(c);
  return node;
}

function shortTime(iso) {
  if (!iso) return "";
  return iso.replace("T", " ").slice(0, 16);
}

function statusBadge(t) {
  if (t.status === "answered") return el("span", { class: "badge answered", text: "answered" + (t.times > 1 ? ` ×${t.times}` : "") });
  if (t.status === "skipped") return el("span", { class: "badge skipped", text: "skipped" });
  return el("span", { class: "badge", text: "not answered" });
}

const SHOW_ALL_KEY = "listening.showAll";

function getShowAll() {
  try { return localStorage.getItem(SHOW_ALL_KEY) === "1"; } catch (e) { return false; }
}

function setShowAll(on) {
  try { localStorage.setItem(SHOW_ALL_KEY, on ? "1" : "0"); } catch (e) { /* private window */ }
}

let DATA = null;

// Default view: only sets that have a listening.json, and in them only the
// tests with no answer yet (a skip counts as an answer). Manifest problems
// stay visible, since they need fixing. "Show all" lists everything.
function visibleSets(sets, showAll) {
  if (showAll) return sets.map(s => ({ set: s, tests: s.tests }));
  const out = [];
  for (const s of sets) {
    if (s.source !== "manifest") continue;
    if (s.error) { out.push({ set: s, tests: [] }); continue; }
    const open = s.tests.filter(t => !t.status);
    if (open.length) out.push({ set: s, tests: open });
  }
  return out;
}

function renderSets() {
  const box = document.getElementById("sets");
  const showAll = getShowAll();
  document.getElementById("show-all").checked = showAll;
  const sets = DATA.sets;
  const shown = visibleSets(sets, showAll);
  const openTests = sets.filter(s => s.source === "manifest" && !s.error)
    .reduce((n, s) => n + s.tests.filter(t => !t.status).length, 0);
  const totalTests = sets.reduce((n, s) => n + s.tests.length, 0);
  document.getElementById("view-note").textContent = showAll
    ? `All ${sets.length} sets, ${totalTests} tests (including folders without a listening.json).`
    : `${openTests} unanswered test${openTests === 1 ? "" : "s"} in sets with a listening.json; ` +
      `${totalTests - openTests} answered, skipped or without a manifest are hidden.`;

  if (!sets.length) {
    box.replaceChildren(el("p", { class: "muted", text: "No WAV files or manifests found." }));
    return;
  }
  if (!shown.length) {
    box.replaceChildren(el("section", { class: "panel empty" },
      el("p", { text: "Nothing waiting: every test with a listening.json has an answer." }),
      el("p", { class: "small muted", text: "Tick “Show all” to see answered tests and folders without a manifest." })));
    return;
  }
  const phases = new Map();
  for (const v of shown) {
    if (!phases.has(v.set.phase)) phases.set(v.set.phase, []);
    phases.get(v.set.phase).push(v);
  }
  const out = [];
  for (const [phase, views] of phases) {
    out.push(el("h2", { text: phase }));
    for (const { set: s, tests } of views) {
      const done = s.tests.filter(t => t.status).length;
      const head = el("div", { class: "set-head" },
        el("h3", { text: s.title }),
        el("code", { class: "small muted", text: "renders/" + s.path }),
        s.source === "fallback" ? el("span", { class: "badge", text: "no manifest" }) : null,
        s.error ? null : el("span", { class: "badge", text: `${done}/${s.tests.length} done` }));
      const panel = el("section", { class: "panel" }, head);
      if (s.intro) panel.append(el("p", { class: "small muted", text: s.intro }));
      if (s.error) {
        panel.append(el("p", { class: "error", text: "Manifest problem: " + s.error }));
      }
      const list = el("ul", { class: "tests" });
      for (const t of tests) {
        const href = `/test.html?set=${encodeURIComponent(s.path)}&test=${encodeURIComponent(t.id)}`;
        const title = t.title === t.id ? t.id : `${t.id}: ${t.title}`;
        const li = el("li", {},
          el("div", {}, el("a", { href, text: title }),
            el("span", { class: "muted small", text: `  ${t.clips} clip${t.clips === 1 ? "" : "s"}` + (t.missing ? `, ${t.missing} missing` : "") })),
          statusBadge(t));
        if (t.question) li.append(el("div", { class: "q small", text: t.question }));
        if (t.summary) li.append(el("div", { class: "summary", text: `${shortTime(t.saved)}: ${t.summary}` }));
        list.append(li);
      }
      if (tests.length) panel.append(list);
      if (showAll && s.has_answers) {
        panel.append(el("p", { class: "small muted" }, "Summary for later sessions: ",
          el("code", { text: `renders/${s.path}/answers.md` })));
      }
      out.push(panel);
    }
  }
  box.replaceChildren(...out);
}

async function load() {
  const box = document.getElementById("sets");
  try {
    const r = await fetch("/api/sets", { cache: "no-store" });
    DATA = await r.json();
  } catch (e) {
    box.replaceChildren(el("p", { class: "error", text: "Can't reach the server: is serve.py running?" }));
    return;
  }
  document.getElementById("renders").textContent = DATA.renders;
  renderSets();
}

document.getElementById("show-all").addEventListener("change", e => {
  setShowAll(e.target.checked);
  renderSets();
});

// Coming back from a test page (back button or bfcache) shows fresh status.
window.addEventListener("pageshow", e => { if (e.persisted) load(); });

load();
