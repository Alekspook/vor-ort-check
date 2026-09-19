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

  console.log("=== Vor-Ort-Check Selbsttest ===");
  results.forEach(r=>console.log((r.ok?"OK  ":"FEHLER "), r.name, r.detail?("— "+r.detail):""));
  const allOk = results.every(r=>r.ok);
  console.log(allOk ? "Alles grün." : "ACHTUNG: mindestens ein Test fehlgeschlagen — nicht deployen.");
  return allOk;
}
selftest();
