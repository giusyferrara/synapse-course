#!/usr/bin/env python3
"""
Spot the Bug — offline variant generator (B1: pre-generate a pool, zero runtime AI cost).

Pipeline (correctness first — nothing is published blind):
    generate  ->  structural-validate  ->  (AI verify pass)  ->  write to a PENDING pool
                                                                  ^ a human approves before it goes live

Two modes, SAME validator and SAME output schema:
    --mock   fill exercises from {{placeholder}} pools. No AI, no keys. Works today.
    --ai     ask the model (reuses ai.router.AIRouter -> Claude Sonnet-4) to author NEW
             exercises, then a second AI pass verifies technical correctness.

Output:  spotbug_variants/<deck>.pending.json   (list of validated exercises, status="pending_review")
Approve: review the file, then:  python tools/spotbug_gen.py --approve --deck <deck>
         -> moves verified items into spotbug_variants/<deck>.json  (the pool the game serves)

Usage:
    python tools/spotbug_gen.py --mock --deck all --n 20
    ANTHROPIC_API_KEY=...  python tools/spotbug_gen.py --ai --deck netmon --n 30 --verify
    python tools/spotbug_gen.py --approve --deck netmon

The whole platform is ENGLISH: all generated content must be English.
"""
import argparse, json, os, re, sys, random, asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "spotbug_variants"

