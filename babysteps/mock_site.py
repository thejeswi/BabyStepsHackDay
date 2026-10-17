"""'Example Mail': a small fake German email provider for reliable demos.

The look follows the style of popular German free-mail portals (yellow buttons, grey page,
Verdana, login card), with a fictional name, no real logos, and a 'Demo' badge, so it
cannot pass for a real login page.

Flows: create account, log in, forgot password (code goes to a fake phone), inbox with one
ordinary email and two scam emails (fake fine, fake security team). State is in memory and resets on server restart.
The fake phone page (/mock/phone) is for the HUMAN only; the agent's browser is blocked
from it (config.BLOCKED_PATH_PREFIXES), the same way a real agent can't read your phone.
"""
import html
import random
import secrets

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(prefix="/mock")

ACCOUNTS: dict[str, dict] = {
    "ayse.yilmaz@example.mail": {"name": "Ayşe Yılmaz", "password": secrets.token_hex(8), "phone": "0170 ••• •42"},
}
SESSIONS: dict[str, str] = {}   # session id -> email
RESET_CODES: dict[str, str] = {}  # email -> code
PHONE_SMS: list[str] = []         # what the fake phone shows

STYLE = """
<style>
 body{margin:0;background:#f3f3f3;color:#333;font:15px/1.45 Verdana,sans-serif}
 a{color:#1c8ad9}
 .topbar{background:#ffd800;height:56px;display:flex;align-items:center;padding:0 20px;gap:20px}
 .topbar .brand{font:bold 22px Verdana,sans-serif;color:#333}
 .topbar .brand span{font-weight:normal}
 .topbar input[type=search]{flex:1;max-width:480px;height:36px;border:0;border-radius:18px;padding:0 16px;font:14px Verdana,sans-serif}
 .topbar .user{margin-left:auto;font-size:13px}
 .wrap{max-width:980px;margin:24px auto;padding:0 16px}
 .card{background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.12);padding:20px}
 .login{display:grid;grid-template-columns:1fr 340px;gap:24px}
 .teaser{background:#fff;border-radius:8px;margin-bottom:12px;padding:14px 16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .teaser b{display:block;margin-bottom:4px}
 h2{font-size:20px;margin:0 0 12px}
 label{display:block;font-size:13px;color:#525252;margin:12px 0 4px}
 input[type=email],input[type=password],input[type=text],input[type=tel],input:not([type]){width:100%;height:40px;border:1px solid #c2c2c2;border-radius:4px;padding:0 12px;font:14px Verdana,sans-serif;box-sizing:border-box}
 input:focus{border-color:#1c8ad9;outline:none;box-shadow:0 0 0 2px rgba(28,138,217,.25)}
 .btn{display:flex;align-items:center;justify-content:center;width:100%;height:40px;padding:0 16px;margin-top:16px;border:0;border-radius:20px;font:bold 15px Verdana,sans-serif;cursor:pointer;background:#ffd800;color:#333}
 .btn:hover{background:#ccad00}
 .err{color:#d40000;margin-top:10px}.ok{color:#1a7f37}
 .links{font-size:13px;margin-top:14px;display:flex;justify-content:space-between}
 .layout{display:grid;grid-template-columns:220px 1fr;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.12)}
 .folders{background:#fafafa;border-right:1px solid #ebebeb;padding:12px 0}
 .folders .write{margin:0 16px 12px;width:auto}
 .folders a{display:flex;justify-content:space-between;padding:8px 16px;color:#333;text-decoration:none}
 .folders a.active{background:#fff;font-weight:bold;border-left:3px solid #1c8ad9}
 .mail{padding:12px 16px;border-bottom:1px solid #ebebeb}
 .mail:hover{background:#f7f7f7}
 .mail .head{display:flex;justify-content:space-between}
 .mail.unread .head{font-weight:bold}
 .mail .subj{margin:2px 0 6px}
 .mail .body{color:#525252;font-size:14px}
 .ad{margin:16px;background:#eee;color:#888;font-size:12px;text-align:center;padding:24px}
 .demo-badge{position:fixed;bottom:8px;right:8px;background:#ff4f4f;color:#fff;font-size:12px;padding:2px 8px}
</style>"""


