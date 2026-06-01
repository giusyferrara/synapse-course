#!/usr/bin/env python3
"""Reproduce high contrast on flashcards: default unchanged, HC front + back readable."""
import os, subprocess, sys, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots"); os.makedirs(OUT, exist_ok=True)
B = "http://127.0.0.1:8097"


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

        # default look (HC off)
        pg.screenshot(path=os.path.join(OUT, "hc_fc_default.png"))

        # turn high contrast ON
        pg.click('button[title="Accessibility"]'); pg.wait_for_timeout(200)
        pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(OUT, "hc_fc_front.png"))

        # reveal the ANSWER (back) and screenshot
        try:
            pg.click("text=Show Answer", timeout=4000); pg.wait_for_timeout(500)
            pg.screenshot(path=os.path.join(OUT, "hc_fc_back.png"))
            back_ok = True
        except Exception as e:
            back_ok = False; print("  (could not click Show Answer:", str(e)[:60], ")")

        # measure contrast on the card's text vs its background
        probe = pg.evaluate("""() => {
          const card = document.querySelector('.card, .flashcard, [class*="card"]');
          if (!card) return {found:false};
          // find a text-bearing descendant
          let txt = card.querySelector('h1,h2,h3,p,div,span,li') || card;
          const cs = getComputedStyle(txt), cb = getComputedStyle(card);
          return {found:true, textColor:cs.color, cardBg:cb.backgroundColor, bodyBg:getComputedStyle(document.body).backgroundColor};
        }""")
        print("contrast probe (HC on):", probe)

        # toggle OFF -> confirm default restored
        pg.click('button[title="High Contrast"]'); pg.wait_for_timeout(300)
        off = pg.evaluate("() => getComputedStyle(document.body).backgroundColor")
        print("body bg after HC off:", off, "(expect cream ~rgb(250,248,243))")
        print("console errors:", errs if errs else "none")
        b.close()
finally:
    srv.terminate()
    try: srv.wait(timeout=5)
    except Exception: srv.kill()
