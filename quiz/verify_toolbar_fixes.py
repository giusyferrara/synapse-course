#!/usr/bin/env python3
"""Verify focus-spotlight + high-contrast fixes on the quiz page; capture screenshots."""
import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots"); os.makedirs(OUT, exist_ok=True)
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
            ctx = b.new_context(viewport={"width": 1280, "height": 820}, device_scale_factor=2)
            ctx.add_cookies([{"name": "synapse_user", "value": "42", "url": B}])
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(B + "/quiz", wait_until="domcontentloaded")
            pg.wait_for_selector(".opt", timeout=10000)
            pg.click('button[title="Accessibility"]'); pg.wait_for_timeout(200)

            snap = lambda: pg.evaluate("""() => ({
              cls: document.body.className,
              overlay: !!(document.getElementById('synapseFocusOverlay')||{classList:{contains:()=>false}}).classList.contains('active'),
              hint: !!document.getElementById('synapseFocusHint'),
              spotlit: !!document.querySelector('[style*="rgba(16, 185, 129"]'),
              bodyBg: getComputedStyle(document.body).backgroundColor,
              cardBg: (document.querySelector('.card')?getComputedStyle(document.querySelector('.card')).backgroundColor:null),
              optBg: (document.querySelector('.opt')?getComputedStyle(document.querySelector('.opt')).backgroundColor:null)
            })""")

            print("== HIGH CONTRAST ==")
            pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(200)
            s = snap(); print("  ON:", {k: s[k] for k in ("cls", "bodyBg", "cardBg", "optBg")})
            pg.screenshot(path=os.path.join(OUT, "fix_high_contrast.png"), full_page=False)
            pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(200)
            print("  OFF:", {k: snap()[k] for k in ("cls", "bodyBg")})

            print("\n== FOCUS MODE (hover spotlight) ==")
            pg.click('button[title="Focus Mode"]'); pg.wait_for_timeout(200)
            box = pg.query_selector("#card").bounding_box()
            pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2); pg.wait_for_timeout(300)
            s = snap(); print("  ON + hovering card:", {k: s[k] for k in ("overlay", "hint", "spotlit")})
            pg.screenshot(path=os.path.join(OUT, "fix_focus_spotlight.png"), full_page=False)
            pg.click('button[title="Focus Mode"]'); pg.wait_for_timeout(200)
            s = snap(); print("  OFF (exit):", {k: s[k] for k in ("overlay", "hint", "spotlit")})

            print("\n== FOCUS ASSISTANT (click-pin) — the previously-stuck one ==")
            pg.click('button[title="Focus Assistant"]'); pg.wait_for_timeout(200)
            pg.click("#card", position={"x": 40, "y": 40}); pg.wait_for_timeout(300)
            s = snap(); print("  ON + clicked card:", {k: s[k] for k in ("overlay", "hint", "spotlit")})
            pg.click('button[title="Focus Assistant"]'); pg.wait_for_timeout(300)
            s = snap(); print("  OFF (exit button works now):", {k: s[k] for k in ("overlay", "hint", "spotlit")})

            print("\nconsole/page errors:", errs if errs else "none")
            b.close()
    finally:
        srv.terminate()
        try: srv.wait(timeout=5)
        except Exception: srv.kill()


if __name__ == "__main__":
    main()
