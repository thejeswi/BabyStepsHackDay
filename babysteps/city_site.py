"""'ServicePortal Musterstadt': a fictional city services portal for the demo, in German.

The look follows the style of a typical German city service portal (square Arial layout,
dark-blue arrow buttons, red portal title), with fictional names and no real logos, plus a
'Demo' badge, so it cannot pass for a real site.

Demo cases: the appointment calendar has no free slots for citizenship or address
registration, but both can be done online (and the pages say so). Passport renewal really
needs an appointment, and slots exist. Also hosts the broadcasting-fee exemption form named
in the demo letter. State is in memory. All rules shown are invented demo content.
"""
import html
import secrets

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/city")
SUBMISSIONS: list[dict] = []

STYLE = """
<style>
 body{font:1rem/1.5 Arial,sans-serif;color:#000;background:#fff;margin:0}
 a{color:#165be0}
 .brandrow{height:44px;display:flex;align-items:center;padding:0 24px;color:#e40422;font-weight:bold;font-size:20px;letter-spacing:.5px;border-bottom:1px solid #dddddd}
 .pageheader{min-height:86px;padding:12px 24px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 5px rgba(0,0,0,.1)}
 .pageheader .institution{color:#e40422;font-size:18px;font-weight:bold;display:block}
 .pageheader .sub{font-size:14px}
 .pageheader nav a{color:#000;text-decoration:none;margin-left:1.2em;font-size:1.1em}
 .breadcrumb{font-size:14px;color:#454545;padding:8px 24px;background:#f5f5f5}
 main{max-width:800px;margin:0 auto;padding:0 24px 40px}
 h1{font-size:1.6875em;font-weight:700;line-height:1.15;margin:1.2em 0 1em}
 h2{font-size:1.2em;margin:1.6em 0 .5em;border-bottom:1px solid #dddddd;padding-bottom:4px}
 .button{display:inline-block;position:relative;min-height:43px;padding:10px 55px 10px 16px;border:1px solid #001c3e;border-radius:0;background:#fff;color:#000;font:1em Arial,sans-serif;text-decoration:none;cursor:pointer;box-sizing:border-box;margin-top:16px}
 .button::after{content:"›";position:absolute;right:0;top:0;bottom:0;width:39px;background:#001c3e;color:#fff;display:flex;align-items:center;justify-content:center;font-size:1.4em}
 .button:hover{background:#f2f2f2}
 .onlinebox{background:#001c3e;color:#fff;padding:16px 24px;margin:16px 0}
 .onlinebox a.button,.onlinebox .button{background:transparent;border:2px solid #fff;color:#fff}
 .onlinebox .button::after{background:transparent;border-left:2px solid #fff}
 label{display:block;margin-top:14px;font-weight:bold}
 label.check{font-weight:normal}
 input,select{display:block;width:100%;min-height:43px;border:1px solid #737373;border-radius:0;padding:10px;font:1em Arial,sans-serif;box-sizing:border-box;margin-top:4px}
 input[type=checkbox],input[type=radio]{display:inline-block;width:auto;min-height:0;margin-right:8px}
 input:focus,select:focus{border:2px solid #0076dd;outline:2px solid #fff;box-shadow:0 0 8px rgba(102,175,233,.8)}
 .box{background:#f5f5f5;padding:16px 24px;margin:16px 0}
 .none{border-left:6px solid #d52f2e;background:#fff3f3;padding:12px 16px;margin:16px 0}
 .ok{border-left:6px solid #15846e;background:#effaf6;padding:12px 16px;margin:16px 0}
 .slot{display:block;margin:8px 0}
 footer{background:#001c3e;color:#fff;padding:20px 24px;font-size:14px;margin-top:40px}
 footer a{color:#fff;margin-right:18px}
 .demo-badge{position:fixed;bottom:8px;right:8px;background:#ff4f4f;color:#fff;font-size:12px;padding:2px 8px}
</style>"""


