# Spot the Bug · AI — handover (dal prototipo alla produzione)

**Prototipo cliccabile:** `templates/spotbug_ai_prototype.html` (standalone, non tocca il gioco live).
Apri `…/spotbug_ai_prototype.html`, gioca, e prova i tre pulsanti:
- **🎲 Nuova variante** — stesso bug, forma di superficie diversa (memorizzare il testo non basta più).
- **🤖 Perché ho sbagliato?** — spiegazione adattata a *cosa* hai toccato di sbagliato.
- **🎯 Ripasso mirato** — quando sbagli ripetutamente una categoria, ti ripropone proprio quella.

Il prototipo gira con un **mock locale** (sostituisce i buchi `{{…}}` da pool fissi) così non genera costi AI. Sotto c'è ciò che serve per renderlo reale.

---

## Perché è un fossato (non copiabile dai concorrenti statici)
Anki/Quizlet hanno contenuti fissi; THM/HTB sono lab pesanti. Un **generatore AI di varianti + tutor che spiega l'errore** è qualcosa che per definizione un contenuto statico non può offrire: gli esercizi diventano infiniti e la spiegazione è personale. È il pezzo che trasforma Synapse da "esercizi belli" a "tutor di sicurezza in tasca".

---

## Backend reale — endpoint `POST /api/spotbug/variant`

Riusa l'infrastruttura già presente: `tutor = request.app.get('tutor')`, `router = tutor.ai_router`, e `await router.get_chat_response(system_prompt, messages)` (esattamente come `chat_ai` a riga ~614 di `app.py`).

### Schema esercizio (identico a quello del gioco)
```
{ lang, ctx, code:[righe], vuln:<indice riga bug>, category,
  options:[4, la corretta = category], why,
  fixLines:[righe con ___], slots:[risposte], tokens:[banco incl. distrattori], fixWhy }
```

### Handler (da incollare in `app.py`, vicino a `chat_ai`)
```python
import json, re

# a few real "seeds" to anchor the style (one per deck is enough)
SPOTBUG_SEEDS = {
  "netmon": '{"lang":"tcpdump","ctx":"capture traffic on eth0 to a file",'
            '"code":["sudo tcpdump -i eth0 -o capture.pcap"],"vuln":0,"category":"Wrong flag",'
            '"options":["Wrong flag","Wrong tool","Wrong value","Wrong syntax"],'
            '"why":"-o is not how tcpdump writes to a file.",'
            '"fixLines":["sudo tcpdump -i eth0 ___ capture.pcap"],"slots":["-w"],'
            '"tokens":["-w","-o","-f","-r"],"fixWhy":"-w writes the packets; -r reads them back."}',
  # ... one seed per api / mobile / dfir / etc.
}

SPOTBUG_PROMPT = (
  "You are an exercise author for a cybersecurity game called Spot the Bug. "
  "Produce ONE new exercise for the given deck, on a realistic command/tool/code snippet, "
  "where EXACTLY one line is wrong or dangerous. "
  "Teach the correct usage and explain WHY. Language: ENGLISH (the whole platform is English). "
  "Reply with VALID JSON ONLY, no extra text, in this exact schema:\n"
  '{"lang":str,"ctx":str,"code":[str],"vuln":int,"category":str,'
  '"options":[str,str,str,str],"why":str,"fixLines":[str],"slots":[str],"tokens":[str],"fixWhy":str}\n'
  "Rules: options[0] MUST equal category and the 4 options MUST be distinct; "
  "the number of '___' in fixLines MUST equal len(slots); every slot MUST be in tokens; "
  "tokens has 3-4 distinct entries (the right one + plausible distractors); "
  "0 <= vuln < len(code); no backticks, no markdown, no '</script>'. "
  "Generate an exercise DIFFERENT from the seed (other tool/flag/scenario), not a mere rewrite."
)

def _validate_spotbug(ex):
    assert isinstance(ex.get("code"), list) and ex["code"], "code"
    assert isinstance(ex.get("vuln"), int) and 0 <= ex["vuln"] < len(ex["code"]), "vuln"
    assert len(ex.get("options", [])) == 4 and len(set(ex["options"])) == 4, "options"
    assert ex["options"][0] == ex.get("category"), "options[0]==category"
    blanks = sum(l.count("___") for l in ex.get("fixLines", []))
    assert blanks == len(ex.get("slots", [])) and blanks >= 1, "blanks==slots"
    assert all(s in ex.get("tokens", []) for s in ex["slots"]), "slot in tokens"
    assert 3 <= len(ex["tokens"]) <= 6 and len(set(ex["tokens"])) == len(ex["tokens"]), "tokens"
    for k in ("lang", "ctx", "why", "fixWhy"):
        assert ex.get(k), k
    return ex

async def spotbug_variant(request):
    try:
        data = await request.json()
        deck = data.get("deck", "netmon")
        weak = data.get("weak_category")
        tutor = request.app.get("tutor")
        router = tutor.ai_router if tutor else None
        if not router:
            return web.json_response({"error": "AI not available"}, status=503)

        seed = SPOTBUG_SEEDS.get(deck, next(iter(SPOTBUG_SEEDS.values())))
        ask = f"Deck: {deck}. Style example (do NOT copy it): {seed}."
        if weak:
            ask += f" Focus on the user's weak category: '{weak}'."

        # up to 2 attempts if the model breaks the schema
        for _ in range(2):
            raw = await router.get_chat_response(
                SPOTBUG_PROMPT, [{"role": "user", "content": ask}]
            )
            m = re.search(r"\{.*\}", raw, re.S)        # estrai il primo blocco JSON
            if not m:
                continue
            try:
                ex = _validate_spotbug(json.loads(m.group(0)))
                return web.json_response(ex)
            except (AssertionError, json.JSONDecodeError):
                continue
        return web.json_response({"error": "generation failed"}, status=502)
    except Exception as e:
        print(f"spotbug_variant error: {e}")
        return web.json_response({"error": "server error"}, status=500)
```

