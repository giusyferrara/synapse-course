#!/usr/bin/env python3
"""ShopSecure v2.0 - Deliberately Vulnerable E-Commerce App - SYNAPSE Platform"""
from flask import (Flask, request, session, redirect, jsonify,
                   render_template_string, send_file, g)
import sqlite3, subprocess, os, pickle, base64

app = Flask(__name__)
app.secret_key = 'shopsecure-weak-key-2026'

# ============================================================================
# Reverse-proxy support: honor X-Forwarded-Prefix header sent by SYNAPSE proxy.
# Flask uses SCRIPT_NAME to build all internal URLs (url_for, redirect to
# paths that include SCRIPT_NAME automatically, session cookie paths, etc.).
# When running behind SYNAPSE labs proxy, every request carries
# X-Forwarded-Prefix: /labs/shopsecure/<token> which we forward into WSGI
# SCRIPT_NAME so Flask knows the external mount path.
# ============================================================================
class PrefixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        prefix = environ.get('HTTP_X_FORWARDED_PREFIX', '')
        if prefix:
            environ['SCRIPT_NAME'] = prefix
            path_info = environ.get('PATH_INFO', '')
            if path_info.startswith(prefix):
                environ['PATH_INFO'] = path_info[len(prefix):] or '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = PrefixMiddleware(app.wsgi_app)

# P is the path prefix used by hardcoded redirects/links in templates.
# When running behind SYNAPSE labs proxy, P gets set per-request from the
# X-Forwarded-Prefix header via before_request hook below (see after init_db).
import os as _os_shim
_DEFAULT_P = _os_shim.environ.get('APP_PATH_PREFIX', '')
P = _DEFAULT_P  # module-level; rebound per-request by before_request hook

DB = '/app/data/shop.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db: db.close()

@app.before_request
def set_prefix_from_header():
    # Rebind global P from X-Forwarded-Prefix so hardcoded '%s/login' % P
    # builds the correct external URL when running behind SYNAPSE labs proxy.
    global P
    from flask import request as _req
    P = _req.headers.get('X-Forwarded-Prefix', _DEFAULT_P)

@app.before_request
def check_db():
    try:
        db = get_db()
        db.execute("SELECT COUNT(*) FROM users").fetchone()
    except:
        init_db()

PRODUCT_IMGS = {
    1: 'https://cdn-icons-png.flaticon.com/128/689/689396.png',
    2: 'https://cdn-icons-png.flaticon.com/128/3474/3474360.png',
    3: 'https://cdn-icons-png.flaticon.com/128/2936/2936690.png',
    4: 'https://cdn-icons-png.flaticon.com/128/3389/3389081.png',
    5: 'https://cdn-icons-png.flaticon.com/128/2168/2168690.png',
    6: 'https://cdn-icons-png.flaticon.com/128/5968/5968350.png',
    7: 'https://cdn-icons-png.flaticon.com/128/4337/4337347.png',
    8: 'https://cdn-icons-png.flaticon.com/128/2965/2965567.png',
}

def init_db():
    os.makedirs('/app/data/invoices', exist_ok=True)
    db = sqlite3.connect(DB)
    c = db.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT, fullname TEXT,
            email TEXT, address TEXT, balance REAL DEFAULT 100.0,
            role TEXT DEFAULT 'user', card_number TEXT
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, description TEXT, price REAL,
            category TEXT, stock INTEGER DEFAULT 10
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER, username TEXT, rating INTEGER,
            comment TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user TEXT, to_user TEXT, amount REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES(NULL,'admin','adminShop2026','Admin User','admin@shopsecure.com','1 Admin St',99999.0,'admin','4111-1111-1111-1111')")
        for i in range(1, 6):
            c.execute("INSERT INTO users VALUES(NULL,'user%d','user%dPass!','User %d','user%d@example.com','%d0 Oak St',%d00.0,'user','4%d%d%d-%d%d%d%d-%d%d%d%d-%d%d%d%d')" % (i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i,i))
        products = [
            ('Laptop Pro 15','High-performance laptop with 16GB RAM and 512GB SSD. Perfect for developers.',999.99,'Electronics',15),
            ('Wireless Mouse','Ergonomic wireless mouse with silent clicks and 18-month battery.',29.99,'Electronics',50),
            ('USB-C Hub','7-in-1 USB-C docking station with HDMI, Ethernet, card reader.',49.99,'Accessories',30),
            ('Security Textbook','Cybersecurity Essentials 4th Edition - OWASP Top 10 and secure coding.',59.99,'Books',20),
            ('Mechanical Keyboard','RGB mechanical gaming keyboard with Cherry MX switches.',89.99,'Electronics',25),
            ('Python Security Course','Learn Python for cybersecurity in 30 days - video course with labs.',39.99,'Courses',999),
            ('Cat6 Network Cable','2m shielded Ethernet cable, gold-plated connectors.',9.99,'Accessories',100),
            ('HD Webcam','1080p USB webcam with built-in noise-cancelling microphone.',44.99,'Electronics',35),
        ]
        for p in products:
            c.execute("INSERT INTO products VALUES(NULL,?,?,?,?,?)", p)
        reviews = [
            (1,'user1',5,'Amazing laptop! Super fast and great battery life. Highly recommend.'),
            (1,'user2',4,'Good value for money. The screen could be brighter but overall solid.'),
            (2,'user3',5,'Best mouse I have ever used. Very comfortable for long sessions.'),
            (4,'user1',5,'Essential reading for any security professional. Great OWASP coverage.'),
            (5,'user4',4,'Love the RGB effects and the key feel is perfect for coding.'),
            (6,'user2',5,'Excellent course! Went from zero to writing security scripts in 2 weeks.'),
        ]
        for r in reviews:
            c.execute("INSERT INTO reviews VALUES(NULL,?,?,?,?,datetime('now'))", r)
        for i in range(1, 4):
            with open('/app/data/invoices/invoice_%d.txt' % i, 'w') as f:
                f.write("INVOICE #%04d\nShopSecure Ltd.\nDate: 2026-01-%02d\nCustomer: user%d\nProduct: Laptop Pro 15\nAmount: GBP %.2f\nVAT: GBP %.2f\nTotal: GBP %.2f\nStatus: PAID\n" % (i, i, i, i*49.99, i*49.99*0.2, i*49.99*1.2))
    db.commit()
    db.close()
    print("[+] Database initialized")