# ---------------------------------------------------------------- seeds (one per deck; expand freely)
# Each seed anchors the style for --ai and provides the {{hole}} templates for --mock.
TEMPLATES = [
    {"id": "tcpdump_w", "deck": "netmon", "lang": "tcpdump",
     "ctxForms": ["capture traffic on {{IF}} to a file", "save packets from {{IF}} to analyse later"],
     "code": ["sudo tcpdump -i {{IF}} -o {{FILE}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-o is not how tcpdump writes to a file.",
     "fixLines": ["sudo tcpdump -i {{IF}} ___ {{FILE}}"], "slots": ["-w"], "tokens": ["-w", "-o", "-f", "-r"],
     "fixWhy": "-w writes the raw packets; you read them back with -r.",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "FILE": ["capture.pcap", "traffic.pcap", "dump.pcap", "wire.pcap"]}},

    # --- netmon seeds vetted from the netmon --ai pilot review (2026-06-04) ---
    {"id": "nmap_scantype", "deck": "netmon", "lang": "nmap",
     "ctxForms": ["scan for open TCP ports on {{HOST}}", "list the open TCP ports on {{HOST}}"],
     "code": ["nmap -sU -p {{RANGE}} {{HOST}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-sU runs a UDP scan, not a TCP scan, so it will not find open TCP ports.",
     "fixLines": ["nmap ___ -p {{RANGE}} {{HOST}}"], "slots": ["-sT"], "tokens": ["-sT", "-sU", "-sn", "-sA"],
     "fixWhy": "-sT does a TCP connect scan to find open TCP ports (-sS SYN scan also works but needs root).",
     "pools": {"HOST": ["127.0.0.1", "192.168.1.10", "10.0.0.5", "target.local"], "RANGE": ["1-1000", "1-65535", "22,80,443", "1-1024"]}},

    {"id": "tcpdump_timestamps", "deck": "netmon", "lang": "tcpdump",
     "ctxForms": ["capture traffic to/from {{HOST}} keeping timestamps", "capture packets on {{IF}} with timestamps"],
     "code": ["sudo tcpdump -i {{IF}} -v -t host {{HOST}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-t SUPPRESSES the timestamp on every line, which defeats the goal of capturing with timestamps.",
     "fixLines": ["sudo tcpdump -i {{IF}} -v ___ host {{HOST}}"], "slots": ["-tt"], "tokens": ["-tt", "-t", "-T", "-A"],
     "fixWhy": "-tt prints an unformatted (epoch) timestamp per packet; -t removes timestamps entirely.",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "HOST": ["192.168.1.100", "10.0.0.5", "8.8.8.8", "172.16.0.9"]}},

    {"id": "tshark_capture_vs_display", "deck": "netmon", "lang": "tshark",
     "ctxForms": ["read {{FILE}} and keep only {{PROTO}} packets", "filter a saved capture {{FILE}} down to {{PROTO}}"],
     "code": ["tshark -r {{FILE}} -f {{PROTO}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-f is a capture (BPF) filter that only applies to a live capture; reading a file needs a display filter.",
     "fixLines": ["tshark -r {{FILE}} ___ {{PROTO}}"], "slots": ["-Y"], "tokens": ["-Y", "-f", "-R", "-d"],
     "fixWhy": "-Y applies a Wireshark display filter when reading a pcap; -f only works during live capture.",
     "pools": {"FILE": ["capture.pcap", "network.pcap", "traffic.pcap", "http.pcap"], "PROTO": ["dns", "http", "tcp", "tls"]}},

    {"id": "tshark_numeric", "deck": "netmon", "lang": "tshark",
     "ctxForms": ["read {{FILE}} and show HTTP requests without slow DNS lookups", "extract HTTP request host+URI from {{FILE}} without name resolution"],
     "code": ["tshark -r {{FILE}} -Y http.request -T fields -e http.host -e http.request.uri"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong value", "Wrong syntax"],
     "why": "Without -n, tshark resolves addresses via DNS — slow, and it leaks lookups for the very hosts you are analysing.",
     "fixLines": ["tshark ___ -r {{FILE}} -Y http.request -T fields -e http.host -e http.request.uri"], "slots": ["-n"], "tokens": ["-n", "-N", "-d", "-q"],
     "fixWhy": "-n disables name resolution: faster analysis and no DNS leakage.",
     "pools": {"FILE": ["capture.pcap", "network.pcap", "traffic.pcap", "http.pcap"]}},

    {"id": "netstat_numeric", "deck": "netmon", "lang": "netstat",
     "ctxForms": ["list listening TCP ports with their process, without slow reverse-DNS", "show TCP listeners + PIDs fast (no name resolution)"],
     "code": ["netstat -tlp"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong value", "Wrong syntax"],
     "why": "Without -n, netstat resolves addresses and ports via reverse DNS, which is slow and noisy.",
     "fixLines": ["netstat -___lp"], "slots": ["tn"], "tokens": ["tn", "tl", "tu", "ta"],
     "fixWhy": "-n shows numeric addresses/ports, avoiding slow reverse-DNS lookups.",
     "pools": {}},

    {"id": "dig_reverse", "deck": "netmon", "lang": "dig",
     "ctxForms": ["do a reverse DNS (PTR) lookup for {{IP}}", "find the hostname behind {{IP}}"],
     "code": ["dig -r {{IP}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong tool", "Wrong value", "Wrong syntax"],
     "why": "-r only tells dig to skip ~/.digrc; it does NOT perform a reverse lookup.",
     "fixLines": ["dig ___ {{IP}}"], "slots": ["-x"], "tokens": ["-x", "-r", "-p", "-t"],
     "fixWhy": "-x builds the in-addr.arpa PTR query automatically for a reverse lookup.",
     "pools": {"IP": ["192.168.1.1", "8.8.8.8", "10.0.0.53", "1.1.1.1"]}},

    {"id": "tcpflow_bpf", "deck": "netmon", "lang": "tcpflow",
     "ctxForms": ["reconstruct TCP flows on port {{PORT}} into {{DIR}}", "reassemble streams on port {{PORT}} with tcpflow"],
     "code": ["sudo tcpflow -i {{IF}} -p {{PORT}} -o {{DIR}}"], "vuln": 0, "category": "Wrong syntax",
     "options": ["Wrong syntax", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "tcpflow takes its filter as a bare BPF expression (port {{PORT}}); -p is the no-promiscuous flag, so '-p {{PORT}}' is not a port filter.",
     "fixLines": ["sudo tcpflow -i {{IF}} ___ {{PORT}} -o {{DIR}}"], "slots": ["port"], "tokens": ["port", "-p", "-P", "dst"],
     "fixWhy": "Filters are bare BPF: 'port {{PORT}}'. (-o correctly sets the output directory.)",
     "pools": {"IF": ["eth0", "wlan0", "ens33", "enp0s3"], "PORT": ["80", "443", "53", "8080"], "DIR": ["/tmp/flows/", "./out/", "/var/tmp/cap/", "flows/"]}},

    {"id": "bola", "deck": "api", "lang": "Python",
     "ctxForms": ["an endpoint returns a {{RES}} by id", "the API reads a {{RES}} given its id"],
     "code": ['@app.get("/api/{{RES}}/<id>")', "def get(id):", "    return db.{{RES}}(id)"], "vuln": 2,
     "category": "BOLA (IDOR)", "options": ["BOLA (IDOR)", "BFLA", "Mass assignment", "SSRF"],
     "why": "Any authenticated user can read someone else's {{RES}} by changing the id — the ownership check is missing.",
     "fixLines": ["row = db.{{RES}}(id)", "if row.owner != ___.id: abort(403)", "return row"], "slots": ["current_user"],
     "tokens": ["current_user", "id", "db", "request"],
     "fixWhy": "Verify the resource belongs to the caller (BOLA = #1 API risk).",
     "pools": {"RES": ["invoices", "orders", "tickets", "documents"]}},

    # --- api seeds vetted from the api --ai run (2026-06-04); one per OWASP API class ---
    {"id": "api_bfla", "deck": "api", "lang": "Python",
     "ctxForms": ["an admin endpoint deletes a {{RES}} by id", "a privileged action on a {{RES}}"],
     "code": ['@app.delete("/api/admin/{{RES}}s/{item_id}")',
              "async def admin_delete(item_id: int, current_user=Depends(get_current_user)):",
              "    await db.delete_{{RES}}(item_id)",
              '    return {"message": "deleted"}'],
     "vuln": 2, "category": "BFLA",
     "options": ["BFLA", "BOLA (IDOR)", "Mass assignment", "Broken authentication"],
     "why": "Any authenticated user can call this admin endpoint — there is no role check, so authentication is mistaken for authorization.",
     "fixLines": ['    if ___.role != "admin":', "        raise HTTPException(403)", "    await db.delete_{{RES}}(item_id)"],
     "slots": ["current_user"], "tokens": ["current_user", "item_id", "db", "request"],
     "fixWhy": "Enforce the required role on every privileged function (function-level authorization).",
     "pools": {"RES": ["user", "account", "product", "invoice"]}},

    {"id": "api_mass_assignment", "deck": "api", "lang": "Python",
     "ctxForms": ["the API updates a {{RES}} from the request body", "a PUT endpoint updates a {{RES}}"],
     "code": ["@app.route('/api/{{RES}}/<int:item_id>', methods=['PUT'])",
              "def update_{{RES}}(item_id):",
              "    record = load_{{RES}}(item_id)",
              "    record.update(**request.json)",
              "    db.session.commit()",
              "    return jsonify(record.to_dict())"],
     "vuln": 3, "category": "Mass assignment",
     "options": ["Mass assignment", "BOLA (IDOR)", "BFLA", "Broken authentication"],
     "why": "Binding the whole JSON body lets an attacker set protected fields (is_admin, price, balance) that should not be user-controllable.",
     "fixLines": ["    allowed = ['name', 'description']",
                  "    data = {k: v for k, v in request.json.items() if k in ___}",
                  "    record.update(**data)"],
     "slots": ["allowed"], "tokens": ["allowed", "request.json", "record", "data"],
     "fixWhy": "Bind only an explicit allowlist of fields; never map the raw request body onto the model.",
     "pools": {"RES": ["product", "profile", "subscription", "article"]}},

    {"id": "api_jwt_none", "deck": "api", "lang": "Python",
     "ctxForms": ["a {{FW}} endpoint validates a JWT", "JWT verification on a protected route"],
     "code": ["token = request.headers.get('Authorization', '').replace('Bearer ', '')",
              "payload = jwt.decode(token, SECRET, algorithms=['HS256', 'none'])",
              "return jsonify({'user_id': payload['user_id']})"],
     "vuln": 1, "category": "Broken authentication",
     "options": ["Broken authentication", "BOLA (IDOR)", "SSRF", "Mass assignment"],
     "why": "Allowing the 'none' algorithm accepts UNSIGNED tokens, so an attacker can forge any payload.",
     "fixLines": ["payload = jwt.decode(token, SECRET, algorithms=['___'])"],
     "slots": ["HS256"], "tokens": ["HS256", "none", "RS256", "ES256"],
     "fixWhy": "Pin the exact expected algorithm; never accept 'none' (it skips signature verification).",
     "pools": {"FW": ["Flask", "FastAPI"]}},

    {"id": "api_jwt_noverify", "deck": "api", "lang": "Python",
     "ctxForms": ["a {{FW}} route decodes a JWT", "JWT handling on a protected endpoint"],
     "code": ["token = request.headers.get('Authorization', '').replace('Bearer ', '')",
              "payload = jwt.decode(token, options={'verify_signature': False})",
              "return jsonify({'user_id': payload['user_id']})"],
     "vuln": 1, "category": "Broken authentication",
     "options": ["Broken authentication", "BOLA (IDOR)", "Mass assignment", "SSRF"],
     "why": "Disabling signature verification lets an attacker forge a token with any payload.",
     "fixLines": ["payload = jwt.decode(token, SECRET, algorithms=['HS256'], options={'verify_signature': ___})"],
     "slots": ["True"], "tokens": ["True", "False", "None", "0"],
     "fixWhy": "Verify the signature with the key and a pinned algorithm; never disable verification.",
     "pools": {"FW": ["Flask", "FastAPI"]}},

    {"id": "api_ssrf", "deck": "api", "lang": "Python",
     "ctxForms": ["the server fetches a user-supplied URL", "an endpoint downloads content from a URL in the request"],
     "code": ["@app.post('/api/{{ACTION}}')",
              "def {{ACTION}}():",
              "    url = request.json['url']",
              "    resp = requests.get(url)",
              "    return {'content': resp.text}"],
     "vuln": 3, "category": "SSRF",
     "options": ["SSRF", "BOLA (IDOR)", "Mass assignment", "Broken authentication"],
     "why": "The server fetches any URL the user supplies, so an attacker can reach internal services or the cloud metadata endpoint (169.254.169.254).",
     "fixLines": ["    host = urlparse(url).hostname",
                  "    if host not in ___:",
                  "        abort(400)",
                  "    resp = requests.get(url)"],
     "slots": ["ALLOWED_HOSTS"], "tokens": ["ALLOWED_HOSTS", "url", "request", "resp"],
     "fixWhy": "Allowlist permitted hosts (and block private/link-local ranges); a scheme check alone does NOT stop SSRF.",
     "pools": {"ACTION": ["fetch_avatar", "import_profile", "load_preview", "fetch_webhook"]}},

    {"id": "api_rate_limit", "deck": "api", "lang": "Python",
     "ctxForms": ["a login endpoint with no throttling", "the auth endpoint accepts unlimited attempts"],
     "code": ["@app.route('/api/login', methods=['POST'])",
              "def login():",
              "    user = User.authenticate(request.json['email'], request.json['password'])",
              "    return {'token': make_token(user)} if user else ({'error': 'bad creds'}, 401)"],
     "vuln": 0, "category": "Missing rate limiting",
     "options": ["Missing rate limiting", "BOLA (IDOR)", "SSRF", "Mass assignment"],
     "why": "With no throttle, an attacker can brute-force or credential-stuff the login endpoint without limit.",
     "fixLines": ["@___.limit('5 per minute')",
                  "@app.route('/api/login', methods=['POST'])"],
     "slots": ["limiter"], "tokens": ["limiter", "app", "request", "flask"],
     "fixWhy": "Rate-limit auth endpoints (e.g. flask-limiter @limiter.limit) and lock out repeated failures.",
     "pools": {}},

    {"id": "api_excessive_data", "deck": "api", "lang": "Python",
     "ctxForms": ["the API returns a {{RES}} object", "an endpoint serializes a {{RES}}"],
     "code": ["@app.route('/api/{{RES}}/<int:item_id>')",
              "def get_{{RES}}(item_id):",
              "    record = load_{{RES}}(item_id)",
              "    return jsonify(record.__dict__)"],
     "vuln": 3, "category": "Excessive data exposure",
     "options": ["Excessive data exposure", "BOLA (IDOR)", "Mass assignment", "BFLA"],
     "why": "Serializing the whole object ships internal/sensitive fields (cost, password_hash, internal_notes) to the client.",
     "fixLines": ["    return jsonify(___(record))   # explicit response schema"],
     "slots": ["public_schema"], "tokens": ["public_schema", "record.__dict__", "vars", "dict"],
     "fixWhy": "Serialize through an explicit response schema exposing only safe fields; never dump __dict__.",
     "pools": {"RES": ["product", "user", "order", "account"]}},

    {"id": "api_info_disclosure", "deck": "api", "lang": "Python",
     "ctxForms": ["the message returned on failed login", "what the API leaks on a failed auth attempt"],
     "code": ["user = User.authenticate(request.json['username'], request.json['password'])",
              "if not user:",
              "    return jsonify({'error': 'no user in table users_prod'}), 401",
              "return jsonify({'token': make_token(user)})"],
     "vuln": 2, "category": "Information disclosure",
     "options": ["Information disclosure", "BOLA (IDOR)", "Mass assignment", "SSRF"],
     "why": "The error leaks internal details (the DB table name, whether the account exists), helping user enumeration and recon.",
     "fixLines": ["    return jsonify({'error': '___'}), 401"],
     "slots": ["Invalid credentials"], "tokens": ["Invalid credentials", "no user in table users_prod", "DB error", "User not found"],
     "fixWhy": "Return one generic message; never reveal whether the user exists or internal schema details.",
     "pools": {}},

    {"id": "store", "deck": "mobile", "lang": "Java",
     "ctxForms": ["the app stores the {{SECRET}}", "where the app keeps the {{SECRET}}"],
     "code": ['prefs.edit().putString("{{SECRET}}", value).apply()   // SharedPreferences, plaintext'], "vuln": 0,
     "category": "Insecure storage", "options": ["Insecure storage", "Weak crypto", "Exported component", "Hardcoded secret"],
     "why": "Plaintext SharedPreferences are readable on rooted devices or in backups.",
     "fixLines": ["store the {{SECRET}} via ___ / EncryptedSharedPreferences"], "slots": ["Keystore"],
     "tokens": ["Keystore", "SD card", "logcat", "clipboard"],
     "fixWhy": "Use the Android Keystore (EncryptedSharedPreferences); never store secrets in plaintext.",
     "pools": {"SECRET": ["token", "refresh_token", "PIN", "api_key"]}},

    # --- mobile seeds vetted from the mobile --ai review (2026-06-04); covers the 6 MASVS classes ---
    {"id": "mobile_ios_storage", "deck": "mobile", "lang": "Swift",
     "ctxForms": ["the iOS app stores the {{SECRET}}", "where the iOS app keeps the {{SECRET}}"],
     "code": ["let defaults = UserDefaults.standard",
              'defaults.set({{SECRET}}, forKey: "{{SECRET}}")',
              "defaults.synchronize()"],
     "vuln": 1, "category": "Insecure storage",
     "options": ["Insecure storage", "Weak crypto", "Exported component", "Hardcoded secret"],
     "why": "UserDefaults is a plaintext plist, readable from device backups or on a jailbroken device.",
     "fixLines": ["store {{SECRET}} in the ___ instead of UserDefaults"], "slots": ["Keychain"],
     "tokens": ["Keychain", "Documents", "Cache", "Bundle"],
     "fixWhy": "Use the iOS Keychain (hardware-backed, access-controlled) for tokens/secrets; never UserDefaults.",
     "pools": {"SECRET": ["authToken", "biometricToken", "refreshToken", "apiKey"]}},

    {"id": "mobile_allow_backup", "deck": "mobile", "lang": "XML",
     "ctxForms": ["the AndroidManifest backup setting", "the <application> backup flag"],
     "code": ['<application android:name=".App"',
              '    android:allowBackup="true"',
              '    android:label="@string/app_name">'],
     "vuln": 1, "category": "Insecure storage",
     "options": ["Insecure storage", "Weak crypto", "Exported component", "Hardcoded secret"],
     "why": "allowBackup=true lets anyone with adb pull the app's private data (SharedPreferences, databases) via backup.",
     "fixLines": ['    android:allowBackup="___"'], "slots": ["false"],
     "tokens": ["false", "true", "encrypted", "secure"],
     "fixWhy": "Set allowBackup=false so app-private data cannot be extracted through adb backup.",
     "pools": {}},

    {"id": "mobile_exported_service", "deck": "mobile", "lang": "XML",
     "ctxForms": ["an internal {{COMP}} in AndroidManifest.xml", "a sensitive {{COMP}} declaration"],
     "code": ['<service android:name=".{{COMP}}"',
              '         android:exported="true" />'],
     "vuln": 1, "category": "Exported component",
     "options": ["Exported component", "Insecure storage", "Weak crypto", "Hardcoded secret"],
     "why": "Exported with no permission, any other app can bind to and trigger this internal service.",
     "fixLines": ['         android:exported="___" />'], "slots": ["false"],
     "tokens": ["false", "true", "system", "signature"],
     "fixWhy": "Set exported=false for internal components (or require a signature permission if it must be reachable).",
     "pools": {"COMP": ["PaymentProcessorService", "SyncService", "AdminService", "KeyVaultService"]}},

    {"id": "mobile_exported_permission", "deck": "mobile", "lang": "XML",
     "ctxForms": ["a broadcast receiver that must stay exported", "an exported receiver for {{ACTION}}"],
     "code": ['<receiver android:name=".PaymentReceiver"',
              '          android:exported="true">',
              '    <intent-filter>',
              '        <action android:name="{{ACTION}}" />',
              '    </intent-filter>',
              '</receiver>'],
     "vuln": 1, "category": "Exported component",
     "options": ["Exported component", "Insecure storage", "Weak crypto", "Missing certificate pinning"],
     "why": "The receiver is exported with no permission, so any app can send it forged broadcasts.",
     "fixLines": ['          android:exported="true"', '          android:permission="___">'], "slots": ["com.app.PAYMENT_PERMISSION"],
     "tokens": ["com.app.PAYMENT_PERMISSION", "android.permission.INTERNET", "true", "false"],
     "fixWhy": "Guard an exported component that must stay reachable with a custom signature permission.",
     "pools": {"ACTION": ["com.app.PAYMENT_COMPLETE", "com.app.SYNC_DONE", "com.app.TOKEN_REFRESH", "com.app.JOB_FINISHED"]}},

    {"id": "mobile_webview_file", "deck": "mobile", "lang": "Kotlin",
     "ctxForms": ["a WebView that loads remote content", "a WebView showing {{URL}}"],
     "code": ["webView.settings.javaScriptEnabled = true",
              "webView.settings.allowFileAccessFromFileURLs = true",
              'webView.loadUrl("{{URL}}")'],
     "vuln": 1, "category": "Insecure WebView",
     "options": ["Insecure WebView", "Weak crypto", "Exported component", "Insecure storage"],
     "why": "allowFileAccessFromFileURLs lets JavaScript in loaded content read local files via file:// URLs.",
     "fixLines": ["webView.settings.allowFileAccessFromFileURLs = ___"], "slots": ["false"],
     "tokens": ["false", "true", "null", "1"],
     "fixWhy": "Disable file-URL JS access (and AllowUniversalAccessFromFileURLs) for any WebView showing remote content.",
     "pools": {"URL": ["https://partner.example.com", "https://portal.example.com/orders", "https://dash.example.com", "https://app.example.com/x"]}},

    {"id": "mobile_weak_crypto", "deck": "mobile", "lang": "Java",
     "ctxForms": ["the app encrypts {{DATA}} at rest", "encrypting {{DATA}} before storing it"],
     "code": ['Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");',
              "cipher.init(Cipher.ENCRYPT_MODE, key);",
              "byte[] out = cipher.doFinal({{DATA}}.getBytes());"],
     "vuln": 0, "category": "Weak crypto",
     "options": ["Weak crypto", "Insecure storage", "Exported component", "Hardcoded secret"],
     "why": "ECB encrypts identical plaintext blocks to identical ciphertext, leaking structure, and gives no integrity.",
     "fixLines": ['Cipher cipher = Cipher.getInstance("AES/___/NoPadding");'], "slots": ["GCM"],
     "tokens": ["GCM", "ECB", "CBC", "none"],
     "fixWhy": "Use AES/GCM (authenticated) with a random nonce; ECB reveals patterns and offers no integrity.",
     "pools": {"DATA": ["paymentInfo", "token", "userData", "secret"]}},

    {"id": "mobile_logs_token", "deck": "mobile", "lang": "Java",
     "ctxForms": ["debugging the auth flow", "logging during authentication"],
     "code": ["String authToken = generateAuthToken(user, pass);",
              'Log.d("Auth", "Generated token: " + authToken);',
              "saveTokenToPrefs(authToken);"],
     "vuln": 1, "category": "Sensitive data in logs",
     "options": ["Sensitive data in logs", "Insecure storage", "Exported component", "Weak crypto"],
     "why": "Tokens written with Log.d land in logcat, readable via adb or by apps holding READ_LOGS.",
     "fixLines": ['Log.d("Auth", "token issued for user: " + ___);'], "slots": ["user"],
     "tokens": ["user", "authToken", "pass", "sessionId"],
     "fixWhy": "Log only non-sensitive identifiers; never log tokens/passwords (and strip debug logs in release).",
     "pools": {}},

    {"id": "mobile_tls_validation_disabled", "deck": "mobile", "lang": "Java",
     "ctxForms": ["the HTTPS client setup for the {{API}} API", "configuring TLS for {{API}} calls"],
     "code": ["HttpsURLConnection conn = (HttpsURLConnection) url.openConnection();",
              "conn.setHostnameVerifier(SSLSocketFactory.ALLOW_ALL_HOSTNAME_VERIFIER);",
              "conn.connect();"],
     "vuln": 1, "category": "Disabled certificate validation",
     "options": ["Disabled certificate validation", "Insecure storage", "Weak crypto", "Exported component"],
     "why": "ALLOW_ALL_HOSTNAME_VERIFIER accepts ANY hostname on the certificate, so a MITM cert is trusted — TLS validation is effectively off.",
     "fixLines": ["conn.setHostnameVerifier(___);"], "slots": ["HttpsURLConnection.getDefaultHostnameVerifier()"],
     "tokens": ["HttpsURLConnection.getDefaultHostnameVerifier()", "SSLSocketFactory.ALLOW_ALL_HOSTNAME_VERIFIER", "(h, s) -> true", "null"],
     "fixWhy": "Keep the default strict hostname verifier (and ideally pin the certificate); never accept all hostnames.",
     "pools": {"API": ["payment", "banking", "auth", "sync"]}},

    {"id": "mw_strings", "deck": "malware", "lang": "strings",
     "ctxForms": ["extract readable strings (including Windows wide/UTF-16) from {{FILE}}",
                  "pull strings from {{FILE}}, including the wide ones"],
     "code": ["strings {{FILE}}"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "By default strings finds 7-bit ASCII only; it misses UTF-16 (wide) strings common in Windows malware.",
     "fixLines": ["strings -e ___ {{FILE}}"], "slots": ["l"], "tokens": ["l", "s", "b", "a"],
     "fixWhy": "strings -e l extracts UTF-16LE (wide) strings; -e b for big-endian.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "loader.dll"]}},

    {"id": "objdump_section", "deck": "malware", "lang": "objdump",
     "ctxForms": ["disassemble the executable code of {{FILE}}", "look at the runnable instructions inside {{FILE}}"],
     "code": ["objdump -d -j .data {{FILE}}"], "vuln": 0, "category": "Wrong value",
     "options": ["Wrong value", "Wrong flag", "Wrong tool", "Wrong syntax"],
     "why": "The .data section holds static data, not code; the runnable instructions live in .text, so this disassembles the wrong section.",
     "fixLines": ["objdump -d -j ___ {{FILE}}"], "slots": [".text"], "tokens": [".text", ".data", ".bss", ".rodata"],
     "fixWhy": "Disassemble .text, where the runnable code lives; .data is only static values.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "loader.dll"]}},

    {"id": "entropy_tool", "deck": "malware", "lang": "binwalk",
     "ctxForms": ["check whether {{FILE}} is packed by measuring its entropy", "decide if {{FILE}} is packed or encrypted"],
     "code": ["hexdump -C {{FILE}}"], "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong flag", "Wrong value", "Wrong approach"],
     "why": "A raw hex dump tells you nothing about packing; you need an entropy view to spot compressed or encrypted regions.",
     "fixLines": ["___ -E {{FILE}}"], "slots": ["binwalk"], "tokens": ["binwalk", "hexdump", "xxd", "cat"],
     "fixWhy": "binwalk -E plots entropy; a high, flat curve signals packing or encryption.",
     "pools": {"FILE": ["sample.exe", "packed.bin", "dropper.exe", "suspicious.exe"]}},

    {"id": "r2_analysis", "deck": "malware", "lang": "radare2",
     "ctxForms": ["open {{FILE}} in radare2 and run full auto-analysis", "analyse all functions and references in {{FILE}} with r2"],
     "code": ["r2 -qc aa {{FILE}}"], "vuln": 0, "category": "Wrong value",
     "options": ["Wrong value", "Wrong flag", "Wrong tool", "Wrong syntax"],
     "why": "aa runs only the basic analysis pass; it misses functions, strings and cross-references needed for malware triage.",
     "fixLines": ["r2 -qc ___ {{FILE}}"], "slots": ["aaa"], "tokens": ["aaa", "aa", "af", "pdf"],
     "fixWhy": "aaa runs the deeper auto-analysis (functions, refs, strings); aa is only the minimal pass.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "trojan.exe", "loader.dll"]}},

    {"id": "upx_unpack", "deck": "malware", "lang": "upx",
     "ctxForms": ["unpack the UPX-packed sample {{FILE}} without destroying the original", "decompress {{FILE}} but keep the packed sample as evidence"],
     "code": ["upx -d {{FILE}}"], "vuln": 0, "category": "Missing flag",
     "options": ["Missing flag", "Wrong flag", "Wrong tool", "Wrong value"],
     "why": "upx -d unpacks in place and overwrites the original file, so the packed evidence sample is lost.",
     "fixLines": ["upx -d ___ unpacked.exe {{FILE}}"], "slots": ["-o"], "tokens": ["-o", "-k", "-q", "-f"],
     "fixWhy": "-o writes the unpacked copy to a new file, leaving the original packed sample intact.",
     "pools": {"FILE": ["trojan.exe", "packed.exe", "sample.exe", "dropper.exe"]}},

    {"id": "binwalk_entropy", "deck": "malware", "lang": "binwalk",
     "ctxForms": ["measure the entropy of {{FILE}} to judge if it is packed", "scan {{FILE}} for high-entropy packed regions"],
     "code": ["binwalk -e {{FILE}}"], "vuln": 0, "category": "Wrong flag",
     "options": ["Wrong flag", "Wrong value", "Wrong tool", "Wrong syntax"],
     "why": "-e extracts embedded files; it does not show entropy, so it will not tell you whether the sample is packed.",
     "fixLines": ["binwalk ___ {{FILE}}"], "slots": ["-E"], "tokens": ["-E", "-e", "-A", "-B"],
     "fixWhy": "-E (capital) plots an entropy curve; high and flat means packed or encrypted.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "dropper.exe", "suspicious.bin"]}},

    {"id": "hash_ioc", "deck": "malware", "lang": "bash",
     "ctxForms": ["compute a reliable hash of {{FILE}} to share as an IOC", "fingerprint {{FILE}} for an indicator of compromise"],
     "code": ["md5sum {{FILE}}"], "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong flag", "Wrong value", "Wrong approach"],
     "why": "MD5 is collision-prone: two different files can produce the same MD5, so it is unsafe as a unique malware identifier.",
     "fixLines": ["___ {{FILE}}"], "slots": ["sha256sum"], "tokens": ["sha256sum", "md5sum", "crc32", "base64"],
     "fixWhy": "Use sha256sum, which is collision-resistant and the standard for malware IOCs.",
     "pools": {"FILE": ["sample.exe", "payload.bin", "trojan.exe", "ransomware.exe"]}},

    {"id": "volatility", "deck": "dfir", "lang": "acquisition",
     "ctxForms": ["order of collection during live acquisition of {{HOST}}", "on compromised {{HOST}}: what do you collect first"],
     "code": ["image the {{HOST}} disk first, then capture RAM", "(RAM is far more volatile than disk)"],
     "vuln": 0, "category": "Wrong approach", "options": ["Wrong approach", "Wrong tool", "Wrong value", "Wrong field"],
     "why": "The order of volatility says collect what disappears first.",
     "fixLines": ["capture ___ first (order of volatility)"], "slots": ["memory"],
     "tokens": ["memory", "the disk", "the logs", "the backups"],
     "fixWhy": "Order of volatility: CPU/cache -> RAM -> network state -> disk -> archives. RAM dies on power-off.",
     "pools": {"HOST": ["WS-014", "SRV-DC1", "LAPTOP-07", "HOST-22"]}},

    # --- dfir seeds vetted/authored from the dfir --ai review (2026-06-05) ---
    {"id": "dfir_mem_psscan", "deck": "dfir", "lang": "Volatility3",
     "ctxForms": ["hunt rootkit-hidden processes in {{HOST}}'s memory image", "list processes from {{DUMP}}, including unlinked ones"],
     "code": ["vol.py -f {{DUMP}} windows.pslist", "# a rootkit may have unlinked its process to hide"],
     "vuln": 0, "category": "Wrong plugin",
     "options": ["Wrong plugin", "Wrong tool", "Wrong value", "Wrong approach"],
     "why": "windows.pslist walks the active process list, which a rootkit can unlink from to stay hidden.",
     "fixLines": ["vol.py -f {{DUMP}} ___"], "slots": ["windows.psscan"],
     "tokens": ["windows.psscan", "windows.pslist", "windows.netscan", "windows.malfind"],
     "fixWhy": "windows.psscan pool-scans memory for EPROCESS structures, revealing unlinked/hidden processes (DKOM).",
     "pools": {"HOST": ["WS-05", "SRV-DB", "LAPTOP-12", "WEB-SRV"], "DUMP": ["memory.dmp", "mem.raw", "dump.mem", "host.lime"]}},

    {"id": "dfir_mem_netscan", "deck": "dfir", "lang": "Volatility3",
     "ctxForms": ["recover the malware's C2 connections from {{HOST}}'s memory", "find network connections in the dump {{DUMP}}"],
     "code": ["vol.py -f {{DUMP}} windows.pslist", "# goal: find the malware's C2 network connections"],
     "vuln": 0, "category": "Wrong plugin",
     "options": ["Wrong plugin", "Wrong tool", "Wrong value", "Wrong approach"],
     "why": "windows.pslist lists processes, not connections, so it cannot reveal the C2 endpoints.",
     "fixLines": ["vol.py -f {{DUMP}} ___"], "slots": ["windows.netscan"],
     "tokens": ["windows.netscan", "windows.pslist", "windows.psscan", "windows.filescan"],
     "fixWhy": "windows.netscan recovers TCP/UDP endpoints and their owning PIDs from the memory image.",
     "pools": {"HOST": ["WS-05", "SRV-DB", "LAPTOP-12", "WEB-SRV"], "DUMP": ["memory.dmp", "mem.raw", "dump.mem", "host.lime"]}},

    {"id": "dfir_imaging_dc3dd", "deck": "dfir", "lang": "acquisition",
     "ctxForms": ["create a court-admissible image of {{DEV}}", "forensically image {{DEV}} with integrity hashing"],
     "code": ["dd if={{DEV}} of=evidence.dd bs=4096", "# imaging done - but is it verifiable?"],
     "vuln": 0, "category": "Missing integrity verification",
     "options": ["Missing integrity verification", "Wrong tool", "Wrong value", "Wrong approach"],
     "why": "Plain dd computes no hash, so the image cannot be proven unaltered for court.",
     "fixLines": ["___ if={{DEV}} of=evidence.dd bs=4096 hash=sha256"], "slots": ["dc3dd"],
     "tokens": ["dc3dd", "dd", "cat", "cp"],
     "fixWhy": "dc3dd with hash=sha256 hashes during acquisition; ewfacquire (E01) is another forensic option.",
     "pools": {"DEV": ["/dev/sda", "/dev/sdb", "/dev/nvme0n1", "/dev/sdc"]}},

    {"id": "dfir_imaging_verify", "deck": "dfir", "lang": "acquisition",
     "ctxForms": ["image {{DEV}} and prove the copy is intact", "acquire {{DEV}} and record an integrity hash"],
     "code": ["dd if={{DEV}} of=evidence.dd bs=4096", "# ready for analysis"],
     "vuln": 0, "category": "Missing integrity verification",
     "options": ["Missing integrity verification", "Wrong tool", "Wrong value", "Wrong approach"],
     "why": "Without hashing the source and the image, you cannot prove the copy was not altered.",
     "fixLines": ["dd if={{DEV}} of=evidence.dd bs=4096 && ___ {{DEV}} evidence.dd"], "slots": ["sha256sum"],
     "tokens": ["sha256sum", "md5sum", "file", "ls"],
     "fixWhy": "Hash both the source and the image (SHA-256) and compare; matching hashes prove integrity.",
     "pools": {"DEV": ["/dev/sda", "/dev/sdb", "/dev/nvme0n1", "/dev/sdc"]}},

    {"id": "dfir_execution_artifact", "deck": "dfir", "lang": "DFIR",
     "ctxForms": ["prove whether {{EXE}} actually RAN on the host", "find execution evidence for {{EXE}}"],
     "code": ["MFTECmd.exe -f C:\\$MFT --csv C:\\analysis", "# trying to prove {{EXE}} was executed"],
     "vuln": 0, "category": "Wrong artifact",
     "options": ["Wrong artifact", "Wrong tool", "Wrong value", "Wrong approach"],
     "why": "The $MFT records file creation/modification, not execution; it cannot prove a program ran.",
     "fixLines": ["___ -d C:\\Windows\\Prefetch --csv C:\\analysis"], "slots": ["PECmd.exe"],
     "tokens": ["PECmd.exe", "MFTECmd.exe", "EvtxECmd.exe", "RegRipper"],
     "fixWhy": "Prefetch (parsed by PECmd) holds run count + last-run times - the execution evidence; also ShimCache/AmCache.",
     "pools": {"EXE": ["suspicious.exe", "psexec.exe", "mimikatz.exe", "dropper.exe"]}},

    {"id": "dfir_timeline", "deck": "dfir", "lang": "plaso",
     "ctxForms": ["build a super-timeline from the image {{SRC}}", "extract timeline events from {{SRC}} into a plaso file"],
     "code": ["psort.py -o l2tcsv -w timeline.csv timeline.plaso", "# ...but timeline.plaso has not been created yet"],
     "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong order", "Wrong value", "Wrong approach"],
     "why": "psort.py only PROCESSES an existing plaso storage file; nothing has extracted the events yet.",
     "fixLines": ["___ timeline.plaso {{SRC}}", "psort.py -o l2tcsv -w timeline.csv timeline.plaso"], "slots": ["log2timeline.py"],
     "tokens": ["log2timeline.py", "psort.py", "vol.py", "MFTECmd.exe"],
     "fixWhy": "log2timeline.py <storage> <source> extracts events into the plaso file; psort.py then formats it.",
     "pools": {"SRC": ["disk.raw", "image.dd", "/evidence/", "C.vhdx"]}},

    {"id": "dfir_event_log", "deck": "dfir", "lang": "PowerShell",
     "ctxForms": ["find failed logons in a saved {{LOG}}.evtx", "search {{LOG}}.evtx for a specific Event ID"],
     "code": ["grep 4625 {{LOG}}.evtx", "# .evtx is a binary event-log file"],
     "vuln": 0, "category": "Wrong tool",
     "options": ["Wrong tool", "Wrong value", "Wrong approach", "Wrong field"],
     "why": "EVTX is a binary format; grep cannot parse it and will miss or garble events.",
     "fixLines": ['___ -Path {{LOG}}.evtx -FilterXPath "*[System[EventID=4625]]"'], "slots": ["Get-WinEvent"],
     "tokens": ["Get-WinEvent", "grep", "strings", "cat"],
     "fixWhy": "Get-WinEvent parses EVTX and filters by Event ID (4625 = failed logon); EvtxECmd --csv is the Zimmerman alternative.",
     "pools": {"LOG": ["Security", "System", "Application", "Windows-PowerShell"]}},
]
DECKS = sorted({t["deck"] for t in TEMPLATES})

# ---------------------------------------------------------------- the strict validator (mirror of the deck validator)
def validate(ex):
    """Raise AssertionError with a reason if the exercise is malformed."""
    assert isinstance(ex, dict), "not an object"
    assert isinstance(ex.get("code"), list) and ex["code"], "code must be a non-empty list"
    assert isinstance(ex.get("vuln"), int) and 0 <= ex["vuln"] < len(ex["code"]), "vuln out of range"
    opts = ex.get("options")
    assert isinstance(opts, list) and len(opts) == 4 and len(set(opts)) == 4, "options must be 4 distinct"
    assert opts[0] == ex.get("category"), "options[0] must equal category"
    blanks = sum(l.count("___") for l in ex.get("fixLines", []))
    assert blanks >= 1 and blanks == len(ex.get("slots", [])), "blank count must equal len(slots)"
    toks = ex.get("tokens", [])
    assert 3 <= len(toks) <= 6 and len(set(toks)) == len(toks), "tokens must be 3-6 distinct"
    assert all(s in toks for s in ex["slots"]), "every slot must be in tokens"
    for k in ("lang", "ctx", "why", "fixWhy"):
        assert isinstance(ex.get(k), str) and ex[k].strip(), f"missing {k}"
    for s in ex["code"] + ex["fixLines"]:
        assert "</script>" not in s, "literal </script> not allowed"
    return ex

def canon(ex):
    """Stable key for dedupe (the bug line + the fix)."""
    return "|".join(ex["code"]) + "##" + "|".join(ex["fixLines"]) + "##" + "|".join(ex["slots"])

# ---------------------------------------------------------------- MOCK generation (no AI)
def gen_mock(deck, n):
    pool = [t for t in TEMPLATES if t["deck"] == deck]
    if not pool:
        return []
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < n * 40:
        tries += 1
        t = random.choice(pool)
        pick = {k: random.choice(v) for k, v in t.get("pools", {}).items()}
        sub = lambda s: re.sub(r"\{\{(\w+)\}\}", lambda m: pick.get(m.group(1), m.group(0)), s)
        ex = {"lang": t["lang"], "ctx": sub(random.choice(t["ctxForms"])),
              "code": [sub(x) for x in t["code"]], "vuln": t["vuln"], "category": sub(t["category"]),
              "options": [sub(x) for x in t["options"]], "why": sub(t["why"]),
              "fixLines": [sub(x) for x in t["fixLines"]], "slots": [sub(x) for x in t["slots"]],
              "tokens": [sub(x) for x in t["tokens"]], "fixWhy": sub(t["fixWhy"])}
        try:
            validate(ex)
        except AssertionError:
            continue
        k = canon(ex)
        if k in seen:
            continue
        seen.add(k)
        ex["_origin"] = "mock"
        out.append(ex)
    return out

# ---------------------------------------------------------------- AI generation (reuses ai.router.AIRouter)
GEN_PROMPT = (
    "You are an exercise author for a cybersecurity game called Spot the Bug. "
    "Produce ONE new exercise for the given deck, on a realistic command/tool/code snippet, "
    "where EXACTLY one line is wrong or dangerous. Teach the correct usage and explain WHY. "
    "Language: ENGLISH (the whole platform is English). "
    "Reply with VALID JSON ONLY, no extra text, in this exact schema:\n"
    '{"lang":str,"ctx":str,"code":[str],"vuln":int,"category":str,'
    '"options":[str,str,str,str],"why":str,"fixLines":[str],"slots":[str],"tokens":[str],"fixWhy":str}\n'
    "Rules: options[0] MUST equal category and the 4 options MUST be distinct; "
    "the number of '___' in fixLines MUST equal len(slots); every slot MUST be in tokens; "
    "tokens has 3-4 distinct entries (the right one + plausible distractors); "
    "0 <= vuln < len(code); no backticks, no markdown, no '</script>'. "
    "SELF-CONSISTENCY (critical): the line at index vuln MUST literally contain the described mistake; never say a flag is missing if it already appears in that line, and never flag a line that is actually correct; the fix MUST genuinely correct that exact line. "
    "VARIETY: vary the tool, technique and bug category widely across the deck's scope; do NOT default to missing- or wrong-flag puzzles. "
    "TOOLS (critical): if the request gives an allowed-tools list, use ONLY those tools and ONLY real, standard flags/options you are certain exist; NEVER invent a tool, flag, or subcommand. If you are unsure whether a flag or tool exists, choose a different idea rather than guess. "
    "Generate an exercise DIFFERENT from the seed (other tool/flag/scenario), not a mere rewrite."
)

# Per-deck constraints that keep the model on ground it actually knows — that is where
# hallucination (invented tools/flags/APIs) stops. Each value is a dict; supported keys:
#   "tools"      -> CLI decks: the ONLY commands allowed (use real flags, never invent).
#   "frameworks" -> code decks: the ONLY frameworks allowed (real mainstream APIs only).
#   "bugs"       -> the vulnerability classes the bug must belong to.
#   "note"       -> extra free-form guidance appended verbatim.
# A deck with no entry falls back to unconstrained generation.
DECK_ALLOWLIST = {
    "netmon": {
        "tools": ["tcpdump", "tshark", "nmap", "ss", "netstat", "ngrep", "tcpflow", "dig"],
    },
    "api": {
        "frameworks": ["Python Flask", "Python FastAPI", "Node.js Express"],
        "bugs": [
            "BOLA / IDOR (missing object-level ownership check)",
            "BFLA (missing role / function-level authorization)",
            "mass assignment (binding untrusted fields to a model)",
            "broken authentication (JWT alg/none, weak session handling)",
            "SSRF (server fetches a user-supplied URL)",
            "missing rate limiting / brute-force protection on auth",
            "excessive data exposure / verbose errors leaking internals",
        ],
        "note": ("Bugs MUST be CONCEPTUAL — a real line of code where a security check is missing or wrong "
                 "(the vuln line is that code line; the fix adds/repairs the check). Do NOT make CLI-flag trivia. "
                 "Use only real, mainstream APIs of the allowed frameworks; never invent decorators, methods, or libraries."),
    },
    "mobile": {
        "tools": ["adb", "apktool", "jadx", "keytool", "frida", "objection"],
        "bugs": [
            "insecure data storage (secrets in plaintext SharedPreferences / NSUserDefaults / files)",
            "exported component (activity/service/receiver exported with no permission)",
            "insecure WebView (JS bridge to untrusted content, file/URL access)",
            "weak crypto or hardcoded key (AES/ECB, a static key shipped in the app)",
            "sensitive data in logs (Log.d / println leaking tokens or PII)",
            "missing certificate pinning / trusting user-added CAs",
        ],
        "note": ("Bugs are mostly CODE/CONFIG in Java/Kotlin or AndroidManifest.xml — a real line where a control is "
                 "missing or wrong, and the fix repairs that exact line. frida and objection are the riskiest tools: "
                 "use ONLY real commands and hooks on real Android/Java classes & methods (e.g. Java.use(...), "
                 "javax.net.ssl, objection 'android sslpinning disable'); never invent a Frida/objection API."),
    },
    "dfir": {
        "tools": ["vol.py", "dd", "dc3dd", "ewfacquire", "sha256sum", "MFTECmd", "EvtxECmd",
                  "wevtutil", "log2timeline.py", "psort.py", "RegRipper", "PECmd"],
        "bugs": [
            "memory forensics: the wrong Volatility 3 plugin (windows.pslist misses hidden/unlinked processes -> windows.psscan)",
            "imaging integrity: imaging without hashing/verification (no SHA-256), or using a non-forensic copy",
            "timeline: wrong order or wrong tool for a super-timeline (log2timeline.py extracts events -> psort.py processes them)",
            "Windows event logs: the wrong tool (grep on a binary .evtx) or the wrong Event ID for the artifact",
            "artifact analysis: wrong artifact/tool for the question (MFT via MFTECmd, registry via RegRipper, execution evidence via PECmd/Prefetch)",
        ],
        "note": ("Volatility 3 ONLY: vol.py with plugin namespaces (windows.pslist, windows.psscan, windows.netscan) — "
                 "NEVER use --profile (that is Volatility 2). For EVERY tool here the bug must be CONCEPTUAL / a usage "
                 "mistake — the wrong artifact, the wrong tool for the question, a missing integrity step, or the wrong "
                 "plugin/Event-ID — NOT obscure flag trivia. Use ONLY flags/options that certainly exist; if unsure a flag "
                 "exists, make the bug a tool/artifact/step choice instead. Do NOT produce chain-of-custody or pure-process "
                 "exercises — there is no single command line to get wrong in those."),
    },
}

def _allow_instruction(deck):
    """Build the per-deck constraint text appended to the generation request."""
    spec = DECK_ALLOWLIST.get(deck)
    if not spec:
        return ""
    parts = []
    if spec.get("tools"):
        if spec.get("bugs"):  # mixed deck (CLI + code/config): tools constrain ONLY the CLI exercises
            parts.append("When an exercise uses a CLI tool, use ONLY one of these: " + ", ".join(spec["tools"]) +
                         ", with real commands/flags/APIs only; never invent a tool, flag, command, or API.")
        else:               # pure CLI deck: every exercise must be one of these tools
            parts.append("Use ONLY one of these tools, nothing else: " + ", ".join(spec["tools"]) +
                         ". Use only real, standard flags; never invent a tool or flag.")
    if spec.get("frameworks"):
        parts.append("Use ONLY these frameworks: " + ", ".join(spec["frameworks"]) +
                     ". Use only their real, mainstream APIs; never invent decorators, methods, or libraries.")
    if spec.get("bugs"):
        parts.append("The bug MUST be one of these vulnerability classes: " + "; ".join(spec["bugs"]) + ".")
    if spec.get("note"):
        parts.append(spec["note"])
    return " " + " ".join(parts)
VERIFY_PROMPT = (
    "You are a senior security engineer reviewing one Spot the Bug exercise for TECHNICAL CORRECTNESS. "
    "Check: is the flagged line (index 'vuln') really the wrong/dangerous one? Is 'category' accurate? "
    "Is the fix in fixLines+slots actually correct and the 'why'/'fixWhy' factually right? "
    'Reply with JSON ONLY: {"correct": true|false, "reason": "<short>"}. Be strict — if unsure, say false.'
)

def _extract_json(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else None

async def gen_ai(deck, n, verify):
    from ai.router import AIRouter
    router = AIRouter()
    seed_ex = gen_mock(deck, 1) or gen_mock(DECKS[0], 1)
    seed = seed_ex[0] if seed_ex else {}
    seed_json = json.dumps({k: seed[k] for k in ("lang", "ctx", "code", "vuln", "category", "options", "why", "fixLines", "slots", "tokens", "fixWhy") if k in seed})
    out, seen, tries = [], set(), 0
    while len(out) < n and tries < n * 4:
        tries += 1
        nonce = random.randint(1000, 9999)
        used_tools = sorted(t for t in {e.get("lang", "") for e in out} if t)
        used_cats = sorted(c for c in {e.get("category", "") for e in out} if c)
        avoid_t = (" Avoid reusing these tools/frameworks already used in this batch: " + ", ".join(used_tools) + ".") if used_tools else ""
        # Variety: for decks with a bug-class list, ROTATE the target class so coverage spreads
        # evenly (this is what api needed — rotating the framework left the bug class stuck on BOLA).
        bug_classes = (DECK_ALLOWLIST.get(deck) or {}).get("bugs")
        if bug_classes:
            target_bug = bug_classes[len(out) % len(bug_classes)]
            variety = (f" This exercise MUST cover this vulnerability class, not another: {target_bug}. "
                       "Pick a fresh endpoint/scenario each time (orders, payments, file upload, login, search, admin, webhook, etc.); "
                       "do NOT keep using a 'user profile update' scene.")
        elif used_cats:
            variety = " Cover a DIFFERENT bug category than these already produced: " + ", ".join(used_cats) + "."
        else:
            variety = ""
        allow = _allow_instruction(deck)
        ask = (f"Deck: {deck}. Style example (do NOT copy it): {seed_json}. "
               f"Make it clearly different (variation #{nonce}).{allow}{variety}{avoid_t}")
        try:
            raw = await router.get_chat_response(GEN_PROMPT, [{"role": "user", "content": ask}])
            ex = _extract_json(raw)
            validate(ex)
        except (AssertionError, json.JSONDecodeError, TypeError) as e:
            print(f"  · rejected (schema): {e}")
            continue
        k = canon(ex)
        if k in seen:
            continue
        if verify:
            try:
                vraw = await router.get_chat_response(VERIFY_PROMPT,
                        [{"role": "user", "content": json.dumps(ex)}])
                verdict = _extract_json(vraw) or {}
                if not verdict.get("correct"):
                    print(f"  · rejected (verify): {verdict.get('reason', '?')}")
                    continue
            except Exception as e:
                print(f"  · verify error, skipping: {e}")
                continue
        seen.add(k)
        ex["_origin"] = "ai-verified" if verify else "ai"
        out.append(ex)
        print(f"  · accepted {len(out)}/{n}: {ex['lang']} — {ex['ctx'][:48]}")
    return out

# ---------------------------------------------------------------- IO / CLI
def write_pending(deck, items):
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"{deck}.pending.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    seen = {canon(e) for e in existing}
    added = [e for e in items if canon(e) not in seen]
    for e in added:
        e["status"] = "pending_review"
    existing.extend(added)
    path.write_text(json.dumps(existing, indent=1, ensure_ascii=False), encoding="utf-8")
    return path, len(added), len(existing)

def approve(deck):
    pend = OUT_DIR / f"{deck}.pending.json"
    if not pend.exists():
        print(f"no pending file for {deck}")
        return
    items = [e for e in json.loads(pend.read_text(encoding="utf-8")) if e.get("status") != "rejected"]
    for e in items:
        for junk in ("status", "_origin"):
            e.pop(junk, None)
        validate(e)  # final gate
    live = OUT_DIR / f"{deck}.json"
    live.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"approved {len(items)} -> {live}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="all", help="deck id or 'all'")
    ap.add_argument("--n", type=int, default=20, help="exercises per deck")
    ap.add_argument("--mock", action="store_true", help="generate from {{placeholder}} pools, no AI")
    ap.add_argument("--ai", action="store_true", help="generate with the AI model")
    ap.add_argument("--verify", action="store_true", help="add the AI correctness-verification pass (with --ai)")
    ap.add_argument("--approve", action="store_true", help="move pending -> live pool")
    args = ap.parse_args()

    decks = DECKS if args.deck == "all" else [args.deck]

    if args.approve:
        for d in decks:
            approve(d)
        return

    if not (args.mock or args.ai):
        ap.error("choose --mock or --ai (or --approve)")

    for d in decks:
        print(f"[{d}] generating {args.n} ({'mock' if args.mock else 'ai'})...")
        items = gen_mock(d, args.n) if args.mock else asyncio.run(gen_ai(d, args.n, args.verify))
        path, added, total = write_pending(d, items)
        print(f"[{d}] +{added} new (pool now {total}) -> {path.name}")

if __name__ == "__main__":
    main()
