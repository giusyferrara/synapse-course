#!/usr/bin/env python3
"""Side-by-side: quiz toolbar (local) vs index toolbar (live via SSH tunnel)."""
import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots"); os.makedirs(OUT, exist_ok=True)
QUIZ = "http://127.0.0.1:8099"
INDEX = "http://127.0.0.1:6281"   # SSH-tunnelled to the live app


def up(url):
    try:
        urllib.request.urlopen(url + "/api/quiz/next", timeout=1)
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False
    return True


def shoot(pg, base, path, label):
    pg.goto(base, wait_until="domcontentloaded")
    pg.wait_for_selector('button[title="Accessibility"]', timeout=12000)
    pg.click('button[title="Accessibility"]')        # open the inline #accessBtns row
    pg.wait_for_timeout(500)
    pg.screenshot(path=path, clip={"x": 0, "y": 0, "width": 1280, "height": 120})
    print("captured", label, "->", os.path.basename(path))


def main():
    srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "quiz", "run_local_demo.py")], cwd=ROOT)
    try:
        for _ in range(40):
            if up(QUIZ): break
            time.sleep(0.5)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 1280, "height": 700}, device_scale_factor=2)
            ctx.add_cookies([
                {"name": "synapse_user", "value": "42", "url": QUIZ},
                {"name": "synapse_user", "value": "1", "url": INDEX},
            ])
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

            shoot(pg, QUIZ + "/quiz", os.path.join(OUT, "toolbar_quiz.png"), "quiz (local, new module)")
            print("QUIZ console/page errors:", errs if errs else "none")

            errs2 = []
            pg.on("pageerror", lambda e: errs2.append(str(e)))
            try:
                shoot(pg, INDEX + "/app", os.path.join(OUT, "toolbar_index.png"), "index (live)")
            except Exception as e:
                print("INDEX capture skipped:", e)
            b.close()
    finally:
        srv.terminate()
        try: srv.wait(timeout=5)
        except Exception: srv.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
