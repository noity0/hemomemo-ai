# 🌍 Hemomemo AI — WEBSITE LIVE KARO (5 minute, Roman Urdu)

Website `web/` me tayyar hai. Ye sirf tarseel/taruf hai — Hemomemo ka dimagh
100% aap ke PC par rehta hai, kisi AI/platform API se kuch nahi judta.

## Tareeqa 1 — NETLIFY DROP (sab se aasan, FREE)
1. Browser me kholo: **https://app.netlify.com/drop**
2. Free account banao (email se).
3. Poora `web` folder **drag-drop** kar do (index.html wala folder —
   `HemomemoUltra-People.zip` andar hi hai, download button chal parega).
4. 30 second me **LIVE URL** mil jayega (misal `hemomemo.netlify.app`).

## Tareeqa 2 — Domain: onegenultra.com
1. Domain kharido (Namecheap/Porkbun/Cloudflare — koi bhi registrar):
   **onegenultra.com** (backup: .net / .org)
2. Netlify: Sites → aap ki site → **Domain management** →
   **Add custom domain** → `onegenultra.com`
3. Registrar ke DNS me Netlify ke bataye huwe records lagao
   (A/CNAME — Netlify khud bol dega kya lagana hai).
4. HTTPS **khud free** ban jata hai (Let's Encrypt).

## Tareeqa 3 — GitHub Pages (FREE, zip 100MB se bara to release-assets me)
1. `gh auth login` (ya github.com par repo banao)
2. Repo me web/ ka code push karo → Settings → Pages → deploy from branch.
3. 124MB wala app-zip GitHub ki **Release** me asset ke tor par lagao aur
   index.html ke download-link me release-URL dal do
   (GitHub kisi file ko 100MB se bara repo me nahi leta — is liye Netlify
   Tareeqa 1 sab se aasan hai).

## Baad me update
`make_package` chala kar naya package → naya zip → web folder dobara upload
(drop dobara) — bas live site update.

## 📜 Oath (yaad rakho)
Website sirf LOGON ko Hemomemo tak pahunchati hai. Koi platform API nahi,
kisi AI-model se koi connection nahi. Dimagh sirf aap ke PC ka hai.
