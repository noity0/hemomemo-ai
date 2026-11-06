/* ☪ Hemomemo AI — portal JS
   Sirf HEMOMO local API (127.0.0.1:8790) se baat karta hai — kisi aur
   AI/platform ki API se koi taluq NAHI (user ka pakka qanoon). */
const API = "http://127.0.0.1:8790";
const LS_KEY = "hemomemo_key";

const $ = (id) => document.getElementById(id);
const msg = (t, cls) => { const m = $("apiMsg"); m.textContent = t || "";
                          m.className = "api-msg " + (cls || ""); };

/* ── app Detect: local API zinda hai? ── */
async function detect() {
  try {
    const r = await fetch(API + "/health", { method: "GET" });
    if (r.ok) {
      $("apiOnline").hidden = false;
      $("apiOffline").hidden = true;
      return true;
    }
  } catch (e) { /* app band hai */ }
  $("apiOnline").hidden = true;
  $("apiOffline").hidden = false;
  return false;
}

function hdrs(key) {
  return {
    "Content-Type": "application/json",
    "X-Hemomemo-Key": key,
    "X-Hemomemo-Ts": String(Math.floor(Date.now() / 1000)),
    "X-Hemomemo-Nonce": Math.random().toString(36).slice(2) +
                      Date.now().toString(36),
  };
}

/* ── sign-up / sign-in ── */
async function auth(ep) {
  const email = $("email").value.trim();
  const pass = $("pass").value;
  msg("…", "");
  try {
    const r = await fetch(API + ep, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });
    const j = await r.json();
    if (r.ok && j.ok) {
      localStorage.setItem(LS_KEY, j.key);
      showKeys(j.key, j.keys || [j.key], j.key_limit || 3);
      msg("✅ Khush-aamdeed, " + email + " — aap ki Hemomemo key tayyar hai.", "ok");
    } else {
      msg("⚠️ " + (j.error || ("masla (" + r.status + ")")), "err");
    }
  } catch (e) { msg("⚠️ API se raabta nahi — app chal rahi hai?", "err"); }
}

/* ── keys dikhao ── */
async function showKeys(key, keys, limit) {
  // me() se taza jaankari (usage + keys)
  try {
    const r = await fetch(API + "/v1/auth/me", { headers: hdrs(key) });
    if (r.ok) {
      const j = await r.json();
      keys = j.keys || keys || [key];
      limit = j.key_limit || limit || 3;
    }
  } catch (e) {}
  $("signinBox").hidden = true;
  $("keysBox").hidden = false;
  $("keyCount").textContent = "(" + (keys ? keys.length : 1) + " / " +
                              (limit || 3) + " — free hadd)";
  const list = $("keyList");
  list.innerHTML = "";
  (keys || [key]).forEach((k) => {
    const row = document.createElement("div");
    row.className = "key-item";
    const c = document.createElement("code");
    c.textContent = k;
    const b = document.createElement("button");
    b.className = "btn ghost";
    b.textContent = "📋 copy";
    b.onclick = () => {
      navigator.clipboard.writeText(k);
      b.textContent = "✓ le li";
      setTimeout(() => (b.textContent = "📋 copy"), 1200);
    };
    row.appendChild(c);
    row.appendChild(b);
    list.appendChild(row);
  });
}

/* ── nayi random key (max 3) ── */
async function newKey() {
  const key = localStorage.getItem(LS_KEY);
  if (!key) return;
  $("btnNewKey").disabled = true;
  msg("nayi key ban rahi hai…", "");
  try {
    const r = await fetch(API + "/v1/auth/key/new", {
      method: "POST", headers: hdrs(key), body: "{}" });
    const j = await r.json();
    if (r.ok && j.ok) {
      await showKeys(j.key, j.keys, j.key_limit || 3);
      msg("🎫 Nayi key tayyar — bilkul random, isi Hemomemo API se juri.", "ok");
    } else {
      msg("⚠️ " + (j.error || ("masla (" + r.status + ")")), "err");
    }
  } catch (e) { msg("⚠️ API se raabta nahi", "err"); }
  $("btnNewKey").disabled = false;
}

/* ── download-counter ──
   Ye sirf ek GINTI-service hai (abacus — free counter, koi AI API NAHI,
   koi AI-model se iska taluq nahi; Hemomemo ka dimagh is se kuch nahi karta).
   Service na chale to counter khud-chup — download hamesha chalta hai. */
const CKEY = "hemomemo_downloads";
const CAPI = "https://abacus.jasoncameron.dev/abacus/" + CKEY;

async function countHit() {
  try {
    const r = await fetch(CAPI + "?value=1");
    const j = await r.json();
    if (j.status === "OK") showCount(j.value);
  } catch (e) { /* ginti-service band — koi masla nahi */ }
}
function showCount(v) {
  const el = $("dlCount");
  if (el) el.textContent = v;
}
(async () => {
  try {
    const r = await fetch(CAPI);
    const j = await r.json();
    if (j.status === "OK") showCount(j.value);
    else showCount("bohat-se");
  } catch (e) { showCount("bohat-se"); }
  document.querySelectorAll("a[download]")
    .forEach((a) => a.addEventListener("click", countHit, { once: true }));
})();

/* ── events ── */
$("btnSignup").onclick = () => auth("/v1/auth/signup");
$("btnSignin").onclick = () => auth("/v1/auth/signin");
$("btnNewKey").onclick = newKey;
$("btnLogout").onclick = () => {
  localStorage.removeItem(LS_KEY);
  $("keysBox").hidden = true;
  $("signinBox").hidden = false;
  msg("sign-out OK — aap ka data aap ke PC par mehfooz hai.", "ok");
};

/* ── start: app detect + purani key wapas ── */
(async () => {
  if (await detect()) {
    const k = localStorage.getItem(LS_KEY);
    if (k) await showKeys(k, null, 3);
  }
  // agar app baad me khule to dobara koshish (har 15s)
  setInterval(async () => {
    if ($("apiOnline").hidden && (await detect())) {
      const k = localStorage.getItem(LS_KEY);
      if (k) await showKeys(k, null, 3);
    }
  }, 15000);
})();
