// Supabase Edge Function "judge": checks the caller is logged in to Sky Castle,
// then forwards the program to the judge server with a signed request.
// Secrets to set on the function: JUDGE_URL (http://<server-ip>:8443/run) and JUDGE_SECRET.
const SB_URL = "https://xupqehazxffimjdvdgbh.supabase.co";
const SB_KEY = "sb_publishable_r5G_XYJgL6BTRmahCPFniQ__Pr9qr0Y";
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) =>
  new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const { username, token, language, files, stdin } = await req.json();
    const check = await fetch(`${SB_URL}/rest/v1/rpc/sg_check`, {
      method: "POST",
      headers: { apikey: SB_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ p_username: username, p_token: token }),
    });
    if (!check.ok || (await check.json()) !== true) return json({ error: "Log in (the gear menu) to run this language." }, 401);

    const body = JSON.stringify({ user: username, language, files, stdin: stdin ?? "" });
    const ts = String(Math.floor(Date.now() / 1000));
    const enc = new TextEncoder();
    const key = await crypto.subtle.importKey("raw", enc.encode(Deno.env.get("JUDGE_SECRET") ?? ""), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const mac = await crypto.subtle.sign("HMAC", key, enc.encode(ts + "." + body));
    const sig = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
    const r = await fetch(Deno.env.get("JUDGE_URL") ?? "", { method: "POST", headers: { "Content-Type": "application/json", "X-Ts": ts, "X-Sig": sig }, body });
    return json(await r.json(), r.status);
  } catch (e) {
    return json({ error: "Judge unavailable: " + String(e) }, 502);
  }
});