CSS = '''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.cdnfonts.com/css/opendyslexic');
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#f4f6f9;color:#1a1a2e}
@media (max-width:768px){.nav{flex-wrap:wrap;padding:10px 14px;gap:8px}.nav .brand{font-size:18px}.nav-links{display:flex;flex-wrap:wrap;justify-content:center;width:100%;margin-top:6px}.nav-links a{margin:4px 8px;font-size:12px}}@media (max-width:480px){.nav .brand{font-size:16px}.nav-links a{font-size:11px;margin:3px 6px}}
.nav{background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);padding:12px 20px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3)}
.nav .brand{font-size:22px;font-weight:700;color:#fff;letter-spacing:1px}
.nav .brand span{color:#00d2ff}
.nav-links{display:flex;flex-wrap:wrap;justify-content:flex-end;align-items:center;gap:2px 0;flex:1;min-width:0}.nav-links a{color:rgba(255,255,255,0.85);text-decoration:none;margin:0 6px;font-size:12px;font-weight:500;transition:all 0.2s;white-space:nowrap}
.nav-links a:hover{color:#00d2ff}
.hero{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:40px;border-radius:16px;margin:24px 0;color:#fff;text-align:center}
.hero h1{font-size:28px;margin-bottom:8px}
.hero p{opacity:0.9;font-size:15px}
.container{max-width:1080px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:12px;padding:24px;margin:16px 0;box-shadow:0 2px 12px rgba(0,0,0,0.06);border:1px solid #e8eaf0}
.card h2{color:#302b63;margin-bottom:12px}
.btn{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px 24px;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:500;transition:transform 0.2s,box-shadow 0.2s;text-decoration:none;display:inline-block}
.btn:hover{transform:translateY(-2px);box-shadow:0 4px 15px rgba(102,126,234,0.4)}
.btn-sm{padding:6px 16px;font-size:12px}
input,textarea,select{padding:10px 14px;border:2px solid #e8eaf0;border-radius:8px;width:100%;margin:6px 0 14px;font-size:14px;font-family:inherit;transition:border 0.2s}
input:focus,textarea:focus{border-color:#667eea;outline:none}
table{width:100%;border-collapse:collapse;margin:12px 0}
th,td{padding:12px 14px;text-align:left;border-bottom:1px solid #f0f0f0}
th{background:#f8f9fc;font-weight:600;color:#302b63;font-size:13px;text-transform:uppercase;letter-spacing:0.5px}
.alert{padding:14px 18px;border-radius:8px;margin:12px 0;font-weight:500}
.alert-success{background:#d4edda;color:#155724;border:1px solid #c3e6cb}
.alert-danger{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}
.alert-warning{background:#fff3cd;color:#856404;border:1px solid #ffeeba}
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px;margin-top:20px}
.product-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 12px rgba(0,0,0,0.06);border:1px solid #e8eaf0;transition:transform 0.2s,box-shadow 0.2s;text-align:center}
.product-card:hover{transform:translateY(-4px);box-shadow:0 8px 25px rgba(0,0,0,0.1)}
.product-card img{width:80px;height:80px;margin-bottom:12px}
.product-card h3{color:#302b63;margin-bottom:6px;font-size:16px}
.product-card .desc{color:#666;font-size:13px;margin-bottom:10px;line-height:1.4}
.price{font-size:22px;font-weight:700;color:#2e7d32;margin:8px 0}
.price-sm{font-size:16px}
.category-tag{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:#e8eaf0;color:#302b63;margin:6px 0}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-admin{background:linear-gradient(135deg,#eb3349,#f45c43);color:#fff}
.badge-user{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.stars{color:#f9a825;font-size:16px;letter-spacing:2px}
.review-card{border-left:3px solid #667eea;padding:12px 16px;margin:10px 0;background:#f8f9fc;border-radius:0 8px 8px 0}
.stat-box{display:inline-block;background:#f8f9fc;padding:12px 20px;border-radius:8px;margin:4px;text-align:center;min-width:100px}
.stat-box .num{font-size:24px;font-weight:700;color:#302b63}
.stat-box .label{font-size:11px;color:#666;text-transform:uppercase}
pre{background:#1a1a2e;color:#00ff41;padding:20px;border-radius:12px;overflow-x:auto;font-size:13px;line-height:1.6;margin-top:16px}
footer{text-align:center;padding:30px;color:#999;font-size:12px;margin-top:40px;border-top:1px solid #e8eaf0}
footer b{color:#eb3349}
label{font-weight:500;color:#302b63;font-size:13px}

body.dyslexia-mode,body.dyslexia-mode *{font-family:'OpenDyslexic','Comic Sans MS',sans-serif!important}
body.dark-mode{background:#0f172a!important;color:#e2e8f0!important}
body.dark-mode .nav{background:linear-gradient(135deg,#1e1b4b,#312e81)!important}
body.dark-mode .card,body.dark-mode .product-card,body.dark-mode .review-card{background:#1e293b!important;color:#e2e8f0!important;border-color:#334155!important}
body.dark-mode .hero{background:linear-gradient(135deg,#4338ca,#6d28d9)!important}
body.dark-mode input,body.dark-mode textarea,body.dark-mode select{background:#1e293b!important;color:#e2e8f0!important;border-color:#475569!important}
body.dark-mode th{background:#1e293b!important;color:#e2e8f0!important}
body.dark-mode td{color:#cbd5e1!important;border-color:#334155!important}
body.dark-mode footer{color:#64748b!important}
body.dark-mode h2,body.dark-mode h3,body.dark-mode h4{color:#c7d2fe!important}
body.dark-mode .price{color:#86efac!important}
body.dark-mode .feature-card{background:#1e293b!important;border-color:#334155!important}
body.dark-mode .btn{background:linear-gradient(135deg,#6366f1,#8b5cf6)!important}
body.dark-mode pre{background:#020617!important}
body.dark-mode .reading-pointer-settings{background:#2d3748!important;color:#e2e8f0!important}
body.high-contrast{background:#000!important;color:#fff!important}
body.high-contrast .nav{background:#000!important;border-bottom:3px solid #ff0!important}
body.high-contrast .card,body.high-contrast .product-card{background:#111!important;color:#fff!important;border:2px solid #ff0!important}
body.high-contrast h2,body.high-contrast h3{color:#ff0!important}
body.high-contrast a{color:#0ff!important}
body.high-contrast .btn{background:#ff0!important;color:#000!important}
body.reduce-motion *{animation:none!important;transition:none!important}
.ss-access{display:inline-flex;align-items:center;gap:6px;margin-left:auto}#synapseA11yNav{display:none!important}
.ss-abtn{width:40px;height:40px;border:none;border-radius:50%;background:rgba(255,255,255,0.18);cursor:pointer;font-size:20px;padding:0;display:flex;align-items:center;justify-content:center;transition:all 0.2s;color:#fff}
.ss-abtn:hover{background:rgba(255,255,255,0.3);transform:scale(1.1)}
.ss-abtn.active{background:#10b981!important;color:#fff!important;box-shadow:0 0 0 3px rgba(16,185,129,0.5)!important}
.ss-abtn img{width:40px;height:40px}
.ss-amenu{display:none;gap:6px;align-items:center}
.ss-amenu.open{display:flex}
.reading-pointer-settings{position:fixed;top:70px;right:20px;background:#fff;border-radius:15px;padding:20px;box-shadow:0 10px 40px rgba(0,0,0,0.2);z-index:10000;min-width:280px;display:none}
.reading-pointer-settings.visible{display:block}
#readingPointerLine{position:fixed;left:0;width:100%;height:4px;background:#667eea;z-index:9999;pointer-events:none;display:none;box-shadow:0 0 12px rgba(102,126,234,0.5)}
#readingPointerLine.active{display:block}
.fa-dimmed{opacity:0.1!important;filter:blur(2px)!important;transition:all 0.3s!important}
.fa-focused{position:relative;z-index:998;box-shadow:0 0 0 4px #667eea,0 8px 32px rgba(102,126,234,0.4)!important;border-radius:12px!important;transition:all 0.3s!important}

</style>'''

JS = """<script>
function toggleAM(){var m=document.getElementById('ssMenu');if(m)m.classList.toggle('open')}
function ssSyncFocus(){var n=document.getElementById('synapseA11yNav');if(!n)return;[['#focusModeBtn','Focus Mode'],['#focusAssistantBtn','Focus Assistant']].forEach(function(p){var hb=n.querySelector(p[0]);var vb=document.querySelector('#ssMenu [title="'+p[1]+'"]');if(hb&&vb)vb.classList.toggle('active',hb.classList.contains('active'))})}
document.addEventListener('click',function(e){if(!e.target.closest('.ss-access')){var m=document.getElementById('ssMenu');if(m)m.classList.remove('open')}});
</script>"""

