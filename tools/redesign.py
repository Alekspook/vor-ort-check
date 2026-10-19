#!/usr/bin/env python3
"""Baut aus index.html die Design-Testversion (neues Design, eigener Speicher, Beispieldaten).
Aufruf: redesign.py <index.html> <ausgabe.html> [--preview]"""
import sys, re, os

src, dst = sys.argv[1], sys.argv[2]
PREVIEW = "--preview" in sys.argv
here = os.path.dirname(os.path.abspath(__file__))
s = open(src, encoding="utf-8").read()

def rep(a, b, count=1):
    global s
    n = s.count(a)
    assert n == count, f"{n}x gefunden statt {count}: {a[:80]!r}"
    s = s.replace(a, b)

def rep_between(start, end, new):
    """Ersetzt alles ab `start` (inklusive) bis vor `end`."""
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + s[j:]

# ---------- 1) Stylesheet komplett ersetzen ----------
css = open(os.path.join(here, "redesign.css"), encoding="utf-8").read()
i = s.index("<style>\n  :root{"); j = s.index("</style>", i) + len("</style>")
s = s[:i] + css + s[j:]

# ---------- 2) Icons ----------
rep("""  cloud: '<path d="M7 18h10a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.1 9.2 4.5 4.5 0 0 0 7 18Z"/>'
};""", """  cloud: '<path d="M7 18h10a4 4 0 0 0 .6-7.96A6 6 0 0 0 6.1 9.2 4.5 4.5 0 0 0 7 18Z"/>',
  chevronLeft: '<path d="M15 5l-7 7 7 7"/>',
  chevronRight: '<path d="M9 5l7 7-7 7"/>'
};""")

# ---------- 3) Abschnitts-Leiste, Fortschrittsring ----------
rep_between("function renderSectionNav(){", "function jumpToSection(id){", """function renderSectionNav(){
  return FORM_SECTIONS.map(sec=>{
    const done = sectionDone(sec.id);
    return `<button type="button" class="nav-chip ${done ? "done" : ""}" onclick="jumpToSection('${sec.id}')">${done ? icon("check",12) : `<span class="nav-dot"></span>`}${sec.label}</button>`;
  }).join("");
}
function progressInfo(){
  const secs = FORM_SECTIONS.filter(s=> s.id !== "abschluss");
  return { done: secs.filter(s=> sectionDone(s.id)).length, total: secs.length };
}
function progressRing(){
  const { done, total } = progressInfo();
  const c = 2 * Math.PI * 15;
  return `<div class="ring ${done === total ? "complete" : ""}" id="progressRing" title="${done} von ${total} Abschnitten erledigt" aria-label="${done} von ${total} Abschnitten erledigt"><svg viewBox="0 0 38 38" width="38" height="38"><circle cx="19" cy="19" r="15" class="ring-bg"/><circle cx="19" cy="19" r="15" class="ring-fg" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${(c * (1 - done/total)).toFixed(1)}"/></svg><span>${done}/${total}</span></div>`;
}
""")
rep("""  const nav = document.getElementById("sectionNav");
  if(nav) nav.innerHTML = renderSectionNav();""", """  const nav = document.getElementById("sectionNav");
  if(nav) nav.innerHTML = renderSectionNav();
  const ring = document.getElementById("progressRing");
  if(ring) ring.outerHTML = progressRing();
  FORM_SECTIONS.forEach(sec=>{ const el = document.getElementById("sec-" + sec.id); if(el) el.classList.toggle("is-done", sectionDone(sec.id)); });""")

# ---------- 4) Dialog & Hinweis ----------
rep_between("function showConfirm(message, onConfirm, okLabel, okColor){", "function deleteRecord(id){", """function showConfirm(message, onConfirm, okLabel, okColor){
  const old = document.getElementById("confirmOverlay");
  if(old) old.remove();
  const overlay = document.createElement("div");
  overlay.id = "confirmOverlay";
  overlay.className = "dialog-backdrop";
  overlay.innerHTML = `
    <div class="dialog" role="dialog" aria-modal="true">
      <p>${message}</p>
      <div class="dialog-actions">
        <button id="confirmOkBtn" class="ok" style="background:${okColor || "var(--danger)"}">${okLabel || "Löschen"}</button>
        <button id="confirmCancelBtn" class="cancel">Abbrechen</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener("click", e=>{ if(e.target === overlay) overlay.remove(); });
  document.getElementById("confirmCancelBtn").onclick = ()=> overlay.remove();
  document.getElementById("confirmOkBtn").onclick = ()=>{ overlay.remove(); onConfirm(); };
}
""")
rep_between("function showToast(message){", "function menuDownloadPDF(){", """function showToast(message){
  const old = document.getElementById("toast");
  if(old) old.remove();
  const el = document.createElement("div");
  el.id = "toast";
  el.className = "toast";
  el.setAttribute("role", "status");
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(()=> el.remove(), 5000);
}
""")

