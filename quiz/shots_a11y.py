#!/usr/bin/env python3
"""Verify the accessibility menu renders + works on the quiz page."""
import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots"); os.makedirs(OUT, exist_ok=True)
BASE = "http://127.0.0.1:8099"


def wait_up(t=30):
    for _ in range(t * 2):
        try:
            urllib.request.urlopen(BASE + "/api/quiz/next", timeout=1)
        except urllib.error.HTTPError:
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "quiz", "run_local_demo.py")], cwd=ROOT)
    errors = []
    try:
        if not wait_up():
            print("server didn't start"); return 1
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 880, "height": 1180}, device_scale_factor=2)
            ctx.add_cookies([{"name": "synapse_user", "value": "42", "url": BASE}])
            pg = ctx.new_page()
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(BASE + "/quiz")
            pg.wait_for_selector(".opt", timeout=10000)

            fab = pg.query_selector("#a11yFab")
            print("a11y FAB present:", fab is not None)
            print("FAB aria-label:", fab.get_attribute("aria-label") if fab else None)
            pg.click("#a11yFab")
            pg.wait_for_selector("#a11yPanel.open", timeout=5000)
            print("panel opened:", pg.query_selector("#a11yPanel.open") is not None)
            pg.wait_for_timeout(300)
            pg.screenshot(path=os.path.join(OUT, "a11y_menu.png"), full_page=True)

            # exercise a toggle (dark mode) — proves it works, not just renders
            pg.click('.a11y-btn[data-mode="dark-mode"]')
            pg.wait_for_timeout(300)
            dark = pg.eval_on_selector("body", "el => el.classList.contains('dark-mode')")
            pressed = pg.get_attribute('.a11y-btn[data-mode="dark-mode"]', "aria-pressed")
            print("dark-mode applied:", dark, "| aria-pressed:", pressed)
            pg.screenshot(path=os.path.join(OUT, "a11y_dark.png"), full_page=True)

            # synapse_a11y suite present?
            has_suite = pg.evaluate("typeof window.synapseToggleReadingMask === 'function'")
            print("synapse_a11y suite loaded (synapseToggleReadingMask is fn):", has_suite)
            b.close()
    finally:
        srv.terminate()
        try: srv.wait(timeout=5)
        except Exception: srv.kill()
    print("CONSOLE/PAGE ERRORS:", errors if errors else "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
