#!/usr/bin/env python3
"""Diagnose focus-mode / focus-assistant / high-contrast on the quiz page."""
import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = "http://127.0.0.1:8099"


def up():
    try: urllib.request.urlopen(B + "/api/quiz/next", timeout=1); return True
    except urllib.error.HTTPError: return True
    except Exception: return False


def main():
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "quiz", "run_local_demo.py")], cwd=ROOT)
    try:
        for _ in range(40):
            if up(): break
            time.sleep(0.5)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1280, "height": 800})
            ctx.add_cookies([{"name": "synapse_user", "value": "42", "url": B}])
            pg = ctx.new_page()
            pg.goto(B + "/quiz", wait_until="domcontentloaded")
            pg.wait_for_selector(".opt", timeout=10000)
            pg.click('button[title="Accessibility"]'); pg.wait_for_timeout(200)

            def snap(tag):
                return pg.evaluate("""() => ({
                  bodyClass: document.body.className,
                  focusOverlay: !!document.getElementById('focusOverlay'),
                  synFocusOverlayActive: !!(document.getElementById('synapseFocusOverlay')||{}).classList && document.getElementById('synapseFocusOverlay').classList.contains('active'),
                  focusMessage: !!document.getElementById('focusMessage'),
                  bodyBg: getComputedStyle(document.body).backgroundColor,
                  bodyColor: getComputedStyle(document.body).color,
                  optBg: (document.querySelector('.opt')? getComputedStyle(document.querySelector('.opt')).backgroundColor : null),
                  cardBg: (document.querySelector('.card')? getComputedStyle(document.querySelector('.card')).backgroundColor : null)
                })""")

            print("== HIGH CONTRAST (⚫⚪) ==")
            print("  baseline:", snap("base"))
            pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(200)
            print("  after 1st click:", snap("hc-on"))
            pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(200)
            print("  after 2nd click:", snap("hc-off"))

            print("\n== FOCUS MODE (🎯, module toggleFocusMode) ==")
            pg.click('button[title="Focus Mode"]'); pg.wait_for_timeout(200)
            print("  after 1st click:", snap("fm-on"))
            pg.click('button[title="Focus Mode"]'); pg.wait_for_timeout(200)
            print("  after 2nd click:", snap("fm-off"))

            print("\n== FOCUS ASSISTANT (💡, focus_assistant.js) ==")
            pg.click('button[title="Focus Assistant"]'); pg.wait_for_timeout(300)
            print("  after 1st click:", snap("fa-on"))
            # try to turn off by clicking the button again
            try:
                pg.click('button[title="Focus Assistant"]', timeout=3000); pg.wait_for_timeout(300)
                print("  after 2nd click (try exit):", snap("fa-off-attempt"))
            except Exception as e:
                print("  2nd click FAILED (button unclickable):", str(e)[:80])
            b.close()
    finally:
        srv.terminate()
        try: srv.wait(timeout=5)
        except Exception: srv.kill()


if __name__ == "__main__":
    main()