# ---------- 5) Kopf, Startseite, Listen ----------
rep_between("function renderFormScreen(){", "/* ---------- Field builders ---------- */", r"""function pdfHeaderButton(){
  const entry = pdfCache["current"];
  if(entry && entry.status==="building") return `<button class="icon-btn building" title="PDF wird erstellt…" aria-label="PDF wird erstellt" disabled><span class="spinner"></span></button>`;
  if(entry && entry.status==="ready") return `<button class="icon-btn ready" title="Protokoll bereit — antippen zum Herunterladen" aria-label="Protokoll herunterladen" onclick="sharePDF('current')">${icon("check",18)}</button>`;
  return `<button class="icon-btn" title="Protokoll als PDF erstellen" aria-label="Protokoll als PDF erstellen" onclick="menuDownloadPDF()">${icon("download",18)}</button>`;
}
function renderFormScreen(){
  const name = [S.kunde.vorname, S.kunde.nachname].filter(Boolean).join(" ");
  const place = [[S.standort.strasse, S.standort.nr].filter(Boolean).join(" "), S.standort.ort].filter(Boolean).join(", ");
  const rec = records.find(r=> r.id === currentRecordId);
  const n = missingRequiredCount();
  return `
    <header>
      <div class="bar-row">
        <button class="bar-btn" onclick="goHome()" aria-label="Zur Startseite">${icon("chevronLeft",24)}</button>
        <div class="bar-title">
          <div class="bar-name">${escapeHtml(name || "Neuer Vor-Ort-Check")}</div>
          <div class="bar-sub">${escapeHtml(place || (rec && rec.status === "fertig" ? "Abgeschlossen" : "Entwurf"))}</div>
        </div>
        ${progressRing()}
        ${pdfHeaderButton()}
        <button class="bar-btn" onclick="toggleMenu(event)" aria-label="Weitere Aktionen">${icon("dots")}</button>
      </div>
      <nav class="section-nav" id="sectionNav" aria-label="Abschnitte">${renderSectionNav()}</nav>
      <div class="save-indicator" id="saveIndicator"></div>
      <div class="error-banner" id="errorBanner" style="display:none;"></div>
      ${menuOpen ? `
        <div class="menu-pop">
          <button onclick="downloadAllPhotos('current')">Alle Fotos aufs Handy laden</button>
          <button class="danger" onclick="menuDeleteCurrent()">Diesen Vor-Ort-Check löschen</button>
        </div>` : ""}
    </header>
    <main id="mainContent" class="form-main"></main>
    <div class="finish-bar">
      <button type="button" id="finishBtn" class="finish-btn ${n ? "incomplete" : ""}" onclick="handleSend()"><span id="finishLabel">${finishLabel(n)}</span></button>
    </div>
  `;
}
function initials(d){
  const parts = [d.kunde.vorname, d.kunde.nachname].filter(Boolean);
  const txt = parts.length ? parts.map(p=> p.trim()[0]).join("") : "?";
  return escapeHtml(txt.slice(0,2).toUpperCase());
}
function recordRow(r, opts){
  const d = r.data;
  const name = [d.kunde.vorname, d.kunde.nachname].filter(Boolean).join(" ") || "Ohne Namen";
  const place = [d.standort.strasse, d.standort.ort].filter(Boolean).join(", ");
  const when = r.status === "fertig" && d.grunddaten.besichtigtAm ? formatDateDE(d.grunddaten.besichtigtAm) : fmtDateTime(r.updatedAt);
  const status = opts && opts.showStatus ? (r.status === "fertig" ? "Abgeschlossen" : "Entwurf") + " · " : "";
  let actions = "";
  if(r.status === "fertig" && !(opts && opts.compact)){
    const entry = pdfCache[r.id];
    actions += `<button title="Alle Fotos aufs Handy laden" aria-label="Alle Fotos aufs Handy laden" onclick="event.stopPropagation(); downloadAllPhotos('${r.id}')">${icon("image",19)}</button>`;
    if(entry && entry.status === "building") actions += `<button class="building" title="PDF wird erstellt…" aria-label="PDF wird erstellt" disabled><span class="spinner-sm"></span></button>`;
    else if(entry && entry.status === "ready") actions += `<button class="ready" title="Protokoll bereit — antippen zum Herunterladen" aria-label="Protokoll herunterladen" onclick="event.stopPropagation(); quickPDF('${r.id}')">${icon("check",19)}</button>`;
    else actions += `<button title="Protokoll als PDF erstellen" aria-label="Protokoll als PDF erstellen" onclick="event.stopPropagation(); quickPDF('${r.id}')">${icon("download",19)}</button>`;
  }
  if(!(opts && opts.compact)) actions += `<button class="danger" title="Löschen" aria-label="Löschen" onclick="event.stopPropagation(); deleteRecord('${r.id}')">${icon("trash",18)}</button>`;
  else actions += `<span style="color:var(--ink-3);display:flex;padding-right:6px;">${icon("chevronRight",18)}</span>`;
  return `
    <div class="rec" data-search="${escapeAttr(listSearchText(r))}">
      <button class="rec-main" onclick="openRecord('${r.id}')">
        <span class="avatar ${r.status === "draft" ? "draft" : ""}">${initials(d)}</span>
        <span class="rec-text">
          <span class="rec-name">${escapeHtml(name)}</span>
          <span class="rec-sub">${status}${escapeHtml(place || "Keine Adresse")} · ${when}</span>
        </span>
      </button>
      <div class="rec-actions">${actions}</div>
    </div>`;
}
function greeting(){
  const h = new Date().getHours();
  return h >= 5 && h < 11 ? "Guten Morgen" : h >= 11 && h < 18 ? "Hallo" : "Guten Abend";
}
function renderHome(){
  const drafts = records.filter(r=> r.status === "draft");
  const fertig = records.filter(r=> r.status === "fertig");
  const recent = records.slice().sort((a,b)=> b.updatedAt - a.updatedAt).slice(0, 4);
  const firstName = ((freshState().grunddaten.besichtigtVon || "").split(" ")[0]) || "";
  const today = new Date().toLocaleDateString("de-DE", { weekday:"long", day:"numeric", month:"long" });
  return `
    <div class="home-top">
      <img class="brand" src="${DWB_LOGO}" alt="DWB Energie">
      <button class="bar-btn backup-btn" onclick="goScreen('backup')" title="Cloud-Backup" aria-label="Cloud-Backup">${icon("cloud",24)}<span class="backup-dot" id="backupDot" ${backupNeedsAttention() ? "" : "hidden"}></span></button>
    </div>
    <div class="save-indicator home-save" id="saveIndicator"></div>
    <main class="home">
      <div class="hello">
        <div class="hello-date">${escapeHtml(today)}</div>
        <h1 class="hello-title">${greeting()}${firstName ? ", " + escapeHtml(firstName) : ""}</h1>
        __PREVIEW_NOTE__
      </div>
      <button class="cta" onclick="startNewRecord()">
        <span class="cta-icon">${icon("zap",24)}</span>
        <span class="cta-text"><strong>Neuer Vor-Ort-Check</strong><span>PV-Bestandsaufnahme starten</span></span>
        ${icon("chevronRight",22)}
      </button>
      <div class="stats">
        <button class="stat" onclick="goScreen('drafts')"><span class="stat-num">${drafts.length}</span><span class="stat-label"><i style="background:var(--sun)"></i>Entwürfe</span></button>
        <button class="stat" onclick="goScreen('fertig')"><span class="stat-num">${fertig.length}</span><span class="stat-label"><i style="background:var(--accent)"></i>Abgeschlossen</span></button>
      </div>
      ${recent.length ? `
        <div class="group-label">Zuletzt bearbeitet</div>
        <div class="group">${recent.map(r=> recordRow(r, { compact: true, showStatus: true })).join("")}</div>` : ""}
    </main>`;
}
let listQuery = "";
function listSearchText(r){
  const d = r.data;
  return [d.kunde.vorname, d.kunde.nachname, d.standort.strasse, d.standort.plz, d.standort.ort].filter(Boolean).join(" ").toLowerCase();
}
function filterList(q){
  listQuery = q;
  const needle = q.trim().toLowerCase();
  document.querySelectorAll(".rec").forEach(el=>{ el.hidden = !!needle && !el.dataset.search.includes(needle); });
}
function renderList(status){
  const items = records.filter(r=>r.status===status).sort((a,b)=>b.updatedAt-a.updatedAt);
  const title = status==="draft" ? "Entwürfe" : "Abgeschlossen";
  const needle = listQuery.trim().toLowerCase();
  return `
    <header>
      <div class="top-row">
        <button class="bar-btn" onclick="goScreen('home')" aria-label="Zur Startseite">${icon("chevronLeft",24)}</button>
        <h1>${title}</h1>
        <span style="width:40px;"></span>
      </div>
    </header>
    <main>
      ${items.length > 5 ? `<input type="search" class="list-search" id="listSearch" placeholder="Suchen" aria-label="Kunde, Straße oder Ort suchen" value="${escapeAttr(listQuery)}" oninput="filterList(this.value)">` : ""}
      ${items.length === 0 ? `<div class="empty">${status === "draft" ? "Keine offenen Entwürfe." : "Noch nichts abgeschlossen."}</div>` : `
        <div class="group" style="margin-top:8px;">${items.map(r=> recordRow(r)).join("").replace(/<div class="rec" data-search="([^"]*)">/g, (m, q)=> needle && !q.includes(needle) ? `<div class="rec" data-search="${q}" hidden>` : m)}</div>`}
      ${status === "fertig" ? `<div class="note" style="margin:12px 4px 0;">Es bleiben die letzten ${MAX_FINISHED} abgeschlossenen Vor-Ort-Checks in der App. Ältere werden automatisch entfernt, sobald ihr PDF gesichert ist.</div>` : ""}
    </main>`;
}

""")
s = s.replace("__PREVIEW_NOTE__", '<div class="preview-note"><strong>Testversion</strong> mit neuem Design und Beispieldaten. Eingaben hier landen nicht in deiner echten App.</div>' if PREVIEW else "")

