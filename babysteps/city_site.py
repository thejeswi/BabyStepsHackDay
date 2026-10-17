"""'Musterstadt Service': a fictional city services portal for the demo.

Shows the two 'did you know' cases: the appointment calendar has no free slots for
citizenship or address registration, but both can be done online (and the pages say so).
Passport renewal really needs an appointment, and slots exist. Also hosts the
broadcasting-fee exemption form mentioned in the demo letter. State is in memory.
All rules shown here are fictional demo content, not legal information.
"""
import html
import secrets

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/city")
SUBMISSIONS: list[dict] = []

STYLE = """
<style>
 body{font-family:Helvetica,Arial,sans-serif;background:#f4f4f1;margin:0;font-size:18px;color:#222}
 header{background:#7a1f2b;color:#fff;padding:14px 24px;font-size:24px;font-weight:bold}
 header small{display:block;font-size:14px;font-weight:normal;opacity:.85}
 nav{background:#fff;padding:10px 24px;border-bottom:1px solid #ddd}nav a{margin-right:18px}
 main{max-width:640px;margin:26px auto;background:#fff;padding:24px 28px;border-radius:8px;box-shadow:0 2px 8px #0002}
 label{display:block;margin-top:14px;font-weight:bold}
 input,select{width:100%;padding:10px;font-size:18px;margin-top:4px;box-sizing:border-box;border:1px solid #999;border-radius:6px}
 input[type=checkbox]{width:auto;margin-right:8px}
 button{margin-top:20px;padding:12px 20px;font-size:18px;background:#7a1f2b;color:#fff;border:0;border-radius:6px;cursor:pointer}
 .tip{background:#fff7d6;border-left:6px solid #e0a800;padding:12px 16px;margin:16px 0}
 .none{color:#b00020;font-weight:bold}.ok{color:#1a7f37}
 .slot{display:inline-block;margin:6px 8px 0 0}
 a{color:#7a1f2b}
</style>"""

NAV = ("<nav><a href='/city/'>Home</a><a href='/city/appointments'>Book an appointment</a>"
       "<a href='/city/citizenship'>Citizenship</a><a href='/city/registration'>Register your address</a>"
       "<a href='/city/forms'>Forms</a></nav>")


def page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"<!doctype html><html><head><meta charset=utf-8><title>{title} · Musterstadt Service</title>"
                        f"{STYLE}</head><body><header>🏛 Musterstadt Service<small>City of Musterstadt · "
                        f"fictional demo portal</small></header>{NAV}<main>{body}</main></body></html>")


def done(what: str, extra: str = "") -> HTMLResponse:
    ref = "MS-" + secrets.token_hex(3).upper()
    SUBMISSIONS.append({"what": what, "ref": ref})
    return page("Received", f"<h2>Thank you, we received your {html.escape(what)}.</h2>"
                f"<p class=ok>Your reference number is <b>{ref}</b>. Please keep it.</p>{extra}")


@router.get("/")
def home() -> HTMLResponse:
    return page("Home", """
<h2>Welcome to Musterstadt Service</h2>
<p>What would you like to do?</p>
<ul>
 <li><a href="/city/appointments">Book an appointment at the citizens' office (Bürgeramt)</a></li>
 <li><a href="/city/citizenship">Apply for German citizenship (Einbürgerung)</a></li>
 <li><a href="/city/registration">Register your new address (Anmeldung)</a></li>
 <li><a href="/city/forms">Forms: broadcasting fee exemption, direct debit and more</a></li>
</ul>""")


@router.get("/appointments")
def appointments() -> HTMLResponse:
    return page("Appointments", """
<h2>Book an appointment at the Bürgeramt</h2>
<form method=get action="/city/appointments/slots">
 <label for=service>What is the appointment for?</label>
 <select id=service name=service>
  <option value="">Please choose…</option>
  <option value="citizenship">Citizenship (Einbürgerung)</option>
  <option value="registration">Register a new address (Anmeldung)</option>
  <option value="passport">New passport or ID card</option>
 </select>
 <button type=submit>Show free appointments</button>
</form>""")