### Registrazione rotta (vicino agli altri `add_post`, ~riga 1119)
```python
app.router.add_post('/api/spotbug/variant', spotbug_variant)
```

---

## Wiring frontend (nel gioco vero `templates/spot_the_bug.html`)
- Aggiungi due bottoni: **🎲 Nuova variante** e, sulla risposta sbagliata, **🤖 Perché ho sbagliato?**.
- 🎲 → `POST /api/spotbug/variant {deck:deckId, weak_category}` → inietti l'oggetto nel motore (è già nello schema: basta `challenges.splice(ci,0,ex)` o sostituire l'esercizio corrente e `render()`).
- 🤖 → riusa `POST /api/chat` con un breve prompt che passa `ex` + l'opzione/riga sbagliata e chiede una spiegazione di 2-3 righe al livello dell'utente.
- Il prototipo mostra esattamente questi due agganci (`fetchVariantFromBackend`, `mockExplain`).

## Costi & robustezza (importante)
- **Cache:** memorizza le varianti generate (per `deck`+hash) e servile a rotazione — l'AI gira solo quando il pool è "magro". Riduce costo e latenza, mantiene l'effetto "infinito".
- **Pre-generazione offline:** un job può generare in batch centinaia di varianti per deck e salvarle come JSON; il gioco le pesca a caso e l'AI è solo il "rifornitore". Costo quasi nullo a runtime.
- **Fallback:** se il backend fallisce o l'utente è offline (PWA), usa il generatore a `{{buchi}}` come nel mock — il gioco non si rompe mai.
- **Auth/rate-limit:** gate dietro login (come il resto) + un piccolo limite per partecipante per evitare abusi.

## Modello
`router.get_chat_response` instrada già a Claude/GPT/Gemini. Per generazione di esercizi conviene Claude (qualità + aderenza allo schema); per la spiegazione "perché ho sbagliato" basta un modello veloce/economico.