def nav_html():
    u = session.get('username')
    r = session.get('role')
    links = '<a href="%s/">Home</a><a href="%s/search">Search</a>' % (P, P)
    if u:
        links += '<a href="%s/mitigations">Mitigations</a><a href="%s/profile">Profile</a><a href="%s/transfer">Transfer</a><a href="%s/invoice">Invoices</a><a href="%s/preferences">Preferences</a><a href="%s/cookie-check">Cookies</a>' % (P, P, P, P, P, P)
        if r == 'admin':
            links += '<a href="%s/admin">Admin</a><a href="%s/admin/health-check">Health</a>' % (P, P)
        links += '<a href="%s/logout">Logout (%s)</a>' % (P, u)
    else:
        links += '<a href="%s/login">Login</a>' % P
    return '''<div class="nav"><span class="brand">&#128722; Shop<span>Secure</span></span><div class="ss-access"><button class="ss-abtn" onclick="toggleAM()" title="Accessibility"><img src="/icons/access.png" onerror="this.outerHTML='&#129419;'"></button><div class="ss-amenu" id="ssMenu"><button class="ss-abtn" onclick="synapseToolbar.toggleDark();this.classList.toggle('active')" title="Dark Mode">&#127769;</button><button class="ss-abtn" onclick="synapseToolbar.toggleDyslexiaFont();this.classList.toggle('active')" title="Dyslexia Font">&#128214;</button><button class="ss-abtn" style="font-size:15px;font-weight:700" onclick="synapseToolbar.increaseFontSize()" title="Larger Text">A+</button><button class="ss-abtn" style="font-size:15px;font-weight:700" onclick="synapseToolbar.decreaseFontSize()" title="Smaller Text">A-</button><button class="ss-abtn" onclick="synapseToolbar.toggleReadingPointer();this.classList.toggle('active')" title="Reading Pointer">&#128205;</button><button class="ss-abtn" onclick="synapseToolbar.toggleTextToSpeech();this.classList.toggle('active')" title="Read Aloud">&#128266;</button><button class="ss-abtn" onclick="synapseToolbar.toggleHighContrast();this.classList.toggle('active')" title="High Contrast">&#9899;&#9898;</button><button class="ss-abtn" onclick="window.toggleFocusMode()" title="Focus Mode">&#127919;</button><button class="ss-abtn" onclick="window.toggleFocusAssistant()" title="Focus Assistant">&#128161;</button><button class="ss-abtn" onclick="synapseToolbar.toggleCalmingAudio();this.classList.toggle('active')" title="Calming Audio">&#127925;</button><button class="ss-abtn" onclick="synapseToolbar.toggleVoiceInput();this.classList.toggle('active')" title="Voice Input">&#127908;</button><button class="ss-abtn" onclick="synapseToolbar.toggleReduceMotion();this.classList.toggle('active')" title="Reduce Motion">&#9889;</button><button class="ss-abtn" onclick="window.synapseToggleLineSpacing&&synapseToggleLineSpacing();this.classList.toggle('active')" title="Line Spacing">&#8597;</button><button class="ss-abtn" onclick="window.synapseToggleReadingMask&&synapseToggleReadingMask();this.classList.toggle('active')" title="Reading Mask">&#128306;</button><button class="ss-abtn" onclick="window.synapseToggleColorOverlay&&synapseToggleColorOverlay();this.classList.toggle('active')" title="Color Overlay">&#127912;</button><button class="ss-abtn" onclick="window.synapseToggleCursorHighlight&&synapseToggleCursorHighlight();this.classList.toggle('active')" title="Cursor Highlight">&#128993;</button><button class="ss-abtn" onclick="window.synapseToggleDictionary&&synapseToggleDictionary();this.classList.toggle('active')" title="Dictionary">&#128218;</button><button class="ss-abtn" onclick="window.synapseToggleCalmMode&&synapseToggleCalmMode();this.classList.toggle('active')" title="Calm Mode">&#129496;</button><button class="ss-abtn" style="background:rgba(220,38,38,0.3)" onclick="synapseToolbar.reset();window.synapseFocusReset&&window.synapseFocusReset();document.querySelectorAll('.ss-abtn.active').forEach(function(x){x.classList.remove('active')})" title="Reset All">&#128260;</button></div></div><div class="nav-links">%s</div></div>''' % links

try:
    CHAT_WIDGET = open('/app/chat_widget.html', 'r').read()
except:
    CHAT_WIDGET = ''

def _a11y_read(p):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ''
SS_FIX_CSS = ('body.synapse-has-toolbar{padding-top:0!important}'
  'body.high-contrast a.btn,body.high-contrast .btn,body.high-contrast .btn-sm{background:#ff0!important;color:#000!important;border:2px solid #000!important;text-shadow:none!important}'
  'body.high-contrast .nav-links a{border:none!important;outline:none!important;background:transparent!important;box-shadow:none!important;color:#ff0!important}'
  'body.high-contrast .product-card img{background:#fff!important;border-radius:8px!important;padding:4px!important;box-sizing:border-box!important}')
A11Y_HEAD = '<style>%s\n%s\n#synapseA11yNav{display:none!important}%s</style>' % (
    _a11y_read('/app/synapse_a11y.css'), _a11y_read('/app/synapse_a11y_toolbar.css'), SS_FIX_CSS)
def _a11y_js(p):
    return _a11y_read(p).replace('closest("#synapseA11yNav")', 'closest("#synapseA11yNav, .ss-access")').replace('</', '<\\/')
A11Y_BODY = '<script>%s</script><script>%s</script><script>%s</script>' % (
    _a11y_js('/app/synapse_a11y.js'), _a11y_js('/app/synapse_a11y_toolbar.js'), _a11y_js('/app/synapse_focus.js'))

def page(title, body):
    base = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShopSecure - %s</title>%s%s</head><body>%s<div class="container">%s</div><footer>ShopSecure v2.0 &mdash; <b>Intentionally Vulnerable</b> &mdash; SYNAPSE Education Platform</footer>%s' % (title, CSS, A11Y_HEAD, nav_html(), body, JS)
    return base + CHAT_WIDGET + A11Y_BODY + '</body></html>'

@app.route('/')
@app.route('/welcome')
def home():
    db = get_db()
    products = db.execute("SELECT * FROM products LIMIT 8").fetchall()
    cards = ''
    for p in products:
        img = PRODUCT_IMGS.get(p['id'], 'https://cdn-icons-png.flaticon.com/128/679/679922.png')
        cards += '<div class="product-card"><img src="%s" alt="%s"><h3>%s</h3><p class="desc">%s</p><span class="category-tag">%s</span><p class="price">&pound;%.2f</p><p style="color:#999;font-size:12px;margin-bottom:10px">%d in stock</p><a href="%s/product?id=%d" class="btn btn-sm">View Details &rarr;</a></div>' % (img, p['name'], p['name'], p['description'][:80], p['category'], p['price'], p['stock'], P, p['id'])
    return page('Home', '<div class="hero"><h1>Welcome to ShopSecure</h1><p>Your trusted online electronics store</p><p style="font-size:11px;margin-top:8px;opacity:0.6">This is a deliberately vulnerable application for security education.</p></div><div style="display:flex;justify-content:center;gap:12px;margin-bottom:20px"><div class="stat-box"><div class="num">8</div><div class="label">Products</div></div><div class="stat-box"><div class="num">6</div><div class="label">Users</div></div><div class="stat-box"><div class="num">11</div><div class="label">Vulns</div></div></div><h2 style="margin-bottom:4px">Featured Products</h2><div class="product-grid">%s</div>' % cards)