@router.get("/appointments/slots")
def slots(service: str = "") -> HTMLResponse:
    if service == "citizenship":
        return page("No appointments", """
<h2>Citizenship (Einbürgerung)</h2><p class=none>There are no free appointments in the next 6 weeks.</p>
<div class=tip><b>New: you don't need an appointment.</b> Since this year you can apply for citizenship
completely online. It takes about 15 minutes. <a href="/city/citizenship/apply">Apply online now</a></div>""")
    if service == "registration":
        return page("No appointments", """
<h2>Register a new address (Anmeldung)</h2><p class=none>There are no free appointments in the next 6 weeks.</p>
<div class=tip><b>Faster: register online.</b> You can register your new address online. You need the
confirmation from your landlord (Wohnungsgeberbestätigung). <a href="/city/registration/online">Register online now</a></div>""")
    if service == "passport":
        times = ["Tue 20 Oct, 09:30", "Tue 20 Oct, 11:00", "Thu 22 Oct, 14:15"]
        opts = "".join(f"<label class=slot><input type=radio name=slot value='{t}'> {t}</label>" for t in times)
        return page("Free appointments", f"""
<h2>New passport or ID card</h2><p>For a passport you must come in person (photo and fingerprints).</p>
<form method=post action="/city/appointments/book"><input type=hidden name=service value=passport>
 {opts}
 <label for=name>Your full name</label><input id=name name=name>
 <button type=submit>Book this appointment</button></form>""")
    return page("Appointments", "<p class=none>Please choose what the appointment is for.</p>"
                "<p><a href='/city/appointments'>Back</a></p>")


@router.post("/appointments/book")
def book(service: str = Form(""), slot: str = Form(""), name: str = Form("")):
    if not slot or not name:
        return page("Missing", "<p class=none>Please choose a time and enter your name.</p>"
                    "<p><a href='/city/appointments/slots?service=passport'>Back</a></p>")
    return done(f"appointment ({html.escape(slot)})",
                "<p>Please bring: your old passport, one biometric photo, EUR 70 fee.</p>")


@router.get("/citizenship")
def citizenship() -> HTMLResponse:
    return page("Citizenship", """
<h2>German citizenship (Einbürgerung)</h2>
<p>You can usually apply if you have lived in Germany for 5 years, can support yourself,
and have German language skills at level B1.</p>
<div class=tip><b>New: apply online, no appointment needed.</b> <a href="/city/citizenship/apply">Start the online application</a></div>
<p>Or <a href="/city/appointments">book an appointment</a> (long waiting times).</p>""")


@router.get("/citizenship/apply")
def citizenship_form() -> HTMLResponse:
    return page("Apply for citizenship", """
<h2>Online application: German citizenship</h2>
<form method=post action="/city/citizenship/apply">
 <label for=name>Full name</label><input id=name name=name>
 <label for=birth>Date of birth</label><input id=birth name=birth placeholder="DD.MM.YYYY">
 <label for=nationality>Current nationality</label><input id=nationality name=nationality>
 <label for=since>Living in Germany since (year)</label><input id=since name=since>
 <label for=german>German language certificate</label>
 <select id=german name=german><option>None yet</option><option>A2</option><option>B1</option><option>B2 or higher</option></select>
 <label><input type=checkbox name=test value=yes> I have passed the citizenship test (Einbürgerungstest)</label>
 <button type=submit>Submit application</button>
</form>""")


@router.post("/citizenship/apply")
def citizenship_submit(name: str = Form(""), german: str = Form(""), test: str = Form("")):
    if not name:
        return page("Missing", "<p class=none>Please enter your name.</p><p><a href='/city/citizenship/apply'>Back</a></p>")
    missing = []
    if german in ("None yet", "A2"):
        missing.append("German certificate at level B1 (you can book a course at the Volkshochschule)")
    if test != "yes":
        missing.append("Citizenship test certificate (Einbürgerungstest)")
    todo = "".join(f"<li>{m}</li>" for m in missing)
    return done("citizenship application",
                "<p>Next, upload these documents within 4 weeks: passport copy, birth certificate, proof of income"
                " for the last 3 months.</p>" + (f"<p><b>Still missing:</b></p><ul>{todo}</ul>" if todo else ""))


