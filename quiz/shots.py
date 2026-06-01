#!/usr/bin/env python3
"""Capture headless screenshots of the quiz UI in three states."""
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "quiz", "shots")
os.makedirs(OUT, exist_ok=True)
BASE = "http://127.0.0.1:8099"


def wait_up(timeout=30):
    for _ in range(timeout * 2):
        try:
            urllib.request.urlopen(BASE + "/api/quiz/next", timeout=1)
        except urllib.error.HTTPError:
            return True          # 401 = server is up
        except Exception:
            time.sleep(0.5)
    return False


def main():
    server = subprocess.Popen([sys.executable, os.path.join(ROOT, "quiz", "run_local_demo.py")],
                              cwd=ROOT)
    try:
        if not wait_up():
            print("server did not start"); return 1
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 880, "height": 1180},
                                      device_scale_factor=2)
            ctx.add_cookies([{"name": "synapse_user", "value": "42", "url": BASE}])
            page = ctx.new_page()

            page.goto(BASE + "/quiz")
            page.wait_for_selector(".opt", timeout=10000)
            page.wait_for_timeout(400)
            page.screenshot(path=os.path.join(OUT, "a_unanswered.png"), full_page=True)
            print("captured a_unanswered.png")

            # answer the first question -> calm feedback + explanation + source
            page.query_selector(".opt").click()
            page.click("#checkBtn")
            page.wait_for_selector("#feedback", state="visible", timeout=10000)
            page.wait_for_timeout(400)
            page.screenshot(path=os.path.join(OUT, "b_answered.png"), full_page=True)
            print("captured b_answered.png")

            # finish the rest of the quiz to reach the progress view
            for _ in range(20):
                if page.query_selector("#summary:not(.hidden)"):
                    break
                page.click("#nextBtn")
                if page.query_selector("#summary:not(.hidden)"):
                    break
                page.wait_for_selector(".opt", timeout=10000)
                page.query_selector(".opt").click()
                page.click("#checkBtn")
                page.wait_for_selector("#feedback", state="visible", timeout=10000)
            page.wait_for_selector("#progressView h3", timeout=10000)
            page.wait_for_timeout(500)
            page.screenshot(path=os.path.join(OUT, "c_progress.png"), full_page=True)
            print("captured c_progress.png")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
