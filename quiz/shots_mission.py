import os,subprocess,sys,time,urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.join(ROOT,"quiz","shots")
B="http://127.0.0.1:8095"; suf=sys.argv[1] if len(sys.argv)>1 else "before"
def up():
    try: urllib.request.urlopen(B+"/mission",timeout=1); return True
    except Exception: return False
srv=subprocess.Popen([sys.executable,os.path.join(ROOT,"quiz","run_mission_demo.py")],cwd=ROOT)
try:
    for _ in range(40):
        if up(): break
        time.sleep(0.5)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b=p.chromium.launch(); ctx=b.new_context(viewport={"width":1280,"height":300},device_scale_factor=2)
        pg=ctx.new_page(); pg.goto(B+"/mission",wait_until="domcontentloaded"); pg.wait_for_timeout(1200)
        java=pg.query_selector("#javaCourseBtn"); access=pg.query_selector("#butterflyAccessBtn")
        def vis(el): return el.is_visible() if el else False
        print(f"{suf}: javaCourse_visible={vis(java)}  accessButton_visible={vis(access)}")
        pg.screenshot(path=os.path.join(OUT,f"mission_navbar_{suf}.png"), clip={"x":0,"y":0,"width":1280,"height":110})
        if suf=="after" and access and vis(access):
            access.click(); pg.wait_for_timeout(400)
            pg.screenshot(path=os.path.join(OUT,"mission_navbar_after_open.png"), clip={"x":0,"y":0,"width":1280,"height":160})
        b.close()
finally:
    srv.terminate()
    try: srv.wait(timeout=5)
    except Exception: srv.kill()
