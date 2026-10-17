// Show the BabySteps chat (served by the Python agent server) once the server is up.
// Chrome usually starts before the server, so keep trying for a while.
const CHAT_URL = "http://127.0.0.1:8000/";  // must match BABYSTEPS_PORT

const wait = document.getElementById("wait");
const chat = document.getElementById("chat");

async function connect(attempt = 0) {
  try {
    await fetch(CHAT_URL, { method: "HEAD", cache: "no-store" });
    chat.src = CHAT_URL;
    chat.hidden = false;
    wait.hidden = true;
  } catch {
    if (attempt === 20) {
      wait.textContent = "BabySteps is not running. Please ask a family member to start it.";
    }
    setTimeout(() => connect(attempt + 1), 1000);
  }
}
connect();
