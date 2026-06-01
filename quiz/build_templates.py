#!/usr/bin/env python3
"""
Authoring source for the Adaptive Vulnerability Assessment Quiz.

Running this script (bootstrap) emits the two editable stores:
  - quiz/quiz_templates/<template_id>.json   (template DEFINITIONS, the logic)
  - quiz/hand_authored/<id>.json             (hand-authored concrete questions)

After bootstrap these JSON files ARE the source of truth; generate_quiz.py
consumes them and expands templates into static/quiz_content/.

Why some questions are hand-authored (generated_from_template: null):
  A template has ONE correct_option shared by all variants. That works when
  the parameter only changes the *scenario* (the answer stays the same).
  For tooling like `nmap -sV` vs `-sn`, the correct answer CHANGES with the
  parameter, so they cannot be one single-correct template — the schema's own
  provision for hand-authored questions is used instead.

Security correctness is non-negotiable: every item carries a source_reference
and the explanation distinguishes the correct CWE from the distractors.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TPL_DIR = os.path.join(HERE, "quiz_templates")
HAND_DIR = os.path.join(HERE, "hand_authored")

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
TEMPLATE_FIELDS = [
    "template_id", "category", "skill_tag", "owasp", "severity", "difficulty",
    "prompt", "code_template", "variables", "correct_option", "distractor_pool",
    "explanation_template", "source_reference", "validation_notes",
    "variants_expected",
]


def T(**kw):
    """Build a template dict, filling optional fields with sensible defaults."""
    kw.setdefault("code_template", None)
    kw.setdefault("variables", {})
    kw.setdefault("owasp", None)
    kw.setdefault("severity", None)
    kw.setdefault("validation_notes", "")
    # variants_expected = product of variable list lengths (1 if none)
    n = 1
    for vals in kw["variables"].values():
        n *= len(vals)
    kw.setdefault("variants_expected", n)
    missing = [f for f in TEMPLATE_FIELDS if f not in kw]
    if missing:
        raise ValueError(f"{kw.get('template_id')}: missing fields {missing}")
    return {f: kw[f] for f in TEMPLATE_FIELDS}


# Common CWE display names used as correct answers / distractors
PATH_TRAVERSAL = "Path Traversal"
CMD_INJ = "OS Command Injection"
XSS = "Cross-Site Scripting (XSS)"
SQLI = "SQL Injection"
CODE_INJ = "Code Injection"
DESER = "Insecure Deserialization"
XXE = "XML External Entity (XXE)"
SSRF = "Server-Side Request Forgery (SSRF)"
UPLOAD = "Unrestricted File Upload"
HARDCODED = "Use of Hard-coded Credentials"
IDOR = "Insecure Direct Object Reference (IDOR)"
OPEN_REDIRECT = "Open Redirect"
BROKEN_CRYPTO = "Use of a Broken or Risky Cryptographic Algorithm"
WEAK_RANDOM = "Use of Insufficiently Random Values"
NO_HTTPONLY = "Sensitive Cookie Without HttpOnly Flag"
NO_SECURE = "Sensitive Cookie Without Secure Flag"
NO_SAMESITE = "Sensitive Cookie with Improper SameSite Attribute"
ERROR_LEAK = "Information Exposure Through an Error Message"
UNCHECKED = "Improper Check for Unusual or Exceptional Conditions"
RES_EXHAUST = "Allocation of Resources Without Limits or Throttling"
MISSING_HEADERS = "Protection Mechanism Failure (Missing Security Headers)"
DIR_LISTING = "Information Exposure Through Directory Listing"
INFO_EXPOSURE = "Exposure of Sensitive Information"
CSRF = "Cross-Site Request Forgery (CSRF)"
SESSION_FIXATION = "Session Fixation"
IMPROPER_AUTH = "Improper Authentication"
MISSING_AUTHZ = "Missing Authorization"
PRIV_MGMT = "Improper Privilege Management"
WEAK_HASH = "Use of Password Hash With Insufficient Computational Effort"

DETECT_PROMPT = "Which vulnerability is most likely present in this code?"

TEMPLATES = []

# ==========================================================================
# DETECT  (code/scenario -> identify the CWE)
# ==========================================================================
TEMPLATES += [
    T(template_id="detect_cwe22_pathtraversal", category="detect", skill_tag="CWE-22",
      owasp="A01", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\n{sink}(Path.of(baseDir, {param}));',
      variables={"param": ["file", "doc", "report"], "sink": ["Files.readString", "Files.readAllBytes"]},
      correct_option=PATH_TRAVERSAL,
      distractor_pool=[SQLI, CSRF, XSS, SSRF, CMD_INJ],
      explanation_template="User input `{param}` flows unsanitised into `Path.of(...)` and is read by `{sink}`. A value like `../../../../etc/passwd` escapes baseDir, so this is Path Traversal (CWE-22). The distractors are other ShopSecure CWEs but none fit: nothing here builds a query, reaches a browser, or makes a network request.",
      source_reference="CWE-22; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Unsanitised input reaches a file-read sink via Path.of; ../ escapes the base directory."),

    T(template_id="detect_cwe78_cmdinjection", category="detect", skill_tag="CWE-78",
      owasp="A03", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\nRuntime.getRuntime().exec(new String[]{"bash", "-c", "{cmd} " + {param}});',
      variables={"param": ["host", "ip", "target"], "cmd": ["ping", "nslookup"]},
      correct_option=CMD_INJ,
      distractor_pool=[CODE_INJ, PATH_TRAVERSAL, SQLI, SSRF],
      explanation_template="`{param}` is concatenated into a `bash -c` string, so input like `; rm -rf /` is interpreted by the shell — OS Command Injection (CWE-78). The key near-miss is Code Injection (CWE-94): that runs code in a language interpreter (e.g. eval), whereas here a real OS shell runs the command. Fix: drop the shell and pass arguments as a list, with allow-listed input.",
      source_reference="CWE-78; OWASP A03:2021 (Injection)",
      validation_notes="User input concatenated into a shell command line ('bash -c ...')."),

    T(template_id="detect_cwe79_xss", category="detect", skill_tag="CWE-79",
      owasp="A03", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\n{sink};',
      variables={"param": ["name", "comment", "q"],
                 "sink": ['response.getWriter().write("<div>" + {param} + "</div>")',
                          'out.println("Hello " + {param})']},
      correct_option=XSS,
      distractor_pool=[SQLI, PATH_TRAVERSAL, CMD_INJ, CSRF],
      explanation_template="`{param}` is written straight into the HTML response with no output encoding, so input like `<script>...</script>` executes in the victim's browser — reflected Cross-Site Scripting (CWE-79). It is not SQLi or command injection: the data reaches a browser, not a database or a shell. Fix: contextually output-encode before rendering.",
      source_reference="CWE-79; OWASP A03:2021 (Injection)",
      validation_notes="Unencoded user input written into the HTML response body."),

    T(template_id="detect_cwe89_sqli", category="detect", skill_tag="CWE-89",
      owasp="A03", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template="""String {param} = request.getParameter("{param}");\nString sql = "SELECT * FROM {table} WHERE name = '" + {param} + "'";\nstmt.executeQuery(sql);""",
      variables={"param": ["name", "user", "q"], "table": ["users", "accounts"]},
      correct_option=SQLI,
      distractor_pool=[XSS, PATH_TRAVERSAL, IDOR, CMD_INJ],
      explanation_template="`{param}` is concatenated into the SQL string, so `' OR '1'='1` (and worse) changes the query's meaning — SQL Injection (CWE-89). The data flows into a database query, not a browser (XSS) or a shell (command injection). Fix: use a parameterised query (PreparedStatement) with bound parameters.",
      source_reference="CWE-89; OWASP A03:2021 (Injection)",
      validation_notes="User input concatenated into a SQL string passed to executeQuery."),

    T(template_id="detect_cwe94_codeinjection", category="detect", skill_tag="CWE-94",
      owasp="A03", severity="high", difficulty="advanced", prompt=DETECT_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\nScriptEngine engine = new ScriptEngineManager().getEngineByName("{engine}");\nengine.eval({param});',
      variables={"param": ["expr", "script"], "engine": ["nashorn", "JavaScript"]},
      correct_option=CODE_INJ,
      distractor_pool=[CMD_INJ, SSRF, SQLI, DESER],
      explanation_template="`{param}` is passed to `engine.eval(...)`, so an attacker supplies arbitrary script that the interpreter executes — Code Injection (CWE-94). The near-miss is OS Command Injection (CWE-78): that runs shell commands, while this runs code inside a language engine (here a JS engine). Fix: never eval untrusted input; use a safe expression library with an allow-list.",
      source_reference="CWE-94; OWASP A03:2021 (Injection)",
      validation_notes="Untrusted input reaches a scripting-engine eval()."),

    T(template_id="detect_cwe502_deserialization", category="detect", skill_tag="CWE-502",
      owasp="A08", severity="high", difficulty="advanced", prompt=DETECT_PROMPT,
      code_template="ObjectInputStream ois = new ObjectInputStream({source});\n{type} obj = ({type}) ois.readObject();",
      variables={"source": ["request.getInputStream()", "socket.getInputStream()"],
                 "type": ["Object", "UserSession"]},
      correct_option=DESER,
      distractor_pool=[CODE_INJ, XXE, SQLI, SSRF],
      explanation_template="Untrusted bytes from `{source}` are passed to `ObjectInputStream.readObject()`. Crafted objects trigger gadget chains that run during deserialisation — Insecure Deserialization (CWE-502), which can reach remote code execution. It is not Code Injection via eval and not XXE (no XML). Fix: avoid native deserialisation of untrusted data; use a safe format (JSON) with a strict schema, or an allow-list of classes.",
      source_reference="CWE-502; OWASP A08:2021 (Software and Data Integrity Failures)",
      validation_notes="Untrusted stream deserialised via readObject()."),

    T(template_id="detect_cwe611_xxe", category="detect", skill_tag="CWE-611",
      owasp="A05", severity="high", difficulty="advanced", prompt=DETECT_PROMPT,
      code_template="// External entity / DTD processing is NOT disabled\n{parser}",
      variables={"parser": [
          "DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();\nDocument doc = f.newDocumentBuilder().parse(request.getInputStream());",
          "SAXParserFactory f = SAXParserFactory.newInstance();\nf.newSAXParser().parse(request.getInputStream(), handler);",
          "XMLInputFactory f = XMLInputFactory.newInstance();\nXMLStreamReader r = f.createXMLStreamReader(request.getInputStream());",
      ]},
      correct_option=XXE,
      distractor_pool=[DESER, SSRF, SQLI, CODE_INJ],
      explanation_template="Untrusted XML is parsed with DTD/external-entity processing left enabled, so a `<!ENTITY ... SYSTEM 'file:///etc/passwd'>` payload makes the parser read local files or fetch URLs — XML External Entity injection (CWE-611). SSRF can be a *consequence* of XXE, but the root weakness is the unsafe XML parser. Fix: disable DTDs and external entities on the factory.",
      source_reference="CWE-611; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Untrusted XML parsed without disabling DTD/external entities."),

    T(template_id="detect_cwe918_ssrf", category="detect", skill_tag="CWE-918",
      owasp="A10", severity="high", difficulty="intermediate",
      prompt="Which vulnerability is most likely present in this server-side code?",
      code_template='String {param} = request.getParameter("{param}");\n{fetch}',
      variables={"param": ["url", "target", "endpoint"],
                 "fetch": ["new java.net.URL({param}).openStream();",
                           "httpClient.send(HttpRequest.newBuilder(java.net.URI.create({param})).build(), HttpResponse.BodyHandlers.ofString());",
                           "restTemplate.getForObject({param}, String.class);"]},
      correct_option=SSRF,
      distractor_pool=[OPEN_REDIRECT, PATH_TRAVERSAL, CSRF, XXE, CMD_INJ],
      explanation_template="The value of `{param}` comes straight from request.getParameter and is fetched server-side. Because the server itself makes a request to an attacker-controlled address, this is Server-Side Request Forgery (CWE-918): the attacker can reach internal-only targets such as cloud metadata (169.254.169.254), localhost admin panels, or internal APIs the browser could never reach. It is NOT Open Redirect — the server fetches the URL itself rather than telling the user's browser to navigate. Fix: validate the URL against an allow-list of hosts and schemes, and block requests to internal/link-local IP ranges.",
      source_reference="CWE-918; OWASP A10:2021 (Server-Side Request Forgery)",
      validation_notes="User input flows into a server-side HTTP fetch. Open Redirect is the deliberate near-miss distractor."),

    T(template_id="detect_cwe434_unrestricted_upload", category="detect", skill_tag="CWE-434",
      owasp="A04", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template="Part filePart = request.getPart(\"file\");\nString name = Path.of(filePart.getSubmittedFileName()).getFileName().toString();  // path stripped\n// no file-type / extension validation\nFiles.copy(filePart.getInputStream(), Path.of(\"{dir}\", name));",
      variables={"dir": ["/var/www/uploads", "webapps/app/uploads", "public/files"]},
      correct_option=UPLOAD,
      distractor_pool=[PATH_TRAVERSAL, CMD_INJ, DESER, SSRF],
      explanation_template="The upload's type/extension is never validated and the file lands in a web-served directory ({dir}), so an attacker uploads `shell.jsp`/`shell.php` and requests it to get code execution — Unrestricted File Upload (CWE-434). It is not Path Traversal: `getFileName()` already strips directory components from the name. Fix: validate type/content, generate a server-side name, and store outside the web root without execute permission.",
      source_reference="CWE-434; OWASP A04:2021 (Insecure Design)",
      validation_notes="No type validation; stored in web root. Traversal is deliberately removed via getFileName() so CWE-434 is unambiguous."),

    T(template_id="detect_cwe798_hardcoded_creds", category="detect", skill_tag="CWE-798",
      owasp="A07", severity="high", difficulty="beginner", prompt=DETECT_PROMPT,
      code_template='private static final String {var} = "{secret}";',
      variables={"var": ["DB_PASSWORD", "API_KEY", "SECRET"], "secret": ["S3cr3tP@ss!", "prod_key_8f3a2b"]},
      correct_option=HARDCODED,
      distractor_pool=[BROKEN_CRYPTO, NO_SECURE, ERROR_LEAK, INFO_EXPOSURE],
      explanation_template="A credential (`{var}`) is embedded directly in source, so anyone with the code or compiled binary obtains it and it cannot be rotated without a redeploy — Use of Hard-coded Credentials (CWE-798). Fix: load it at runtime from an environment variable or a secrets manager and keep it out of version control.",
      source_reference="CWE-798; OWASP A07:2021 (Identification and Authentication Failures)",
      validation_notes="A secret literal is stored in source code."),

    T(template_id="detect_cwe639_idor", category="detect", skill_tag="CWE-639",
      owasp="A01", severity="high", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template="String {param} = request.getParameter(\"{param}\");\nvar record = {repo}.findById(Long.valueOf({param}));\nreturn record;  // no check that the record belongs to the logged-in user",
      variables={"param": ["id", "accountId", "orderId"], "repo": ["accountRepo", "orderRepo"]},
      correct_option=IDOR,
      distractor_pool=[MISSING_AUTHZ, SQLI, IMPROPER_AUTH, PATH_TRAVERSAL],
      explanation_template="The record is looked up directly by a client-supplied identifier (`{param}`) with no ownership check, so changing the id returns another user's record — Insecure Direct Object Reference (CWE-639). The key near-miss is Missing Authorization (CWE-862): IDOR specifically means a *direct object reference* used without an object-level ownership/authorisation check. Fix: verify the object belongs to the current user.",
      source_reference="CWE-639; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Direct object reference by user-supplied id with no ownership check."),

    T(template_id="detect_cwe601_open_redirect", category="detect", skill_tag="CWE-601",
      owasp="A01", severity="medium", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\n{redirect}',
      variables={"param": ["next", "url", "returnTo"],
                 "redirect": ["response.sendRedirect({param});", 'return "redirect:" + {param};']},
      correct_option=OPEN_REDIRECT,
      distractor_pool=[SSRF, XSS, PATH_TRAVERSAL, CSRF],
      explanation_template="A user-controlled value (`{param}`) is used as a redirect target, so a link to your site can bounce the victim to `evil.com` for phishing — Open Redirect (CWE-601). The near-miss is SSRF: there the *server* fetches the URL; here the *browser* is told to navigate. Fix: redirect only to an allow-list of internal paths.",
      source_reference="CWE-601; OWASP A01:2021 (Broken Access Control)",
      validation_notes="User input used as redirect destination. SSRF is the near-miss distractor."),

    T(template_id="detect_cwe327_broken_crypto", category="detect", skill_tag="CWE-327",
      owasp="A02", severity="medium", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='Cipher c = Cipher.getInstance("{algo}");',
      variables={"algo": ["DES", "DESede", "AES/ECB/PKCS5Padding"]},
      correct_option=BROKEN_CRYPTO,
      distractor_pool=[WEAK_HASH, WEAK_RANDOM, HARDCODED, INFO_EXPOSURE],
      explanation_template="`{algo}` is a broken/risky choice: DES and 3DES are obsolete and weak, and AES in ECB mode leaks plaintext patterns (identical blocks encrypt identically) — Use of a Broken or Risky Cryptographic Algorithm (CWE-327). Fix: use an authenticated mode such as AES-256-GCM with a unique IV per message.",
      source_reference="CWE-327; OWASP A02:2021 (Cryptographic Failures)",
      validation_notes="Weak cipher/mode (DES/3DES/ECB)."),

    T(template_id="detect_cwe330_weak_randomness", category="detect", skill_tag="CWE-330",
      owasp="A02", severity="medium", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template="String {param} = Long.toHexString(new java.util.Random().nextLong());  // used as a {param}",
      variables={"param": ["sessionToken", "resetToken", "csrfToken"]},
      correct_option=WEAK_RANDOM,
      distractor_pool=[BROKEN_CRYPTO, HARDCODED, SESSION_FIXATION, IDOR],
      explanation_template="`java.util.Random` is a predictable PRNG, so a `{param}` generated from it can be guessed or reconstructed by an attacker — Use of Insufficiently Random Values (CWE-330). Security tokens must be unpredictable. Fix: use `java.security.SecureRandom`.",
      source_reference="CWE-330; OWASP A02:2021 (Cryptographic Failures)",
      validation_notes="Security token derived from non-cryptographic java.util.Random."),

    T(template_id="detect_cwe1004_cookie_httponly", category="detect", skill_tag="CWE-1004",
      owasp="A05", severity="medium", difficulty="beginner", prompt=DETECT_PROMPT,
      code_template='Cookie c = new Cookie("{name}", value);\nc.setSecure(true);\n// HttpOnly flag not set\nresponse.addCookie(c);',
      variables={"name": ["session", "SID", "auth"]},
      correct_option=NO_HTTPONLY,
      distractor_pool=[NO_SECURE, NO_SAMESITE, XSS, SESSION_FIXATION],
      explanation_template="The `{name}` cookie is created without the HttpOnly flag, so client-side JavaScript can read it (e.g. `document.cookie`) and an XSS bug could exfiltrate the session — Sensitive Cookie Without HttpOnly Flag (CWE-1004). Note Secure IS set here, so 'without Secure' is wrong. Fix: set HttpOnly on session cookies.",
      source_reference="CWE-1004; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Secure is set but HttpOnly is missing — disambiguates from CWE-614."),

    T(template_id="detect_cwe614_cookie_secure", category="detect", skill_tag="CWE-614",
      owasp="A05", severity="medium", difficulty="beginner", prompt=DETECT_PROMPT,
      code_template='Cookie c = new Cookie("{name}", value);\nc.setHttpOnly(true);\n// Secure flag not set - cookie may be sent over plain HTTP\nresponse.addCookie(c);',
      variables={"name": ["session", "SID", "auth"]},
      correct_option=NO_SECURE,
      distractor_pool=[NO_HTTPONLY, NO_SAMESITE, CSRF, INFO_EXPOSURE],
      explanation_template="The `{name}` cookie is created without the Secure flag, so the browser will send it over unencrypted HTTP where a network attacker can capture it — Sensitive Cookie Without Secure Flag (CWE-614). Note HttpOnly IS set here, so 'without HttpOnly' is wrong. Fix: set Secure so the cookie is only sent over HTTPS.",
      source_reference="CWE-614; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="HttpOnly is set but Secure is missing — disambiguates from CWE-1004."),

    T(template_id="detect_cwe209_error_leak", category="detect", skill_tag="CWE-209",
      owasp="A04", severity="medium", difficulty="beginner", prompt=DETECT_PROMPT,
      code_template="try {\n    process(request);\n} catch (Exception e) {\n    response.getWriter().write({leak});\n}",
      variables={"leak": ["e.toString()", "e.getMessage()", "stackTraceToString(e)"]},
      correct_option=ERROR_LEAK,
      distractor_pool=[INFO_EXPOSURE, UNCHECKED, SQLI, XSS],
      explanation_template="The raw exception detail (`{leak}`) is written into the HTTP response, leaking stack traces, SQL fragments, framework versions, or file paths that help an attacker — Information Exposure Through an Error Message (CWE-209). Fix: log the detail server-side and return a generic message with an error id.",
      source_reference="CWE-209; OWASP A04:2021 (Insecure Design)",
      validation_notes="Exception detail returned to the client."),

    T(template_id="detect_cwe754_unchecked_condition", category="detect", skill_tag="CWE-754",
      owasp=None, severity="medium", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template="User u = userRepo.findByName({param});\n// return value not checked for null\nif (u.getRole().equals(\"ADMIN\")) grantAccess();",
      variables={"param": ['"admin"', 'request.getParameter("user")', "name"]},
      correct_option=UNCHECKED,
      distractor_pool=[IDOR, IMPROPER_AUTH, INFO_EXPOSURE, SQLI],
      explanation_template="`findByName({param})` can return null, but the code immediately calls `u.getRole()` without checking — Improper Check for Unusual or Exceptional Conditions (CWE-754). Beyond a crash (NullPointerException / denial of service), unchecked error paths can skip security logic and leave the app in an inconsistent state. Fix: check the result before use and fail safely.",
      source_reference="CWE-754",
      validation_notes="Return value not checked before dereference."),

    T(template_id="detect_cwe770_resource_exhaustion", category="detect", skill_tag="CWE-770",
      owasp=None, severity="medium", difficulty="intermediate", prompt=DETECT_PROMPT,
      code_template='int n = Integer.parseInt(request.getParameter("{param}"));\nbyte[] buffer = new byte[n];  // no upper bound enforced on n',
      variables={"param": ["count", "size", "length"]},
      correct_option=RES_EXHAUST,
      distractor_pool=[UNCHECKED, INFO_EXPOSURE, SQLI, IDOR],
      explanation_template="The client fully controls `n` (`{param}`) and the code allocates `new byte[n]` with no cap, so a huge value exhausts memory and crashes the service — Allocation of Resources Without Limits or Throttling (CWE-770), a denial-of-service. Fix: enforce a sane maximum before allocating.",
      source_reference="CWE-770",
      validation_notes="Unbounded allocation driven by client-controlled size."),

    T(template_id="detect_cwe693_missing_headers", category="detect", skill_tag="CWE-693",
      owasp="A05", severity="low", difficulty="beginner",
      prompt="Reviewing {context}, which weakness is indicated by the response headers below?",
      code_template="HTTP/1.1 200 OK\nContent-Type: text/html\n(no Content-Security-Policy, X-Frame-Options, or X-Content-Type-Options header)",
      variables={"context": ["a Java servlet", "the aiohttp web server", "the application's default responses"]},
      correct_option=MISSING_HEADERS,
      distractor_pool=[NO_SECURE, XSS, ERROR_LEAK, INFO_EXPOSURE],
      explanation_template="The response omits defence-in-depth security headers (Content-Security-Policy, X-Frame-Options, X-Content-Type-Options), weakening the browser-side protections that limit XSS, framing, and MIME-sniffing — Protection Mechanism Failure / Missing Security Headers (CWE-693). Fix: send a baseline set of security headers on every response.",
      source_reference="CWE-693; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Absent baseline security headers."),

    T(template_id="detect_cwe548_directory_listing", category="detect", skill_tag="CWE-548",
      owasp="A05", severity="low", difficulty="beginner",
      prompt="Which weakness does this web-server configuration introduce?",
      code_template="{config}",
      variables={"config": ["location /files/ {\n    autoindex on;   # nginx\n}",
                            "<Directory /var/www/files>\n    Options +Indexes   # Apache\n</Directory>",
                            "<servlet>listings = true</servlet>   <!-- Tomcat DefaultServlet -->"]},
      correct_option=DIR_LISTING,
      distractor_pool=[PATH_TRAVERSAL, INFO_EXPOSURE, MISSING_HEADERS, UPLOAD],
      explanation_template="The config enables automatic directory listing, so when no index file is present the server lists every file in the folder — attackers enumerate backups, configs, and source — Information Exposure Through Directory Listing (CWE-548). Fix: disable autoindex / Options Indexes / directory listings.",
      source_reference="CWE-548; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Directory listing explicitly enabled."),

    T(template_id="detect_cwe200_info_exposure", category="detect", skill_tag="CWE-200",
      owasp="A01", severity="low", difficulty="beginner", prompt=DETECT_PROMPT,
      code_template='return Map.of("name", user.getName(), {leak});  // serialised into the JSON API response',
      variables={"leak": ['"passwordHash", user.getPasswordHash()',
                          '"ssn", user.getSsn()',
                          '"apiToken", user.getApiToken()']},
      correct_option=INFO_EXPOSURE,
      distractor_pool=[ERROR_LEAK, IDOR, MISSING_AUTHZ, DIR_LISTING],
      explanation_template="A sensitive field ({leak}) is serialised straight into the API response, exposing data the client should never receive — Exposure of Sensitive Information (CWE-200). The near-miss is CWE-209, but that is specifically about *error messages*; this is a normal response. Fix: return a DTO/view model with only the fields the client needs.",
      source_reference="CWE-200; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Sensitive field serialised into a normal (non-error) response."),

    T(template_id="detect_cwe1275_cookie_samesite", category="detect", skill_tag="CWE-1275",
      owasp="A05", severity="low", difficulty="beginner",
      prompt="Which cookie weakness is shown here?",
      code_template="Set-Cookie: {name}=...; Secure; HttpOnly\n(no SameSite attribute set)",
      variables={"name": ["session", "SID", "auth"]},
      correct_option=NO_SAMESITE,
      distractor_pool=[CSRF, NO_HTTPONLY, NO_SECURE, SESSION_FIXATION],
      explanation_template="The `{name}` cookie sets Secure and HttpOnly but omits SameSite, so the browser attaches it to cross-site requests — which makes CSRF easier — Sensitive Cookie with Improper SameSite Attribute (CWE-1275). CSRF (CWE-352) is the *attack* this enables; the cookie misconfiguration itself is CWE-1275. Fix: set SameSite=Lax or Strict.",
      source_reference="CWE-1275; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Secure+HttpOnly present but SameSite missing. CSRF is the near-miss (attack vs cookie weakness)."),

    # --- NEW: completes the detect leg for CWE-352 ---
    T(template_id="detect_cwe352_csrf", category="detect", skill_tag="CWE-352",
      owasp="A01", severity="medium", difficulty="intermediate",
      prompt="This endpoint changes state and is authenticated only by the session cookie. Which vulnerability is most likely present?",
      code_template="// State-changing POST, authenticated by the session cookie only.\n// No anti-CSRF token (synchroniser token) is validated.\n{endpoint}",
      variables={"endpoint": [
          '@PostMapping("/transfer")\npublic void transfer(@RequestParam("amount") int amount) {\n    accountService.transfer(amount);\n}',
          '@PostMapping("/changeEmail")\npublic void changeEmail(@RequestParam("email") String email) {\n    accountService.changeEmail(email);\n}',
          '@PostMapping("/deleteAccount")\npublic void deleteAccount() {\n    accountService.deleteAccount(currentUserId());\n}']},
      correct_option=CSRF,
      distractor_pool=[XSS, SQLI, IDOR, SSRF, MISSING_AUTHZ],
      explanation_template="The endpoint performs a state-changing action and trusts the session cookie alone, with no anti-CSRF token. Because browsers automatically attach the session cookie to requests triggered by other sites, an attacker can host a page that auto-submits this POST and the victim's browser executes it as them — Cross-Site Request Forgery (CWE-352). It is not XSS (no script is reflected), not SQLi (no query), not IDOR (the issue isn't a guessable object id), not SSRF (no outbound request), and not Missing Authorization — the user IS authorised; the request just isn't proven to be intentional. Fix: validate a per-session synchroniser token on every state-changing request and set cookies SameSite=Lax/Strict.",
      source_reference="CWE-352; OWASP A01:2021 (Broken Access Control)",
      validation_notes="State-changing request with cookie-only auth and no anti-CSRF token. Endpoint signature co-varies with the action (amount/email/no-arg). Missing Authorization is the key near-miss: authorised-but-not-intentional (CSRF) vs not-authorised (CWE-862)."),
]

# ==========================================================================
# REMEDIATE  (given the vuln -> choose the correct fix)
# ==========================================================================
TEMPLATES += [
    T(template_id="remediate_cwe89_sqli", category="remediate", skill_tag="CWE-89",
      owasp="A03", severity="high", difficulty="beginner",
      prompt="This query concatenates user input. What is the correct fix?",
      code_template="String sql = \"SELECT * FROM {table} WHERE name = '\" + name + \"'\";\nstmt.executeQuery(sql);",
      variables={"table": ["users", "orders", "accounts"]},
      correct_option="Use a parameterised query (PreparedStatement) with bound parameters",
      distractor_pool=["HTML-encode the input before building the query",
                       "Remove single quotes from the input",
                       "Hash the input before querying",
                       "Add a Content-Security-Policy header"],
      explanation_template="Parameterised queries send the SQL and the data separately, so user input can never change the query structure — the correct, complete fix for SQL Injection (CWE-89). Stripping quotes is bypassable, and HTML/CSP fixes belong to XSS, not SQLi.",
      source_reference="CWE-89; OWASP A03:2021 (Injection)",
      validation_notes="Only PreparedStatement fully fixes SQLi; distractors are XSS fixes or bypassable blacklisting."),

    T(template_id="remediate_cwe79_xss", category="remediate", skill_tag="CWE-79",
      owasp="A03", severity="high", difficulty="intermediate",
      prompt="This reflects user input into an HTML page. What is the correct fix?",
      code_template='out.write("<div>" + {field} + "</div>");',
      variables={"field": ["comment", "name", "bio"]},
      correct_option="Contextually output-encode the data for the HTML context before rendering",
      distractor_pool=["Use a PreparedStatement",
                       "URL-encode the database connection string",
                       "Strip semicolons from the input",
                       "Set the HttpOnly flag on the session cookie"],
      explanation_template="Output-encoding for the exact context (HTML body, attribute, JS) neutralises markup so the browser renders it as text — the correct fix for XSS (CWE-79). PreparedStatement fixes SQLi; HttpOnly only limits cookie theft after XSS already works.",
      source_reference="CWE-79; OWASP A03:2021 (Injection)",
      validation_notes="Contextual output encoding is the fix; distractors address other CWEs."),

    T(template_id="remediate_cwe22_pathtraversal", category="remediate", skill_tag="CWE-22",
      owasp="A01", severity="high", difficulty="intermediate",
      prompt="This reads a file named by the user. What is the correct fix?",
      code_template='Path p = Path.of(baseDir, request.getParameter("{param}"));\nFiles.readAllBytes(p);',
      variables={"param": ["file", "doc", "name"]},
      correct_option="Canonicalise the resolved path and verify it stays within the intended base directory (allow-list)",
      distractor_pool=["Replace the substring \"../\" once",
                       "URL-decode the filename twice before use",
                       "Run the file read as a lower-privileged OS user",
                       "HTML-encode the filename"],
      explanation_template="Resolving the path and checking it still lives under baseDir (e.g. via toRealPath/normalize + startsWith) reliably stops traversal (CWE-22). A single `../` string replace is trivially bypassed (`....//`, encoding), and HTML-encoding is irrelevant to filesystem access.",
      source_reference="CWE-22; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Canonicalisation + containment check; blacklist replace is bypassable."),

    T(template_id="remediate_cwe78_cmdinjection", category="remediate", skill_tag="CWE-78",
      owasp="A03", severity="high", difficulty="intermediate",
      prompt="This runs a shell command built from user input. What is the correct fix?",
      code_template='Runtime.getRuntime().exec(new String[]{"bash", "-c", "ping " + {param}});',
      variables={"param": ["host", "ip", "target"]},
      correct_option="Avoid the shell: pass the program and arguments as a list to ProcessBuilder, and validate input against an allow-list",
      distractor_pool=["Escape spaces in the input",
                       "Wrap the command string in double quotes",
                       "Run the command with sudo",
                       "HTML-encode the host value"],
      explanation_template="Invoking the program directly with an argument array (no `bash -c`) means user input is treated as a single data argument, not shell syntax — the correct fix for OS Command Injection (CWE-78). Escaping/quoting is error-prone and bypassable; sudo makes it worse.",
      source_reference="CWE-78; OWASP A03:2021 (Injection)",
      validation_notes="Argument-array execution without a shell, plus allow-list."),

    T(template_id="remediate_cwe502_deserialization", category="remediate", skill_tag="CWE-502",
      owasp="A08", severity="high", difficulty="advanced",
      prompt="This deserialises untrusted bytes. What is the correct fix?",
      code_template="Object o = new ObjectInputStream({source}).readObject();",
      variables={"source": ["request.getInputStream()", "socket.getInputStream()", "new FileInputStream(f)"]},
      correct_option="Avoid native deserialisation of untrusted data; use a safe format (e.g. JSON) with a strict schema, or an allow-list of permitted classes",
      distractor_pool=["Encrypt the serialised bytes before reading them",
                       "Catch and log the deserialisation exception",
                       "Compress the stream before deserialising",
                       "Validate the object's fields after readObject() returns"],
      explanation_template="Gadget chains execute DURING readObject(), before you ever see the object, so validating fields afterwards is too late (CWE-502). The robust fix is to not natively deserialise untrusted input at all — use JSON with a schema, or restrict to an allow-list of classes.",
      source_reference="CWE-502; OWASP A08:2021 (Software and Data Integrity Failures)",
      validation_notes="Field validation after readObject is too late; safe-format/allow-list is the fix."),

    T(template_id="remediate_cwe611_xxe", category="remediate", skill_tag="CWE-611",
      owasp="A05", severity="high", difficulty="advanced",
      prompt="This parses untrusted XML. What is the correct fix?",
      code_template="DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();\nDocument d = dbf.newDocumentBuilder().parse(untrustedXml);",
      variables={"flavour": ["document", "SAX", "stream"]},
      correct_option="Disable DTDs and external entity resolution on the parser factory (e.g. disallow-doctype-decl = true)",
      distractor_pool=["Validate the XML against an XSD after parsing",
                       "Encrypt the XML payload in transit",
                       "Increase the parser's memory limit",
                       "HTML-encode the XML before parsing"],
      explanation_template="Turning off DTD processing and external entities on the factory removes the XXE attack surface entirely (CWE-611). Validating against an XSD happens after the entities already resolved, so it is too late; transport encryption and memory limits don't address entity expansion.",
      source_reference="CWE-611; OWASP A05:2021 (Security Misconfiguration)",
      validation_notes="Disable DTD/external entities at the factory."),

    T(template_id="remediate_cwe434_unrestricted_upload", category="remediate", skill_tag="CWE-434",
      owasp="A04", severity="high", difficulty="intermediate",
      prompt="This stores an uploaded file. What is the correct fix?",
      code_template='Files.copy(filePart.getInputStream(), Path.of("{dir}", filePart.getSubmittedFileName()));',
      variables={"dir": ["/var/www/uploads", "webapps/app/uploads", "public/files"]},
      correct_option="Validate the file type/content, generate a server-side filename, and store outside the web root with no execute permission",
      distractor_pool=["Append a .txt suffix only in the displayed URL",
                       "Reject filenames containing the word \"shell\"",
                       "Set the upload size limit to 10 MB",
                       "Base64-encode the file before storing it"],
      explanation_template="Validating type/content + a server-generated name + storage outside an executable web root prevents an attacker turning an upload into a runnable web shell (CWE-434). A size limit is good hygiene but does not stop a malicious file type; the others are cosmetic.",
      source_reference="CWE-434; OWASP A04:2021 (Insecure Design)",
      validation_notes="Type validation + non-executable storage is the real fix."),

    T(template_id="remediate_cwe798_hardcoded_creds", category="remediate", skill_tag="CWE-798",
      owasp="A07", severity="high", difficulty="beginner",
      prompt="A secret is hard-coded in source. What is the correct fix?",
      code_template='private static final String {var} = "S3cr3tValue!";',
      variables={"var": ["DB_PASSWORD", "API_KEY", "SMTP_PASSWORD"]},
      correct_option="Load the secret at runtime from an environment variable or a secrets manager, and keep it out of source control",
      distractor_pool=["Base64-encode the credential in the source",
                       "Move the credential into a code comment",
                       "Obfuscate the variable name",
                       "Encrypt the credential with a key also stored in the source"],
      explanation_template="Externalising the secret (env var / secrets manager) keeps it out of the codebase and lets you rotate it — the correct fix for hard-coded credentials (CWE-798). Encoding, commenting, renaming, or encrypting-with-a-bundled-key all still ship the secret to anyone with the code.",
      source_reference="CWE-798; OWASP A07:2021 (Identification and Authentication Failures)",
      validation_notes="Externalise the secret; all distractors still expose it."),

    T(template_id="remediate_cwe918_ssrf", category="remediate", skill_tag="CWE-918",
      owasp="A10", severity="high", difficulty="intermediate",
      prompt="The server fetches a user-supplied URL. What is the correct fix?",
      code_template='new java.net.URL(request.getParameter("{param}")).openStream();',
      variables={"param": ["url", "target", "endpoint"]},
      correct_option="Validate the URL against an allow-list of permitted hosts/schemes and block internal/link-local IP ranges",
      distractor_pool=["URL-encode the user-supplied URL",
                       "Follow only the first HTTP redirect",
                       "Set a short connection timeout",
                       "Send the request over HTTPS only"],
      explanation_template="An allow-list of hosts/schemes plus blocking internal ranges (127.0.0.0/8, 169.254.169.254, RFC1918) stops the server reaching internal targets — the correct fix for SSRF (CWE-918). Timeouts, HTTPS, and URL-encoding don't stop the request reaching an internal address.",
      source_reference="CWE-918; OWASP A10:2021 (Server-Side Request Forgery)",
      validation_notes="Host/scheme allow-list + internal-range blocking."),

    T(template_id="remediate_cwe916_weak_password_hash", category="remediate", skill_tag="CWE-916",
      owasp="A02", severity="medium", difficulty="beginner",
      prompt="Passwords are stored using {algo}(password). What is the correct fix?",
      code_template="String hash = {algo}(password);  // stored in the users table",
      variables={"algo": ["md5", "sha1", "sha256"]},
      correct_option="Use a slow, salted password hash designed for the purpose: bcrypt, scrypt, or Argon2",
      distractor_pool=["Switch from MD5 to SHA-256",
                       "Hash the password twice with SHA-1",
                       "Encrypt the password with AES",
                       "Prepend the username as a static salt"],
      explanation_template="Fast general-purpose hashes — even SHA-256 — can be brute-forced billions/sec on a GPU. Password storage needs a deliberately slow, salted algorithm (bcrypt/scrypt/Argon2) — the fix for CWE-916. 'Switch to SHA-256' is the classic wrong answer: still far too fast. Encryption is reversible (wrong tool); a static salt is weak.",
      source_reference="CWE-916; OWASP A02:2021 (Cryptographic Failures)",
      validation_notes="Slow salted KDF is correct; SHA-256 is the deliberate near-miss."),

    T(template_id="remediate_cwe327_broken_crypto", category="remediate", skill_tag="CWE-327",
      owasp="A02", severity="medium", difficulty="intermediate",
      prompt="Data is encrypted with {algo}. What is the correct fix?",
      code_template='Cipher c = Cipher.getInstance("{algo}");',
      variables={"algo": ["DES", "AES/ECB/PKCS5Padding", "Blowfish"]},
      correct_option="Use a modern authenticated cipher such as AES-256-GCM with a unique IV per message",
      distractor_pool=["Increase the DES key length",
                       "Switch to AES in ECB mode",
                       "Apply the cipher twice (double encryption)",
                       "Derive the key with MD5"],
      explanation_template="AES-256-GCM gives confidentiality AND integrity with a unique IV per message — the correct fix for broken/risky crypto (CWE-327). ECB still leaks patterns, double-encryption with a weak cipher is still weak, and MD5 key derivation is insecure.",
      source_reference="CWE-327; OWASP A02:2021 (Cryptographic Failures)",
      validation_notes="AES-GCM authenticated mode; ECB distractor is still broken."),

    T(template_id="remediate_cwe352_csrf", category="remediate", skill_tag="CWE-352",
      owasp="A01", severity="medium", difficulty="intermediate",
      prompt="A state-changing endpoint (/{action}) is authenticated only by the session cookie. What is the correct fix?",
      code_template='@PostMapping("/{action}")  // changes state; no CSRF defence',
      variables={"action": ["transfer", "changeEmail", "deleteAccount"]},
      correct_option="Require a per-session anti-CSRF (synchroniser) token validated on every state-changing request, and set cookies SameSite=Lax/Strict",
      distractor_pool=["Check the User-Agent header",
                       "Only accept the request over HTTPS",
                       "Add a CAPTCHA to the login page",
                       "Return the response as JSON"],
      explanation_template="A synchroniser token the attacker's site cannot read, plus SameSite cookies, ensures the request was intentionally issued by your own page — the correct fix for CSRF (CWE-352). User-Agent checks are spoofable, HTTPS doesn't prove intent, and a login CAPTCHA doesn't protect this endpoint.",
      source_reference="CWE-352; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Synchroniser token + SameSite; distractors don't prove request intent."),

    T(template_id="remediate_cwe601_open_redirect", category="remediate", skill_tag="CWE-601",
      owasp="A01", severity="medium", difficulty="intermediate",
      prompt="A redirect target comes from user input ({param}). What is the correct fix?",
      code_template='response.sendRedirect(request.getParameter("{param}"));',
      variables={"param": ["next", "url", "returnTo"]},
      correct_option="Redirect only to an allow-list of internal paths; never redirect to a raw user-supplied absolute URL",
      distractor_pool=["URL-encode the destination",
                       "Check that the URL contains your domain name as a substring",
                       "Open the redirect in a new tab",
                       "Add rel=noopener to the link"],
      explanation_template="Mapping the input to an allow-list of known-good internal paths is the reliable fix for Open Redirect (CWE-601). A substring check is bypassable (`https://evil.com/?x=yourdomain.com` or `https://yourdomain.com.evil.com`); encoding and tab/noopener don't stop the redirect.",
      source_reference="CWE-601; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Allow-list of internal paths; substring check is bypassable."),

    T(template_id="remediate_cwe307_rate_limiting", category="remediate", skill_tag="CWE-307",
      owasp="A07", severity="medium", difficulty="intermediate",
      prompt="The {endpoint} endpoint has no protection against repeated attempts. What is the correct fix?",
      code_template='@PostMapping("{endpoint}")  // no attempt throttling',
      variables={"endpoint": ["/login", "/verify-otp", "/reset-password"]},
      correct_option="Throttle attempts per account and per IP (rate limiting / temporary lockout with backoff) and monitor for abuse",
      distractor_pool=["Increase the minimum password length",
                       "Hash passwords with bcrypt",
                       "Hide the details in the error message",
                       "Add a CAPTCHA only after a successful login"],
      explanation_template="Rate limiting / lockout with backoff directly stops brute-force and credential-stuffing against this endpoint — the fix for CWE-307. Stronger passwords and bcrypt are good but don't limit attempt volume; hiding error detail is unrelated; a post-success CAPTCHA protects nothing.",
      source_reference="CWE-307; OWASP A07:2021 (Identification and Authentication Failures)",
      validation_notes="Per-account/IP throttling addresses excessive attempts."),

    T(template_id="remediate_cwe1021_clickjacking", category="remediate", skill_tag="CWE-1021",
      owasp="A05", severity="low", difficulty="beginner",
      prompt="{context} can be loaded inside an <iframe> on any external site, enabling clickjacking. Which change best mitigates this?",
      code_template="HTTP/1.1 200 OK\nContent-Type: text/html\nSet-Cookie: session=abc123; HttpOnly; Secure\n(no framing-protection header is sent)",
      variables={"context": ["A page served by this Java servlet",
                             "A response from the aiohttp web server",
                             "The application's default HTTP responses"]},
      correct_option="Send `X-Frame-Options: DENY` (or `Content-Security-Policy: frame-ancestors 'none'`)",
      distractor_pool=["Set the `HttpOnly` flag on the session cookie",
                       "Add a per-request anti-CSRF token to forms",
                       "Enable HTTP Strict-Transport-Security (HSTS)",
                       "Set `X-Content-Type-Options: nosniff`"],
      explanation_template="Clickjacking (CWE-1021) happens when your pages can be framed by any origin: an attacker overlays an invisible iframe of your site over decoy UI and tricks the user into clicking real buttons. The fix is to tell the browser who may frame you - `X-Frame-Options: DENY` (legacy) or, preferably, `Content-Security-Policy: frame-ancestors 'none'` (modern). The other options are all genuine security improvements but solve different problems: HttpOnly mitigates cookie theft via XSS (CWE-1004), anti-CSRF tokens stop CSRF (CWE-352), HSTS prevents protocol-downgrade (CWE-319), and nosniff adds MIME-sniffing protection. None of them stop framing. Note: clickjacking is typically low severity, but real severity is context-dependent - on a page with one-click money transfer it can be serious.",
      source_reference="CWE-1021; OWASP A05:2021 (Security Misconfiguration); OWASP Clickjacking Defense Cheat Sheet",
      validation_notes="Single correct option covers both equivalent mechanisms (XFO DENY / CSP frame-ancestors 'none'). Distractors are real headers/fixes for OTHER problems. nosniff is described without pinning a CWE (per review)."),
]

# ==========================================================================
# UNDERSTAND  (why exploitable / attacker capability / impact)
# ==========================================================================
UNDERSTAND_PROMPT = "Given this code, what can an attacker most directly achieve?"
TEMPLATES += [
    T(template_id="understand_cwe89_sqli", category="understand", skill_tag="CWE-89",
      owasp="A03", severity="high", difficulty="intermediate", prompt=UNDERSTAND_PROMPT,
      code_template='String sql = "SELECT * FROM {table} WHERE id = " + request.getParameter("id");',
      variables={"table": ["users", "orders", "payments"]},
      correct_option="Read, modify, or delete arbitrary database records — and sometimes bypass authentication or run admin operations",
      distractor_pool=["Run JavaScript in another user's browser",
                       "Read arbitrary files from the web server's disk",
                       "Make the server send requests to internal services",
                       "Embed the page inside a malicious iframe"],
      explanation_template="Because input is concatenated into the SQL, an attacker rewrites the query (`' OR '1'='1`, UNION SELECT, etc.) and reaches the whole database — the impact of SQL Injection (CWE-89). The distractors are the impacts of XSS, Path Traversal, SSRF, and Clickjacking respectively.",
      source_reference="CWE-89; OWASP A03:2021 (Injection)",
      validation_notes="Correct = DB read/write/auth-bypass; distractors are other CWEs' impacts."),

    T(template_id="understand_cwe79_xss", category="understand", skill_tag="CWE-79",
      owasp="A03", severity="high", difficulty="intermediate",
      prompt="This comment is stored and later shown to every visitor. What can an attacker most directly achieve?",
      code_template='out.write("<p>" + {field} + "</p>");  // {field} is stored and shown to all users',
      variables={"field": ["comment", "review", "post"]},
      correct_option="Execute attacker-controlled JavaScript in other users' browsers — steal sessions or act as them",
      distractor_pool=["Read arbitrary rows from the database",
                       "Execute OS commands on the server",
                       "Read the server's environment variables",
                       "Bind to internal network services"],
      explanation_template="Stored, unencoded input runs as script in every viewer's browser — stored XSS (CWE-79) — letting the attacker steal session cookies or perform actions as the victim. The distractors are server-side impacts (SQLi, command injection, SSRF), but XSS executes in the browser.",
      source_reference="CWE-79; OWASP A03:2021 (Injection)",
      validation_notes="Correct = client-side JS execution; distractors are server-side impacts."),

    T(template_id="understand_cwe639_idor", category="understand", skill_tag="CWE-639",
      owasp="A01", severity="high", difficulty="intermediate",
      prompt="Why is this endpoint exploitable?",
      code_template="GET /api/{resource}?id=1004   // returns the record without checking ownership",
      variables={"resource": ["invoice", "message", "profile"]},
      correct_option="An attacker can change the id to read other users' records because no ownership/authorisation check is performed",
      distractor_pool=["The id is not URL-encoded",
                       "The database query is not parameterised",
                       "The response is missing a Content-Security-Policy header",
                       "The session cookie lacks the HttpOnly flag"],
      explanation_template="The record is selected purely by a client-supplied id with no check that it belongs to the caller, so incrementing the id walks through other users' data — Insecure Direct Object Reference (CWE-639). Encoding, parameterisation, CSP, and HttpOnly are unrelated to the missing ownership check.",
      source_reference="CWE-639; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Correct = missing object-level ownership check."),

    T(template_id="understand_cwe502_deserialization", category="understand", skill_tag="CWE-502",
      owasp="A08", severity="high", difficulty="advanced",
      prompt="Why is deserialising untrusted data dangerous here?",
      code_template="Object o = new ObjectInputStream({source}).readObject();",
      variables={"source": ["request.getInputStream()", "socket.getInputStream()", "new FileInputStream(uploaded)"]},
      correct_option="Crafted objects trigger 'gadget chains' during deserialisation that can run arbitrary code — before any of your validation runs",
      distractor_pool=["It always leaks the database password",
                       "It can only cause a denial of service, nothing more",
                       "It exposes the application's source code to the client",
                       "It is safe as long as the class implements Serializable"],
      explanation_template="readObject() reconstructs arbitrary object graphs; library 'gadget' classes can be chained so that code executes during deserialisation — potential RCE (CWE-502) — before you can inspect anything. DoS is only one possible outcome, and implementing Serializable does not make it safe.",
      source_reference="CWE-502; OWASP A08:2021 (Software and Data Integrity Failures)",
      validation_notes="Correct = RCE via gadget chains at readObject time."),

    T(template_id="understand_cwe287_improper_auth", category="understand", skill_tag="CWE-287",
      owasp="A07", severity="high", difficulty="intermediate",
      prompt="What is the core weakness in this login logic?",
      code_template="{scenario}",
      variables={"scenario": [
          "if (username != null) { login(username); }   // password is never checked",
          "boolean ok = valid || debugMode;\nif (ok) login();   // debug bypass left enabled",
          "if (submittedToken != null) { login(); }   // token presence checked, validity not"]},
      correct_option="Authentication is improperly implemented — identity is not actually verified, so anyone can authenticate",
      distractor_pool=["The user lacks permission for a specific resource (an authorisation problem)",
                       "The session token is predictable",
                       "The password is hashed with a weak algorithm",
                       "The login form is missing a CSRF token"],
      explanation_template="The code lets a caller through without genuinely verifying who they are (no real password/token check) — Improper Authentication (CWE-287). This is distinct from authorisation (CWE-862), which is about what an already-identified user may do.",
      source_reference="CWE-287; OWASP A07:2021 (Identification and Authentication Failures)",
      validation_notes="Correct = identity not verified; contrasts with authorisation."),

    T(template_id="understand_cwe862_missing_authz", category="understand", skill_tag="CWE-862",
      owasp="A01", severity="high", difficulty="intermediate",
      prompt="A logged-in user (any role) can call this admin endpoint. What is the weakness?",
      code_template='@GetMapping("/admin/{action}")\npublic Resp {action}() { /* authenticated, but no role/permission check */ }',
      variables={"action": ["users", "settings", "logs"]},
      correct_option="Missing Authorization — the endpoint confirms you are logged in but never checks you are allowed to perform this action",
      distractor_pool=["Improper Authentication — identity is not verified",
                       "Insecure Direct Object Reference via a guessable id",
                       "Cross-Site Request Forgery",
                       "Information exposure through an error message"],
      explanation_template="Authentication succeeds (the user is logged in) but there is no authorisation check for the admin function — Missing Authorization (CWE-862). Contrast: CWE-287 is failing to verify identity; CWE-639 is accessing a specific object via a direct id; here the whole privileged action lacks a permission gate.",
      source_reference="CWE-862; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Correct = authenticated but no permission check; contrasts 287/639."),

    T(template_id="understand_cwe269_privilege_mgmt", category="understand", skill_tag="CWE-269",
      owasp="A04", severity="high", difficulty="advanced",
      prompt="What is the underlying weakness in this scenario?",
      code_template="{scenario}",
      variables={"scenario": [
          "The service runs as root and never drops privileges after binding port 80.",
          'user.setRole("ADMIN") is set for one task and is never reset afterwards.',
          "New accounts inherit the creating admin's ADMIN role by default."]},
      correct_option="Improper Privilege Management — privileges are granted too broadly or never dropped/reset, leaving excess rights",
      distractor_pool=["Missing Authorization on a single endpoint",
                       "Improper Authentication at login",
                       "Insecure Direct Object Reference",
                       "Use of hard-coded credentials"],
      explanation_template="Each case leaves a subject with more privilege than it needs for longer than it needs — Improper Privilege Management (CWE-269), a least-privilege violation. It differs from a single missing authz check (CWE-862): the problem is how privileges are assigned and retained overall.",
      source_reference="CWE-269; OWASP A04:2021 (Insecure Design)",
      validation_notes="Correct = least-privilege/privilege-retention failure."),

    T(template_id="understand_cwe384_session_fixation", category="understand", skill_tag="CWE-384",
      owasp="A07", severity="medium", difficulty="intermediate",
      prompt="Why is failing to regenerate the session ID at login dangerous ({context})?",
      code_template="// the session ID is NOT regenerated after a successful login\nif (validLogin) { session.setAttribute(\"user\", user); }",
      variables={"context": ["servlet container", "framework default", "custom session store"]},
      correct_option="An attacker who planted a known session ID before login can reuse it afterwards to hijack the now-authenticated session",
      distractor_pool=["The password can be read directly from the session",
                       "The session cookie becomes readable by JavaScript",
                       "The server runs out of sessions (denial of service)",
                       "The login form can be embedded in an iframe"],
      explanation_template="If the ID stays the same across the login boundary, an attacker who fixed the victim's session ID beforehand is now inside the authenticated session — Session Fixation (CWE-384). Fix: regenerate the session ID on any privilege change (login).",
      source_reference="CWE-384; OWASP A07:2021 (Identification and Authentication Failures)",
      validation_notes="Correct = pre-set session id reused post-login."),

    T(template_id="understand_cwe352_csrf", category="understand", skill_tag="CWE-352",
      owasp="A01", severity="medium", difficulty="intermediate",
      prompt="Why can an attacker abuse this form from another website?",
      code_template='<form action="/{action}" method="POST"> ... </form>\n<!-- no anti-CSRF token; relies on the session cookie -->',
      variables={"action": ["transfer", "change-email", "delete"]},
      correct_option="The browser auto-attaches the session cookie to cross-site requests, so a forged request from another site executes as the victim",
      distractor_pool=["The input is not sanitised, allowing script injection",
                       "The server fetches an attacker-controlled URL",
                       "The id parameter can be incremented to reach other records",
                       "The stored password hash is too weak"],
      explanation_template="Cookies are sent automatically on cross-site requests, so an attacker's page can submit this state-changing form and the victim's authenticated cookie makes it succeed — Cross-Site Request Forgery (CWE-352). This is about *ambient cookie authority*, not script injection (XSS) or object ids (IDOR).",
      source_reference="CWE-352; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Correct = ambient cookie authority on cross-site requests."),

    # --- NEW: completes the understand leg for CWE-22 ---
    T(template_id="understand_cwe22_pathtraversal", category="understand", skill_tag="CWE-22",
      owasp="A01", severity="high", difficulty="intermediate", prompt=UNDERSTAND_PROMPT,
      code_template='String {param} = request.getParameter("{param}");\nPath p = Path.of("/var/app/data", {param});\nreturn Files.readString(p);',
      variables={"param": ["file", "doc", "report"]},
      correct_option="Read files outside /var/app/data (e.g. ../../etc/passwd or the app's config/secrets) by injecting ../ sequences",
      distractor_pool=["Execute arbitrary OS commands on the server",
                       "Run attacker JavaScript in another user's browser",
                       "Make the server send requests to internal-only services",
                       "Inject SQL into the backend database",
                       "Embed the page inside a malicious iframe"],
      explanation_template="`{param}` is concatenated into a filesystem path with no validation, so input like `../../../../etc/passwd` walks out of /var/app/data and `Files.readString` returns whatever it points to — Path Traversal (CWE-22). The direct impact is unauthorised reading of arbitrary files (OS files, app config, secrets). It is not OS command execution, XSS, SSRF, or SQL injection: nothing here runs a shell, reaches a browser, makes a network request, or touches a database. (With a file *write* sink, traversal could escalate toward code execution, but the direct impact of this read is information disclosure.)",
      source_reference="CWE-22; OWASP A01:2021 (Broken Access Control)",
      validation_notes="Correct = arbitrary file read; distractors are the impacts of CWE-78/79/918/89/1021."),
]

# ==========================================================================
# SEVERITY  (template: constant-correct, varies the named CWE)
# ==========================================================================
TEMPLATES += [
    T(template_id="severity_context_dependent_same_cwe", category="severity", skill_tag="SEVERITY",
      owasp=None, severity=None, difficulty="advanced",
      prompt="The same weakness — {cwe} — is found in two places in an internet-facing app. Which context makes it HIGHER severity?",
      code_template=None,
      variables={"cwe": ["Information Exposure (CWE-200)", "Open Redirect (CWE-601)",
                         "Missing Authorization (CWE-862)", "Weak Password Hashing (CWE-916)"]},
      correct_option="When the affected component handles sensitive data or is reachable by unauthenticated, internet-facing users",
      distractor_pool=["When it sits behind a VPN that requires MFA",
                       "When a tested WAF rule already blocks the known payloads",
                       "When it is only reachable after authenticating as the data's owner",
                       "When it appears only in disabled / dead code"],
      explanation_template="Severity is not a fixed property of a CWE — it depends on context. The SAME {cwe} is more severe when it touches sensitive data or is reachable by unauthenticated users; it is less severe behind strong compensating controls (VPN+MFA, an effective WAF rule) or when only reachable by the legitimate owner. This is exactly why CVSS has exploitability and impact dimensions rather than a single per-CWE number.",
      source_reference="FIRST CVSS v3.1 Specification; OWASP Risk Rating Methodology",
      validation_notes="Correct option is constant across the varied CWE; teaches context-dependence of severity."),
]

# ==========================================================================
# HAND-AUTHORED CONCRETE QUESTIONS (generated_from_template: null)
#   Used where the correct answer co-varies with the parameter, so a single
#   correct_option template cannot represent them.
# ==========================================================================
def Q(qid, category, skill_tag, prompt, options, explanation, source_reference,
      difficulty="beginner", owasp=None, severity=None, code_snippet=None,
      validation_notes=""):
    """Build a hand-authored concrete question. options = list of (text, is_correct)."""
    assert sum(1 for _, c in options if c) == 1, f"{qid}: exactly one correct option required"
    opts = []
    for i, (text, correct) in enumerate(options):
        opts.append({"id": chr(ord("A") + i), "text": text, "correct": bool(correct)})
    return {
        "id": qid,
        "generated_from_template": None,
        "category": category,
        "skill_tag": skill_tag,
        "owasp": owasp,
        "severity": severity,
        "difficulty": difficulty,
        "linked_deck": None,
        "prompt": prompt,
        "code_snippet": code_snippet,
        "options": opts,
        "explanation": explanation,
        "source_reference": source_reference,
        "validation_notes": validation_notes,
    }


HAND = {}

# ---- TOOLING ----
HAND["tooling_nmap_flags"] = [
    Q("tooling_nmap_sv_0001", "tooling", "TOOL-nmap",
      "In nmap, what does the `-sV` option do?",
      [("Probe open ports to determine the service and version running", True),
       ("Perform a host-discovery (ping) sweep without scanning ports", False),
       ("Scan all 65535 TCP ports", False),
       ("Attempt to identify the remote operating system", False)],
      "`-sV` is service/version detection: nmap interrogates open ports to fingerprint the service and its version. `-sn` is ping sweep, `-p-` scans all ports, and `-O` is OS detection.",
      "nmap reference (man nmap): Service and Version Detection", difficulty="beginner"),
    Q("tooling_nmap_sn_0002", "tooling", "TOOL-nmap",
      "In nmap, what does the `-sn` option do?",
      [("Perform host discovery (ping sweep) without a port scan", True),
       ("Detect the service version on open ports", False),
       ("Run the default NSE script set", False),
       ("Scan UDP ports only", False)],
      "`-sn` is a 'no port scan' host-discovery sweep — it tells you which hosts are up without scanning their ports. `-sV` does version detection, `-sC` runs default scripts, `-sU` scans UDP.",
      "nmap reference (man nmap): Host Discovery", difficulty="beginner"),
    Q("tooling_nmap_pall_0003", "tooling", "TOOL-nmap",
      "In nmap, what does `-p-` do?",
      [("Scan all 65535 TCP ports rather than just the default top ~1000", True),
       ("Scan only the single most common port", False),
       ("Disable port scanning entirely", False),
       ("Scan ports in random order", False)],
      "`-p-` expands the scan to every TCP port (1-65535). By default nmap scans only the top ~1000 ports, so services on unusual ports are missed without `-p-`.",
      "nmap reference (man nmap): Port Specification", difficulty="intermediate"),
    Q("tooling_nmap_o_0004", "tooling", "TOOL-nmap",
      "In nmap, what does the `-O` option do?",
      [("Attempt to fingerprint the remote operating system", True),
       ("Detect the version of each network service", False),
       ("Write output to a file", False),
       ("Scan only open ports found earlier", False)],
      "`-O` enables OS detection via TCP/IP stack fingerprinting. Note `-sV` (lowercase, service version) is different from `-O` (operating system).",
      "nmap reference (man nmap): OS Detection", difficulty="intermediate"),
]

HAND["tooling_hashing_encryption_encoding"] = [
    Q("tooling_classify_base64_0001", "tooling", "TOOL-crypto-concepts",
      "Base64 is best described as which of the following?",
      [("Encoding — a reversible representation that provides NO confidentiality", True),
       ("Encryption — it keeps data secret without a key", False),
       ("Hashing — a one-way fingerprint of the data", False),
       ("Compression — it reduces the data size", False)],
      "Base64 is encoding: anyone can decode it without a key, so it provides no confidentiality. It is not encryption (no key, no secrecy), not hashing (it is reversible), and it actually increases size by ~33%.",
      "RFC 4648 (Base64); general cryptography concepts", difficulty="beginner"),
    Q("tooling_classify_aes_0002", "tooling", "TOOL-crypto-concepts",
      "AES-256-GCM is best described as which of the following?",
      [("Encryption — provides confidentiality (and, in GCM, integrity) using a key", True),
       ("Encoding — a reversible representation needing no key", False),
       ("Hashing — a one-way fingerprint", False),
       ("A password-storage algorithm like bcrypt", False)],
      "AES-256-GCM is symmetric authenticated encryption: with the key it provides confidentiality and integrity. Encoding needs no key; hashing is one-way; password storage needs a slow KDF (bcrypt/Argon2), not a bulk cipher.",
      "NIST SP 800-38D (GCM); general cryptography concepts", difficulty="intermediate"),
    Q("tooling_classify_sha256_0003", "tooling", "TOOL-crypto-concepts",
      "SHA-256 is best described as which of the following?",
      [("Hashing — a one-way fixed-size fingerprint that cannot be reversed", True),
       ("Encryption — reversible with the right key", False),
       ("Encoding — reversible without any key", False),
       ("A secure password-storage function", False)],
      "SHA-256 is a one-way cryptographic hash: you cannot reverse it to recover the input. It is not encryption or encoding. It is also too FAST to store passwords directly — use a slow salted KDF (bcrypt/scrypt/Argon2) for that.",
      "NIST FIPS 180-4 (SHA-2); CWE-916", difficulty="intermediate"),
    Q("tooling_classify_purpose_0004", "tooling", "TOOL-crypto-concepts",
      "You need to verify a downloaded file has not been altered, without keeping it secret. Which primitive fits?",
      [("A cryptographic hash (e.g. SHA-256) compared against a published checksum", True),
       ("Base64 encoding of the file", False),
       ("AES encryption of the file", False),
       ("bcrypt of the file contents", False)],
      "Integrity verification uses a hash compared to a trusted published value. Encoding gives no integrity guarantee, encryption is about secrecy not public verification, and bcrypt is for passwords (slow, salted, not for file integrity).",
      "General cryptography concepts (integrity vs confidentiality)", difficulty="intermediate"),
]

HAND["tooling_password_hashing"] = [
    Q("tooling_pwhash_choice_0001", "tooling", "CWE-916",
      "Which algorithm is the appropriate choice for storing user passwords?",
      [("Argon2 (or bcrypt / scrypt) — slow and salted by design", True),
       ("SHA-256", False),
       ("MD5", False),
       ("AES-256", False)],
      "Password storage needs a deliberately slow, salted KDF — Argon2, bcrypt, or scrypt — to resist GPU brute force (CWE-916). SHA-256/MD5 are far too fast; AES is reversible encryption, the wrong tool for one-way password storage.",
      "OWASP Password Storage Cheat Sheet; CWE-916", difficulty="beginner", owasp="A02"),
    Q("tooling_pwhash_salt_0002", "tooling", "CWE-916",
      "Why does a password hash need a unique per-user salt?",
      [("So identical passwords produce different hashes, defeating precomputed rainbow tables", True),
       ("To make the hash reversible for password recovery", False),
       ("To compress the stored hash", False),
       ("To encrypt the password in transit", False)],
      "A unique salt means two users with the same password get different stored hashes, which defeats rainbow tables and forces per-account cracking. Salts do not make hashes reversible, compress them, or handle transport security (that is TLS).",
      "OWASP Password Storage Cheat Sheet; CWE-916", difficulty="intermediate", owasp="A02"),
    Q("tooling_pwhash_workfactor_0003", "tooling", "CWE-916",
      "What is the purpose of the 'work factor' / cost parameter in bcrypt or Argon2?",
      [("To make each hash deliberately expensive, slowing brute-force attacks (and raise it as hardware improves)", True),
       ("To shorten the resulting hash", False),
       ("To make the algorithm reversible", False),
       ("To remove the need for a salt", False)],
      "The cost/work factor sets how much CPU/memory each hash takes, so attackers can only try few guesses per second; you increase it over time as hardware gets faster. It does not shorten the hash, reverse it, or replace the salt.",
      "OWASP Password Storage Cheat Sheet; CWE-916", difficulty="intermediate", owasp="A02"),
]

HAND["tooling_encoding_concepts"] = [
    Q("tooling_base64_notencryption_0001", "tooling", "TOOL-encoding",
      "A developer says user data is 'secured' because it is Base64-encoded before storage. Is this correct?",
      [("No — Base64 is reversible with no key, so it provides zero confidentiality", True),
       ("Yes — Base64 is a strong form of encryption", False),
       ("Yes — as long as the string looks unreadable", False),
       ("Yes — Base64 cannot be decoded without the original software", False)],
      "Base64 is just a reversible text representation: `base64 -d` decodes it instantly with no key. It is not security. To protect confidentiality use encryption (e.g. AES-GCM) with a properly managed key.",
      "RFC 4648; general cryptography concepts", difficulty="beginner"),
    Q("tooling_urlencoding_purpose_0002", "tooling", "TOOL-encoding",
      "What is the purpose of URL (percent) encoding such as %20 for a space?",
      [("To safely represent characters that have special meaning in a URL — it is not a security control", True),
       ("To encrypt the query string", False),
       ("To hash the parameters", False),
       ("To compress the URL", False)],
      "URL-encoding makes characters safe to transmit in a URL (spaces, &, ? etc.). It is a transport/representation concern, not encryption, hashing, or compression, and provides no confidentiality.",
      "RFC 3986 (URI); general web concepts", difficulty="beginner"),
]

HAND["tooling_proxy_tls_discovery"] = [
    Q("tooling_intercepting_proxy_0001", "tooling", "TOOL-proxy",
      "What does an intercepting proxy (e.g. Burp Suite, OWASP ZAP) primarily let a tester do?",
      [("View and modify HTTP(S) requests/responses between the browser and server", True),
       ("Decrypt arbitrary TLS traffic without installing a trusted certificate", False),
       ("Brute-force password hashes offline", False),
       ("Scan a network for live hosts", False)],
      "An intercepting proxy sits in the middle of the browser-server conversation so you can inspect and tamper with requests/responses. It can read HTTPS only because you trust its CA cert in the browser; it does not magically break TLS, crack hashes, or do host discovery (that is nmap).",
      "OWASP Web Security Testing Guide; Burp/ZAP documentation", difficulty="beginner"),
    Q("tooling_tls_guarantees_0002", "tooling", "TOOL-tls",
      "What does TLS (HTTPS) provide?",
      [("Confidentiality and integrity in transit, plus authentication of the server's identity", True),
       ("Authorisation — deciding what an authenticated user may do", False),
       ("Protection against SQL injection in the application", False),
       ("Secure storage of passwords in the database", False)],
      "TLS protects data in transit (confidentiality + integrity) and authenticates the server via its certificate. It does NOT handle application authorisation, fix injection bugs, or store passwords — those are separate application concerns.",
      "RFC 8446 (TLS 1.3); OWASP Transport Layer Security Cheat Sheet", difficulty="intermediate"),
    Q("tooling_content_discovery_0003", "tooling", "TOOL-content-discovery",
      "What do tools like gobuster, dirb, and ffuf do in a web assessment?",
      [("Brute-force/guess hidden paths and files using a wordlist (content/directory discovery)", True),
       ("Decrypt the site's TLS certificate", False),
       ("Automatically patch discovered vulnerabilities", False),
       ("Capture packets on the local network", False)],
      "These are content-discovery tools: they request many candidate paths from a wordlist to find unlinked pages, admin panels, or backups. They do not break TLS, patch bugs, or sniff packets (that is tcpdump/Wireshark).",
      "OWASP Web Security Testing Guide (Resource Enumeration)", difficulty="intermediate"),
    Q("tooling_curl_headers_0004", "tooling", "TOOL-curl",
      "What does `curl -I https://example.com` return?",
      [("Only the HTTP response headers (a HEAD request), not the body", True),
       ("The full HTML body with headers stripped", False),
       ("The site's TLS private key", False),
       ("A list of open ports on the host", False)],
      "`curl -I` issues a HEAD request and prints just the response headers — handy for checking status codes, security headers, cookies, and redirects. It does not return the body, private keys, or port information.",
      "curl manual (man curl): --head", difficulty="beginner"),
]

# ---- SEVERITY (prioritisation — correct answer co-varies with the scenario) ----
HAND["severity_prioritisation"] = [
    Q("severity_prioritise_0001", "severity", "SEVERITY",
      "On a public, internet-facing app you find all of the following. Which should you remediate FIRST?",
      [("Unauthenticated SQL injection on the login page (full DB read/write)", True),
       ("Missing X-Content-Type-Options header on static pages", False),
       ("A self-XSS that only affects the attacker's own account", False),
       ("Verbose error message exposing a stack trace on a 500 page", False)],
      "Prioritise by risk = likelihood x impact. Unauthenticated SQLi on an internet-facing endpoint is both easy to exploit and catastrophic (full database compromise), so it goes first. The others are real but lower-risk: a missing header is defence-in-depth, self-XSS harms only the attacker, and a stack trace is information disclosure.",
      "OWASP Risk Rating Methodology; FIRST CVSS v3.1", difficulty="advanced", severity=None),
    Q("severity_prioritise_0002", "severity", "SEVERITY",
      "Two findings on an internet-facing app: (1) IDOR exposing other customers' invoices to any logged-in user; (2) clickjacking on the public marketing homepage. Which is higher priority?",
      [("The IDOR — it directly exposes other users' data and is trivially exploitable", True),
       ("The clickjacking — missing X-Frame-Options is always critical", False),
       ("They are identical in severity because both are web bugs", False),
       ("Neither needs fixing until a pentest confirms them", False)],
      "The IDOR is a confidentiality breach of real customer data, reachable by any authenticated user — high risk. Clickjacking on a static marketing page with no sensitive actions is low impact. Severity depends on data sensitivity and exploitability, not on the vulnerability's name.",
      "OWASP Risk Rating Methodology; CWE-639; CWE-1021", difficulty="advanced", severity=None),
    Q("severity_prioritise_0003", "severity", "SEVERITY",
      "A finding has CATASTROPHIC impact but is only exploitable by a fully-authenticated admin on an internal-only host. How should you weigh it against an easy-to-exploit, medium-impact bug on the public internet?",
      [("Combine impact AND likelihood — the easy internet-facing bug often warrants faster remediation despite lower impact", True),
       ("Always fix the highest-impact bug first, regardless of how it is exploited", False),
       ("Impact is irrelevant; only exploitability matters", False),
       ("Internal-only bugs never need fixing", False)],
      "Risk is a function of BOTH impact and likelihood/exploitability. A bug requiring admin access on an internal host has low likelihood, so an easily exploitable internet-facing medium-impact bug can present more real-world risk. (Internal bugs still matter for defence-in-depth and insider/lateral-movement scenarios.)",
      "FIRST CVSS v3.1 (Exploitability vs Impact); OWASP Risk Rating Methodology", difficulty="advanced", severity=None),
    Q("severity_compensating_0004", "severity", "SEVERITY",
      "Which factor most legitimately LOWERS the practical severity of a vulnerability in production?",
      [("An effective compensating control (e.g. the endpoint is reachable only via VPN with MFA)", True),
       ("The vulnerability having a high CWE number", False),
       ("The code being written in a memory-safe language", False),
       ("The bug being found by a senior engineer", False)],
      "Compensating controls and reduced exposure lower real-world likelihood, and therefore practical severity — this is the 'Environmental' dimension in CVSS. The CWE number, the language, and who found it do not change how exploitable or impactful the bug is.",
      "FIRST CVSS v3.1 (Environmental metrics); OWASP Risk Rating Methodology", difficulty="intermediate", severity=None),
    Q("severity_cwe209_context_0005", "severity", "CWE-209",
      "App A's error page leaks a full SQL query and DB schema; App B's leaks a generic message with a random trace id. Which is higher severity and why?",
      [("App A — it reveals information (SQL, schema) that directly helps an attacker plan further attacks", True),
       ("App B — random trace ids are always sensitive", False),
       ("They are equal because both return an error page", False),
       ("App B — returning any error at all is the real problem", False)],
      "The severity of information exposure (CWE-209) depends on WHAT leaks. App A hands an attacker the database structure and queries (very useful for SQLi/recon); App B's opaque trace id reveals nothing actionable. Same CWE, very different severity — context decides.",
      "CWE-209; OWASP Risk Rating Methodology", difficulty="intermediate", severity=None),
]


# --------------------------------------------------------------------------
# Emit JSON stores
# --------------------------------------------------------------------------
def main():
    os.makedirs(TPL_DIR, exist_ok=True)
    os.makedirs(HAND_DIR, exist_ok=True)

    # sanity: unique template ids
    ids = [t["template_id"] for t in TEMPLATES]
    assert len(ids) == len(set(ids)), "duplicate template_id"

    for t in TEMPLATES:
        path = os.path.join(TPL_DIR, t["template_id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(t, f, indent=2, ensure_ascii=False)

    hand_count = 0
    for name, qs in HAND.items():
        path = os.path.join(HAND_DIR, name + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(qs, f, indent=2, ensure_ascii=False)
        hand_count += len(qs)

    proj = sum(t["variants_expected"] for t in TEMPLATES)
    print(f"Templates written : {len(TEMPLATES)}  -> {TPL_DIR}")
    print(f"  projected template questions : {proj}")
    print(f"Hand-authored sets: {len(HAND)} files, {hand_count} questions -> {HAND_DIR}")
    print(f"Projected total questions: {proj + hand_count}")


if __name__ == "__main__":
    main()