def page(title: str, crumb: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html><html lang=de><head><meta charset=utf-8>
<title>{title} - ServicePortal Musterstadt</title>{STYLE}</head><body>
<div class=brandrow>Musterstadt</div>
<div class=pageheader><div><span class=institution>ServicePortal</span><span class=sub>Stadt Musterstadt</span></div>
<nav><a href="/city/">Dienstleistungen</a><a href="/city/standorte">Standorte</a><a href="/city/termin">Terminvereinbarung</a><a href="/city/formulare">Themen</a></nav></div>
<div class=breadcrumb>Sie befinden sich hier: ServicePortal Musterstadt › {crumb}</div>
<main>{body}</main>
<footer><a href="/city/">Service</a><a href="/city/standorte">Behörden</a><a href="/city/formulare">Formulare</a><a href="#">zum Seitenanfang</a></footer>
<div class=demo-badge>Demo · fiktive Stadt</div></body></html>""")


def done(what: str, extra: str = "") -> HTMLResponse:
    ref = "MS-" + secrets.token_hex(3).upper()
    SUBMISSIONS.append({"what": what, "ref": ref})
    return page("Eingang bestätigt", "Bestätigung",
                f"<h1>Vielen Dank! Ihr Antrag ist eingegangen.</h1><div class=ok>Ihre Vorgangsnummer lautet "
                f"<b>{ref}</b>. Bitte bewahren Sie sie auf.</div>{extra}")


def back(href: str, msg: str) -> HTMLResponse:
    return page("Fehler", "Fehler", f"<h1>Es ist ein Fehler aufgetreten</h1><div class=none>{html.escape(msg)}</div>"
                f"<a class=button href='{href}'>Zurück</a>")


@router.get("/")
def home() -> HTMLResponse:
    return page("Dienstleistungen", "Dienstleistungen", """
<h1>Dienstleistungen der Stadt Musterstadt</h1>
<p>Was möchten Sie erledigen?</p>
<div class=box><a href="/city/termin">Termin beim Bürgeramt buchen</a></div>
<div class=box><a href="/city/einbuergerung">Einbürgerung - Verleihung der deutschen Staatsangehörigkeit beantragen</a></div>
<div class=box><a href="/city/anmeldung">Wohnsitz - Alleinige Wohnung oder Hauptwohnung anmelden</a></div>
<div class=box><a href="/city/formulare">Formulare: Befreiung vom Rundfunkbeitrag, Lastschrift und mehr</a></div>""")


@router.get("/standorte")
def standorte() -> HTMLResponse:
    return page("Standorte", "Standorte", "<h1>Standorte</h1><div class=box><b>Bürgeramt Musterstadt-Mitte</b><br>"
                "Rathausplatz 1, 12345 Musterstadt<br>Öffnungszeiten: nur mit Termin</div>")


@router.get("/termin")
def termin() -> HTMLResponse:
    return page("Terminvereinbarung", "Terminvereinbarung", """
<h1>Online-Terminbuchung bei Musterstädter Behörden</h1>
<h2>Terminbuchung über die Auswahl einer Dienstleistung</h2>
<form method=get action="/city/termin/auswahl">
 <label for=service>Dienstleistung</label>
 <select id=service name=service>
  <option value="">Bitte auswählen …</option>
  <option value="citizenship">Einbürgerung</option>
  <option value="registration">Anmeldung einer Wohnung</option>
  <option value="passport">Reisepass / Personalausweis beantragen</option>
 </select>
 <button class=button type=submit>Termin suchen</button>
</form>
<h2>Termin ändern oder absagen</h2><p>Nutzen Sie den Link in Ihrer Bestätigungs-E-Mail.</p>""")


@router.get("/termin/auswahl")
def slots(service: str = "") -> HTMLResponse:
    if service == "citizenship":
        return page("Terminvereinbarung", "Terminvereinbarung › Einbürgerung", """
<h1>Einbürgerung</h1>
<div class=none>Leider sind aktuell keine Termine für ihre Auswahl verfügbar.</div>
<div class=onlinebox><b>Neu: Einbürgerung ohne Termin.</b> Seit diesem Jahr können Sie die Einbürgerung
vollständig online beantragen. Das dauert etwa 15 Minuten.<br>
<a class=button href="/city/einbuergerung/online">Jetzt online erledigen</a></div>""")
    if service == "registration":
        return page("Terminvereinbarung", "Terminvereinbarung › Anmeldung", """
<h1>Anmeldung einer Wohnung</h1>
<div class=none>Leider sind aktuell keine Termine für ihre Auswahl verfügbar.</div>
<div class=onlinebox><b>Schneller: online anmelden.</b> Sie können Ihre Wohnung online anmelden. Sie brauchen
die Wohnungsgeberbestätigung Ihres Vermieters.<br>
<a class=button href="/city/anmeldung/online">Jetzt online erledigen</a></div>""")
    if service == "passport":
        times = ["Di, 20.10.2026, 09:30 Uhr", "Di, 20.10.2026, 11:00 Uhr", "Do, 22.10.2026, 14:15 Uhr"]
        opts = "".join(f"<label class='slot check'><input type=radio name=slot value='{t}'> {t} · Bürgeramt Mitte</label>"
                       for t in times)
        return page("Terminvereinbarung", "Terminvereinbarung › Reisepass", f"""
<h1>Reisepass / Personalausweis beantragen</h1>
<p>Für einen Reisepass müssen Sie persönlich vorsprechen (Foto und Fingerabdrücke).</p>
<h2>Bitte wählen Sie eine Uhrzeit</h2>
<form method=post action="/city/termin/buchen"><input type=hidden name=service value=passport>
 {opts}
 <h2>Termin eintragen</h2>
 <label for=name>Name</label><input id=name name=name>
 <label for=email>E-Mail</label><input id=email name=email type=email>
 <button class=button type=submit>Termin eintragen</button></form>""")
    return back("/city/termin", "Bitte wählen Sie eine Dienstleistung aus.")


@router.post("/termin/buchen")
def book(service: str = Form(""), slot: str = Form(""), name: str = Form("")):
    if not slot or not name:
        return back("/city/termin/auswahl?service=passport", "Bitte wählen Sie eine Uhrzeit und geben Sie Ihren Namen ein.")
    return done(f"Termin ({html.escape(slot)})",
                "<p>Bitte mitbringen: Ihren alten Reisepass, ein biometrisches Passfoto, Gebühr 70 EUR.</p>")


@router.get("/einbuergerung")
def citizenship() -> HTMLResponse:
    return page("Einbürgerung", "Dienstleistungen › Einbürgerung", """
<h1>Einbürgerung - Verleihung der deutschen Staatsangehörigkeit beantragen</h1>
<p>Sie leben dauerhaft in Musterstadt und möchten die deutsche Staatsangehörigkeit erwerben.</p>
<div class=onlinebox><b>Online Verfahren:</b> Die Einbürgerung kann vollständig online beantragt werden.
Ein Termin ist nicht erforderlich.<br><a class=button href="/city/einbuergerung/online">Jetzt online erledigen</a></div>
<h2>Voraussetzungen</h2><ul><li>seit mindestens 5 Jahren rechtmäßiger gewöhnlicher Aufenthalt in Deutschland</li>
<li>Sicherung des Lebensunterhalts</li><li>Deutschkenntnisse auf Niveau B1</li><li>bestandener Einbürgerungstest</li></ul>
<h2>Erforderliche Unterlagen</h2><ul><li>Reisepass</li><li>Geburtsurkunde</li><li>Einkommensnachweise der letzten 3 Monate</li></ul>
<h2>Gebühren</h2><p>255 EUR</p>
<h2>Für Sie zuständig</h2><div class=box><b>Bürgeramt Musterstadt-Mitte</b><br>
<a class=button href="/city/termin">An diesem Standort einen Termin buchen</a></div>""")


@router.get("/einbuergerung/online")
def citizenship_form() -> HTMLResponse:
    return page("Einbürgerung online", "Einbürgerung › Online-Antrag", """
<h1>Online-Antrag: Einbürgerung</h1>
<form method=post action="/city/einbuergerung/online">
 <label for=name>Vor- und Nachname</label><input id=name name=name>
 <label for=birth>Geburtsdatum</label><input id=birth name=birth placeholder="TT.MM.JJJJ">
 <label for=nationality>Derzeitige Staatsangehörigkeit</label><input id=nationality name=nationality>
 <label for=since>In Deutschland seit (Jahr)</label><input id=since name=since>
 <label for=german>Deutsch-Sprachzertifikat</label>
 <select id=german name=german><option>noch keines</option><option>A2</option><option>B1</option><option>B2 oder höher</option></select>
 <label class=check><input type=checkbox name=test value=yes> Ich habe den Einbürgerungstest bestanden</label>
 <button class=button type=submit>Antrag absenden</button>
</form>""")


@router.post("/einbuergerung/online")
def citizenship_submit(name: str = Form(""), german: str = Form(""), test: str = Form("")):
    if not name:
        return back("/city/einbuergerung/online", "Bitte geben Sie Ihren Namen ein.")
    missing = []
    if german in ("noch keines", "A2"):
        missing.append("Deutsch-Zertifikat auf Niveau B1 (Kurse z. B. an der Volkshochschule)")
    if test != "yes":
        missing.append("Zertifikat über den Einbürgerungstest")
    todo = "".join(f"<li>{m}</li>" for m in missing)
    return done("Einbürgerungsantrag",
                "<p>Bitte laden Sie innerhalb von 4 Wochen hoch: Kopie des Reisepasses, Geburtsurkunde, "
                "Einkommensnachweise der letzten 3 Monate.</p>" + (f"<p><b>Es fehlt noch:</b></p><ul>{todo}</ul>" if todo else ""))


@router.get("/anmeldung")
def registration() -> HTMLResponse:
    return page("Anmeldung", "Dienstleistungen › Anmeldung", """
<h1>Wohnsitz - Alleinige Wohnung oder Hauptwohnung anmelden</h1>
<p>Wenn Sie eine Wohnung beziehen, müssen Sie sich innerhalb von 14 Tagen nach Ihrem Einzug anmelden.</p>
<div class=onlinebox><b>Online Verfahren:</b> ohne Termin, rund um die Uhr.<br>
<a class=button href="/city/anmeldung/online">Jetzt online erledigen</a></div>
<h2>Erforderliche Unterlagen</h2><ul><li>Personalausweis oder Reisepass</li><li>Wohnungsgeberbestätigung</li></ul>""")


@router.get("/anmeldung/online")
def registration_form() -> HTMLResponse:
    return page("Anmeldung online", "Anmeldung › Online-Anmeldung", """
<h1>Wohnung online anmelden</h1>
<form method=post action="/city/anmeldung/online">
 <label for=name>Vor- und Nachname</label><input id=name name=name>
 <label for=address>Neue Anschrift</label><input id=address name=address>
 <label for=movein>Einzugsdatum</label><input id=movein name=movein placeholder="TT.MM.JJJJ">
 <label class=check><input type=checkbox name=landlord value=yes> Die Wohnungsgeberbestätigung liegt mir vor</label>
 <button class=button type=submit>Anmeldung absenden</button>
</form>""")


@router.post("/anmeldung/online")
def registration_submit(name: str = Form(""), address: str = Form(""), landlord: str = Form("")):
    if not name or not address:
        return back("/city/anmeldung/online", "Bitte geben Sie Ihren Namen und die neue Anschrift ein.")
    if landlord != "yes":
        return back("/city/anmeldung/online", "Sie brauchen zuerst die Wohnungsgeberbestätigung Ihres Vermieters.")
    return done("Anmeldung", "<p>Ihre Meldebescheinigung kommt innerhalb von 2 Wochen per Post.</p>")


@router.get("/formulare")
def forms() -> HTMLResponse:
    return page("Formulare", "Formulare", """
<h1>Formulare</h1>
<div class=box><a href="/city/formulare/rundfunk-befreiung">Befreiung vom Rundfunkbeitrag beantragen</a></div>
<div class=box><a href="/city/formulare/lastschrift">Lastschrift für den Rundfunkbeitrag (SEPA-Mandat)</a></div>""")


@router.get("/formulare/rundfunk-befreiung")
def exemption_form() -> HTMLResponse:
    return page("Befreiung Rundfunkbeitrag", "Formulare › Befreiung vom Rundfunkbeitrag", """
<h1>Antrag auf Befreiung vom Rundfunkbeitrag</h1>
<p>Eine Befreiung ist möglich, wenn Sie eine der folgenden Leistungen erhalten. Den Leistungsbescheid reichen Sie später nach.</p>
<form method=post action="/city/formulare/rundfunk-befreiung">
 <label for=name>Vor- und Nachname</label><input id=name name=name>
 <label for=number>Beitragsnummer</label><input id=number name=number>
 <label for=reason>Welche Leistung erhalten Sie?</label>
 <select id=reason name=reason><option value="">Bitte auswählen …</option>
  <option>Grundsicherung im Alter und bei Erwerbsminderung</option>
  <option>Bürgergeld</option>
  <option>Wohngeld</option>
  <option>keine dieser Leistungen</option></select>
 <button class=button type=submit>Antrag absenden</button>
</form>""")


@router.post("/formulare/rundfunk-befreiung")
def exemption_submit(name: str = Form(""), number: str = Form(""), reason: str = Form("")):
    if not name or not number or not reason:
        return back("/city/formulare/rundfunk-befreiung", "Bitte füllen Sie alle Felder aus.")
    if reason == "keine dieser Leistungen":
        return page("Keine Befreiung", "Formulare", "<h1>Befreiung nicht möglich</h1>"
                    "<p>Ohne eine dieser Leistungen ist eine Befreiung in der Regel nicht möglich.</p>")
    return done("Antrag auf Befreiung vom Rundfunkbeitrag",
                "<p>Bitte senden Sie innerhalb von 4 Wochen eine Kopie Ihres Leistungsbescheids.</p>")


@router.get("/formulare/lastschrift")
def debit_form() -> HTMLResponse:
    return page("Lastschrift", "Formulare › Lastschrift", """
<h1>SEPA-Lastschriftmandat für den Rundfunkbeitrag</h1>
<form method=post action="/city/formulare/lastschrift">
 <label for=name>Kontoinhaber</label><input id=name name=name>
 <label for=iban>IBAN</label><input id=iban name=iban>
 <label for=number>Beitragsnummer</label><input id=number name=number>
 <button class=button type=submit>Mandat erteilen</button></form>""")


@router.post("/formulare/lastschrift")
def debit_submit(name: str = Form(""), iban: str = Form("")):
    if not name or not iban:
        return back("/city/formulare/lastschrift", "Bitte füllen Sie alle Felder aus.")
    return done("SEPA-Lastschriftmandat")