@router.get("/registration")
def registration() -> HTMLResponse:
    return page("Register your address", """
<h2>Register your new address (Anmeldung)</h2>
<p>You must register within 2 weeks after moving in.</p>
<div class=tip><b>Register online</b>, no appointment needed: <a href="/city/registration/online">start here</a></div>""")


@router.get("/registration/online")
def registration_form() -> HTMLResponse:
    return page("Register online", """
<h2>Register your new address online</h2>
<form method=post action="/city/registration/online">
 <label for=name>Full name</label><input id=name name=name>
 <label for=address>New address</label><input id=address name=address>
 <label for=movein>Date you moved in</label><input id=movein name=movein placeholder="DD.MM.YYYY">
 <label><input type=checkbox name=landlord value=yes> I have the landlord's confirmation (Wohnungsgeberbestätigung)</label>
 <button type=submit>Submit registration</button>
</form>""")


@router.post("/registration/online")
def registration_submit(name: str = Form(""), address: str = Form(""), landlord: str = Form("")):
    if not name or not address:
        return page("Missing", "<p class=none>Please enter your name and new address.</p>")
    if landlord != "yes":
        return page("Missing", "<p class=none>You need the landlord's confirmation first. Ask your landlord for the "
                    "'Wohnungsgeberbestätigung'.</p>")
    return done("address registration", "<p>Your registration certificate will arrive by post within 2 weeks.</p>")


@router.get("/forms")
def forms() -> HTMLResponse:
    return page("Forms", """
<h2>Forms</h2><ul>
 <li><a href="/city/forms/fee-exemption">Broadcasting fee exemption (Befreiung vom Rundfunkbeitrag)</a></li>
 <li><a href="/city/forms/direct-debit">Direct debit for the broadcasting fee</a></li></ul>""")


@router.get("/forms/fee-exemption")
def exemption_form() -> HTMLResponse:
    return page("Fee exemption", """
<h2>Apply for exemption from the broadcasting fee</h2>
<p>You can be exempted if you receive one of these benefits. Attach the benefit notice later.</p>
<form method=post action="/city/forms/fee-exemption">
 <label for=name>Full name</label><input id=name name=name>
 <label for=number>Contribution number (Beitragsnummer)</label><input id=number name=number>
 <label for=reason>Which benefit do you receive?</label>
 <select id=reason name=reason><option value="">Please choose…</option>
  <option>Basic income support in old age (Grundsicherung im Alter)</option>
  <option>Citizen's income (Bürgergeld)</option>
  <option>Housing benefit (Wohngeld)</option>
  <option>None of these</option></select>
 <button type=submit>Send application</button>
</form>""")


@router.post("/forms/fee-exemption")
def exemption_submit(name: str = Form(""), number: str = Form(""), reason: str = Form("")):
    if not name or not number or not reason:
        return page("Missing", "<p class=none>Please fill in all fields.</p>")
    if reason == "None of these":
        return page("Not eligible", "<p>Without one of these benefits an exemption is usually not possible.</p>")
    return done("fee exemption application", "<p>Please send a copy of your benefit notice within 4 weeks.</p>")


@router.get("/forms/direct-debit")
def debit_form() -> HTMLResponse:
    return page("Direct debit", """
<h2>Direct debit for the broadcasting fee</h2>
<form method=post action="/city/forms/direct-debit">
 <label for=name>Account holder</label><input id=name name=name>
 <label for=iban>IBAN</label><input id=iban name=iban>
 <label for=number>Contribution number</label><input id=number name=number>
 <button type=submit>Confirm direct debit</button></form>""")


@router.post("/forms/direct-debit")
def debit_submit(name: str = Form(""), iban: str = Form("")):
    if not name or not iban:
        return page("Missing", "<p class=none>Please fill in all fields.</p>")
    return done("direct debit mandate")