def page(title: str, body: str, user: str = "") -> HTMLResponse:
    right = (f"<span class=user>{html.escape(user)} · <a href='/mock/logout'>Logout</a></span>" if user else "")
    return HTMLResponse(f"""<!doctype html><html lang=de><head><meta charset=utf-8><title>{title} - Example Mail</title>
{STYLE}</head><body><div class=topbar><div class=brand>✉ Example<span>Mail</span></div>
<input type=search placeholder="E-Mails durchsuchen" aria-label="E-Mails durchsuchen">{right}</div>
<div class=wrap>{body}</div><div class=demo-badge>Demo · fiktiver Anbieter</div></body></html>""")


def small(title: str, body: str) -> HTMLResponse:
    return page(title, f"<div class=card style='max-width:460px;margin:0 auto'>{body}</div>")


def current_user(request: Request) -> str | None:
    return SESSIONS.get(request.cookies.get("sid", ""))


@router.get("/start")
def start() -> HTMLResponse:
    # Shown in the helper's own window at launch; English, because it is addressed to the user.
    return HTMLResponse(f"<!doctype html><meta charset=utf-8><title>BabySteps</title>{STYLE}<div class=wrap>"
                        "<div class=card><h2>Hello!</h2><p>This window is controlled by your helper. Just watch, "
                        "or type when the helper asks you to.</p><p><a href='/mock/'>Example Mail</a> · "
                        "<a href='/city/'>ServicePortal Musterstadt</a></p></div></div>")


@router.get("/demo-login")
def demo_login():
    """For the presenter only: log Ayşe in once before the demo, like a mail account that stays
    logged in. The agent's browser is blocked from this path (config.BLOCKED_PATH_PREFIXES),
    so it can't skip the password flow."""
    sid = secrets.token_hex(16)
    SESSIONS[sid] = "ayse.yilmaz@example.mail"
    r = RedirectResponse("/mock/inbox", status_code=303)
    r.set_cookie("sid", sid)
    return r


@router.get("/")
def login_form(request: Request, msg: str = ""):
    if current_user(request):  # still logged in: straight to the inbox, like real mail sites
        return RedirectResponse("/mock/inbox", status_code=303)
    teasers = "".join(f"<div class=teaser><b>{t}</b>{d}</div>" for t, d in [
        ("Wetter: Goldener Oktober", "Bis zu 19 Grad am Wochenende in Musterstadt."),
        ("Rente: Was sich 2027 ändert", "Die wichtigsten Neuerungen im Überblick."),
        ("Vorsicht vor falschen Rechnungen", "Verbraucherschützer warnen vor einer neuen Betrugsmasche."),
    ])
    return page("Login", f"""
<div class=login><div>{teasers}</div>
<div class=card><h2>Login</h2>
<form method=post action="/mock/login">
 <label for=email>E-Mail-Adresse</label><input id=email name=email type=email autocomplete=username>
 <label for=password>Passwort</label><input id=password name=password type=password autocomplete=current-password>
 <button class=btn type=submit>Login</button>
</form>
<p class=err>{html.escape(msg)}</p>
<div class=links><a href="/mock/forgot">Passwort vergessen?</a><a href="/mock/signup">Kostenlos registrieren!</a></div>
</div></div>""")


@router.post("/login")
def login(email: str = Form(""), password: str = Form("")):
    acc = ACCOUNTS.get(email.strip().lower())
    if not acc or acc["password"] != password:
        return RedirectResponse("/mock/?msg=E-Mail-Adresse+oder+Passwort+falsch.", status_code=303)
    sid = secrets.token_hex(16)
    SESSIONS[sid] = email.strip().lower()
    r = RedirectResponse("/mock/inbox", status_code=303)
    r.set_cookie("sid", sid)
    return r


