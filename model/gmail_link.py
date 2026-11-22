"""gmail_link.py - Hemomemo GMAIL-LINK (user-qanoon: email API allowed)
====================================================================
READ  : imaplib  -> imap.gmail.com:993 (SSL)
SEND  : smtplib  -> smtp.gmail.com:587 (STARTTLS)
CONFIG: data/email_link.json  (OWNER-machine par, zip me KABHI nahi)

email_link.json format (user khud banaye - app-password chahiye):
  {"email": "aap.name@gmail.com",
   "app_password": "abcd efgh ijkl mnop"}

App-password banana (2-Step-Verification ON hone par):
  myaccount.google.com -> Security -> 2-Step Verification -> App passwords

SECURITY:
  - password/quote kabhi log/chat me nahi aata
  - net_guard whitelist me imap/smtp hosts shamil (bypass urlopen-guard,
    magar hosts waise bhi ALLOWED_HOSTS me - consistency)
  - koi AI-API nahi - dimagh 100% local
"""
import email
import email.header
import email.message
import email.utils
import imaplib
import json
import os
import re
import smtplib
import ssl
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(_ROOT, "data", "email_link.json")

IMAP_HOST, IMAP_PORT = "imap.gmail.com", 993
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587

_HELP_APP_PW = (
    "[gmail] App-password chahiye:\n"
    "1) myaccount.google.com kholo -> Security\n"
    "2) '2-Step Verification' ON karo (agar nahi hai)\n"
    "3) 'App passwords' -> naya banao (16-harf code)\n"
    "4) file banao: data/email_link.json ->\n"
    '   {"email": "aap@gmail.com", "app_password": "abcd efgh ijkl mnop"}\n'
    "Phir inbox/email commands dobara chalao - sab local aur seedha.")

# --------------------------------------------------------------- config


def _cfg():
    """email_link.json -> dict | None (kabhi password print na karo)."""
    try:
        with open(CFG_PATH, "r", encoding="utf-8") as f:
            c = json.load(f)
        if not isinstance(c, dict):
            return None
        em = (c.get("email") or "").strip()
        pw = (c.get("app_password") or "").replace(" ", "")
        if em and pw:
            return {"email": em, "app_password": pw}
    except Exception:
        pass
    return None


def status():
    """(configured, email) - chat me dikhane ke liye (password NAHI)."""
    c = _cfg()
    return (True, c["email"]) if c else (False, "")

# ----------------------------------------------------------------- READ


def _dec_hdr(v):
    """RFC2047 subject/from ko insaani-text me badlo."""
    try:
        parts = email.header.decode_header(v or "")
        out = []
        for s, enc in parts:
            out.append(s.decode(enc or "utf-8", "replace")
                       if isinstance(s, bytes) else s)
        return "".join(out)
    except Exception:
        return v or ""


def _body_snip(msg, limit=220):
    """Pehla text/plain (warna text/html tagless) snippet."""
    body = ""
    try:
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    payload = part.get_payload(decode=True) or b""
                    body = payload.decode(
                        part.get_content_charset() or "utf-8", "replace")
                    break
                if ct == "text/html" and not body:
                    payload = part.get_payload(decode=True) or b""
                    body = re.sub(r"<[^>]+>", " ", payload.decode(
                        part.get_content_charset() or "utf-8", "replace"))
        else:
            payload = msg.get_payload(decode=True) or b""
            body = payload.decode(
                msg.get_content_charset() or "utf-8", "replace")
            if msg.get_content_type() == "text/html":
                body = re.sub(r"<[^>]+>", " ", body)
    except Exception:
        body = ""
    body = re.sub(r"\s+", " ", body).strip()
    return body[:limit]