# ---------- 6) Feld-Bausteine ----------
rep_between("function textField(label, path, opts={}){", "function verbrauchTotal(){", r"""function reqMark(required){ return required ? ' <span class="req" aria-hidden="true">*</span>' : ""; }
function textField(label, path, opts={}){
  const val = getPath(S, path) ?? "";
  const type = opts.type || "text";
  return `
    <label class="row row-input" id="${domId(path)}">
      <span class="row-label">${label}${reqMark(opts.required)}</span>
      <input type="${type}" value="${escapeAttr(val)}" placeholder="${opts.placeholder||""}" ${type==="tel" ? 'inputmode="tel"' : ""} ${type==="email" ? 'autocapitalize="off"' : ""}
        oninput="setPath(S,'${path}', this.value); scheduleAutosave();">
    </label>`;
}
function textareaField(label, path, opts={}){
  const val = getPath(S, path) ?? "";
  return `
    <label class="row row-input" id="${domId(path)}">
      <span class="row-label">${label}${reqMark(opts.required)}</span>
      <textarea rows="2" placeholder="${opts.placeholder || "Optional"}" oninput="setPath(S,'${path}', this.value); scheduleAutosave();">${escapeHtml(val)}</textarea>
    </label>`;
}
function radioField(label, path, options, opts={}){
  const val = getPath(S, path) ?? "";
  return `
    <div class="row row-choice" id="${domId(path)}" role="radiogroup" aria-label="${escapeAttr(label)}">
      <span class="row-label">${label}${reqMark(opts.required)}</span>
      <div class="chips">
        ${options.map(o=>`
          <label class="chip ${val===o?"checked":""}">
            <input type="radio" name="${path}" ${val===o?"checked":""} onchange="setPath(S,'${path}','${escapeAttr(o)}'); scheduleAutosave(); render();">
            <span>${o}</span>
          </label>`).join("")}
      </div>
    </div>`;
}
function checkField(label, path){
  const val = !!getPath(S, path);
  return `
    <label class="row row-switch">
      <span class="row-text">${label}</span>
      <input type="checkbox" class="switch" ${val?"checked":""} onchange="setPath(S,'${path}', this.checked); scheduleAutosave(); render();">
    </label>`;
}
function kwhField(label, path){
  const val = getPath(S, path) ?? "";
  return `
    <label class="row row-input" id="${domId(path)}">
      <span class="row-label">${label}</span>
      <span class="input-unit"><input type="number" inputmode="decimal" value="${escapeAttr(val)}" placeholder="0"
        oninput="setPath(S,'${path}', this.value); scheduleAutosave(); updateVerbrauchTotal();"><em>kWh/Jahr</em></span>
    </label>`;
}
""")
rep_between("function photoSlot(path, label, required, noSketch){", "function handlePhoto(evt, path){", r"""function removePhoto(path, label){
  showConfirm(`${label} entfernen?`, ()=>{ setPath(S, path, null); scheduleAutosave(); render(); }, "Entfernen");
}
function photoSlot(path, label, required, noSketch){
  const val = getPath(S, path);
  if(val){
    return `
    <div class="row row-photo" id="${domId(path)}">
      <span class="row-label">${label}${reqMark(required)}</span>
      <div class="photo-preview">
        <img src="${val}" alt="${escapeAttr(label)}" loading="lazy" decoding="async">
        <div class="photo-actions">
          ${noSketch ? "" : `<button type="button" onclick="openSketchModal('${path}','${escapeAttr(label)}')">${icon("edit",15)} Einzeichnen</button>`}
          <button type="button" class="round" aria-label="${escapeAttr(label)} entfernen" onclick="removePhoto('${path}','${escapeAttr(label)}')">${icon("close",16)}</button>
        </div>
      </div>
    </div>`;
  }
  return `
    <div class="row row-photo" id="${domId(path)}">
      <span class="row-label">${label}${reqMark(required)}</span>
      <div class="photo-pick">
        <label class="pick-btn">
          <input type="file" accept="image/*" capture="environment" onchange="handlePhoto(event,'${path}')" hidden>
          ${icon("camera",20)}<span>Kamera</span>
        </label>
        <label class="pick-btn">
          <input type="file" accept="image/*" onchange="handlePhoto(event,'${path}')" hidden>
          ${icon("image",20)}<span>Galerie</span>
        </label>
      </div>
    </div>`;
}
""")
rep("""  const el = document.getElementById("verbrauchTotalValue");
  if(el) el.textContent = verbrauchTotal().toLocaleString("de-DE") + " kWh/Jahr";""", """  const el = document.getElementById("verbrauchTotalValue");
  if(el) el.textContent = verbrauchTotal().toLocaleString("de-DE") + " kWh";""")