@router.get("/signup")
def signup_form(msg: str = "") -> HTMLResponse:
    return small("Registrieren", f"""
<h2>Kostenlos registrieren</h2>
<form method=post action="/mock/signup">
 <label for=name>Vor- und Nachname</label><input id=name name=name>
 <label for=username>Wunsch-E-Mail-Adresse</label><input id=username name=username placeholder="z. B. ayse.yilmaz"> @example.mail
 <label for=phone>Handynummer (für das Zurücksetzen des Passworts)</label><input id=phone name=phone type=tel>
 <label for=password>Passwort wählen</label><input id=password name=password type=password autocomplete=new-password>
 <label for=password2>Passwort wiederholen</label><input id=password2 name=password2 type=password autocomplete=new-password>
 <button class=btn type=submit>E-Mail-Adresse erstellen</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/signup")
def signup(name: str = Form(""), username: str = Form(""), phone: str = Form(""),
           password: str = Form(""), password2: str = Form("")):
    email = username.strip().lower().removesuffix("@example.mail") + "@example.mail"
    if not name or not username:
        return RedirectResponse("/mock/signup?msg=Bitte+Namen+und+Wunsch-Adresse+eingeben.", status_code=303)
    if email in ACCOUNTS:
        return RedirectResponse("/mock/signup?msg=Diese+E-Mail-Adresse+ist+bereits+vergeben.", status_code=303)
    if len(password) < 8:
        return RedirectResponse("/mock/signup?msg=Das+Passwort+muss+mindestens+8+Zeichen+haben.", status_code=303)
    if password != password2:
        return RedirectResponse("/mock/signup?msg=Die+Passwörter+stimmen+nicht+überein.", status_code=303)
    ACCOUNTS[email] = {"name": name, "password": password, "phone": phone}
    return small("Willkommen", f"<h2>Willkommen, {html.escape(name)}!</h2><p class=ok>Ihre neue Adresse lautet "
                 f"<b>{html.escape(email)}</b>.</p><p><a href='/mock/'>Jetzt einloggen</a></p>")


@router.get("/forgot")
def forgot_form(msg: str = "") -> HTMLResponse:
    # Button deliberately says "anfordern", not "senden": "senden" is on the irreversible-click
    # word list (browser.py), and requesting a reset code is a routine step.
    return small("Passwort vergessen", f"""
<h2>Passwort vergessen?</h2><p>Kein Problem. Geben Sie Ihre E-Mail-Adresse ein. Wir schicken Ihnen einen Code per SMS.</p>
<form method=post action="/mock/forgot">
 <label for=email>E-Mail-Adresse</label><input id=email name=email type=email>
 <button class=btn type=submit>Code per SMS anfordern</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/forgot")
def forgot(email: str = Form("")):
    email = email.strip().lower()
    if email not in ACCOUNTS:
        return RedirectResponse("/mock/forgot?msg=Diese+E-Mail-Adresse+ist+uns+nicht+bekannt.", status_code=303)
    code = f"{random.randint(0, 999999):06d}"
    RESET_CODES[email] = code
    PHONE_SMS.append(f"Example Mail: Ihr Code lautet {code}. Geben Sie diesen Code niemals weiter.")
    return RedirectResponse(f"/mock/reset?email={email}", status_code=303)


@router.get("/reset")
def reset_form(email: str, msg: str = "") -> HTMLResponse:
    e = html.escape(email)
    return small("Neues Passwort", f"""
<h2>Neues Passwort festlegen</h2><p>Wir haben Ihnen einen 6-stelligen Code per SMS geschickt.</p>
<form method=post action="/mock/reset">
 <input type=hidden name=email value="{e}">
 <label for=code>Code aus der SMS</label><input id=code name=code inputmode=numeric autocomplete=one-time-code>
 <label for=password>Neues Passwort</label><input id=password name=password type=password autocomplete=new-password>
 <label for=password2>Neues Passwort wiederholen</label><input id=password2 name=password2 type=password autocomplete=new-password>
 <button class=btn type=submit>Neues Passwort speichern</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/reset")
def reset(email: str = Form(""), code: str = Form(""), password: str = Form(""), password2: str = Form("")):
    email = email.strip().lower()
    back = f"/mock/reset?email={email}&msg="
    if RESET_CODES.get(email) != code.strip():
        return RedirectResponse(back + "Der+Code+ist+nicht+richtig.", status_code=303)
    if len(password) < 8 or password != password2:
        return RedirectResponse(back + "Die+Passwörter+müssen+übereinstimmen+und+mindestens+8+Zeichen+haben.", status_code=303)
    ACCOUNTS[email]["password"] = password
    del RESET_CODES[email]
    return small("Fertig", "<h2>Ihr Passwort wurde geändert.</h2><p class=ok>Sie können sich jetzt damit einloggen.</p>"
                 "<p><a href='/mock/'>Zum Login</a></p>")


@router.get("/inbox")
def inbox(request: Request):
    email = current_user(request)
    if not email:
        return RedirectResponse("/mock/", status_code=303)
    return page("Posteingang", """
<div class=layout>
 <div class=folders>
  <button class="btn write" type=button>E-Mail schreiben</button>
  <a class=active href="/mock/inbox">Posteingang <span>3</span></a><a href="#">Gesendet</a><a href="#">Entwürfe</a>
  <a href="#">Spam</a><a href="#">Papierkorb</a>
 </div>
 <div>
  <div class="mail unread"><div class=head><span>Ordnungsamt Musterstadt &lt;bussgeld@ordnungsamt-musterstadt.info&gt;</span><span>Heute</span></div>
   <div class=subj>LETZTE MAHNUNG: Bußgeld 289,50 EUR (Az. 77-XK-2291) - Zahlung innerhalb 24 Stunden</div>
   <div class=body>Sehr geehrte Bürgerin, laut unseren Unterlagen ist ein BUSSGELD in Höhe von 289,50 EUR NICHT BEZAHLT.
   Zahlen Sie INNERHALB VON 24 STUNDEN, andernfalls wird ein HAFTBEFEHL erlassen und die Polizei kommt zu Ihnen nach Hause.
   Überweisen Sie an M. Kovacs Consulting Ltd, IBAN LT12 1000 0111 0100 1000, oder kaufen Sie Google-Play-Karten im Wert
   von 290 EUR und rufen Sie mit den Codes unter +44 20 7946 0958 an. Kontaktieren Sie in dieser Sache NICHT das Bürgeramt.</div></div>
  <div class="mail unread"><div class=head><span>Gisela Hoffmann (Nachbarin)</span><span>Heute</span></div>
   <div class=subj>Kaffee am Sonntag?</div>
   <div class=body>Liebe Ayşe, hast du Lust auf Kaffee am Sonntag um 15 Uhr? Ich bringe Kuchen mit. Liebe Grüße, Gisela</div></div>
  <div class="mail unread"><div class=head><span>Example-Mail Sicherheitsteam &lt;security@examp1e-mail-support.net&gt;</span><span>Heute</span></div>
   <div class=subj>DRINGEND: Ihr Konto wird in 24 Stunden GESCHLOSSEN!</div>
   <div class=body>Um Ihre E-Mails zu behalten, laden Sie sofort unser Sicherheitsprogramm herunter und geben Sie Ihre
   Bankdaten ein: <a href="https://examp1e-mail-support.net/SecurityTool.exe">SecurityTool herunterladen</a></div></div>
  <div class=ad>Anzeige</div>
 </div>
</div>""", user=email)


@router.get("/logout")
def logout(request: Request):
    SESSIONS.pop(request.cookies.get("sid", ""), None)
    return RedirectResponse("/mock/", status_code=303)


@router.get("/phone")
def phone() -> HTMLResponse:
    msgs = "".join(f"<div class=teaser>{html.escape(m)}</div>" for m in reversed(PHONE_SMS)) or "<p>Keine Nachrichten.</p>"
    return HTMLResponse(f"<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=3>"
                        f"<title>Phone</title>{STYLE}<div class=topbar style='background:#333;color:#fff'>"
                        f"📱 Ayşe's phone · text messages</div><div class=wrap style='max-width:420px'>{msgs}</div>")