@app.route('/login', methods=['GET','POST'])
def login():
    error = ''
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        db = get_db()
        try:
            query = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (u, p)
            user = db.execute(query).fetchone()
            if user:
                session['username'] = user['username']
                session['role'] = user['role']
                session['user_id'] = user['id']
                return redirect('%s/' % P, code=303)
            else:
                error = 'Invalid username or password'
        except Exception as e:
            error = 'Database error: %s<br><small>Query: %s</small>' % (str(e), query)
    err_html = '<div class="alert alert-danger">%s</div>' % error if error else ''
    return page('Login', '<div class="card" style="max-width:420px;margin:40px auto"><h2 style="text-align:center">Sign In</h2><p style="text-align:center;color:#666;margin-bottom:20px">Access your ShopSecure account</p>%s<form method="POST" action="%s/login"><label>Username</label><input name="username" placeholder="e.g. user1" autocomplete="off" required><label>Password</label><input name="password" type="password" placeholder="e.g. user1Pass!" autocomplete="off" required><button class="btn" style="width:100%%;margin-top:8px">Sign In &rarr;</button></form><div style="margin-top:16px;padding:12px;background:#f8f9fc;border-radius:8px;font-size:12px;color:#666"><strong>Demo Accounts:</strong><br>user1 / user1Pass! through user5 / user5Pass!<br>admin / adminShop2026</div></div>' % (err_html, P))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('%s/' % P, code=303)

@app.route('/search')
def search():
    q = request.args.get('q','')
    results_html = ''
    if q:
        db = get_db()
        try:
            sql = "SELECT * FROM products WHERE name LIKE '%%%s%%' OR description LIKE '%%%s%%' OR category LIKE '%%%s%%'" % (q, q, q)
            products = db.execute(sql).fetchall()
            if products:
                results_html = '<table><tr><th>Product</th><th>Description</th><th>Price</th><th></th></tr>'
                for p in products:
                    results_html += '<tr><td><strong>%s</strong></td><td>%s</td><td class="price-sm">&pound;%.2f</td><td><a href="%s/product?id=%d" class="btn btn-sm">View</a></td></tr>' % (p['name'], p['description'][:60], p['price'], P, p['id'])
                results_html += '</table>'
            else:
                results_html = '<div class="alert alert-warning">No products found for "%s"</div>' % q
        except Exception as e:
            results_html = '<div class="alert alert-danger">Search error: %s</div>' % str(e)
    result_card = '<div class="card"><h3>Results for: %s</h3>%s</div>' % (q, results_html) if q else '<div class="card" style="text-align:center;color:#999;padding:40px">Enter a search term to find products</div>'
    return page('Search', '<div class="card"><h2>Search Products</h2><form method="GET" action="%s/search" style="display:flex;gap:8px;margin-top:12px"><input name="q" value="%s" placeholder="Search for laptops, keyboards, courses..." style="flex:1"><button class="btn">Search</button></form></div>%s' % (P, q, result_card))

@app.route('/product')
def product():
    pid = request.args.get('id','1')
    db = get_db()
    p = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        return page('Not Found', '<div class="alert alert-danger">Product not found</div>')
    img = PRODUCT_IMGS.get(p['id'], 'https://cdn-icons-png.flaticon.com/128/679/679922.png')
    reviews = db.execute("SELECT * FROM reviews WHERE product_id=? ORDER BY created_at DESC", (pid,)).fetchall()
    reviews_html = ''
    avg_rating = 0
    if reviews:
        avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
    for r in reviews:
        stars = '&#9733;' * r['rating'] + '&#9734;' * (5 - r['rating'])
        reviews_html += '<div class="review-card"><strong>%s</strong> <span class="stars">%s</span><span style="color:#999;font-size:12px;margin-left:8px">%s</span><p style="margin-top:6px;color:#333">%s</p></div>' % (r['username'], stars, r['created_at'], r['comment'])
    review_form = ''
    if session.get('username'):
        review_form = '<div style="margin-top:20px;padding-top:20px;border-top:2px solid #e8eaf0"><h3>Write a Review</h3><form method="POST" action="%s/review"><input type="hidden" name="product_id" value="%s"><label>Rating</label><select name="rating"><option value="5">Excellent</option><option value="4">Good</option><option value="3">OK</option><option value="2">Poor</option><option value="1">Terrible</option></select><label>Your Review</label><textarea name="comment" rows="3" placeholder="Share your experience..."></textarea><button class="btn">Submit Review</button></form></div>' % (P, pid)
    else:
        review_form = '<p style="margin-top:16px;color:#666;text-align:center"><a href="%s/login">Sign in</a> to write a review</p>' % P
    avg_str = ' &mdash; Average: %.1f/5' % avg_rating if reviews else ''
    return page(p['name'], '<div class="card" style="display:flex;gap:24px;align-items:flex-start"><img src="%s" style="width:120px;height:120px"><div style="flex:1"><h2>%s</h2><span class="category-tag">%s</span><p style="margin:12px 0;color:#555;line-height:1.6">%s</p><p class="price">&pound;%.2f</p><p style="color:#666;font-size:13px">%d in stock</p></div></div><div class="card"><h3>Customer Reviews (%d)%s</h3>%s%s</div>' % (img, p['name'], p['category'], p['description'], p['price'], p['stock'], len(reviews), avg_str, reviews_html or '<p style="color:#999;text-align:center;padding:20px">No reviews yet. Be the first!</p>', review_form))

@app.route('/review', methods=['POST'])
def add_review():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    pid = request.form.get('product_id')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    db = get_db()
    db.execute("INSERT INTO reviews(product_id,username,rating,comment) VALUES(?,?,?,?)",
               (pid, session['username'], rating, comment))
    db.commit()
    return redirect('%s/product?id=%s' % (P, pid), code=303)

@app.route('/profile', methods=['GET','POST'])
def profile():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    msg = ''
    uid = request.args.get('id', session.get('user_id'))
    db = get_db()
    if request.method == 'POST':
        fullname = request.form.get('fullname','')
        email = request.form.get('email','')
        address = request.form.get('address','')
        db.execute("UPDATE users SET fullname=?,email=?,address=? WHERE id=?",
                   (fullname, email, address, session['user_id']))
        db.commit()
        msg = '<div class="alert alert-success">Profile updated successfully!</div>'
        uid = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    if not user:
        return page('Profile', '<div class="alert alert-danger">User not found</div>')
    is_own = str(uid) == str(session.get('user_id'))
    is_admin = session.get('role') == 'admin'
    card_display = user['card_number'] if (is_own or is_admin) else '****-****-****-' + str(user['card_number'])[-4:]
    edit_form = ''
    if is_own:
        edit_form = '<div style="margin-top:20px;padding-top:20px;border-top:2px solid #e8eaf0"><h3>Edit Profile</h3><form method="POST" action="%s/profile"><label>Full Name</label><input name="fullname" value="%s"><label>Email</label><input name="email" type="email" value="%s"><label>Address</label><input name="address" value="%s"><button class="btn">Save Changes</button></form></div>' % (P, user['fullname'], user['email'], user['address'])
    badge_class = 'badge-admin' if user['role'] == 'admin' else 'badge-user'
    viewer = session.get('username','?')
    viewing_id = str(uid)
    own_id = str(session.get('user_id'))
    teaching_banner = ''
    if viewing_id != own_id:
        teaching_banner = '<div style="background:#1e3a8a;color:#dbeafe;padding:10px 14px;border-radius:8px;margin-bottom:14px;font-size:13px;line-height:1.6"><strong>&#128100; You are <code style="background:#0f172a;padding:2px 6px;border-radius:3px;color:#fbbf24">' + viewer + '</code> viewing the profile of <code style="background:#0f172a;padding:2px 6px;border-radius:3px;color:#fbbf24">' + user["username"] + '</code>.</strong><br>Any HTML in this profile (Address, Full Name, Email) is rendered without escaping &mdash; if it contains an <code>&lt;iframe&gt;</code> or <code>&lt;script&gt;</code>, it executes inside <em>your</em> session context.</div>'
    profile_card = '<div class="card"><h2>%s <span class="badge %s">%s</span></h2><table style="margin-top:16px"><tr><th style="width:120px">Username</th><td>%s</td></tr><tr><th>Email</th><td>%s</td></tr><tr><th>Address</th><td>%s</td></tr><tr><th>Balance</th><td><strong style="color:#2e7d32;font-size:18px">&pound;%.2f</strong></td></tr><tr><th>Card</th><td><code style="background:#f0f0f0;padding:4px 8px;border-radius:4px">%s</code></td></tr></table>%s</div>' % (user['fullname'], badge_class, user['role'].upper(), user['username'], user['email'], user['address'], user['balance'], card_display, edit_form)
    return page('Profile', msg + teaching_banner + profile_card)