# ---------- 7) Formular-Aufbau ----------
rep_between("function renderAllSections(){", "/* Dachfotos: 8 Plätze", r"""function secHead(num, id, title, tag){
  return `<h2 class="sec-title"><span class="sec-num">${num}</span>${title}${tag ? `<span class="tag ${tag.toLowerCase()}">${tag}</span>` : ""}</h2>`;
}
function sec(num, id, title, body, tag){
  return `<section class="sec ${tag === "DC" ? "sec-dc" : ""} ${sectionDone(id) ? "is-done" : ""}" id="sec-${id}">${secHead(num, id, title, tag)}${body}</section>`;
}
function renderAllSections(){
  const e = S.elektro, z = e.zaehler, h = e.hausanschluss;
  return [
    sec(1, "kunde", "Kunde", `
      <div class="group">
        <div class="row row-static"><span class="row-label">Fachberater</span><strong>${escapeHtml(S.grunddaten.besichtigtVon || "")}</strong></div>
        ${textField("Besichtigt am", "grunddaten.besichtigtAm", {type:"date"})}
      </div>
      <div class="group-label">Interessent/in</div>
      <div class="group">
        ${radioField("Anrede", "kunde.anrede", ["Familie","Herr","Frau"])}
        ${textField("Vorname", "kunde.vorname", {placeholder:"Max"})}
        ${textField("Nachname", "kunde.nachname", {placeholder:"Mustermann", required:true})}
        ${textField("Telefon", "kunde.telefon", {type:"tel", placeholder:"0171 …"})}
        ${textField("E-Mail", "kunde.email", {type:"email", required:true, placeholder:"name@beispiel.de"})}
      </div>
      <div class="group-label">Standort</div>
      <div class="group">
        <label class="row row-input">
          <span class="row-label">Adresse suchen</span>
          <input type="text" id="addressSearchInput" placeholder="Straße, Ort …" autocomplete="off" oninput="onAddressSearchInput(this.value)">
          <div class="address-suggestions" id="addressSuggestions"></div>
        </label>
        ${textField("Straße", "standort.strasse", {required:true})}
        ${textField("Hausnummer", "standort.nr", {required:true})}
        ${textField("PLZ", "standort.plz", {required:true})}
        ${textField("Ort", "standort.ort", {required:true})}
      </div>`),
    sec(2, "verbrauch", "Verbrauch", `
      <div class="group">
        ${kwhField("Haushalt", "elektro.stromverbrauch")}
        ${kwhField("Wärmepumpe", "elektro.grossverbraucher.waermepumpe")}
        ${kwhField("E-Auto", "elektro.grossverbraucher.eauto")}
        ${kwhField("Sauna", "elektro.grossverbraucher.sauna")}
        ${kwhField("Pool", "elektro.grossverbraucher.pool")}
        <div class="row row-total"><span>Gesamtverbrauch</span><strong id="verbrauchTotalValue">${verbrauchTotal().toLocaleString("de-DE")} kWh</strong></div>
      </div>`),
    sec(3, "dach", "Gebäude &amp; Dach", `
      <div class="group">
        ${radioField("Kategorie", "gebaeude.kategorie", ["Einfamilienhaus","Reihenhaus","Sonstige"], {required:true})}
        ${textField("Besonderheiten", "gebaeude.besonderheiten", {placeholder:"Optional"})}
      </div>
      ${renderRoofs()}`, "DC"),
    sec(4, "zaehler", "Zählerschrank", `
      <div class="group">
        ${radioField("Neuer Zählerschrank", "elektro.zaehler.neuerZaehlerschrank", ["Erforderlich","nicht erforderlich","muss geprüft werden"])}
      </div>
      <div class="group-label">Fotos</div>
      <div class="group">
        ${photoSlot("elektro.zaehler.uebersicht","Übersicht", true)}
        ${photoSlot("elektro.zaehler.ohneAbdeckungen","Ohne Abdeckungen", false)}
        ${photoSlot("elektro.zaehler.typenschild","Typenschild", false)}
        ${photoSlot("elektro.zaehler.vorsicherung","Vorsicherung / SLS (unter dem Zähler)", false)}
        ${photoSlot("elektro.zaehler.anschlussbereich","Anschlussbereich (über dem Zähler)", false)}
        ${photoSlot("elektro.zaehler.verteilerfeld1","Verteilerfeld 1", false)}
        ${photoSlot("elektro.zaehler.verteilerfeld2","Verteilerfeld 2", false)}
      </div>
      <div class="group-label">Verteilungen</div>
      <div class="group">
        ${radioField("Weitere Unterverteilungen", "elektro.zaehler.weitereUV", ["vorhanden","nicht vorhanden"])}
        ${z.weitereUV === "vorhanden" ? `<div class="conditional">${photoSlot("elektro.zaehler.weitereUVFoto","Foto weitere Unterverteilung", false)}</div>` : ""}
        ${radioField("Neue Unterverteilung", "elektro.zaehler.neueUV", ["erforderlich","nicht erforderlich"])}
        ${z.neueUV === "erforderlich" ? `<div class="conditional">${photoSlot("elektro.zaehler.neueUVFoto","Foto neue Unterverteilung", false)}</div>` : ""}
        ${radioField("Wanddurchbrüche", "elektro.zaehler.wanddurchbrueche", ["erforderlich","nicht erforderlich"])}
        ${z.wanddurchbrueche === "erforderlich" ? `<div class="conditional">
          ${photoSlot("elektro.zaehler.wanddurchbruecheFoto1","Foto Wanddurchbruch 1", false)}
          ${photoSlot("elektro.zaehler.wanddurchbruecheFoto2","Foto Wanddurchbruch 2", false)}
        </div>` : ""}
      </div>`, "AC"),
    sec(5, "ha", "Hausanschluss", `
      <div class="group">
        ${radioField("Hausanschluss", "elektro.hausanschluss.typ", ["HA-Innen","HA-Außen","kein eigener HA vorhanden"], {required:true})}
        ${photoSlot("elektro.hausanschluss.foto","Übersichtsfoto", false)}
        ${radioField("Potenzialausgleichsschiene", "elektro.hausanschluss.potenzialausgleich", ["vorhanden","nicht vorhanden"])}
        ${h.potenzialausgleich === "vorhanden" ? `<div class="conditional">${photoSlot("elektro.hausanschluss.potenzialausgleichFoto","Foto Potenzialausgleichsschiene", false)}</div>` : ""}
        ${radioField("Fundamenterder", "elektro.hausanschluss.fundamenterder", ["vorhanden","nicht vorhanden"])}
        ${h.fundamenterder === "vorhanden" ? `<div class="conditional">${photoSlot("elektro.hausanschluss.fundamenterderFoto","Foto Fundamenterder", false)}</div>` : ""}
        ${textareaField("Bemerkungen", "elektro.hausanschluss.bemerkung")}
      </div>`, "AC"),
    sec(6, "wp", "Wärmepumpe &amp; Wallbox", `
      <div class="group">
        ${radioField("Wärmepumpe", "elektro.waermepumpe", ["vorhanden","nicht vorhanden","geplant"])}
        ${e.waermepumpe === "vorhanden" ? `<div class="conditional">
          ${photoSlot("elektro.fotoWPTypenschild","Foto Typenschild Wärmepumpe", false)}
          ${photoSlot("elektro.fotoWPZaehler","Foto Wärmepumpenzähler", false)}
        </div>` : ""}
        ${radioField("Wallbox", "elektro.wallbox", ["vorhanden","nicht vorhanden","gewünscht"])}
        ${e.wallbox === "vorhanden" ? `<div class="conditional">${photoSlot("elektro.fotoWallboxTypenschild","Foto Wallbox Typenschild", false)}</div>` : ""}
        ${e.wallbox === "gewünscht" ? `<div class="conditional">${photoSlot("elektro.fotoWallboxStandort","Foto Wallbox Standortwunsch", false)}</div>` : ""}
        ${radioField("Sind Durchbrüche notwendig?", "elektro.wallboxDurchbrueche", ["Ja","Nein"])}
        ${e.wallboxDurchbrueche === "Ja" ? `<div class="conditional">${photoSlot("elektro.fotoWallboxDurchbruch","Foto Kabelweg / Durchbruch", false)}</div>` : ""}
      </div>`, "AC"),
    sec(7, "hardware", "Hardware &amp; Messkonzept", `
      <div class="group">
        ${checkField("Wechselrichter", "elektro.komponenten.hybrid")}
        ${e.komponenten.hybrid ? `<div class="conditional">${photoAnnotateField("elektro.fotoWechselrichter","Montageort Wechselrichter", false)}</div>` : ""}
        ${checkField("Batteriespeicher", "elektro.komponenten.batterie")}
        ${e.komponenten.batterie ? `<div class="conditional">${photoAnnotateField("elektro.fotoSpeicher","Montageort Batteriespeicher", false)}</div>` : ""}
        ${checkField("Notstrom", "elektro.komponenten.notstrom")}
        ${textareaField("Bemerkung", "elektro.montageortBemerkung")}
      </div>
      <div class="group-label">Messkonzept</div>
      <div class="group">
        ${radioField("Zähler-Messkonzept", "elektro.messkonzept", ["keine Änderung","Zusammenlegung","Kaskade"], {required:true})}
      </div>`, "AC"),
    sec(8, "abschluss", "Weitere Fotos", `
      ${S.zusatzbilder.length ? `<div class="group">${S.zusatzbilder.map((f,i)=> photoSlot(`zusatzbilder.${i}`, `Bild ${i+1}`, false)).join("")}</div>` : ""}
      <button class="ghost-btn" onclick="addExtraPhoto()">${icon("plus",18)} Foto hinzufügen</button>
      <div class="note" style="margin:14px 4px 0;">„Abschließen" verschiebt den Vor-Ort-Check nach Abgeschlossen. Das PDF erstellst du oben rechts oder in der Liste.</div>`)
  ].join("");
}

function renderRoofs(){
  const cards = S.daecher.map((d,i)=>`
    <div class="group-label">Dach ${i+1}${S.daecher.length>1 ? `<button class="remove-roof" onclick="removeRoof(${i})">Entfernen</button>` : ""}</div>
    <div class="group">
      ${radioField("Art", `daecher.${i}.dachart`, ["Schrägdach","Flachdach","Blechdach","Carport","Sonstige"], {required:true})}
      ${radioField("Eindeckung", `daecher.${i}.dachaufbau`, ["Ziegel","Bitumen","Trapez","Blechfalz","Sonstige"])}
      ${radioField("Regenrinne", `daecher.${i}.regenrinne`, ["vorhanden","nicht vorhanden"])}
      ${d.regenrinne === "vorhanden" ? `<div class="conditional">${radioField("Material Regenrinne", `daecher.${i}.regenrinneMaterial`, ["Zink","Kupfer","Kunststoff"])}</div>` : ""}
      ${textareaField("Bemerkungen", `daecher.${i}.bemerkung1`)}
      ${roofPhotoGrid(i)}
      ${radioField("Kabelweg", `daecher.${i}.dcLeitungsweg`, ["vorh. Leerrohr","alter Kaminschacht","Fassade im Alurohr","Sonstige"])}
      ${d.dcLeitungsweg ? `<div class="conditional">
        ${photoSlot(`daecher.${i}.dcFotos.0`, "Kabelweg Bild 1", true)}
        ${photoSlot(`daecher.${i}.dcFotos.1`, "Kabelweg Bild 2", false)}
      </div>` : ""}
      ${radioField("Wanddurchbrüche notwendig", `daecher.${i}.wanddurchbrueche`, ["Ja","Nein"])}
      ${d.wanddurchbrueche === "Ja" ? `<div class="conditional">
        ${photoSlot(`daecher.${i}.wanddurchbruecheFotos.0`, "Foto Wanddurchbruch 1", false)}
        ${photoSlot(`daecher.${i}.wanddurchbruecheFotos.1`, "Foto Wanddurchbruch 2", false)}
        ${photoSlot(`daecher.${i}.wanddurchbruecheFotos.2`, "Foto Wanddurchbruch 3", false)}
      </div>` : ""}
      ${radioField("Traufhöhe", `daecher.${i}.traufe8`, ["über 5m","unter 5m"])}
      ${radioField("Gerüst erforderlich", `daecher.${i}.geruest`, ["Ja","Nein","Fallschutz reicht","muss geprüft werden","Kunde stellt Gerüst"])}
      ${textareaField("Bemerkungen Gerüst", `daecher.${i}.geruestBemerkung`)}
    </div>
  `).join("");
  return cards + `<button class="ghost-btn" onclick="addRoof()">${icon("plus",18)} Weiteres Dach</button>`;
}
""")
rep_between("function roofPhotoGrid(i){", "async function addRoofPhotos(evt, i){", r"""function roofPhotoGrid(i){
  const urls = roofPhotoUrls(i);
  const free = ROOF_PHOTO_MAX - urls.length;
  return `
    <div class="row row-photo" id="${domId(`daecher.${i}.fotos.0`)}">
      <div class="row-head"><span class="row-label">Dachfotos${reqMark(true)}</span><span class="field-count">${urls.length} / ${ROOF_PHOTO_MAX}</span></div>
      ${urls.length ? `<div class="photo-grid">${urls.map((u,k)=>`
        <div class="photo-thumb">
          <img src="${u}" alt="Dachfoto ${k+1}" loading="lazy" decoding="async">
          <span class="thumb-num">${k+1}</span>
          <button type="button" class="thumb-remove" aria-label="Dachfoto ${k+1} entfernen" onclick="removeRoofPhoto(${i},${k})">${icon("close",14)}</button>
        </div>`).join("")}</div>` : ""}
      ${free > 0 ? `
      <div class="photo-pick">
        <label class="pick-btn">
          <input type="file" accept="image/*" capture="environment" onchange="addRoofPhotos(event,${i})" hidden>
          ${icon("camera",20)}<span>Kamera</span>
        </label>
        <label class="pick-btn">
          <input type="file" accept="image/*" multiple onchange="addRoofPhotos(event,${i})" hidden>
          ${icon("image",20)}<span>Galerie</span>
        </label>
      </div>` : `<div class="note" style="margin:0;">Alle ${ROOF_PHOTO_MAX} Plätze belegt.</div>`}
    </div>`;
}
""")
# Validierung: markiert jetzt Zeilen statt .field
rep('document.querySelectorAll(".field.invalid").forEach(el=>el.classList.remove("invalid"));',
    'document.querySelectorAll(".invalid").forEach(el=>el.classList.remove("invalid"));')

