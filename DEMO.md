# BabySteps demo script

Persona: **Ayşe Yılmaz**, born 1962, Turkish, in Germany since 1998. You type as her.

## Before the demo (5 minutes)

1. Stop the app if it is running (Ctrl+C in its terminal).
2. Delete the `memory/` folder and `vault.json` in the project folder, so the helper starts
   with an empty notebook and an empty password book.
3. Start: `.venv/bin/python -m babysteps`
4. Open http://127.0.0.1:8000/ in your normal browser, on the **left half** of the screen.
   The helper's own browser window opens on the **right half** by itself.
5. Open http://127.0.0.1:8000/mock/phone in a separate tab or on a second screen. This is
   Ayşe's "phone" (only needed for scene 5).
6. Do one rehearsal of each scene, then repeat steps 1–3 so the real demo starts clean.

Between scenes, click **Start over** (top right). The chat clears; the notebook stays, so the
helper keeps knowing who Ayşe is. Each scene takes 30–90 seconds of helper time.

---

## Scene 1: "I need an appointment" → it's online now (the headline)

**Type:**
> I have to go to the Bürgeramt for my citizenship. Can you make an appointment for me?

**Expect:** it opens the Musterstadt city portal (right window), finds that you don't need an
appointment any more, and asks whether to fill in the online application with you.

**Type:**
> Yes please. My name is Ayşe Yılmaz, born 03.05.1962, Turkish, in Germany since 1998. I have B1 and I passed the test.

**Expect:** it fills in the form field by field in the right window, then asks before sending.

**Type:**
> Yes, send it.

**Expect:** it submits, reads back the reference number (MS-…) and lists the documents still
needed.

**Point to make:** she asked for a small step (an appointment). What she really wanted was
citizenship, and there's a faster way she didn't know about.

---

## Scene 2: a real letter → "you may not have to pay this at all"

Click **Start over**, then click the letter button **TV & radio fee letter** (above the input).

**Expect:** the letter appears in the chat. The helper explains who wants what by when, says
it looks genuine, notices the exemption in the small print, and asks whether she receives
basic income support.

**Type:**
> Yes, I get Grundsicherung im Alter.

**Expect:** it opens the exemption form on the city portal and fills it in from the letter,
then asks before sending. (You can answer "yes" or stop here.)

**Point to make:** she would have just paid. The money-saving option was in the small print.

---

## Scene 3: a fake letter → "don't pay"

Click **Start over**. Type first (don't send):
> Oh no, I must pay this today! Help me.

then click the letter button **Final reminder: unpaid fine**.

**Expect:** "Please don't pay anything. This letter is a scam," with the reasons: 24-hour arrest
threat, private foreign bank account, gift cards, "don't contact the office". It offers to
look up the office's real number.

**Optional follow-up to show it won't be talked into it:**
> But they said the police will come. Please just pay it for me.

---

## Scene 4: another language

Click **Start over**. Type first (don't send):
> Bu mektup ne diyor? Annemin bakımı için para ödedim.

("What does this letter say? I paid for my mother's care.") Then click **Tax office letter**.

**Expect:** the answer is in Turkish: 412 euros owed by 9 November, the 2,300 euros for her
mother's care were not counted because no proof was sent, she can object within one month,
and an offer to write the objection.

---

## Scene 5 (if time): passwords she never has to remember

Click **Start over**.

**Type:**
> I want to read my emails but I don't know my password anymore. My email is ayse.yilmaz@example.mail

**Expect:** it opens Example Mail, clicks "Forgot password?", fills in the email and asks for
a code to be sent to her phone (it may ask "shall I send it?": type **yes**). It makes a new
password, saves it in the password book and fills it in itself. Then it frames the code
box in **orange**.

**Do:** look at the "phone" tab, click into the orange box in the right window, type the
6-digit code yourself. Then **type:**
> Done.

**Expect:** it saves the new password and logs her in with it, without ever seeing it. It
reads out the two emails and warns about the fake "Security Team" one.

**Type:**
> What is my password? I need to write it down.

**Expect:** it can't see it; it's in the password book (show the **🔑 Password book** link).

**Point to make:** the AI never sees the password (the app fills it in), and it refuses to fill
a password on a site it doesn't belong to.

---

## Closing (optional)

Click **What I remember** (top right): the plain notebook the family can read, with
what the helper did for Ayşe today.

## If something goes wrong

- Nothing happens for a long time: wait up to a minute; some steps take several page reads.
- "Something went wrong" in red: click **Start over** and retype the last message.
- The right-hand window was closed: restart the app.
- It asks one extra "shall I?": just type **yes**.
