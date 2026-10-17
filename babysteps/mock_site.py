"""'Example Mail': a small fake email provider for reliable demos.

Flows: create account, log in, forgot password (code goes to a fake phone), inbox with one
ordinary email and one scam email. State is in memory and resets on server restart.
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
    "inge.mueller@example.mail": {"name": "Inge Müller", "password": secrets.token_hex(8), "phone": "0170 ••• •42"},
}
SESSIONS: dict[str, str] = {}   # session id -> email
RESET_CODES: dict[str, str] = {}  # email -> code
PHONE_SMS: list[str] = []         # what the fake phone shows

STYLE = """
<style>
 body{font-family:Helvetica,Arial,sans-serif;background:#eef3f8;margin:0;font-size:18px;color:#222}
 header{background:#2a5d9f;color:#fff;padding:14px 24px;font-size:24px;font-weight:bold}
 main{max-width:520px;margin:30px auto;background:#fff;padding:24px 28px;border-radius:10px;box-shadow:0 2px 8px #0002}
 label{display:block;margin-top:14px;font-weight:bold}
 input,select{width:100%;padding:10px;font-size:18px;margin-top:4px;box-sizing:border-box;border:1px solid #999;border-radius:6px}
 button{margin-top:20px;padding:12px 20px;font-size:18px;background:#2a5d9f;color:#fff;border:0;border-radius:6px;cursor:pointer}
 .err{color:#b00020;margin-top:10px}.ok{color:#1a7f37;margin-top:10px}
 .mail{border-bottom:1px solid #ddd;padding:12px 0}.mail b{display:block}
 a{color:#2a5d9f}
</style>"""


def page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"<!doctype html><html><head><meta charset=utf-8><title>{title}</title>{STYLE}</head>"
                        f"<body><header>✉ Example Mail</header><main>{body}</main></body></html>")


def current_user(request: Request) -> str | None:
    return SESSIONS.get(request.cookies.get("sid", ""))


@router.get("/start")
def start() -> HTMLResponse:
    return page("Start", "<h2>Hello!</h2><p>This browser is controlled by your helper. Just watch, "
                "or type when the helper asks you to.</p><p><a href='/mock/'>Example Mail</a></p>")


@router.get("/")
def login_form(msg: str = "") -> HTMLResponse:
    return page("Log in", f"""
<h2>Log in to Example Mail</h2>
<form method=post action="/mock/login">
 <label for=email>Email address</label><input id=email name=email type=email autocomplete=username>
 <label for=password>Password</label><input id=password name=password type=password autocomplete=current-password>
 <button type=submit>Log in</button>
</form>
<p class=err>{html.escape(msg)}</p>
<p><a href="/mock/forgot">Forgot password?</a> · <a href="/mock/signup">Create a new account</a></p>""")


@router.post("/login")
def login(email: str = Form(""), password: str = Form("")):
    acc = ACCOUNTS.get(email.strip().lower())
    if not acc or acc["password"] != password:
        return RedirectResponse("/mock/?msg=Wrong+email+or+password.", status_code=303)
    sid = secrets.token_hex(16)
    SESSIONS[sid] = email.strip().lower()
    r = RedirectResponse("/mock/inbox", status_code=303)
    r.set_cookie("sid", sid)
    return r


@router.get("/signup")
def signup_form(msg: str = "") -> HTMLResponse:
    return page("Create account", f"""
<h2>Create your Example Mail account</h2>
<form method=post action="/mock/signup">
 <label for=name>Your full name</label><input id=name name=name>
 <label for=username>Choose your new email address</label><input id=username name=username placeholder="e.g. inge.mueller">
 <span>@example.mail</span>
 <label for=phone>Mobile phone number (for password resets)</label><input id=phone name=phone type=tel>
 <label for=password>Choose a password</label><input id=password name=password type=password autocomplete=new-password>
 <label for=password2>Repeat the password</label><input id=password2 name=password2 type=password autocomplete=new-password>
 <button type=submit>Create account</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/signup")
def signup(name: str = Form(""), username: str = Form(""), phone: str = Form(""),
           password: str = Form(""), password2: str = Form("")):
    email = username.strip().lower().removesuffix("@example.mail") + "@example.mail"
    if not name or not username:
        return RedirectResponse("/mock/signup?msg=Please+fill+in+your+name+and+email.", status_code=303)
    if email in ACCOUNTS:
        return RedirectResponse("/mock/signup?msg=This+email+address+is+taken.", status_code=303)
    if len(password) < 8:
        return RedirectResponse("/mock/signup?msg=The+password+needs+at+least+8+characters.", status_code=303)
    if password != password2:
        return RedirectResponse("/mock/signup?msg=The+two+passwords+are+not+the+same.", status_code=303)
    ACCOUNTS[email] = {"name": name, "password": password, "phone": phone}
    return page("Welcome", f"<h2>Welcome, {html.escape(name)}!</h2><p class=ok>Your new address is "
                f"<b>{html.escape(email)}</b>.</p><p><a href='/mock/'>Log in now</a></p>")


@router.get("/forgot")
def forgot_form(msg: str = "") -> HTMLResponse:
    return page("Forgot password", f"""
<h2>Forgot your password?</h2><p>No problem. Enter your email address and we will text a code to your phone.</p>
<form method=post action="/mock/forgot">
 <label for=email>Email address</label><input id=email name=email type=email>
 <button type=submit>Text me a code</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/forgot")
def forgot(email: str = Form("")):
    email = email.strip().lower()
    if email not in ACCOUNTS:
        return RedirectResponse("/mock/forgot?msg=We+don't+know+this+email+address.", status_code=303)
    code = f"{random.randint(0, 999999):06d}"
    RESET_CODES[email] = code
    PHONE_SMS.append(f"Example Mail: your code is {code}. Never tell this code to anyone.")
    return RedirectResponse(f"/mock/reset?email={email}", status_code=303)


@router.get("/reset")
def reset_form(email: str, msg: str = "") -> HTMLResponse:
    e = html.escape(email)
    return page("New password", f"""
<h2>Set a new password</h2><p>We sent a 6-digit code to your phone.</p>
<form method=post action="/mock/reset">
 <input type=hidden name=email value="{e}">
 <label for=code>Code from your phone</label><input id=code name=code inputmode=numeric autocomplete=one-time-code>
 <label for=password>New password</label><input id=password name=password type=password autocomplete=new-password>
 <label for=password2>Repeat new password</label><input id=password2 name=password2 type=password autocomplete=new-password>
 <button type=submit>Save new password</button>
</form><p class=err>{html.escape(msg)}</p>""")


@router.post("/reset")
def reset(email: str = Form(""), code: str = Form(""), password: str = Form(""), password2: str = Form("")):
    email = email.strip().lower()
    back = f"/mock/reset?email={email}&msg="
    if RESET_CODES.get(email) != code.strip():
        return RedirectResponse(back + "That+code+is+not+right.", status_code=303)
    if len(password) < 8 or password != password2:
        return RedirectResponse(back + "Passwords+must+match+and+have+8+or+more+characters.", status_code=303)
    ACCOUNTS[email]["password"] = password
    del RESET_CODES[email]
    return page("Done", "<h2>Your password is changed.</h2><p class=ok>You can log in with it now.</p>"
                "<p><a href='/mock/'>Log in</a></p>")


@router.get("/inbox")
def inbox(request: Request):
    email = current_user(request)
    if not email:
        return RedirectResponse("/mock/", status_code=303)
    name = html.escape(ACCOUNTS[email]["name"])
    return page("Inbox", f"""
<h2>Inbox of {name}</h2>
<div class=mail><b>From: Gisela (neighbour)</b>Coffee on Sunday at 3? I'll bring cake.</div>
<div class=mail><b>From: Example-Mail Security Team &lt;security@examp1e-mail-support.net&gt;</b>
URGENT: Your account will be CLOSED in 24 hours! To keep your emails, download our security tool
and enter your bank details: <a href="https://examp1e-mail-support.net/SecurityTool.exe">Download SecurityTool</a></div>
<p><a href="/mock/logout">Log out</a></p>""")


@router.get("/logout")
def logout(request: Request):
    SESSIONS.pop(request.cookies.get("sid", ""), None)
    return RedirectResponse("/mock/", status_code=303)


@router.get("/phone")
def phone() -> HTMLResponse:
    msgs = "".join(f"<div class=mail>{html.escape(m)}</div>" for m in reversed(PHONE_SMS)) or "<p>No messages.</p>"
    return HTMLResponse(f"<!doctype html><meta charset=utf-8><meta http-equiv=refresh content=3>"
                        f"<title>Phone</title>{STYLE}<header>📱 Your phone (text messages)</header><main>{msgs}</main>")
