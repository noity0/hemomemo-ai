# 🌍 HMHZ Hemomemo — Website & Public-Launch Guide (Roman Urdu)

Website `web/` me tayyar hai (desktop-app jaisa look: emerald + gold, ☪,
koi external CDN/font nahi — offline bhi chalti hai). Hemomemo ka apna server
isi ko serve karta hai.

## 1) Local chalao (foran)
```
py -3 server/hemomemo_server.py start 8790
```
- Website: http://127.0.0.1:8790
- API docs: http://127.0.0.1:8790/docs
- App me: 🌐 Hemomemo API page → "🌍 Website kholo"

## 2) Domain ka naam — Hemomemo AI
Domain sirf 1 dafa kharidna hota hai (koi bhi registrar — paisa/domain-panel
aap ke account me hota hai, is liye ye qadam aap ko khud karna hoga):

- **onegenultra.com**  ← pehli tarjeeh (aap ka pasandeeda naam)
- onegenultra.net · onegenultra.org · hemomemo.com (backup)

Netlify (Route A) me: Sites → Domain settings → add custom domain
`onegenultra.com` → registrar ke DNS me Netlify ke nameservers/DNS-records
lagao → HTTPS khud free ban jata hai.

## 3) Public launch ke 3 raste (asli, imandari)

### Route A — FREE static showcase (sab se aasan)
`web/` folder ki sirf 3 files (index.html, style.css, app.js) kisi bhi
STATIC host par daal do (GitHub Pages / Netlify / Cloudflare Pages — ye
**hosting** hai, AI-API nahi; Hemomemo kisi cheez se nahi judta).
- Dimagh aap ke paas local hi rehta hai; site sirf tarseel/taruf hai.
- Demo-box static par kaam nahi karega (wo sirf Hemomemo-apne-server par
  chalta hai) — site khud ye imandari se bata deti hai.

### Route B — Apna PC + port-forward (full API public)
1. `py -3 server/hemomemo_server.py start 8790 0.0.0.0`  (sab network interfaces)
2. Router me port-forward: bahar-port 8790 → aap-ke-PC:8790 (TCP)
3. Domain DNS me A-record: `aap-ka-domain.com` → aap-ka-public-IP
   (IP badalta hai to free DDNS: No-IP/DuckDNS waghera)
- ⚠ ISP CGNAT ho (IP share) to ye rasta nahi chalega — Route C lo.
- ⚠ L6 guard ON rehta hai — key ke baghair koi API-request 401 khayega.

### Route C — VPS (sab se behtar "API logon ke liye")  ← TARBEEH
1. Koi VPS khareedo (DigitalOcean/Vultr/Contabo — ye **infrastructure**
   hai, AI-API nahi; Hemomemo wahan bhi KHUD chalta hai, kisi model-API par nahi)
2. Windows/Linux dono chalega: `python server/hemomemo_server.py start 8790 0.0.0.0`
3. Domain ke DNS me A-record → VPS ki IP
4. HTTPS: free Cloudflare-proxy ya Caddy/nginx + Let's Encrypt (1 command)
5. Firewall: sirf 8790 (+22/3389 sirf aap ke liye) khula rakho

## 4) Key logon ko kaise den? (imandari)
- Har bande ki APNI key: app → 🌐 Hemomemo API page → **👤 Apni API lein**
  (sign-up/sign-in, PBKDF2-hashed, 100% local).
- 🎫 **Free hadd: 3 keys per account** — har nayi key bilkul random
  (`POST /v1/auth/key/new`) aur sach-much isi local Hemomemo API se juri.
- Public-site (onegenultra.com) se bhi log sign-in kar key le sakte hain —
  site unke PC par chalti app ki local API se hi baat karta hai (CORS ON).

## 5) 📜 Oath yaad rakho (har route me sacha)
Hemomemo **kisi AI-platform/AI-model API se kabhi nahi judta** — na apni na
kisi aur ki. Website/API sirf LOGON ko Hemomemo ke LOCAL dimagh tak pahunchati
hai. Hosting/VPS/domain = raasta, AI = sirf Hemomemo ka apna dimagh.