# ---------- 8) Nur Testversion: eigener Speicher, kein Backup/Upload, Beispieldaten ----------
if PREVIEW:
    rep('const IDB_NAME = "vorortcheck_db";', 'const IDB_NAME = "vorortcheck_design_preview";')
    rep("function scheduleBackup(delay){\n  if(!backupUser) return;", "function scheduleBackup(delay){\n  return;")
    rep("async function uploadPhotoForLink(dataUrl){\n  if(!supabaseClient) return null;", "async function uploadPhotoForLink(dataUrl){\n  return null;")
    rep("function backupNeedsAttention(){\n  return", "function backupNeedsAttention(){\n  return false &&")
    rep("""  screen = "home";
  render();
  enforceFinishedLimit();""", """  if(!records.length && !loadFailed){ records = seedDemoRecords(); await saveRecords(); }
  screen = "home";
  render();
  enforceFinishedLimit();""")
    rep("/* ---------- Boot ---------- */", r"""/* ---------- Beispieldaten (nur Testversion) ---------- */
function demoPhoto(label, hueA, hueB){
  const c = document.createElement("canvas"); c.width = 1200; c.height = 900;
  const x = c.getContext("2d");
  const g = x.createLinearGradient(0, 0, 1200, 900);
  g.addColorStop(0, `hsl(${hueA} 35% 62%)`); g.addColorStop(1, `hsl(${hueB} 40% 32%)`);
  x.fillStyle = g; x.fillRect(0, 0, 1200, 900);
  x.fillStyle = "rgba(255,255,255,.9)"; x.font = "600 64px -apple-system, Helvetica, Arial"; x.fillText(label, 70, 820);
  x.font = "500 34px -apple-system, Helvetica, Arial"; x.fillStyle = "rgba(255,255,255,.7)"; x.fillText("Beispielfoto", 72, 140);
  return c.toDataURL("image/jpeg", 0.8);
}
function seedDemoRecords(){
  const mk = (vor, nach, anrede, str, nr, plz, ort, status, daysAgo, fill)=>{
    const d = freshState();
    Object.assign(d.kunde, { anrede, vorname: vor, nachname: nach, telefon: "0171 0000000", email: (vor || nach).toLowerCase() + "@beispiel.de" });
    Object.assign(d.standort, { strasse: str, nr, plz, ort });
    const day = new Date(Date.now() - daysAgo * 864e5);
    d.grunddaten.besichtigtAm = day.toISOString().slice(0,10);
    fill(d);
    return { id: d.meta.id, status, updatedAt: Date.now() - daysAgo * 864e5, data: d };
  };
  return [
    mk("Lena", "Hoffmann", "Frau", "Lindenallee", "12", "14641", "Nauen", "draft", 0, d=>{
      d.gebaeude.kategorie = "Einfamilienhaus";
      d.elektro.stromverbrauch = "4200"; d.elektro.grossverbraucher.eauto = "2500";
      Object.assign(d.daecher[0], { dachart: "Schrägdach", dachaufbau: "Ziegel", regenrinne: "vorhanden", regenrinneMaterial: "Zink", dcLeitungsweg: "alter Kaminschacht", traufe8: "unter 5m" });
      d.daecher[0].fotos[0] = demoPhoto("Dach Süd", 20, 200); d.daecher[0].fotos[1] = demoPhoto("Dach Ost", 35, 210); d.daecher[0].drohnenFotos[0] = demoPhoto("Drohne", 190, 230);
      d.daecher[0].dcFotos[0] = demoPhoto("Kaminschacht", 25, 15);
      d.elektro.zaehler.neuerZaehlerschrank = "muss geprüft werden";
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 170, 200);
    }),
    mk("Jonas", "Weber", "Herr", "Am Mühlenberg", "3", "14712", "Rathenow", "fertig", 2, d=>{
      d.gebaeude.kategorie = "Reihenhaus"; d.elektro.stromverbrauch = "3600";
      Object.assign(d.daecher[0], { dachart: "Flachdach", dachaufbau: "Bitumen", dcLeitungsweg: "Fassade im Alurohr", traufe8: "über 5m", geruest: "Ja" });
      d.daecher[0].fotos[0] = demoPhoto("Flachdach", 200, 220);
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 160, 190);
      d.elektro.hausanschluss.typ = "HA-Innen"; d.elektro.messkonzept = "keine Änderung";
    }),
    mk("", "Familie Schulz", "Familie", "Birkenweg", "7a", "14612", "Falkensee", "fertig", 6, d=>{
      d.gebaeude.kategorie = "Einfamilienhaus"; d.elektro.stromverbrauch = "5100"; d.elektro.grossverbraucher.waermepumpe = "3800";
      Object.assign(d.daecher[0], { dachart: "Schrägdach", dachaufbau: "Ziegel", dcLeitungsweg: "vorh. Leerrohr", traufe8: "unter 5m", geruest: "Fallschutz reicht" });
      d.daecher[0].fotos[0] = demoPhoto("Dach", 15, 205);
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 150, 200);
      d.elektro.hausanschluss.typ = "HA-Außen"; d.elektro.messkonzept = "Kaskade";
    })
  ];
}

/* ---------- Boot ---------- */""")

open(dst, "w", encoding="utf-8").write(s)
print("geschrieben:", dst, len(s)//1024, "KB", "(Testversion)" if PREVIEW else "")
