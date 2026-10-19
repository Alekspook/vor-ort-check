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
      </div>
      <div class="note" style="margin:8px 2px 0;">In der Galerie kannst du mehrere Fotos auf einmal auswählen.</div>` : `<div class="note" style="margin:0;">Alle ${ROOF_PHOTO_MAX} Plätze belegt.</div>`}
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
      Object.assign(d.daecher[0], { dachart: "Schrägdach", dachaufbau: "Ziegel", regenrinne: "Ja", regenrinneMaterial: "Zink", dcLeitungsweg: "Kaminschacht", traufhoehe: "4,73" });
      d.daecher[0].fotos[0] = demoPhoto("Dach Süd", 20, 200); d.daecher[0].fotos[1] = demoPhoto("Dach Ost", 35, 210); d.daecher[0].drohnenFotos[0] = demoPhoto("Drohne", 190, 230);
      d.daecher[0].dcFotos[0] = demoPhoto("Kaminschacht", 25, 15);
      d.daecher[0].ziegelFoto = demoPhoto("Ziegel mit Zollstock", 18, 30);
      d.elektro.zaehler.neuerZaehlerschrank = "Prüfen";
      d.abschluss.bemerkung = "Kundin möchte Speicher im Keller, Termin für Angebot nächste Woche.";
      d.abschluss.angebot = ["Tiefenerder", "Wallbox"];
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 170, 200);
    }),
    mk("Jonas", "Weber", "Herr", "Am Mühlenberg", "3", "14712", "Rathenow", "fertig", 2, d=>{
      d.gebaeude.kategorie = "Reihenhaus"; d.elektro.stromverbrauch = "3600";
      Object.assign(d.daecher[0], { dachart: "Flachdach", dachaufbau: "Bitumen", dcLeitungsweg: "Alurohr Fassade", traufhoehe: "6,10", geruest: "Ja" });
      d.daecher[0].fotos[0] = demoPhoto("Flachdach", 200, 220);
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 160, 190);
      d.elektro.hausanschluss.typ = "Innen"; d.elektro.messkonzept = "Keine Änderung";
    }),
    mk("", "Familie Schulz", "Familie", "Birkenweg", "7a", "14612", "Falkensee", "fertig", 6, d=>{
      d.gebaeude.kategorie = "Einfamilienhaus"; d.elektro.stromverbrauch = "5100"; d.elektro.grossverbraucher.waermepumpe = "3800";
      Object.assign(d.daecher[0], { dachart: "Schrägdach", dachaufbau: "Ziegel", dcLeitungsweg: "Leerrohr", traufhoehe: "3,90", geruest: "Fallschutz reicht" });
      d.daecher[0].fotos[0] = demoPhoto("Dach", 15, 205);
      d.elektro.zaehler.uebersicht = demoPhoto("Zählerschrank", 150, 200);
      d.elektro.hausanschluss.typ = "Außen"; d.elektro.messkonzept = "Kaskade";
    })
  ];
}

/* ---------- Boot ---------- */""")


# ---------- 9) Inhaltliche Änderungen (Begriffe, Traufhöhe in m, Raumübersicht, Tiefenerder, EcoFlow-Turm, Bemerkungen, Angebot) ----------
rep("""    traufe8:"", geruest:"", geruestBemerkung:\"\"""", """    traufe8:"", traufhoehe:"", geruest:"", geruestBemerkung:\"\"""")
rep("zaehler:{ uebersicht:null, ohneAbdeckungen:null,", "zaehler:{ raumuebersicht:null, uebersicht:null, ohneAbdeckungen:null,")
rep("""    zusatzbilder:[],
    email:{""", """    zusatzbilder:[],
    abschluss:{ bemerkung:"", angebot:[] },
    email:{""")
rep("let S = null;\n", r"""let S = null;

/* Alte Antworten auf die neuen, kürzeren Begriffe umstellen (beim Laden, nicht gespeichert
   bis zur nächsten Änderung). Felder, die es nicht mehr gibt, bleiben in den Daten erhalten. */
const VALUE_RENAMES = {
  janein: { "vorhanden":"Ja", "nicht vorhanden":"Nein" },
  erforderlich: { "erforderlich":"Ja", "nicht erforderlich":"Nein" },
  kabelweg: { "vorh. Leerrohr":"Leerrohr", "alter Kaminschacht":"Kaminschacht", "Fassade im Alurohr":"Alurohr Fassade" },
  geruest: { "muss geprüft werden":"Prüfen", "Kunde stellt Gerüst":"Stellt Kunde" },
  zaehlerschrank: { "Erforderlich":"Ja", "nicht erforderlich":"Nein", "muss geprüft werden":"Prüfen" },
  ha: { "HA-Innen":"Innen", "HA-Außen":"Außen", "kein eigener HA vorhanden":"Kein eigener" },
  wp: { "vorhanden":"Vorhanden", "nicht vorhanden":"Keine", "geplant":"Geplant" },
  wallbox: { "vorhanden":"Vorhanden", "nicht vorhanden":"Keine", "gewünscht":"Gewünscht" },
  messkonzept: { "keine Änderung":"Keine Änderung" }
};
function normalizeRecordData(d){
  if(!d || typeof d !== "object") return d;
  const map = (obj, key, table)=>{ if(obj && typeof obj[key] === "string" && Object.prototype.hasOwnProperty.call(table, obj[key])) obj[key] = table[obj[key]]; };
  const R = VALUE_RENAMES;
  (d.daecher || []).forEach(r=>{
    map(r, "dcLeitungsweg", R.kabelweg); map(r, "regenrinne", R.janein); map(r, "geruest", R.geruest);
    if(r.traufhoehe === undefined) r.traufhoehe = "";
  });
  const e = d.elektro || {}, z = e.zaehler || {}, h = e.hausanschluss || {};
  map(z, "neuerZaehlerschrank", R.zaehlerschrank); map(z, "weitereUV", R.janein); map(z, "neueUV", R.erforderlich); map(z, "wanddurchbrueche", R.erforderlich);
  if(e.zaehler && z.raumuebersicht === undefined) z.raumuebersicht = null;
  map(h, "typ", R.ha); map(h, "potenzialausgleich", R.janein); map(h, "fundamenterder", R.janein);
  map(e, "waermepumpe", R.wp); map(e, "wallbox", R.wallbox); map(e, "messkonzept", R.messkonzept);
  if(!d.abschluss || typeof d.abschluss !== "object") d.abschluss = { bemerkung:"", angebot:[] };
  if(!Array.isArray(d.abschluss.angebot)) d.abschluss.angebot = [];
  if(typeof d.abschluss.bemerkung !== "string") d.abschluss.bemerkung = "";
  d.abschluss.angebot = d.abschluss.angebot.map(v=> v === "Unterverteilung" ? "UV" : v);
  // Notstrom ist keine Hardware-Option mehr, sondern eine Angebots-Position.
  if(e.komponenten && e.komponenten.notstrom){
    if(!d.abschluss.angebot.includes("Notstrom")) d.abschluss.angebot.push("Notstrom");
    e.komponenten.notstrom = false;
  }
  return d;
}
""")
rep("const r = { id: row.id, status: row.status, updatedAt: row.updatedAt, data: row.data };",
    "const r = { id: row.id, status: row.status, updatedAt: row.updatedAt, data: normalizeRecordData(row.data) };")
rep("const data = await unpackPhotos(row.data);", "const data = normalizeRecordData(await unpackPhotos(row.data));")
rep("  records = legacy;\n", "  records = legacy;\n  legacy.forEach(r=> normalizeRecordData(r.data));\n")
rep("r.dcLeitungsweg && r.traufe8 && r.geruest", "r.dcLeitungsweg && (r.traufhoehe || r.traufe8) && r.geruest")

# Neue Feld-Bausteine
rep("function verbrauchTotal(){", r"""function meterField(label, path, legacy){
  const val = getPath(S, path) ?? "";
  return `
    <label class="row row-input" id="${domId(path)}">
      <span class="row-label">${label}</span>
      <span class="input-unit"><input type="text" inputmode="decimal" value="${escapeAttr(val)}" placeholder="${legacy ? "bisher: " + escapeAttr(legacy) : "z. B. 4,73"}"
        oninput="setPath(S,'${path}', this.value); scheduleAutosave();"><em>m</em></span>
    </label>`;
}
function toggleInList(path, value, on){
  const list = (getPath(S, path) || []).filter(v=> v !== value);
  if(on) list.push(value);
  setPath(S, path, list);
  scheduleAutosave();
  render();
}
function multiChipField(label, path, options){
  const vals = getPath(S, path) || [];
  return `
    <div class="row row-choice" id="${domId(path)}" aria-label="${escapeAttr(label)}">
      <span class="row-label">${label}</span>
      <div class="chips">
        ${options.map(o=>`
          <label class="chip ${vals.includes(o) ? "checked" : ""}">
            <input type="checkbox" ${vals.includes(o) ? "checked" : ""} onchange="toggleInList('${path}','${escapeAttr(o)}', this.checked)">
            <span>${o}</span>
          </label>`).join("")}
      </div>
    </div>`;
}
// Einzel-Bemerkungen gibt es nicht mehr; alte Inhalte bleiben sichtbar und bearbeitbar.
function legacyNote(label, path){ return getPath(S, path) ? textareaField(label + " (alt)", path) : ""; }
const ANGEBOT_POSITIONEN = ["Tiefenerder", "Notstrom", "Wallbox", "Neuer Zählerschrank", "UV", "Gerüst"];
function verbrauchTotal(){""")

# Formular: Dach
rep("""      ${radioField("Regenrinne", `daecher.${i}.regenrinne`, ["vorhanden","nicht vorhanden"])}
      ${d.regenrinne === "vorhanden" ? """, """      ${radioField("Regenrinne vorhanden?", `daecher.${i}.regenrinne`, ["Ja","Nein"])}
      ${d.regenrinne === "Ja" ? """)
rep("""      ${textareaField("Bemerkungen", `daecher.${i}.bemerkung1`)}
      ${roofPhotoGrid(i)}""", """      ${legacyNote("Bemerkungen", `daecher.${i}.bemerkung1`)}
      ${roofPhotoGrid(i)}""")
rep("""["vorh. Leerrohr","alter Kaminschacht","Fassade im Alurohr","Sonstige"]""", """["Leerrohr","Kaminschacht","Alurohr Fassade","Sonstige"]""")
rep("""radioField("Wanddurchbrüche notwendig", `daecher.${i}.wanddurchbrueche`""", """radioField("Wanddurchbrüche nötig?", `daecher.${i}.wanddurchbrueche`""")
rep("""      ${radioField("Traufhöhe", `daecher.${i}.traufe8`, ["über 5m","unter 5m"])}
      ${radioField("Gerüst erforderlich", `daecher.${i}.geruest`, ["Ja","Nein","Fallschutz reicht","muss geprüft werden","Kunde stellt Gerüst"])}
      ${textareaField("Bemerkungen Gerüst", `daecher.${i}.geruestBemerkung`)}""", """      ${meterField("Traufhöhe", `daecher.${i}.traufhoehe`, d.traufe8)}
      ${radioField("Gerüst nötig?", `daecher.${i}.geruest`, ["Ja","Nein","Fallschutz reicht","Prüfen","Stellt Kunde"])}
      ${legacyNote("Bemerkungen Gerüst", `daecher.${i}.geruestBemerkung`)}""")
# Formular: Zählerschrank
rep("""${radioField("Neuer Zählerschrank", "elektro.zaehler.neuerZaehlerschrank", ["Erforderlich","nicht erforderlich","muss geprüft werden"])}""",
    """${radioField("Neuer Zählerschrank nötig?", "elektro.zaehler.neuerZaehlerschrank", ["Ja","Nein","Prüfen"])}""")
rep("""        ${photoSlot("elektro.zaehler.uebersicht","Übersicht", true)}
        ${photoSlot("elektro.zaehler.ohneAbdeckungen","Ohne Abdeckungen", false)}""", """        ${photoSlot("elektro.zaehler.raumuebersicht","Raumübersicht", false)}
        ${photoSlot("elektro.zaehler.uebersicht","Übersicht Zählerschrank", true)}
        ${z.ohneAbdeckungen ? photoSlot("elektro.zaehler.ohneAbdeckungen","Ohne Abdeckungen (alt)", false) : ""}""")
rep("""        ${radioField("Weitere Unterverteilungen", "elektro.zaehler.weitereUV", ["vorhanden","nicht vorhanden"])}
        ${z.weitereUV === "vorhanden" ? """, """        ${radioField("Weitere Unterverteilung vorhanden?", "elektro.zaehler.weitereUV", ["Ja","Nein"])}
        ${z.weitereUV === "Ja" ? """)
rep("""        ${radioField("Neue Unterverteilung", "elektro.zaehler.neueUV", ["erforderlich","nicht erforderlich"])}
        ${z.neueUV === "erforderlich" ? """, """        ${radioField("Neue Unterverteilung nötig?", "elektro.zaehler.neueUV", ["Ja","Nein"])}
        ${z.neueUV === "Ja" ? """)
rep("""        ${radioField("Wanddurchbrüche", "elektro.zaehler.wanddurchbrueche", ["erforderlich","nicht erforderlich"])}
        ${z.wanddurchbrueche === "erforderlich" ? """, """        ${radioField("Wanddurchbrüche nötig?", "elektro.zaehler.wanddurchbrueche", ["Ja","Nein"])}
        ${z.wanddurchbrueche === "Ja" ? """)
# Formular: Hausanschluss
rep("""        ${radioField("Hausanschluss", "elektro.hausanschluss.typ", ["HA-Innen","HA-Außen","kein eigener HA vorhanden"], {required:true})}""",
    """        ${radioField("Lage Hausanschluss", "elektro.hausanschluss.typ", ["Innen","Außen","Kein eigener"], {required:true})}""")
rep("""        ${radioField("Potenzialausgleichsschiene", "elektro.hausanschluss.potenzialausgleich", ["vorhanden","nicht vorhanden"])}
        ${h.potenzialausgleich === "vorhanden" ? """, """        ${radioField("Potenzialausgleichsschiene vorhanden?", "elektro.hausanschluss.potenzialausgleich", ["Ja","Nein"])}
        ${h.potenzialausgleich === "Ja" ? """)
rep("""        ${radioField("Fundamenterder", "elektro.hausanschluss.fundamenterder", ["vorhanden","nicht vorhanden"])}
        ${h.fundamenterder === "vorhanden" ? `<div class="conditional">${photoSlot("elektro.hausanschluss.fundamenterderFoto","Foto Fundamenterder", false)}</div>` : ""}
        ${textareaField("Bemerkungen", "elektro.hausanschluss.bemerkung")}""", """        ${radioField("Tiefenerder vorhanden?", "elektro.hausanschluss.fundamenterder", ["Ja","Nein"])}
        ${h.fundamenterder === "Ja" ? `<div class="conditional">${photoSlot("elektro.hausanschluss.fundamenterderFoto","Foto Tiefenerder", false)}</div>` : ""}
        ${legacyNote("Bemerkungen", "elektro.hausanschluss.bemerkung")}""")
# Formular: Wärmepumpe & Wallbox
rep("""        ${radioField("Wärmepumpe", "elektro.waermepumpe", ["vorhanden","nicht vorhanden","geplant"])}
        ${e.waermepumpe === "vorhanden" ? """, """        ${radioField("Wärmepumpe", "elektro.waermepumpe", ["Vorhanden","Keine","Geplant"])}
        ${e.waermepumpe === "Vorhanden" ? """)
rep("""        ${radioField("Wallbox", "elektro.wallbox", ["vorhanden","nicht vorhanden","gewünscht"])}
        ${e.wallbox === "vorhanden" ? """, """        ${radioField("Wallbox", "elektro.wallbox", ["Vorhanden","Keine","Gewünscht"])}
        ${e.wallbox === "Vorhanden" ? """)
rep("""        ${e.wallbox === "gewünscht" ? """, """        ${e.wallbox === "Gewünscht" ? """)
rep("""radioField("Sind Durchbrüche notwendig?", "elektro.wallboxDurchbrueche\"""", """radioField("Durchbrüche nötig?", "elektro.wallboxDurchbrueche\"""")
# Formular: Hardware (EcoFlow OCEAN 2 = Wechselrichter + Speicher in einem Turm)
rep("""        ${checkField("Wechselrichter", "elektro.komponenten.hybrid")}
        ${e.komponenten.hybrid ? `<div class="conditional">${photoAnnotateField("elektro.fotoWechselrichter","Montageort Wechselrichter", false)}</div>` : ""}
        ${checkField("Batteriespeicher", "elektro.komponenten.batterie")}
        ${e.komponenten.batterie ? `<div class="conditional">${photoAnnotateField("elektro.fotoSpeicher","Montageort Batteriespeicher", false)}</div>` : ""}
        ${checkField("Notstrom", "elektro.komponenten.notstrom")}
        ${textareaField("Bemerkung", "elektro.montageortBemerkung")}""", """        ${checkField("Wechselrichter + Speicher", "elektro.komponenten.hybrid")}
        ${e.komponenten.hybrid ? `<div class="conditional">${photoAnnotateField("elektro.fotoWechselrichter","Montageort Wechselrichter + Speicher", false)}</div>` : ""}
        ${e.komponenten.batterie || e.fotoSpeicher ? checkField("Batteriespeicher separat (alt)", "elektro.komponenten.batterie") : ""}
        ${e.komponenten.batterie && e.fotoSpeicher !== undefined ? `<div class="conditional">${photoAnnotateField("elektro.fotoSpeicher","Montageort Batteriespeicher (alt)", false)}</div>` : ""}
        ${legacyNote("Bemerkung", "elektro.montageortBemerkung")}""")
rep("""["keine Änderung","Zusammenlegung","Kaskade"]""", """["Keine Änderung","Zusammenlegung","Kaskade"]""")
# Formular: Abschluss mit allgemeiner Bemerkung und Angebots-Positionen
rep("""    sec(8, "abschluss", "Weitere Fotos", `
      ${S.zusatzbilder.length ? `<div class="group">${S.zusatzbilder.map((f,i)=> photoSlot(`zusatzbilder.${i}`, `Bild ${i+1}`, false)).join("")}</div>` : ""}
      <button class="ghost-btn" onclick="addExtraPhoto()">${icon("plus",18)} Foto hinzufügen</button>""", """    sec(8, "abschluss", "Abschluss", `
      <div class="group">
        ${textareaField("Allgemeine Bemerkung", "abschluss.bemerkung", {placeholder:"Alle Notizen zu diesem Termin …"})}
      </div>
      <div class="group-label">Im Angebot berücksichtigen</div>
      <div class="group">
        ${multiChipField("Positionen", "abschluss.angebot", ANGEBOT_POSITIONEN)}
      </div>
      <div class="group-label">Weitere Fotos</div>
      ${S.zusatzbilder.length ? `<div class="group">${S.zusatzbilder.map((f,i)=> photoSlot(`zusatzbilder.${i}`, `Bild ${i+1}`, false)).join("")}</div>` : ""}
      <button class="ghost-btn" onclick="addExtraPhoto()">${icon("plus",18)} Foto hinzufügen</button>""")

# PDF
rep("""      ["Traufhöhe", r.traufe8],""", """      ["Traufhöhe", r.traufhoehe ? String(r.traufhoehe).replace(".", ",") + " m" : r.traufe8],""")
rep("""    {label:"Übersicht", url:d.elektro.zaehler.uebersicht},
    {label:"Ohne Abdeckungen\"""", """    {label:"Raumübersicht", url:d.elektro.zaehler.raumuebersicht},
    {label:"Übersicht", url:d.elektro.zaehler.uebersicht},
    {label:"Ohne Abdeckungen\"""")
rep("""  kv("Fundamenterder", d.elektro.hausanschluss.fundamenterder);
  await photoGrid([{label:"Fundamenterder", url:d.elektro.hausanschluss.fundamenterderFoto}]);""", """  kv("Tiefenerder", d.elektro.hausanschluss.fundamenterder);
  await photoGrid([{label:"Tiefenerder", url:d.elektro.hausanschluss.fundamenterderFoto}]);""")
rep('const KOMP_LABELS = { hybrid:"Wechselrichter", batterie:"Batteriespeicher", notstrom:"Notstrom" };',
    'const KOMP_LABELS = { hybrid:"Wechselrichter + Speicher", batterie:"Batteriespeicher", notstrom:"Notstrom" };')
rep("""    {label:"Montageort Wechselrichter", url:d.elektro.fotoWechselrichter},""", """    {label:"Montageort Wechselrichter + Speicher", url:d.elektro.fotoWechselrichter},""")
rep("""  /* Weitere Fotos */
  const extra =""", """  /* Abschluss: allgemeine Bemerkung und Positionen fürs Angebot */
  const angebot = (d.abschluss && d.abschluss.angebot || []).join(", ");
  if(d.abschluss && (d.abschluss.bemerkung || angebot)){
    sectionHeader("ABSCHLUSS", PDF_BLUE_DEEP);
    kvGroup([["Im Angebot berücksichtigen", angebot], ["Bemerkung", d.abschluss.bemerkung]]);
    y += 3;
  }

  /* Weitere Fotos */
  const extra =""")
# Foto-Export & Text-Zusammenfassung
rep("""  add("Zählerschrank Übersicht", z.uebersicht);""", """  add("Raumübersicht", z.raumuebersicht);
  add("Zählerschrank Übersicht", z.uebersicht);""")
rep("""  add("Fundamenterder", h.fundamenterderFoto);""", """  add("Tiefenerder", h.fundamenterderFoto);""")
rep("""  add("Montageort Wechselrichter", e.fotoWechselrichter);""", """  add("Montageort Wechselrichter Speicher", e.fotoWechselrichter);""")
rep("Traufhöhe: ${r.traufe8||\"-\"}", "Traufhöhe: ${r.traufhoehe ? r.traufhoehe + \" m\" : (r.traufe8||\"-\")}")
rep("| Fundamenterder: ${d.elektro.hausanschluss.fundamenterder", "| Tiefenerder: ${d.elektro.hausanschluss.fundamenterder")


# ---------- 10) Ziegelmaß-Foto (nur bei Eindeckung Ziegel) ----------
rep('traufe8:"", traufhoehe:"", geruest:"", geruestBemerkung:""', 'traufe8:"", traufhoehe:"", ziegelFoto:null, geruest:"", geruestBemerkung:""')
rep("    if(r.traufhoehe === undefined) r.traufhoehe = \"\";", "    if(r.traufhoehe === undefined) r.traufhoehe = \"\";\n    if(r.ziegelFoto === undefined) r.ziegelFoto = null;")
rep("""      ${radioField("Eindeckung", `daecher.${i}.dachaufbau`, ["Ziegel","Bitumen","Trapez","Blechfalz","Sonstige"])}""",
    """      ${radioField("Eindeckung", `daecher.${i}.dachaufbau`, ["Ziegel","Bitumen","Trapez","Blechfalz","Sonstige"])}
      ${d.dachaufbau === "Ziegel" || d.ziegelFoto ? `<div class="conditional">${photoSlot(`daecher.${i}.ziegelFoto`, "Ziegelmaß (Foto mit Zollstock)", false)}</div>` : ""}""")
rep("    const dachfotos = [", """    await photoGrid([{label:"Ziegelmaß", url:r.ziegelFoto}]);
    const dachfotos = [""")
rep("    (r.drohnenFotos||[]).forEach((u,k)=> add(`${p}Dachfoto ${k+6}`, u));",
    "    (r.drohnenFotos||[]).forEach((u,k)=> add(`${p}Dachfoto ${k+6}`, u));\n    add(`${p}Ziegelmaß`, r.ziegelFoto);")


# ---------- 11) Abstellort für die Module (Lieferung) ----------
rep('gebaeude:{ kategorie:"", besonderheiten:"" },', 'gebaeude:{ kategorie:"", besonderheiten:"", abstellortFoto:null },')
rep("  if(!d.abschluss || typeof d.abschluss !== \"object\")", "  if(d.gebaeude && d.gebaeude.abstellortFoto === undefined) d.gebaeude.abstellortFoto = null;\n  if(!d.abschluss || typeof d.abschluss !== \"object\")")
rep("""  return cards + `<button class="ghost-btn" onclick="addRoof()">${icon("plus",18)} Weiteres Dach</button>`;""",
    """  return cards + `<button class="ghost-btn" onclick="addRoof()">${icon("plus",18)} Weiteres Dach</button>
    <div class="group-label">Baustelle</div>
    <div class="group">
      ${photoSlot("gebaeude.abstellortFoto", "Abstellort Module (Lieferung)", false)}
    </div>`;""")
rep("""  for(let i=0;i<d.daecher.length;i++){
    await roofSection(PDF_BLUE_DEEP, `DACH ${i+1}`, d.daecher[i]);
  }
""", """  for(let i=0;i<d.daecher.length;i++){
    await roofSection(PDF_BLUE_DEEP, `DACH ${i+1}`, d.daecher[i]);
  }
  if(d.gebaeude && d.gebaeude.abstellortFoto){
    sectionHeader("BAUSTELLE", PDF_BLUE_DEEP);
    await photoGrid([{label:"Abstellort Module (Lieferung)", url:d.gebaeude.abstellortFoto}]);
    y += 3;
  }
""")
rep("  const e = d.elektro, z = e.zaehler, h = e.hausanschluss;\n", "  add(\"Abstellort Module\", d.gebaeude && d.gebaeude.abstellortFoto);\n  const e = d.elektro, z = e.zaehler, h = e.hausanschluss;\n")


# ---------- 12) Einzeichnen neu: unverzerrt, volle Auflösung, Rückgängig + Wiederholen, Farben, Stärken, Pfeil ----------
rep("""  undo: '<path d="M3 10h9a5 5 0 0 1 0 10h-4"/><path d="M3 10l4-4"/><path d="M3 10l4 4"/>',""",
    """  undo: '<path d="M3 10h9a5 5 0 0 1 0 10h-4"/><path d="M3 10l4-4"/><path d="M3 10l4 4"/>',
  redo: '<path d="M21 10h-9a5 5 0 0 0 0 10h4"/><path d="M21 10l-4-4"/><path d="M21 10l-4 4"/>',
  arrow: '<line x1="5" y1="19" x2="19" y2="5"/><path d="M10 5h9v9"/>',""")
rep_between("/* ---------- Skizze (Zeichnen auf Foto) ---------- */", "/* ---------- Adress-Autocomplete ---------- */", r"""/* ---------- Einzeichnen auf Fotos ----------
   Striche werden in Bild-Koordinaten gespeichert: Anzeige unverzerrt (eingepasst),
   Ergebnis in voller Auflösung (max. 2400 px) als JPEG. */
const SKETCH_COLORS = [["#E53935","Rot"], ["#FFC400","Gelb"], ["#2FA97C","Grün"], ["#FFFFFF","Weiß"]];
const SKETCH_SIZES = [["dünn",0.004], ["mittel",0.008], ["dick",0.014]];
let sk = null;
function openSketchModal(path, label){
  const src = getPath(S, path);
  if(!src) return;
  const modal = document.createElement("div");
  modal.className = "sketch-modal";
  modal.id = "sketchModal";
  modal.innerHTML = `
    <div class="sketch-modal-head"><h2>${escapeHtml(label || "Einzeichnen")}</h2></div>
    <div class="sketch-canvas-wrap"><canvas id="sketchCanvas"></canvas></div>
    <div class="sketch-toolbar">
      <div class="sk-group">
        <button type="button" class="sk-btn" id="skUndo" onclick="sketchUndo()" aria-label="Rückgängig" title="Rückgängig">${icon("undo",20)}</button>
        <button type="button" class="sk-btn" id="skRedo" onclick="sketchRedo()" aria-label="Wiederholen" title="Wiederholen">${icon("redo",20)}</button>
      </div>
      <div class="sk-group">
        <button type="button" class="sk-btn active" data-tool="pen" onclick="setSketchTool('pen')" aria-label="Stift" title="Stift">${icon("edit",20)}</button>
        <button type="button" class="sk-btn" data-tool="arrow" onclick="setSketchTool('arrow')" aria-label="Pfeil" title="Pfeil">${icon("arrow",20)}</button>
      </div>
      <div class="sk-group">${SKETCH_COLORS.map(([c,n],i)=>`<button type="button" class="sk-color ${i===0 ? "active" : ""}" style="--c:${c}" data-color="${c}" onclick="setSketchColor('${c}')" aria-label="Farbe ${n}" title="${n}"></button>`).join("")}</div>
      <div class="sk-group">${SKETCH_SIZES.map(([n,f],i)=>`<button type="button" class="sk-size ${i===1 ? "active" : ""}" data-size="${f}" onclick="setSketchSize(${f})" aria-label="Strichstärke ${n}" title="${n}"><i style="width:${5+i*5}px;height:${5+i*5}px"></i></button>`).join("")}</div>
    </div>
    <div class="sketch-footer">
      <button type="button" class="cancel" onclick="sketchCancel()">Abbrechen</button>
      <button type="button" class="save" onclick="saveSketch()">Fertig</button>
    </div>`;
  document.body.appendChild(modal);
  const canvas = document.getElementById("sketchCanvas");
  sk = { path, canvas, ctx: canvas.getContext("2d"), img: null, w: 0, h: 0, ops: [], redo: [], current: null, pointerId: null,
         tool: "pen", color: SKETCH_COLORS[0][0], size: SKETCH_SIZES[1][1], base: null, view: null };
  const img = new Image();
  img.onload = ()=>{
    if(!sk) return;
    sk.img = img;
    const k = Math.min(1, 2400 / Math.max(img.naturalWidth, img.naturalHeight));
    sk.w = Math.round(img.naturalWidth * k); sk.h = Math.round(img.naturalHeight * k);
    layoutSketch();
  };
  img.src = src;
  canvas.addEventListener("pointerdown", sketchDown);
  canvas.addEventListener("pointermove", sketchMove);
  canvas.addEventListener("pointerup", sketchUp);
  canvas.addEventListener("pointercancel", sketchUp);
  window.addEventListener("resize", layoutSketch);
  updateSketchButtons();
}
function layoutSketch(){
  if(!sk || !sk.img) return;
  const wrap = sk.canvas.parentElement;
  const dpr = window.devicePixelRatio || 1;
  const cw = wrap.clientWidth, ch = wrap.clientHeight;
  sk.canvas.width = Math.round(cw * dpr); sk.canvas.height = Math.round(ch * dpr);
  sk.canvas.style.width = cw + "px"; sk.canvas.style.height = ch + "px";
  const s = Math.min(cw / sk.w, ch / sk.h);
  sk.view = { dpr, s, ox: (cw - sk.w * s) / 2, oy: (ch - sk.h * s) / 2 };
  renderSketchBase();
  drawSketch();
}
function drawSketchOp(ctx, op){
  const lw = op.size * Math.max(sk.w, sk.h);
  ctx.strokeStyle = op.color; ctx.fillStyle = op.color; ctx.lineWidth = lw; ctx.lineCap = "round"; ctx.lineJoin = "round";
  if(op.type === "pen"){
    const p = op.points;
    ctx.beginPath(); ctx.moveTo(p[0].x, p[0].y);
    if(p.length === 1) ctx.lineTo(p[0].x + 0.01, p[0].y);
    for(let i = 1; i < p.length - 1; i++) ctx.quadraticCurveTo(p[i].x, p[i].y, (p[i].x + p[i+1].x) / 2, (p[i].y + p[i+1].y) / 2);
    if(p.length > 1) ctx.lineTo(p[p.length-1].x, p[p.length-1].y);
    ctx.stroke();
  }else{
    const a = op.a, b = op.b, ang = Math.atan2(b.y - a.y, b.x - a.x), head = lw * 4;
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x - Math.cos(ang) * head * 0.6, b.y - Math.sin(ang) * head * 0.6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - head * Math.cos(ang - 0.45), b.y - head * Math.sin(ang - 0.45));
    ctx.lineTo(b.x - head * Math.cos(ang + 0.45), b.y - head * Math.sin(ang + 0.45));
    ctx.closePath(); ctx.fill();
  }
}
// Foto + fertige Striche einmal vorzeichnen, damit beim Zeichnen nur der aktuelle Strich neu gemalt wird.
function renderSketchBase(){
  const v = sk.view;
  const base = document.createElement("canvas");
  base.width = sk.canvas.width; base.height = sk.canvas.height;
  const c = base.getContext("2d");
  c.fillStyle = "#111"; c.fillRect(0, 0, base.width, base.height);
  c.setTransform(v.dpr * v.s, 0, 0, v.dpr * v.s, v.dpr * v.ox, v.dpr * v.oy);
  c.drawImage(sk.img, 0, 0, sk.w, sk.h);
  sk.ops.forEach(op=> drawSketchOp(c, op));
  sk.base = base;
}
function drawSketch(){
  const v = sk.view, c = sk.ctx;
  c.setTransform(1, 0, 0, 1, 0, 0);
  c.drawImage(sk.base, 0, 0);
  if(sk.current){ c.setTransform(v.dpr * v.s, 0, 0, v.dpr * v.s, v.dpr * v.ox, v.dpr * v.oy); drawSketchOp(c, sk.current); }
}
function sketchPoint(e){
  const r = sk.canvas.getBoundingClientRect(), v = sk.view;
  return { x: (e.clientX - r.left - v.ox) / v.s, y: (e.clientY - r.top - v.oy) / v.s };
}
function sketchDown(e){
  if(!sk || !sk.view || sk.current) return;
  sk.pointerId = e.pointerId;
  try{ sk.canvas.setPointerCapture(e.pointerId); }catch(err){}
  const p = sketchPoint(e);
  sk.current = sk.tool === "arrow"
    ? { type: "arrow", color: sk.color, size: sk.size, a: p, b: p }
    : { type: "pen", color: sk.color, size: sk.size, points: [p] };
  drawSketch();
}
function sketchMove(e){
  if(!sk || !sk.current || e.pointerId !== sk.pointerId) return;
  const p = sketchPoint(e);
  if(sk.current.type === "arrow") sk.current.b = p; else sk.current.points.push(p);
  drawSketch();
}
function sketchUp(e){
  if(!sk || !sk.current || e.pointerId !== sk.pointerId) return;
  const op = sk.current;
  sk.current = null;
  const tooShort = op.type === "arrow" && Math.hypot(op.b.x - op.a.x, op.b.y - op.a.y) < Math.max(sk.w, sk.h) * 0.01;
  if(!tooShort){ sk.ops.push(op); sk.redo = []; }
  renderSketchBase(); drawSketch(); updateSketchButtons();
}
function sketchUndo(){ if(!sk || !sk.ops.length) return; sk.redo.push(sk.ops.pop()); renderSketchBase(); drawSketch(); updateSketchButtons(); }
function sketchRedo(){ if(!sk || !sk.redo.length) return; sk.ops.push(sk.redo.pop()); renderSketchBase(); drawSketch(); updateSketchButtons(); }
function updateSketchButtons(){
  const u = document.getElementById("skUndo"), r = document.getElementById("skRedo");
  if(u) u.disabled = !sk || !sk.ops.length;
  if(r) r.disabled = !sk || !sk.redo.length;
}
function setSketchTool(t){ if(!sk) return; sk.tool = t; document.querySelectorAll(".sk-btn[data-tool]").forEach(b=> b.classList.toggle("active", b.dataset.tool === t)); }
function setSketchColor(c){ if(!sk) return; sk.color = c; document.querySelectorAll(".sk-color").forEach(b=> b.classList.toggle("active", b.dataset.color === c)); }
function setSketchSize(f){ if(!sk) return; sk.size = f; document.querySelectorAll(".sk-size").forEach(b=> b.classList.toggle("active", Number(b.dataset.size) === f)); }
function closeSketchModal(){
  const m = document.getElementById("sketchModal");
  if(m) m.remove();
  window.removeEventListener("resize", layoutSketch);
  sk = null;
}
function sketchCancel(){
  if(sk && sk.ops.length) showConfirm("Eingezeichnetes verwerfen?", closeSketchModal, "Verwerfen");
  else closeSketchModal();
}
function saveSketch(){
  if(!sk || !sk.img || !sk.ops.length){ closeSketchModal(); return; }
  const out = document.createElement("canvas");
  out.width = sk.w; out.height = sk.h;
  const c = out.getContext("2d");
  c.drawImage(sk.img, 0, 0, sk.w, sk.h);
  sk.ops.forEach(op=> drawSketchOp(c, op));
  setPath(S, sk.path, out.toDataURL("image/jpeg", 0.9));
  closeSketchModal();
  clearTimeout(saveTimer);
  saveCurrentRecord();
  render();
}

""")


# ---------- 13) AR-Vorschau EcoFlow OCEAN 2 (AR Quick Look, Modelle in ar/) ----------
rep("""        ${e.komponenten.hybrid ? `<div class="conditional">${photoAnnotateField("elektro.fotoWechselrichter","Montageort Wechselrichter + Speicher", false)}</div>` : ""}""",
    """        ${e.komponenten.hybrid ? `<div class="conditional">${photoAnnotateField("elektro.fotoWechselrichter","Montageort Wechselrichter + Speicher", false)}${arPreviewRow()}</div>` : ""}""")
rep("function legacyNote(label, path){", r"""const AR_ICON = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 28 40"><rect x="2" y="1" width="24" height="14" rx="2" fill="#E8EBEC" stroke="#0D6B66" stroke-width="1.5"/><rect x="8" y="10" width="12" height="1.6" rx=".8" fill="#0D6B66"/><rect x="2" y="17" width="24" height="10" rx="2" fill="#E8EBEC" stroke="#0D6B66" stroke-width="1.5"/><rect x="2" y="29" width="24" height="10" rx="2" fill="#E8EBEC" stroke="#0D6B66" stroke-width="1.5"/></svg>');
// iPhone öffnet <a rel="ar"> mit einem <img> darin direkt in AR Quick Look (Kamera, Wand erkennen, Originalgröße).
function arPreviewRow(){
  return `
    <div class="row ar-row">
      <span class="row-label">An der Wand ansehen (AR)</span>
      <div class="ar-links">
        ${[1,2,3].map(n=>`<a rel="ar" class="ar-btn" href="ar/ocean2-${n}.usdz#allowsContentScaling=0"><img src="${AR_ICON}" alt="">${n} Batterie${n > 1 ? "n" : ""}<small>${n * 5} kWh</small></a>`).join("")}
      </div>
      <div class="note" style="margin-top:8px;">Kamera auf die Wand richten – der Turm erscheint in Originalgröße. Mit dem Auslöser ein Foto machen und es oben über „Galerie" einfügen. Vereinfachtes Modell, Maße laut EcoFlow.</div>
    </div>`;
}
function legacyNote(label, path){""")

open(dst, "w", encoding="utf-8").write(s)
print("geschrieben:", dst, len(s)//1024, "KB", "(Testversion)" if PREVIEW else "")
