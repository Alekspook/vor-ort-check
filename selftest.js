/* Vor-Ort-Check – Selbsttest für die PDF-/Upload-/Teilen-Kette
 *
 * Wird NICHT von der App geladen (kein <script> in index.html) — ist nur
 * ein Entwickler-Werkzeug. Vor jeder Änderung an buildPDF, uploadPhotoForLink,
 * finishRecord, preparePDF oder sharePDF: Code in der Browser-Konsole der
 * laufenden App einfügen und ausführen. Prüft genau die drei Fehler, die
 * in der Vergangenheit wiederholt aufgetreten sind, damit sie nicht durch
 * eine spätere Änderung an anderer Stelle erneut einschleichen:
 *
 *  1) Fotos bekommen beim PDF-Bau einen klickbaren Link (Supabase-Upload läuft)
 *  2) navigator.share() bekommt eine echte Datei (nie eine URL/Text) —
 *     sonst kann beim Fallback der echte Name über eine blob:-URL durchsickern
 *  3) "Abschließen" verschiebt den Eintrag SOFORT nach Abgeschlossen,
 *     unabhängig davon, wie lange der PDF-Bau/Foto-Upload braucht
 *  4) Cloud-Backup: Fotos werden als Link gesichert und kommen beim
 *     Wiederherstellen bitgenau zurück
 *  5) Ein von iOS abgebrochener Speichervorgang wird erkannt und gemeldet,
 *     statt still zu hängen (so gingen bei Carolin Day die Eingaben verloren)
 *
 * Ergebnis erscheint in der Konsole. Bei einem ❌ nicht deployen.
 */