@app.route('/transfer', methods=['GET','POST'])
def transfer():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    msg = ''
    if request.method == 'POST':
        to_user = request.form.get('to','')
        amount = float(request.form.get('amount', 0))
        db = get_db()
        me = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
        target = db.execute("SELECT * FROM users WHERE username=?", (to_user,)).fetchone()
        if not target:
            msg = '<div class="alert alert-danger">User not found</div>'
        elif amount <= 0:
            msg = '<div class="alert alert-danger">Invalid amount</div>'
        elif me['balance'] < amount:
            msg = '<div class="alert alert-danger">Insufficient funds</div>'
        else:
            db.execute("UPDATE users SET balance=balance-? WHERE username=?", (amount, session['username']))
            db.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, to_user))
            db.execute("INSERT INTO transfers(from_user,to_user,amount) VALUES(?,?,?)", (session['username'], to_user, amount))
            db.commit()
            msg = '<div class="alert alert-success">&pound;%.2f sent to %s!</div>' % (amount, to_user)
    db = get_db()
    me = db.execute("SELECT balance FROM users WHERE username=?", (session['username'],)).fetchone()
    history = db.execute("SELECT * FROM transfers WHERE from_user=? OR to_user=? ORDER BY created_at DESC LIMIT 10",
                         (session['username'], session['username'])).fetchall()
    hist_html = ''
    for t in history:
        if t['from_user'] == session['username']:
            hist_html += '<tr><td>Sent to <strong>%s</strong></td><td style="color:#c62828">-&pound;%.2f</td><td style="color:#999">%s</td></tr>' % (t['to_user'], t['amount'], t['created_at'])
        else:
            hist_html += '<tr><td>From <strong>%s</strong></td><td style="color:#2e7d32">+&pound;%.2f</td><td style="color:#999">%s</td></tr>' % (t['from_user'], t['amount'], t['created_at'])
    return page('Transfer', '%s<div class="card"><h2>Transfer Funds</h2><div class="stat-box" style="display:block;margin:12px 0"><div class="num">&pound;%.2f</div><div class="label">Your Balance</div></div><form method="POST" action="%s/transfer" style="margin-top:12px"><label>Recipient Username</label><input name="to" placeholder="e.g. user2" required><label>Amount</label><input name="amount" type="number" step="0.01" min="0.01" required><button class="btn" style="width:100%%">Send Money &rarr;</button></form></div><div class="card"><h3>Recent Transfers</h3><table><tr><th>Details</th><th>Amount</th><th>Date</th></tr>%s</table></div>' % (msg, me['balance'], P, hist_html or '<tr><td colspan="3" style="color:#999;text-align:center">No transfers yet</td></tr>'))

@app.route('/invoice')
def invoice():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    filename = request.args.get('file', '')
    if filename:
        filepath = '/app/data/invoices/' + filename
        try:
            content = open(filepath).read()
            is_dangerous = '..' in filename
            border_color = '#dc2626' if is_dangerous else '#10b981'
            label = 'PATH TRAVERSAL! You accessed a file outside /invoices/' if is_dangerous else 'File contents'
            icon = '&#9888;' if is_dangerous else '&#9989;'
            html = '<div class="card"><h2>File Viewer</h2>'
            html += '<div style="background:%s;color:white;padding:10px 16px;border-radius:8px 8px 0 0;font-weight:700">%s %s</div>' % ('#991b1b' if is_dangerous else '#166534', icon, label)
            html += '<div style="background:#1a1a2e;color:#e2e8f0;padding:16px;border-radius:0 0 8px 8px;font-family:monospace;font-size:13px;white-space:pre-wrap;max-height:400px;overflow-y:auto;border:2px solid %s">%s</div>' % (border_color, content.replace('<','&lt;').replace('>','&gt;'))
            html += '<div style="margin-top:12px;background:#f8fafc;padding:12px;border-radius:8px;font-size:12px">'
            html += '<strong>Requested:</strong> <code>%s</code><br>' % filename.replace('<','&lt;')
            html += '<strong>Resolved to:</strong> <code>%s</code></div>' % filepath.replace('<','&lt;')
            html += '<a href="%s/invoice" class="btn" style="margin-top:12px">Back to Invoices</a></div>' % P
            return page('File Viewer', html)
        except Exception as e:
            return page('Error', '<div class="alert alert-danger">Cannot read: <code>%s</code><br>%s<br><a href="%s/invoice" class="btn" style="margin-top:8px">Back</a></div>' % (filepath, str(e), P))
    invoices = os.listdir('/app/data/invoices/')
    links = ''
    for f in sorted(invoices):
        links += '<tr><td>%s</td><td><a href="%s/invoice?file=%s" class="btn btn-sm">Download</a></td></tr>' % (f, P, f)
    explore = '<div class="card" style="margin-top:16px;border:2px solid #f59e0b;border-radius:12px">'
    explore += '<h3 style="color:#92400e">&#128269; Explore: File Request</h3>'
    explore += '<p style="font-size:13px;color:#555;margin-bottom:12px">The server retrieves files based on the <code>file</code> parameter. What happens if you request a different filename?</p>'
    explore += '<div style="display:flex;gap:8px;margin-bottom:12px">'
    explore += '<input id="fileExplore" value="invoice_1.txt" placeholder="Enter a filename..." style="flex:1;padding:10px;border:2px solid #d1d5db;border-radius:8px;font-family:monospace;font-size:14px">'
    explore += '<button onclick="window.location.href=\'%s/invoice?file=\'+document.getElementById(\'fileExplore\').value" class="btn" style="background:#f59e0b">Request File</button></div>' % P
    explore += '<div style="background:#fffbeb;padding:10px;border-radius:8px;font-size:12px;color:#92400e">'
    explore += '<strong>&#128161; Hint:</strong> The server builds the path like this: <code>/app/data/invoices/ + [your input]</code><br>'
    explore += 'Normal: <code>invoice_1.txt</code> &rarr; <code>/app/data/invoices/invoice_1.txt</code><br>'
    explore += 'What if your input contained characters that navigate the file system? Ask the AI tutor!</div></div>'
    return page('Invoices', '<div class="card"><h2>Your Invoices</h2><p style="color:#666;margin-bottom:12px">Download your purchase invoices below.</p><table><tr><th>File</th><th>Action</th></tr>%s</table></div>' % links + explore)

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return page('Forbidden', '<div class="alert alert-danger">Admin access required</div>'), 403
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    rows = ''
    for u in users:
        badge_class = 'badge-admin' if u['role'] == 'admin' else 'badge-user'
        rows += '<tr><td>%d</td><td><a href="%s/profile?id=%d">%s</a></td><td>%s</td><td>%s</td><td><strong>&pound;%.2f</strong></td><td><code>%s</code></td><td><span class="badge %s">%s</span></td></tr>' % (u['id'], P, u['id'], u['username'], u['fullname'], u['email'], u['balance'], u['card_number'], badge_class, u['role'].upper())
    return page('Admin', '<div class="card"><h2>Admin Panel &mdash; User Management</h2><p style="color:#666;margin-bottom:16px">All registered users and their details.</p><table><tr><th>ID</th><th>Username</th><th>Name</th><th>Email</th><th>Balance</th><th>Card</th><th>Role</th></tr>%s</table></div>' % rows)

