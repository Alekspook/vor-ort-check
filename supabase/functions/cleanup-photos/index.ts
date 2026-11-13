// Vor-Ort-Check: räumt nicht mehr gebrauchte Fotos aus dem Speicher "photos" auf.
//
// Ein Foto bleibt, solange es in irgendeinem Backup (Tabelle public.backups)
// vorkommt. Fotos, die in keinem Backup mehr stehen (Kunde aus der App
// gelöscht, durch das 15er-Limit herausgefallen, Foto ersetzt), werden nach
// GRACE_DAYS Tagen gelöscht. Die Wartezeit schützt Fotos, deren Backup noch
// aussteht.
//
// Aufruf: von der App nach einem erfolgreichen Backup, höchstens 1x pro Tag,
// mit dem Login des Nutzers. "?dry=1" zählt nur, ohne zu löschen.
import { createClient } from "jsr:@supabase/supabase-js@2";

const GRACE_DAYS = 14;
const MAX_SHARE = 0.7; // Sicherung: nie mehr als 70 % aller Fotos auf einmal löschen
const KEY_RE = /^[0-9a-f]{64}\.(jpg|png)$/;
const REF_RE = /\/object\/public\/photos\/([0-9a-f]{64}\.(?:jpg|png))/g;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const dryRun = new URL(req.url).searchParams.get("dry") === "1";
  const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
    auth: { persistSession: false },
  });

  try {
    if (!dryRun) {
      const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
      const { data: u, error: authErr } = await admin.auth.getUser(jwt);
      if (authErr || !u?.user) return json({ error: "Nicht angemeldet" }, 401);
      const { count } = await admin.from("backups").select("id", { count: "exact", head: true }).eq("owner", u.user.id);
      if (!count) return json({ error: "Kein Backup für dieses Konto" }, 403);
    }

    const { data: rows, error: rowsErr } = await admin.from("backups").select("data");
    if (rowsErr) throw rowsErr;
    const refs = new Set<string>();
    for (const r of rows || []) for (const m of JSON.stringify(r.data).matchAll(REF_RE)) refs.add(m[1]);
    if (!rows?.length || refs.size === 0) return json({ error: "Backups leer, Abbruch zur Sicherheit" }, 409);

    const objs: { name: string; created_at: string | null; metadata: { size?: number } | null }[] = [];
    for (let offset = 0; ; offset += 1000) {
      const { data, error } = await admin.storage.from("photos").list("", {
        limit: 1000, offset, sortBy: { column: "name", order: "asc" },
      });
      if (error) throw error;
      objs.push(...(data as typeof objs));
      if (!data || data.length < 1000) break;
    }

    const cutoff = Date.now() - GRACE_DAYS * 86400000;
    const keyed = objs.filter((o) => KEY_RE.test(o.name));
    const victims = keyed.filter((o) => !refs.has(o.name) && o.created_at && Date.parse(o.created_at) < cutoff);
    const bytes = victims.reduce((s, o) => s + (o.metadata?.size || 0), 0);
    const summary = {
      dryRun, objects: objs.length, referenced: refs.size,
      toDelete: victims.length, freedMB: Math.round(bytes / 1e6),
    };
    if (victims.length > keyed.length * MAX_SHARE) return json({ ...summary, error: "Zu viele Löschungen, Abbruch zur Sicherheit" }, 409);
    if (dryRun) return json(summary);

    let deleted = 0;
    for (let i = 0; i < victims.length; i += 100) {
      const names = victims.slice(i, i + 100).map((o) => o.name);
      const { data, error } = await admin.storage.from("photos").remove(names);
      if (error) throw error;
      deleted += data?.length || 0;
    }
    return json({ ...summary, deleted });
  } catch (e) {
    return json({ error: String((e as Error)?.message || e) }, 500);
  }
});