async function selftest(){
  const results = [];
  function check(name, ok, detail){ results.push({name, ok, detail}); }

  const testImg = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAADAAQDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAj/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=";

  // --- Test 1: Foto-Upload / klickbarer Link im PDF ---
  try{
    let d = freshState();
    d.kunde.vorname="Selftest"; d.kunde.nachname="Check";
    d.grunddaten.besichtigtVon="Alexander Bajric"; d.grunddaten.besichtigtAm="2026-01-01";
    d.daecher[0].dachart="Satteldach";
    d.daecher[0].fotos[0]=testImg;
    const doc = await buildPDF(d);
    const bin = atob(doc.output('datauristring').split('base64,')[1]);
    const hasLink = bin.indexOf('/URI (https://rpfhadlvtudzxscvaikz') !== -1;
    check("Foto bekommt klickbaren Link im PDF", hasLink, hasLink ? "" : "Kein Supabase-Link im PDF gefunden — Upload/Bucket prüfen");
  }catch(e){ check("Foto bekommt klickbaren Link im PDF", false, e.message); }

  // --- Test 2: navigator.share() bekommt Datei, keine URL ---
  try{
    const realShare = navigator.share, realCanShare = navigator.canShare;
    let sharedWith = null;
    navigator.canShare = ()=>true;
    navigator.share = async (opts)=>{ sharedWith = opts; };
    pdfCache["__selftest"] = { status:"ready", blob: new Blob(["x"],{type:"application/pdf"}), filename:"selftest.pdf" };
    sharePDF("__selftest");
    await new Promise(r=>setTimeout(r,50));
    const hasFiles = sharedWith && Array.isArray(sharedWith.files);
    const hasUrl = sharedWith && ('url' in sharedWith);
    check("Teilen übergibt echte Datei, keine URL", !!hasFiles && !hasUrl,
      !sharedWith ? "navigator.share wurde gar nicht aufgerufen" : hasUrl ? "navigator.share bekam eine URL statt einer Datei!" : "");
    delete pdfCache["__selftest"];
    navigator.share = realShare; navigator.canShare = realCanShare;
  }catch(e){ check("Teilen übergibt echte Datei, keine URL", false, e.message); }

  // --- Test 3: Abschließen verschiebt sofort, unabhängig vom PDF-Bau ---
  try{
    startNewRecord();
    S.kunde.nachname="SelftestFinish"; S.kunde.email="x@x.de";
    S.standort.strasse="S"; S.standort.nr="1"; S.standort.plz="11111"; S.standort.ort="O";
    S.gebaeude.kategorie="Einfamilienhaus";
    S.elektro.hausanschluss.typ="Kabel";
    S.elektro.messkonzept="keine Änderung";
    S.daecher[0].dachart="Satteldach";
    const id = currentRecordId;
    await finishRecord();
    const rec = records.find(r=>r.id===id);
    check("Abschließen verschiebt sofort nach Abgeschlossen", !!rec && rec.status==="fertig" && screen==="fertig",
      rec ? `status=${rec.status}, screen=${screen}` : "Datensatz nicht gefunden");
    records = records.filter(r=>r.id!==id);
    delete pdfCache[id];
  }catch(e){ check("Abschließen verschiebt sofort nach Abgeschlossen", false, e.message); }

  // --- Test 4: Backup-Verpackung – Fotos kommen beim Wiederherstellen identisch zurück ---
  try{
    const c = document.createElement("canvas"); c.width = 40; c.height = 30;
    const ctx = c.getContext("2d"); ctx.fillStyle = "#" + Math.floor(Math.random()*0xffffff).toString(16).padStart(6,"0"); ctx.fillRect(0,0,40,30);
    const img = c.toDataURL("image/jpeg", 0.9);
    const packed = await packPhotos({ a:{ b:[img, null, "text"] } });
    const noRaw = !JSON.stringify(packed).includes("data:image");
    photoUrlPromises.clear();
    const unpacked = await unpackPhotos(packed);
    const same = unpacked.a.b[0] === img && unpacked.a.b[1] === null && unpacked.a.b[2] === "text";
    check("Backup: Fotos werden verlinkt und kommen identisch zurück", noRaw && same,
      !noRaw ? "Rohfoto im Backup-Datensatz gelandet" : !same ? "Foto nach Wiederherstellen nicht identisch" : "");
  }catch(e){ check("Backup: Fotos werden verlinkt und kommen identisch zurück", false, e.message); }

  // --- Test 5: Speichern – Abbruch durch iOS wird erkannt statt still zu hängen ---
  try{
    const realAlert = window.alert, realTx = IDBDatabase.prototype.transaction;
    window.alert = ()=>{};
    const tmp = { id: "__selftest_save", status: "draft", updatedAt: Date.now(), data: freshState() };
    records.push(tmp);
    IDBDatabase.prototype.transaction = function(names, mode){
      const tx = realTx.apply(this, arguments);
      if(mode === "readwrite") setTimeout(()=>{ try{ tx.abort(); }catch(e){} }, 0);
      return tx;
    };
    const okDuringAbort = await withTimeout(saveRecords(), 40000, "saveRecords hängt");
    IDBDatabase.prototype.transaction = realTx;
    const okAfter = await saveRecords();
    const row = await idbRequest(REC_STORE, "readonly", s=> s.get(tmp.id));
    records = records.filter(r=> r !== tmp);
    await saveRecords();
    window.alert = realAlert;
    check("Speichern: Abbruch wird erkannt, danach wird wieder gespeichert", okDuringAbort === false && okAfter === true && !!row,
      okDuringAbort !== false ? "Abbruch wurde NICHT erkannt" : !okAfter || !row ? "Nach dem Abbruch wird nicht wieder gespeichert" : "");
  }catch(e){ check("Speichern: Abbruch wird erkannt, danach wird wieder gespeichert", false, e.message); }

  // --- Test 6: "Alle Fotos aufs Handy" – jedes Foto kommt mit, als echte Dateien ---
  try{
    const d = freshState();
    d.kunde.vorname = "Jörg"; d.kunde.nachname = "Müller";
    const slots = [];
    const put = (obj, key)=>{ obj[key] = testImg; slots.push(1); };
    [0,1,2,3,4].forEach(k=> put(d.daecher[0].fotos, k));
    [0,1,2].forEach(k=> put(d.daecher[0].drohnenFotos, k));
    [0,1].forEach(k=> put(d.daecher[0].dcFotos, k));
    [0,1,2].forEach(k=> put(d.daecher[0].wanddurchbruecheFotos, k));
    Object.keys(d.elektro.zaehler).filter(k=> d.elektro.zaehler[k] === null).forEach(k=> put(d.elektro.zaehler, k));
    Object.keys(d.elektro.hausanschluss).filter(k=> d.elektro.hausanschluss[k] === null).forEach(k=> put(d.elektro.hausanschluss, k));
    Object.keys(d.elektro).filter(k=> d.elektro[k] === null).forEach(k=> put(d.elektro, k));
    d.zusatzbilder = [testImg, testImg]; slots.push(1, 1);
    const list = recordPhotoList(d);
    const unlabeled = list.filter(p=> p.label === "Foto").length;
    const realShare = navigator.share, realCanShare = navigator.canShare;
    let shared = null;
    navigator.canShare = ()=> true;
    navigator.share = async (opts)=>{ shared = opts; };
    const realS = S; S = d;
    downloadAllPhotos("current");
    S = realS;
    await new Promise(r=> setTimeout(r, 50));
    navigator.share = realShare; navigator.canShare = realCanShare;
    const files = shared && shared.files || [];
    const namesOk = files.length && files.every(f=> /^Joerg-Mueller-\d\d-[A-Za-z0-9-]+\.(jpg|png)$/.test(f.name) && f.size > 0);
    check("Alle Fotos: jedes Foto als Datei im Teilen-Menü", list.length === slots.length && unlabeled === 0 && files.length === slots.length && namesOk && !("url" in shared),
      list.length !== slots.length ? `${list.length} von ${slots.length} Fotos erfasst` : unlabeled ? `${unlabeled} Foto(s) ohne Bezeichnung` : !namesOk ? "Dateinamen/Dateien fehlerhaft" : "");
  }catch(e){ check("Alle Fotos: jedes Foto als Datei im Teilen-Menü", false, e.message); }

  // --- Test 7: Aufnahmedatum der Foto-Kopien wird auf "jetzt" gesetzt (Sortierung in der Fotos-App) ---
  try{
    const enc = s=> Array.from(s, c=> c.charCodeAt(0));
    const payload = [...enc("Exif\0\0"), ...enc("2020:01:02 03:04:05"), 0, ...enc("<x>2020-01-02T03:04:05</x>")];
    const len = payload.length + 2;
    const jpeg = new Uint8Array([0xFF,0xD8, 0xFF,0xE1, len >> 8, len & 255, ...payload, 0xFF,0xDA, 0,2, 0x12,0x34, 0xFF,0xD9]);
    let b64 = ""; jpeg.forEach(b=> b64 += String.fromCharCode(b));
    const file = dataUrlToFile("data:image/jpeg;base64," + btoa(b64), "t.jpg", new Date(2031, 4, 6, 7, 8, 9));
    const out = new TextDecoder("latin1").decode(new Uint8Array(await file.arrayBuffer()));
    const ok = out.includes("2031:05:06 07:08:09") && out.includes("2031-05-06T07:08:09") && !out.includes("2020") && file.size === jpeg.length;
    check("Alle Fotos: Aufnahmedatum der Kopien wird auf jetzt gesetzt", ok, ok ? "" : "Datum nicht ersetzt oder Datei verändert");
  }catch(e){ check("Alle Fotos: Aufnahmedatum der Kopien wird auf jetzt gesetzt", false, e.message); }

  // --- Test 8: Nur 15 abgeschlossene bleiben; nie Entwürfe, nie ungesicherte PDFs ---
  {
    const realRecords = records, realSave = saveRecords, realQueue = queueBackupDelete, realToast = showToast, realCurrent = currentRecordId;
    const queued = [];
    try{
      saveRecords = async ()=> true;              // im Test nichts wirklich speichern/löschen
      queueBackupDelete = id=> queued.push(id);
      showToast = ()=>{};
      currentRecordId = null;
      const mk = (id, status, t, exported)=>{ const r = { id, status, updatedAt: t, data: freshState() }; if(exported !== "legacy") r.pdfExportedAt = exported; return r; };
      records = [mk("draftOld", "draft", 1, "legacy")];
      for(let i = 0; i <= 16; i++) records.push(mk("T"+i, "fertig", 100+i, i === 1 || i === 16 ? null : "legacy"));
      enforceFinishedLimit();
      const step1 = !records.some(r=> r.id==="T0") && records.some(r=> r.id==="T1") && records.some(r=> r.id==="draftOld") && records.some(r=> r.id==="T16");
      markPdfExported("T1");
      const step2 = !records.some(r=> r.id==="T1") && records.filter(r=> r.status==="fertig").length === 15 && records.some(r=> r.id==="draftOld");
      const backupOk = queued.join(",") === "T0,T1";
      check("Limit 15: Älteste gesicherte weg, Entwürfe und ungesicherte bleiben", step1 && step2 && backupOk,
        !step1 ? "Falscher Eintrag gelöscht/behalten (Schritt 1)" : !step2 ? "Nach dem Sichern nicht korrekt aufgeräumt" : !backupOk ? "Backup-Löschung falsch: " + queued.join(",") : "");
    }catch(e){ check("Limit 15: Älteste gesicherte weg, Entwürfe und ungesicherte bleiben", false, e.message); }
    finally{
      records = realRecords; saveRecords = realSave; queueBackupDelete = realQueue; showToast = realToast; currentRecordId = realCurrent;
    }
  }

  // --- Test 9: Fotoplätze haben feste Höhe, auch ungeladen (sonst springt die Seite in Safari) ---
  try{
    const box = document.createElement("div");
    box.className = "photo-preview";
    box.style.cssText = "position:absolute;left:-9999px;width:300px;";
    box.innerHTML = '<img src="data:image/jpeg;base64,AAAA" alt="" loading="lazy" decoding="async">';
    document.body.appendChild(box);
    const h = box.querySelector("img").offsetHeight;
    box.remove();
    check("Fotoplätze behalten ihre Höhe, bevor das Foto geladen ist", h >= 200, h >= 200 ? "" : `Höhe ungeladen: ${h}px — Seite springt bei Auswahl`);
  }catch(e){ check("Fotoplätze behalten ihre Höhe, bevor das Foto geladen ist", false, e.message); }

  // --- Test 10: Alte Datensätze werden auf die neuen Begriffe umgestellt, nichts geht verloren ---
  try{
    const d = freshState();
    delete d.abschluss; delete d.elektro.zaehler.raumuebersicht; delete d.daecher[0].traufhoehe; delete d.daecher[0].ziegelFoto; delete d.gebaeude.abstellortFoto;
    Object.assign(d.daecher[0], { dcLeitungsweg:"Fassade im Alurohr", regenrinne:"vorhanden", geruest:"Kunde stellt Gerüst", traufe8:"über 5m", bemerkung1:"alt" });
    Object.assign(d.elektro.zaehler, { neuerZaehlerschrank:"muss geprüft werden", weitereUV:"vorhanden", neueUV:"erforderlich" });
    Object.assign(d.elektro.hausanschluss, { typ:"HA-Innen", fundamenterder:"vorhanden" });
    Object.assign(d.elektro, { waermepumpe:"geplant", wallbox:"gewünscht", messkonzept:"keine Änderung" });
    d.elektro.komponenten.notstrom = true;
    normalizeRecordData(d);
    const got = [d.daecher[0].dcLeitungsweg, d.daecher[0].regenrinne, d.daecher[0].geruest, d.elektro.zaehler.neuerZaehlerschrank, d.elektro.zaehler.weitereUV,
      d.elektro.zaehler.neueUV, d.elektro.hausanschluss.typ, d.elektro.hausanschluss.fundamenterder, d.elektro.waermepumpe, d.elektro.wallbox, d.elektro.messkonzept].join("|");
    const want = "Alurohr Fassade|Ja|Stellt Kunde|Prüfen|Ja|Ja|Innen|Ja|Geplant|Gewünscht|Keine Änderung";
    const kept = d.daecher[0].traufe8 === "über 5m" && d.daecher[0].bemerkung1 === "alt";
    const added = d.abschluss && d.abschluss.angebot.includes("Notstrom") && d.elektro.zaehler.raumuebersicht === null && d.daecher[0].ziegelFoto === null && d.gebaeude.abstellortFoto === null;
    check("Alte Datensätze: Begriffe umgestellt, alte Angaben erhalten", got === want && kept && added,
      got !== want ? "Umstellung falsch: " + got : !kept ? "Alte Angaben verloren" : !added ? "Neue Felder fehlen" : "");
  }catch(e){ check("Alte Datensätze: Begriffe umgestellt, alte Angaben erhalten", false, e.message); }

  // --- Test 11: Firmen – Logo/Schriftzug, Kontakt, Fachberater im PDF; alte Datensätze ohne Firma ---
  try{
    const problems = [];
    let prev = null;
    for(const f of FIRMEN){
      const d = prev || freshState(); d.kunde.nachname = "Firmatest";
      setFirma(d, f.id);   // beim zweiten Durchlauf: Firmenwechsel am selben Datensatz
      prev = d;
      const out = (await buildPDF(d)).output();
      if(f.logo && !/\/Subtype \/Image/.test(out)) problems.push(f.name + ": Logo fehlt");
      if(!f.logo && !out.includes("(" + f.name + ") Tj")) problems.push(f.name + ": Schriftzug fehlt");
      if(f.email && !out.includes(f.email)) problems.push(f.name + ": E-Mail fehlt");
      if(!out.includes(BERATER_TELEFON)) problems.push(f.name + ": Telefon fehlt");
      if(f.berater && !out.includes("Besichtigt von " + f.berater)) problems.push(f.name + ": Fachberater falsch (" + d.grunddaten.besichtigtVon + ")");
    }
    const old = freshState(); delete old.firma; normalizeRecordData(old);
    if(!(old.firma === "" && firmaOf(old) === null)) problems.push("Altdaten falsch");
    check("Firmen: Logo/Schriftzug, Kontakt, Fachberater im PDF; Firmenwechsel; Altdaten", !problems.length, problems.join("; "));
  }catch(e){ check("Firmen: Logo/Schriftzug, Kontakt, Fachberater im PDF; Firmenwechsel; Altdaten", false, e.message); }

  // --- Test 12: Cloud-Fotos werden verkleinert, kleine bleiben unverändert ---
  try{
    const big = document.createElement("canvas"); big.width = 4032; big.height = 3024;
    const bx = big.getContext("2d");
    for(let i=0;i<4000;i++){ bx.fillStyle = "hsl(" + (i*37%360) + ",70%," + (30+i%40) + "%)"; bx.fillRect((i*97)%4032, (i*61)%3024, 60, 45); }
    const bigUrl = big.toDataURL("image/jpeg", 0.95); big.width = big.height = 0;
    const bigBytes = (await (await fetch(bigUrl)).blob()).size;
    const shrunk = await shrinkForCloud(bigUrl);
    const shrunkImg = await loadImageEl(URL.createObjectURL(shrunk.blob));
    const dimOk = Math.max(shrunkImg.naturalWidth, shrunkImg.naturalHeight) === CLOUD_MAX_DIM && shrunk.mime === "image/jpeg";
    const smaller = shrunk.blob.size < bigBytes / 2;
    const small = document.createElement("canvas"); small.width = 40; small.height = 30;
    small.getContext("2d").fillRect(0,0,40,30);
    const smallUrl = small.toDataURL("image/jpeg", 0.9);
    const keptSmall = await shrinkForCloud(smallUrl);
    const smallSame = (await blobToDataUrl(keptSmall.blob)) === smallUrl;
    check("Cloud-Fotos: groß wird auf 2000 px verkleinert, klein bleibt gleich", dimOk && smaller && smallSame,
      !dimOk ? "Maße falsch: " + shrunkImg.naturalWidth + "x" + shrunkImg.naturalHeight : !smaller ? ("Nicht kleiner: " + bigBytes + " → " + shrunk.blob.size) : !smallSame ? "Kleines Foto verändert" : "");
  }catch(e){ check("Cloud-Fotos: groß wird auf 2000 px verkleinert, klein bleibt gleich", false, e.message); }

  // --- Test 13: Wiederhergestelltes (verkleinertes) Foto behält den Cloud-Namen ---
  try{
    const fakeKey = "ab".repeat(32) + ".jpg";
    const realFetch = window.fetch;
    const tiny = document.createElement("canvas"); tiny.width = 8; tiny.height = 8;
    const tinyBlob = await new Promise(res=> tiny.toBlob(res, "image/jpeg", 0.5));
    window.fetch = async (u, o)=> String(u).includes(fakeKey) ? new Response(tinyBlob, { status: 200 }) : realFetch(u, o);
    let restored;
    try{ restored = await unpackPhotos({ $photo: SUPABASE_URL + "/storage/v1/object/public/photos/" + fakeKey }); }
    finally{ window.fetch = realFetch; }
    const key = await photoKeyFor(restored);
    photoKeys.delete(restored); photoUrlPromises.delete(restored);
    check("Wiederherstellen: verkleinertes Foto wird nicht doppelt hochgeladen", key === fakeKey, key !== fakeKey ? "Schlüssel " + key : "");
  }catch(e){ check("Wiederherstellen: verkleinertes Foto wird nicht doppelt hochgeladen", false, e.message); }

  // --- Test 14: Kundendaten einfügen (Lead-Liste) ---
  try{
    const problems = [];
    const lead = "Vor-Ort-Check\nAnrede: Frau\nVorname: Katrin\nNachname: Weyer\nTelefon: 01514 4562555\nE-Mail: katrin.griehl@t-online.de\nStraße: Siegfriedstraße\nHausnummer: 22\nPLZ: 14513\nOrt: Teltow";
    const want = { "kunde.anrede":"Frau", "kunde.vorname":"Katrin", "kunde.nachname":"Weyer", "kunde.telefon":"01514 4562555", "kunde.email":"katrin.griehl@t-online.de",
      "standort.strasse":"Siegfriedstraße", "standort.nr":"22", "standort.plz":"14513", "standort.ort":"Teltow" };
    const got = parseKundendaten(lead);
    Object.keys(want).forEach(k=>{ if(got[k] !== want[k]) problems.push(k + "=" + got[k]); });
    const adr = parseKundendaten("Vorname: Max\r\nAdresse: Am Hollager Berg 1a, 49134 Wallenhorst\nTelefon:");
    if(adr["standort.strasse"] !== "Am Hollager Berg" || adr["standort.nr"] !== "1a" || adr["standort.plz"] !== "49134" || adr["standort.ort"] !== "Wallenhorst" || "kunde.telefon" in adr) problems.push("Adresse: " + JSON.stringify(adr));
    if("kunde.anrede" in parseKundendaten("Anrede: Dr.")) problems.push("Anrede Dr. übernommen");
    if(Object.keys(parseKundendaten("Hallo, bitte zurückrufen")).length) problems.push("Freitext erkannt");
    // Übernahme in einen offenen Check: vorhandene Werte bleiben, wenn der Text dafür nichts hat
    const savedS = S, savedScreen = screen, savedToast = window.showToast, savedRender = window.render, savedAuto = window.scheduleAutosave;
    let toast = "";
    try{
      S = freshState(); S.kunde.telefon = "0170 111"; S.standort.ort = "Altort";
      window.showToast = m=>{ toast = m; }; window.render = ()=>{}; window.scheduleAutosave = ()=>{};
      applyKundendaten("Vorname: Katrin\nNachname: Weyer\nOrt: Teltow");
      if(S.kunde.vorname !== "Katrin" || S.standort.ort !== "Teltow" || S.kunde.telefon !== "0170 111") problems.push("Übernahme falsch");
      if(toast !== "Kundendaten übernommen") problems.push("Meldung: " + toast);
      const before = JSON.stringify(S);
      applyKundendaten("irgendwas ohne Doppelpunkt");
      if(JSON.stringify(S) !== before) problems.push("Ohne Treffer verändert");
      if(!/Keine Kundendaten erkannt/.test(toast)) problems.push("Kein Hinweis bei Fehltreffer");
    }finally{
      S = savedS; screen = savedScreen; window.showToast = savedToast; window.render = savedRender; window.scheduleAutosave = savedAuto;
    }
    check("Kundendaten einfügen: Lead-Text wird richtig verteilt", !problems.length, problems.join("; "));
  }catch(e){ check("Kundendaten einfügen: Lead-Text wird richtig verteilt", false, e.message); }

  console.log("=== Vor-Ort-Check Selbsttest ===");
  results.forEach(r=>console.log((r.ok?"OK  ":"FEHLER "), r.name, r.detail?("— "+r.detail):""));
  const allOk = results.every(r=>r.ok);
  console.log(allOk ? "Alles grün." : "ACHTUNG: mindestens ein Test fehlgeschlagen — nicht deployen.");
  return allOk;
}
selftest();