@app.route('/admin/health-check', methods=['GET','POST'])
def health_check():
    if session.get('role') != 'admin':
        return page('Forbidden', '<div class="alert alert-danger">Admin access required</div>'), 403
    output = ''
    host = ''
    if request.method == 'POST':
        host = request.form.get('host', '')
        try:
            result = subprocess.run('ping -c 2 %s' % host, shell=True, capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            output = 'Command timed out after 10 seconds'
        except Exception as e:
            output = 'Error: %s' % str(e)
    output_html = '<pre>%s</pre>' % output if output else ''
    return page('Health Check', '<div class="card"><h2>Server Health Check</h2><p style="color:#666">Monitor server connectivity by pinging external hosts.</p><form method="POST" action="%s/admin/health-check" style="display:flex;gap:8px;margin-top:16px"><input name="host" value="%s" placeholder="e.g. google.com" style="flex:1"><button class="btn">Run Check</button></form>%s</div>' % (P, host, output_html))

@app.route('/mitigations')
def mitigations():
    try:
        content = open('/app/mitigations.html', 'r').read()
        content = content.replace('{P}', P)
    except:
        content = '<div class="alert alert-danger">Mitigations page not found</div>'
    return page('Security Mitigations Guide', content)

@app.route('/preferences', methods=['GET'])
def preferences():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    u = session.get('username','user')
    db = get_db()
    dbuser = db.execute('SELECT balance, role, email FROM users WHERE username=?', (u,)).fetchone()
    real_balance = int(dbuser[0]) if dbuser else 100
    real_role = dbuser[1] if dbuser else 'user'
    real_email = dbuser[2] if dbuser else u+'@shop.com'
    normal = "username: %s\nrole: %s\nemail: %s\nbalance: %s\ntheme: dark\nlanguage: en" % (u, real_role, real_email, real_balance)
    html = '<div class="card"><h2>User Preferences (CWE-502: Insecure Deserialisation)</h2>'
    html += '<p style="color:#666;margin-bottom:8px">When you <strong>export</strong> settings, the server <em>serialises</em> your data into a file. When you <strong>import</strong>, it <em>deserialises</em> (loads) the file back. If the server uses Python <code>pickle</code> without validation, an attacker can tamper the file to execute code or change data.</p>'
    html += '<p style="color:#991b1b;font-weight:600;margin-bottom:20px">Follow the steps below to see how this works!</p>'

    # ---- STEP 1: EXPORT (Serialisation) ----
    html += '<div style="background:#f0f7ff;border:2px solid #3b82f6;border-radius:12px;padding:20px;margin-bottom:16px">'
    html += '<h3 style="color:#1e40af;margin-bottom:6px">&#x1f4e4; Step 1: Export Your Settings (Serialisation)</h3>'
    html += '<p style="font-size:13px;color:#555;margin-bottom:10px">The server serialises your profile into a file. Click Export to see what it looks like.</p>'
    html += '<button onclick="doExport()" class="btn" style="background:#3b82f6;color:white;padding:10px 24px;font-size:15px" id="exportBtn">&#x1f4e4; Export Settings</button>'
    html += '<div id="exportedFile" style="display:none;margin-top:12px">'
    html += '<p style="font-size:12px;color:#1e40af;margin-bottom:4px"><strong>&#9989; Your exported file:</strong></p>'
    html += '<textarea id="fileViewer" style="width:100%%;height:110px;font-family:monospace;font-size:13px;background:#f8fafc;border:2px solid #93c5fd;border-radius:8px;padding:10px" readonly>' + normal + '</textarea>'
    html += '<p style="font-size:12px;color:#3b82f6;margin-top:6px">&#128712; This is safe data. The server stored your username, role, email, and balance.</p>'
    html += '</div></div>'

    # ---- STEP 2: TAMPER (Attacker modifies the file) ----
    html += '<div id="step2" style="display:none;margin-bottom:16px">'

    # Attack 1: RCE
    html += '<div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;padding:20px;margin-bottom:16px">'
    html += '<h3 style="color:#991b1b;margin-bottom:6px">&#9889; Step 2a: Tamper the File &#8212; RCE Attack</h3>'
    html += '<p style="font-size:13px;color:#555;margin-bottom:12px">An attacker replaces the safe file with <strong>Python code</strong>. When the server calls <code>pickle.loads()</code>, it executes the code! Fill in the 2 blanks:</p>'
    html += '<div style="background:#1a1a2e;color:#e2e8f0;padding:16px;border-radius:8px;font-family:monospace;font-size:14px;line-height:2.4;margin-bottom:12px">'
    html += 'import os<br><br>class Exploit:<br>'
    html += '&nbsp;&nbsp;def <input id="rce1" style="background:#2d3748;color:#fbbf24;border:2px solid #4a5568;border-radius:4px;padding:4px 8px;font-family:monospace;font-size:14px;width:150px" placeholder="which method?"> (self):<br>'
    html += '&nbsp;&nbsp;&nbsp;&nbsp;return (<input id="rce2" style="background:#2d3748;color:#fbbf24;border:2px solid #4a5568;border-radius:4px;padding:4px 8px;font-family:monospace;font-size:14px;width:130px" placeholder="which function?">, ("echo ATTACK > /tmp/pwned.txt",))</div>'
    html += '</div>'

    # Attack 2: Tampering
    html += '<div style="background:#fef9c3;border:2px solid #facc15;border-radius:12px;padding:20px">'
    html += '<h3 style="color:#854d0e;margin-bottom:6px">&#128275; Step 2b: Tamper the File &#8212; Data Tampering</h3>'
    html += '<p style="font-size:13px;color:#555;margin-bottom:12px">Or the attacker edits the values directly. Edit the file below: change <strong>role</strong> to get full access and set a high <strong>balance</strong>.</p>'
    html += '<textarea id="tamperFile" style="width:100%%;height:140px;font-family:monospace;font-size:14px;background:#1a1a2e;color:#fbbf24;border:2px solid #ca8a04;border-radius:8px;padding:12px;line-height:1.8" spellcheck="false">' + normal + '</textarea>'
    html += '<p style="font-size:12px;color:#854d0e;margin-top:6px">&#128161; Hint: What role gives full access? What balance would you want?</p>'
    html += '</div></div>'

    # ---- STEP 3: IMPORT (Deserialisation) ----
    html += '<div id="step3" style="display:none;background:#fef9c3;border:2px solid #f59e0b;border-radius:12px;padding:20px;margin-bottom:16px">'
    html += '<h3 style="color:#92400e;margin-bottom:6px">&#x1f4e5; Step 3: Import the Tampered File (Deserialisation)</h3>'
    html += '<p style="font-size:13px;color:#555;margin-bottom:12px">The server calls <code>pickle.loads()</code> on whatever file you send &#8212; <strong>no validation!</strong> Choose which attack to execute:</p>'
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">'
    html += '<button onclick="runRCE()" class="btn" style="background:#dc2626;color:white;padding:12px 24px;font-size:15px">&#9889; Import RCE Attack</button>'
    html += '<button onclick="runTamper()" class="btn" style="background:#ca8a04;color:white;padding:12px 24px;font-size:15px">&#128275; Import Tampered Data</button></div>'
    html += '<div id="importResult" style="margin-top:16px"></div></div>'

    # Reset
    html += '<div style="background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:16px;text-align:center">'
    html += '<a href="%s/preferences/reset" class="btn" style="background:#16a34a;padding:10px 24px">&#128260; Reset My Account</a></div></div>' % P

    # JavaScript
    html += '<script>\n'
    html += 'function doExport(){document.getElementById("exportedFile").style.display="block";document.getElementById("exportBtn").innerHTML="&#9989; Exported!";document.getElementById("step2").style.display="block";document.getElementById("step3").style.display="block";}\n'
    html += 'function runRCE(){\n'
    html += '  var a=document.getElementById("rce1").value.trim(),b=document.getElementById("rce2").value.trim(),r=document.getElementById("importResult");\n'
    html += '  if(a!=="__reduce__"||b!=="os.system"){\n'
    html += '    var h=[];if(a!=="__reduce__")h.push("Fill in the method: __r______");if(b!=="os.system")h.push("Fill in the function: os.s_____");\n'
    html += '    r.innerHTML=\'<div style="background:#fef2f2;border:2px solid #fca5a5;border-radius:8px;padding:12px;color:#991b1b">&#10060; Complete the RCE blanks first! \'+h.join(" | ")+\'</div>\';return;}\n'
    html += '  fetch("%s/preferences/demo-attack-run").then(function(x){return x.json()}).then(function(d){\n' % P
    html += '    r.innerHTML=\'<div style="background:#fef2f2;border:2px solid #dc2626;border-radius:8px;padding:16px;color:#991b1b"><strong>&#9888; SERVER EXECUTED YOUR COMMAND!</strong><br><br><code>\'+d.command+\'</code><br>File created: <strong>\'+d.file_check+\'</strong><br><br>&#128165; <code>pickle.loads()</code> called <code>__reduce__()</code> which ran <code>os.system()</code>.<br>An attacker could delete files, install backdoors, or steal all data!</div>\';});\n'
    html += '}\n'
    html += 'function runTamper(){\n'
    html += '  var f=document.getElementById("tamperFile").value,r=document.getElementById("importResult");\n'
    html += '  var hasAdmin=f.match(/role:\\s*admin/i),hasMoney=f.match(/balance:\\s*(\\d+)/);\n'
    html += '  var realBalance="100";var bigMoney=hasMoney&&hasMoney[1]!==realBalance;\n'
    html += '  if(!hasAdmin||!bigMoney){\n'
    html += '    var h=[];if(!hasAdmin)h.push("Change role to something powerful");if(!bigMoney)h.push("Set a much higher balance");\n'
    html += '    r.innerHTML=\'<div style="background:#fef9c3;border:2px solid #facc15;border-radius:8px;padding:12px;color:#854d0e">&#10060; Edit the file first! \'+h.join(" | ")+\'</div>\';return;}\n'
    html += '  fetch("%s/preferences/demo-tampering-run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({file_content:f})}).then(function(x){return x.json()}).then(function(d){\n' % P
    html += '    r.innerHTML=\'<div style="background:#fef9c3;border:2px solid #f59e0b;border-radius:8px;padding:16px;color:#92400e"><strong>&#128275; DATA TAMPERED SUCCESSFULLY!</strong><br><br>Your role: <strong>\'+d.role+\'</strong><br>Your balance: <strong>$\'+d.balance+\'</strong><br><br>The server deserialised the file and applied ALL fields without checking!<br><a href="%s/profile" style="color:#1e40af;font-weight:700;font-size:16px">&#8594; Go to Profile to verify!</a></div>\';});\n' % P
    html += '}\n'
    html += '</script>'
    return page('Preferences', html)

@app.route('/preferences/export')
def export_prefs():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    prefs = {'username': user['username'], 'fullname': user['fullname'], 'email': user['email'], 'address': user['address'], 'theme': 'default'}
    from flask import Response
    encoded = base64.b64encode(pickle.dumps(prefs))
    return Response(encoded, mimetype='application/octet-stream', headers={'Content-Disposition': 'attachment; filename=%s_prefs.prefs' % user['username']})

@app.route('/preferences/import', methods=['POST'])
def import_prefs():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    f = request.files.get('prefs_file')
    if not f:
        return page('Error', '<div class="alert alert-danger">No file uploaded</div>')
    try:
        raw = f.read()
        decoded = base64.b64decode(raw)
        prefs = pickle.loads(decoded)
        db = get_db()
        if prefs.get('fullname'):
            db.execute("UPDATE users SET fullname=? WHERE username=?", (prefs['fullname'], session['username']))
        if prefs.get('email'):
            db.execute("UPDATE users SET email=? WHERE username=?", (prefs['email'], session['username']))
        if prefs.get('address'):
            db.execute("UPDATE users SET address=? WHERE username=?", (prefs['address'], session['username']))
        if prefs.get('role'):
            db.execute("UPDATE users SET role=? WHERE username=?", (prefs['role'], session['username']))
            session['role'] = prefs['role']
        if prefs.get('balance'):
            db.execute("UPDATE users SET balance=? WHERE username=?", (float(prefs['balance']), session['username']))
        db.commit()
        items = ''.join('<tr><th>%s</th><td>%s</td></tr>' % (k,v) for k,v in prefs.items())
        return page('Import OK', '<div class="alert alert-success">Preferences imported!</div><div class="card"><table>%s</table><a href="%s/profile" class="btn" style="margin-top:12px">View Profile</a></div>' % (items, P))
    except Exception as e:
        return page('Import Error', '<div class="alert alert-danger">Failed: %s</div>' % str(e))

@app.route('/preferences/demo-attack')
def demo_attack():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    import os as _os
    class Exploit:
        def __reduce__(self):
            return (_os.system, ('echo ATTACK_SUCCESSFUL > /tmp/pwned.txt',))
    payload = base64.b64encode(pickle.dumps(Exploit()))
    from flask import Response
    return Response(payload, mimetype='application/octet-stream', headers={'Content-Disposition': 'attachment; filename=evil_demo.prefs'})

@app.route('/preferences/demo-attack-run')
def demo_attack_run():
    import subprocess
    cmd = "echo ATTACK > /tmp/pwned.txt"
    try:
        subprocess.run(cmd, shell=True, timeout=5)
        import os as _os
        exists = _os.path.exists('/tmp/pwned.txt')
        return jsonify({'command': cmd, 'result': 'executed', 'file_check': 'YES - /tmp/pwned.txt created!' if exists else 'No'})
    except:
        return jsonify({'command': cmd, 'result': 'blocked', 'file_check': 'No'})

@app.route('/preferences/demo-tampering-run', methods=['GET','POST'])
def demo_tampering_run():
    if session.get('username'):
        if request.method == 'POST':
            data = request.get_json() or {}
            file_content = data.get('file_content', '')
        else:
            file_content = ''
        # Parse the values from what the user typed
        new_role = 'customer'
        new_balance = 1000
        for line in file_content.split('\n'):
            if line.strip().startswith('role:'):
                new_role = line.split(':', 1)[1].strip()
            if line.strip().startswith('balance:'):
                try:
                    new_balance = int(line.split(':', 1)[1].strip())
                except:
                    pass
        # CWE-502 additive exploit: attacker steals from admin's account
        db = get_db()
        attacker_row = db.execute('SELECT balance FROM users WHERE username=?', (session['username'],)).fetchone()
        admin_row = db.execute('SELECT balance FROM users WHERE username=?', ('admin',)).fetchone()
        attacker_balance = float(attacker_row[0]) if attacker_row else 0.0
        admin_balance = float(admin_row[0]) if admin_row else 0.0
        stolen_amount = float(new_balance)
        # Conservation of money: transfer stolen_amount from admin to attacker
        new_attacker_balance = attacker_balance + stolen_amount
        new_admin_balance = admin_balance - stolen_amount
        session['role'] = new_role
        session['balance'] = new_attacker_balance
        db.execute('UPDATE users SET role=?, balance=? WHERE username=?', (new_role, new_attacker_balance, session['username']))
        db.execute('UPDATE users SET balance=? WHERE username=?', (new_admin_balance, 'admin'))
        db.commit()
        return jsonify({'role': new_role, 'balance': new_attacker_balance, 'previous_balance': attacker_balance, 'stolen_from_admin': stolen_amount, 'admin_balance_after': new_admin_balance})
    return jsonify({'error': 'Not logged in'})

@app.route('/preferences/demo-tampering')
def demo_tampering():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    tampered = {'username': session['username'], 'fullname': 'HACKED Admin', 'email': 'hacker@evil.com', 'address': '1337 Hacker Lane', 'role': 'admin', 'balance': 99999.99}
    payload = base64.b64encode(pickle.dumps(tampered))
    from flask import Response
    return Response(payload, mimetype='application/octet-stream', headers={'Content-Disposition': 'attachment; filename=tampered_prefs.prefs'})

@app.route('/preferences/reset')
def reset_account():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    u = session['username']
    db = get_db()
    defaults = {
        'admin': ('Administrator', 'admin@shopsecure.local', 'HQ', 100000.0, 'admin'),
        'user1': ('User 1', 'user1@example.com', '10 Oak St', 100.0, 'user'),
        'user2': ('User 2', 'user2@example.com', '20 Oak St', 200.0, 'user'),
        'user3': ('User 3', 'user3@example.com', '30 Oak St', 300.0, 'user'),
        'user4': ('User 4', 'user4@example.com', '40 Oak St', 400.0, 'user'),
        'user5': ('User 5', 'user5@example.com', '50 Oak St', 500.0, 'user'),
    }
    if u in defaults:
        d = defaults[u]
        db.execute("UPDATE users SET fullname=?, email=?, address=?, balance=?, role=? WHERE username=?", (d[0], d[1], d[2], d[3], d[4], u))
        db.commit()
        session['role'] = 'user'
        return page('Account Reset', '<div class="alert alert-success">Account reset!</div><div class="card"><table><tr><th>Name</th><td>%s</td></tr><tr><th>Balance</th><td>&pound;%.2f</td></tr><tr><th>Role</th><td>%s</td></tr></table><br><a href="%s/profile" class="btn">View Profile</a> <a href="%s/preferences" class="btn" style="background:#6366f1">Preferences</a></div>' % (d[0], d[3], d[4], P, P))
    return page('Reset', '<div class="alert alert-warning">Reset only for demo accounts (user1-user5)</div>')

@app.route('/csrf-demo')
def csrf_demo():
    to_user = request.args.get('to', 'admin')
    amount = request.args.get('amount', '50')
    # Silent CSRF: auto-submits transfer POST using victim's session cookie.
    # No UI - the attack is invisible. Evidence appears in /transfer history.
    html = '<!DOCTYPE html><html><head><title></title></head>'
    html += '<body style="margin:0;padding:0;background:transparent">'
    html += '<iframe name="csrf_frame" style="display:none"></iframe>'
    html += '<form action="%s/transfer" method="POST" id="csrfForm" target="csrf_frame" style="display:none">' % P
    html += '<input type="hidden" name="to" value="%s">' % to_user
    html += '<input type="hidden" name="amount" value="%s">' % amount
    html += '</form>'
    html += '<script>document.getElementById("csrfForm").submit();</script>'
    html += '</body></html>'
    return html
@app.route('/csrf-challenge', methods=['GET', 'POST'])
def csrf_challenge():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    msg = ''
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'reset':
            db = get_db()
            defaults = {'user1':'10 Oak St','user2':'20 Oak St','user3':'30 Oak St','user4':'40 Oak St','user5':'50 Oak St','admin':'HQ'}
            addr = defaults.get(session['username'], 'Unknown')
            db.execute("UPDATE users SET address=? WHERE username=?", (addr, session['username']))
            db.commit()
            msg = '<div class="alert alert-success">Your address has been reset to default. The trap is removed.</div>'
        elif action == 'plant':
            payload = request.form.get('payload', '').strip()
            import re
            # Accept iframe with src ending in /csrf-demo (any prefix - works on IP or multi-tenant lab)
            m = re.match(r'^<iframe\s+src=["\']([^"\']*?/csrf-demo\?to=[A-Za-z0-9_]+&amount=\d+)["\']([^>]*)></iframe>$', payload)
            if not m:
                msg = '<div class="alert alert-danger">Payload rejected. Only iframes pointing to /shop/csrf-demo with to= and amount= parameters are accepted.</div>'
            else:
                # Rewrite the src to include the actual prefix so the attack works when viewed through the lab proxy
                original_src = m.group(1)
                extra_attrs = m.group(2)  # preserves style/width/etc
                # Extract the query part (everything after /csrf-demo)
                query_part = original_src.split('/csrf-demo', 1)[1]
                rewritten_src = P + '/csrf-demo' + query_part
                rewritten_payload = '<iframe src="' + rewritten_src + '"' + extra_attrs + '></iframe>'
                db = get_db()
                db.execute("UPDATE users SET address=? WHERE username=?", (rewritten_payload, session['username']))
                db.commit()
                db_user = db.execute("SELECT id FROM users WHERE username=?", (session['username'],)).fetchone()
                user_id = db_user['id'] if db_user else '?'
                msg = '<div class="alert alert-success" style="line-height:1.7"><strong>&#9989; Trap planted in your profile.</strong><br>Your <code>address</code> field now contains the malicious iframe. The next user who visits <code>' + P + '/profile?id=' + str(user_id) + '</code> while authenticated will trigger the transfer with their own session cookie.<br><br><strong>Next steps:</strong><br>1. <a href="' + P + '/logout">Logout</a><br>2. <a href="' + P + '/login">Login as the victim</a> (e.g. <code>admin</code>)<br>3. Visit <code>' + P + '/profile?id=' + str(user_id) + '</code> &mdash; the trap fires automatically.<br>4. Verify the transfer on <a href="' + P + '/transfer">' + P + '/transfer</a>.</div>'
    try:
        tpl = open('/app/csrf_challenge.html', 'r').read()
        tpl = tpl.replace('{P}', P)
    except:
        tpl = '<div class="alert alert-danger">CSRF challenge template not found</div>'
    return page('CSRF Challenge', msg + tpl)

@app.route('/cookie-check')
def cookie_check():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    try:
        content = open('/app/cookie_check.html', 'r').read()
    except:
        content = '<div class="alert alert-danger">Cookie check not found</div>'
    return page('Cookie Security Check', content)

@app.route('/mitigation-challenges')
def mitigation_challenges():
    if not session.get('username'):
        return redirect('%s/login' % P, code=303)
    try:
        content = open('/app/mitigation_challenges.html', 'r').read()
    except:
        content = '<div class="alert alert-danger">Challenges not found</div>'
    return page('Mitigation Challenges', content)

@app.route('/reset-db')
def reset_db():
    import os
    try:
        os.remove('/app/data/shop.db')
    except:
        pass
    init_db()
    session.clear()
    return page('Database Reset', '<div class="alert alert-success">Database has been completely reset to original state!</div><div class="card" style="text-align:center"><p>All users, products, reviews, and transfers restored to defaults.</p><br><a href="%s/login" class="btn">Login Again</a></div>' % P)

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  ShopSecure v2.0 - VULNERABLE BY DESIGN")
    print("  SYNAPSE Cybersecurity Education Platform")
    print("=" * 50)
    print("  URL: http://localhost:8080/welcome")
    print("  Admin:  admin / adminShop2026")
    print("  Users:  user1/user1Pass! ... user5/user5Pass!")
    print("=" * 50)
    app.run(host='0.0.0.0', port=8080, debug=False)