def read_inbox(max_msgs=5, unseen_only=False, timeout=20.0):
    """Naye/haaliya emails -> [{from,subject,date,snippet,unseen}].

    Auth-fail par {} + 'app-password' ishara (graceful, crash nahi).
    """
    c = _cfg()
    if not c:
        return [], "no-config"
    msgs, err = [], ""
    imap = None
    try:
        imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT,
                                 ssl_context=ssl.create_default_context(),
                                 timeout=timeout)
        imap.login(c["email"], c["app_password"])
        imap.select("INBOX", readonly=True)
        crit = "(UNSEEN)" if unseen_only else "(ALL)"
        typ, data = imap.search(None, crit)
        if typ != "OK":
            return [], "search-fail"
        ids = (data[0] or b"").split()
        if unseen_only and not ids:
            imap.select("INBOX", readonly=False)
            typ, data = imap.search(None, "(ALL)")
            ids = (data[0] or b"").split()
        for iid in reversed(ids[-max_msgs:]):
            typ, md = imap.fetch(iid, "(FLAGS RFC822)")
            if typ != "OK" or not md or not md[0]:
                continue
            flags = (md[0][0] if isinstance(md[0], tuple) else b"") or b""
            raw = md[0][1] if isinstance(md[0], tuple) and len(md[0]) > 1 \
                else (md[0] if isinstance(md[0], bytes) else b"")
            if not raw:
                continue
            msg = email.message_from_bytes(raw)
            frm = email.utils.parseaddr(_dec_hdr(msg.get("From", "")))
            msgs.append({
                "from": frm[1] or _dec_hdr(msg.get("From", "")),
                "name": _dec_hdr(frm[0] or ""),
                "subject": _dec_hdr(msg.get("Subject", "")).strip(),
                "date": _dec_hdr(msg.get("Date", "")),
                "snippet": _body_snip(msg),
                "unseen": b"\\Seen" not in flags})
        try:
            imap.logout()
        except Exception:
            pass
    except imaplib.IMAP4.error:
        err = "app-password"
    except Exception as e:
        err = str(e)[:200]
    finally:
        try:
            if imap is not None:
                imap.shutdown()
        except Exception:
            pass
    return msgs, err


def read_inbox_text(max_msgs=5, unseen_only=False):
    """Chat-ready inbox-jawab -> (text, meta)."""
    ok, em = status()
    if not ok:
        return _HELP_APP_PW, {"source": "gmail", "state": "no-config"}
    t0 = time.time()
    msgs, err = read_inbox(max_msgs=max_msgs, unseen_only=unseen_only)
    if err == "app-password":
        return _HELP_APP_PW, {"source": "gmail", "state": "auth-fail"}
    if err and not msgs:
        return ("[gmail] Inbox nahi khula: %s\n(Internet/Gmail waqt-"
                "zayed check karo, phir dobara koshish karo.)" % err,
                {"source": "gmail", "state": "error"})
    if not msgs:
        return "[gmail] %s ka inbox - khali (koi email nahi)." % em, \
            {"source": "gmail", "state": "empty"}
    unseen = sum(1 for m in msgs if m["unseen"])
    lines = ["[gmail] %s ka inbox - haaliya %d emails (%d naye, %.1fs):"
             % (em, len(msgs), unseen, time.time() - t0)]
    for i, m in enumerate(msgs, 1):
        nid = " [NAYA]" if m["unseen"] else ""
        lines.append("%d.%s %s | %s | %s\n   %s"
                     % (i, nid, m["subject"][:80] or "(be-subject)",
                        m["from"][:60], m["date"][:22],
                        m["snippet"][:180]))
    return "\n".join(lines), {"source": "gmail", "state": "ok",
                              "n": len(msgs), "unseen": unseen}

# ----------------------------------------------------------------- SEND


