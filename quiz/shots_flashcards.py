import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots"); os.makedirs(OUT, exist_ok=True)
B = "http://127.0.0.1:8097"; suffix = sys.argv[1] if len(sys.argv) > 1 else "before"
def up():
    try: urllib.request.urlopen(B + "/flashcards", timeout=1); return True
    except Exception: return False
srv = subprocess.Popen([sys.executable, os.path.join(ROOT, "quiz", "run_flashcards_demo.py")], cwd=ROOT)
try:
    for _ in range(40):
        if up(): break
        time.sleep(0.5)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 1280, "height": 760}, device_scale_factor=2)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(B + "/flashcards", wait_until="domcontentloaded"); pg.wait_for_timeout(1200)
        pg.screenshot(path=os.path.join(OUT, "flashcards_%s.png" % suffix))
        has_toolbar = pg.query_selector("#synapseA11yNav") is not None
        print("suffix=%s  toolbar_present=%s  console_errors=%s" % (suffix, has_toolbar, errs if errs else "none"))
        if suffix == "after" and has_toolbar:
            pg.click('button[title="Accessibility"]'); pg.wait_for_timeout(400)
            pg.screenshot(path=os.path.join(OUT, "flashcards_after_open.png"), clip={"x":0,"y":0,"width":1280,"height":120})
            print("  captured flashcards_after_open.png")
        b.close()
finally:
    srv.terminate()
    try: srv.wait(timeout=5)
    except Exception: srv.kill()
