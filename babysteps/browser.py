"""The agent's browser: a visible Chromium window with a fresh, empty profile.

Safety limits are enforced here in code, not in the prompt:
- main-frame navigations to hosts outside config.ALLOWED_HOSTS are aborted;
- paths in config.BLOCKED_PATH_PREFIXES are aborted (the fake phone);
- downloads are refused;
- typing into password fields is refused (the user types secrets themselves);
- clicks on irreversible-looking buttons need the user's answer first (see agent.py).
"""
import asyncio
import re
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, Request, Route, async_playwright

from . import config

# Assigns a number to each visible interactive element and returns a compact listing.
# Password values are never returned. Runs inside the page.
_READ_PAGE_JS = r"""
(maxElements) => {
  document.querySelectorAll('[data-bs-ref]').forEach(e => e.removeAttribute('data-bs-ref'));
  // The orange frame is for one request only; it disappears once the helper looks again.
  document.querySelectorAll('[data-bs-highlight]').forEach(e => { e.style.outline = ''; e.removeAttribute('data-bs-highlight'); });
  const sel = 'a[href], button, input, select, textarea, [role=button], [role=link], [role=checkbox], [onclick]';
  const out = [];
  let n = 0;
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (r.width === 0 || r.height === 0 || st.visibility === 'hidden' || st.display === 'none') continue;
    if (el.type === 'hidden') continue;
    n += 1;
    if (n > maxElements) break;
    el.setAttribute('data-bs-ref', String(n));
    const tag = el.tagName.toLowerCase();
    let label = '';
    if (el.id) { const l = document.querySelector(`label[for="${el.id}"]`); if (l) label = l.innerText.trim(); }
    if (!label && el.closest('label')) label = el.closest('label').innerText.trim();
    const text = (el.innerText || el.value || '').trim().slice(0, 80);
    const parts = [`[${n}] ${tag}`];
    if (el.type && tag === 'input') parts[0] += `(type=${el.type})`;
    if (text && tag !== 'input' && tag !== 'select' && tag !== 'textarea') parts.push(JSON.stringify(text));
    if (label) parts.push(`label=${JSON.stringify(label.slice(0, 80))}`);
    if (el.placeholder) parts.push(`placeholder=${JSON.stringify(el.placeholder)}`);
    if (el.getAttribute('aria-label')) parts.push(`aria-label=${JSON.stringify(el.getAttribute('aria-label'))}`);
    if (el.name) parts.push(`name=${JSON.stringify(el.name)}`);
    if (tag === 'a') parts.push(`href=${JSON.stringify(el.getAttribute('href'))}`);
    if (tag === 'input' || tag === 'textarea') {
      parts.push(el.type === 'password' ? (el.value ? 'value=(filled, hidden)' : 'value=(empty)') : `value=${JSON.stringify(el.value)}`);
    }
    if (tag === 'select') parts.push('options=' + JSON.stringify([...el.options].map(o => o.text)));
    if (el.type === 'checkbox' || el.type === 'radio') parts.push(el.checked ? 'checked' : 'unchecked');
    out.push(parts.join(' '));
  }
  return { elements: out, truncated: n > maxElements, text: document.body ? document.body.innerText : '' };
}
"""

_HIGHLIGHT_JS = r"""
(ref) => {
  document.querySelectorAll('[data-bs-highlight]').forEach(e => { e.style.outline = ''; e.removeAttribute('data-bs-highlight'); });
  const el = document.querySelector(`[data-bs-ref="${ref}"]`);
  if (!el) return false;
  el.setAttribute('data-bs-highlight', '1');
  el.style.outline = '6px solid #ff8800';
  el.style.outlineOffset = '4px';
  el.scrollIntoView({block: 'center'});
  return true;
}
"""