def send_email(to, subject, body, timeout=25.0):
    """Email bhejo -> (ok, message). Smtp Gmail STARTTLS."""
    c = _cfg()
    if not c:
        return False, "no-config"
    to = (to or "").strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", to):
        return False, "galat-email-pata: %s" % to[:80]
    subject = (subject or "").strip() or "(be-subject)"
    msg = email.message.EmailMessage()
    msg["From"] = c["email"]
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain="hemomemo.local")
    msg.set_content(body or "")
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=timeout) as s:
            s.ehlo()
            s.starttls(context=ssl.create_default_context())
            s.ehlo()
            s.login(c["email"], c["app_password"])
            s.send_message(msg)
        return True, "bhej-diya: %s -> %s" % (subject[:60], to)
    except smtplib.SMTPAuthenticationError:
        return False, "app-password"
    except Exception as e:
        return False, str(e)[:200]


def send_from_command(d):
    """{to,subject,body} -> chat-ready jawab (text, meta)."""
    ok, em = status()
    if not ok:
        return _HELP_APP_PW, {"source": "gmail-send", "state": "no-config"}
    if not d.get("to"):
        return ("[gmail-send] Format yaad rakho:\n"
                "  send email to kisi@gmail.com subject: Salaam "
                "body: kaise ho?\n"
                "(teeno hisse likhne par hi email jayega.)",
                {"source": "gmail-send", "state": "need-fields"})
    ok2, msg = send_email(d.get("to"), d.get("subject"), d.get("body"))
    if msg == "app-password":
        return _HELP_APP_PW, {"source": "gmail-send", "state": "auth-fail"}
    if ok2:
        return "[gmail] %s" % msg, {"source": "gmail-send", "state": "sent",
                                    "to": d.get("to")}
    return "[gmail] Bhejne me masla: %s" % msg, \
        {"source": "gmail-send", "state": "error"}

# ------------------------------------------------- intent-detect (app hook)


_READ_RX = re.compile(
    r"(?i)\b(?:check\s+(?:my\s+)?(?:e?mails?|inbox|mail)"
    r"|inbox\s+(?:check|dikhao|kholo|parho|parh|read)"
    r"|mer[aiy]+\s+(?:e?mails?|inbox)\s*(?:dikhao|check|parho)?"
    r"|naye?\s+(?:e?mails?|messages?|mail)"
    r"|e?mails?\s+(?:check|parho|read|dikhao))\b")

_SEND_RX = re.compile(r"(?i)^\s*(?:send\s+(?:an?\s+)?e?mail|send\s+mail"
                      r"|e?mail\s+bhejo|mail\s+bhejo)\s*[:,]?\s*(.*)$")
_TO_RX = re.compile(r"(?i)\b(?:to|ko)\s*[:=]?\s*([\w.+-]+@[\w.-]+\.\w+)")
_SUB_RX = re.compile(r"(?i)\bsubject\s*[:=]\s*(.+?)(?=\s*\bbody\s*[:=]|$)")
_BOD_RX = re.compile(r"(?i)\bbody\s*[:=]\s*(.+)$", re.S)


def wants_mail(text):
    """('read',None) | ('send',{to,subject,body}) | (False,None)."""
    t = (text or "").strip()
    if not t:
        return False, None
    m = _SEND_RX.match(t)
    if m:
        rest = m.group(1) or ""
        d = {"to": "", "subject": "", "body": ""}
        mt = _TO_RX.search(rest)
        if mt:
            d["to"] = mt.group(1)
        ms = _SUB_RX.search(rest)
        if ms:
            d["subject"] = ms.group(1).strip().strip('"')
        mb = _BOD_RX.search(rest)
        if mb:
            d["body"] = mb.group(1).strip()
        return "send", d
    if _READ_RX.search(t):
        return "read", None
    return False, None


if __name__ == "__main__":
    print("status:", status())
    for _t in ("inbox check karo", "send email to a@b.com subject: Hi "
               "body: Salaam bhai", "aaj mausam kaisa hai"):
        print(_t, "->", wants_mail(_t))
    txt, meta = read_inbox_text(3)
    print(txt[:400], "|", meta)