# Button texts that mean "this can't be undone". English + German, matched as whole words.
_IRREVERSIBLE = re.compile(
    r"\b(send|submit|book|buy|pay|purchase|order|delete|remove|confirm|transfer|donate|"
    r"senden|absenden|buchen|kaufen|bezahlen|zahlen|bestellen|löschen|entfernen|bestätigen|überweisen)\b",
    re.IGNORECASE,
)


class ToolError(Exception):
    """An error the model should see and react to (returned as is_error tool_result)."""


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme in ("about", "data", "blob"):
        return True
    host = (parsed.hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in config.ALLOWED_HOSTS)


def path_blocked(url: str) -> bool:
    parsed = urlparse(url)
    return any(parsed.path.startswith(p) for p in config.BLOCKED_PATH_PREFIXES)


class Browser:
    def __init__(self) -> None:
        self._pw = None
        self._browser = None
        self._context = None
        self.page: Page | None = None
        self.blocked_log: list[str] = []

    async def start(self) -> None:
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=config.HEADLESS,
            args=[
                f"--window-position={config.BROWSER_WINDOW_POSITION}",
                f"--window-size={config.BROWSER_WINDOW_SIZE}",
            ],
        )
        # A new context = fresh profile: no cookies, no saved logins from the real browser.
        self._context = await self._browser.new_context(accept_downloads=False, viewport=None)
        await self._context.route("**/*", self._route)
        self._context.on("page", self._on_new_page)
        self.page = await self._context.new_page()
        await self.page.goto(f"{config.BASE_URL}/mock/start")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    def _on_new_page(self, page: Page) -> None:
        # Links that open a new tab: follow the newest tab, as a person would.
        self.page = page

    async def _route(self, route: Route, request: Request) -> None:
        if request.is_navigation_request() and request.frame.parent_frame is None:
            if not host_allowed(request.url) or path_blocked(request.url):
                self.blocked_log.append(request.url)
                await route.abort("blockedbyclient")
                return
        await route.continue_()

    def _page(self) -> Page:
        if self.page is None:
            raise RuntimeError("Browser not started")
        return self.page

    async def _settle(self) -> None:
        page = self._page()
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception as e:  # slow pages are normal; the next read_page shows the state
            print(f"[browser] load wait ended early: {e!r}")
        await asyncio.sleep(0.4)

    def _consume_blocked(self) -> str:
        if not self.blocked_log:
            return ""
        urls = ", ".join(self.blocked_log)
        self.blocked_log.clear()
        return f" NOTE: navigation to {urls} was blocked (not an allowed site)."

    # ---- tools -----------------------------------------------------------

    async def open_url(self, url: str) -> str:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if not host_allowed(url) or path_blocked(url):
            raise ToolError(f"{url} is not an allowed site. Allowed: {', '.join(config.ALLOWED_HOSTS)}")
        page = self._page()
        try:
            await page.goto(url, timeout=15000)
        except Exception as e:
            raise ToolError(f"Could not open {url}: {e}") from e
        await self._settle()
        return f"Opened {page.url} (title: {await page.title()!r}). Call read_page to see it."

    async def read_page(self) -> str:
        page = self._page()
        for attempt in range(4):
            try:
                data = await page.evaluate(_READ_PAGE_JS, config.MAX_ELEMENTS)
                break
            except PlaywrightError as e:
                # A form submit or redirect can still be under way; wait for the new page and retry.
                if "Execution context was destroyed" not in str(e) or attempt == 3:
                    raise
                print(f"[browser] page was navigating during read (attempt {attempt + 1}); retrying")
                await self._settle()
                page = self._page()
        text = data["text"]
        cut = len(text) > config.PAGE_TEXT_LIMIT
        text = text[: config.PAGE_TEXT_LIMIT]
        lines = [
            f"URL: {page.url}",
            f"Title: {await page.title()}",
            "",
            "Interactive elements:" + (" (list cut off, scroll for more)" if data["truncated"] else ""),
            *data["elements"],
            "",
            "Visible text" + (" (cut off)" if cut else "") + ":",
            text,
        ]
        return "\n".join(lines) + self._consume_blocked()

    async def _locate(self, ref: int):
        loc = self._page().locator(f'[data-bs-ref="{ref}"]')
        if await loc.count() != 1:
            raise ToolError(f"Element [{ref}] not found. The page probably changed; call read_page again.")
        return loc

    async def element_text(self, ref: int) -> str:
        loc = await self._locate(ref)
        return (await loc.evaluate("e => (e.innerText || e.value || e.getAttribute('aria-label') || '').trim()"))

    def looks_irreversible(self, text: str) -> bool:
        return bool(_IRREVERSIBLE.search(text))

    async def click(self, ref: int) -> str:
        loc = await self._locate(ref)
        try:
            await loc.click(timeout=5000)
        except Exception as e:
            raise ToolError(f"Could not click [{ref}]: {e}") from e
        await self._settle()
        if self.blocked_log and self._page().url.startswith("chrome-error://"):
            await self._page().go_back(timeout=8000)  # don't leave the user staring at an error page
            await self._settle()
        return f"Clicked [{ref}]. Now on {self._page().url}. Call read_page to see the result." + self._consume_blocked()

    async def type_text(self, ref: int, text: str, press_enter: bool) -> str:
        loc = await self._locate(ref)
        # Whole-token match on name/id so "shipping" or "opinion" don't count as "pin".
        is_password = await loc.evaluate(
            r"""e => e.type === 'password'
                || /(current-password|new-password|one-time-code)/.test(e.autocomplete || '')
                || /(^|[_\-\s])(pass(word)?|passwort|pin|otp|code|passcode|tan|iban)([_\-\s]|$)/i.test((e.name || '') + ' ' + (e.id || ''))"""
        )
        if is_password:
            raise ToolError(
                f"[{ref}] is a password, code or bank-account field. You must not type secrets. "
                "Use ask_user_to_type so the user types it themselves."
            )
        try:
            await loc.fill(text, timeout=5000)
            if press_enter:
                await loc.press("Enter")
                await self._settle()
        except Exception as e:
            raise ToolError(f"Could not type into [{ref}]: {e}") from e
        return f"Typed into [{ref}]." + (" Pressed Enter." if press_enter else "") + self._consume_blocked()

    async def fill_secret(self, ref: int, value: str) -> None:
        """Fill a field with a secret. The value is never returned or logged."""
        loc = await self._locate(ref)
        try:
            await loc.fill(value, timeout=5000)
        except Exception as e:
            raise ToolError(f"Could not fill [{ref}]: {type(e).__name__}") from None  # message could echo the value

    async def read_secret(self, ref: int) -> str:
        """Read what the user typed into a field (for saving it). Never shown to the model."""
        loc = await self._locate(ref)
        return await loc.input_value()

    def url(self) -> str:
        return self._page().url

    async def select_option(self, ref: int, option: str) -> str:
        loc = await self._locate(ref)
        try:
            await loc.select_option(label=option, timeout=5000)
        except Exception as e:
            raise ToolError(f"Could not select {option!r} in [{ref}]: {e}") from e
        return f"Selected {option!r} in [{ref}]."

    async def highlight(self, ref: int) -> str:
        await self._locate(ref)
        ok = await self._page().evaluate(_HIGHLIGHT_JS, ref)
        if not ok:
            raise ToolError(f"Could not highlight [{ref}]")
        await self._page().bring_to_front()
        return f"Box [{ref}] is now marked with an orange frame on the user's screen."

    async def scroll(self, direction: str) -> str:
        dy = 600 if direction == "down" else -600
        await self._page().mouse.wheel(0, dy)
        await asyncio.sleep(0.3)
        return f"Scrolled {direction}. Call read_page to see the page."

    async def go_back(self) -> str:
        await self._page().go_back(timeout=8000)
        await self._settle()
        return f"Went back. Now on {self._page().url}."
