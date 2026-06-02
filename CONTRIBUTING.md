# Contributing to SYNAPSE

SYNAPSE is a publicly deployed adaptive tutoring platform for Java programming,
Python for cybersecurity, and secure software development. It is built around
**five interacting subsystems**: an adaptive AI tutor coordinated by a Model
Context Protocol (MCP) server, a course content engine serving structured
modules, a persistent accessibility layer, a dual-language code-execution
environment, and **ShopSecure** — a deliberately vulnerable web application used
as the hands-on security target. A research instrumentation layer records
behavioural signals under anonymous participant codes in a PostgreSQL database.

This guide explains how to extend each of these without disturbing the others.
Throughout, **SYNAPSE** refers to the platform and its tutor; **ShopSecure**
refers specifically to the vulnerable Flask application subsystem.

If you only want to *run* the platform, see `README.md`.

---

## Repository map

```
app.py                      aiohttp entry point, HTTP routes, ShopSecure tutor branch
ai/
  router.py                 AIRouter: provider setup, conversational dispatch, SYNAPSE_SYSTEM_PROMPT
ai_clients/                 thin per-provider clients (Anthropic, OpenAI, Google, DALL-E)
core/
  course_content.py         course structure + per-topic content loading
  tutor.py                  tutoring logic and prompt construction
  engine.py                 supporting services
web/
  course_handlers.py        composes the three-step learner-facing pipeline
  research_handlers.py      ShopSecure research-task handling and baseline reset
  (quiz / labs / auth / metrics handlers)
mcp_educational_server.py   MCP server: registers the tutoring tools
shopsecure/                 ShopSecure — deliberately vulnerable Flask app (Docker)
quiz/
  quiz_templates/           reusable question bank (detect / understand / remediate)
  quiz_engine.py            variant generation and scoring
static/course_content/      one JSON file per course module
templates/                  HTML templates (course pages, quiz, flashcards, research task)
```

SYNAPSE is implemented in Python 3.12 on the aiohttp asynchronous HTTP framework;
persistent storage uses PostgreSQL. Configuration is read from environment
variables — copy `.env.example` to `.env` and fill in your own values:

```
ANTHROPIC_API_KEY   OPENAI_API_KEY   GOOGLE_API_KEY
DATABASE_URL=postgresql://USER:PASSWORD@localhost/security_tutor
ADMIN_KEY
```

The platform is **public**: anyone in the world can reach it with no institutional
account. Every contribution must respect that — see *Contribution conventions* at
the end.

---

## 1. Add a course module (course content engine)

A module is one self-contained topic with four tabs: **Theory**, **Slides**
(worked examples), **Flowchart**, and **Practice** (exercises). Each module is a
single JSON file in `static/course_content/`, and the course page loads one
module per file.

### 1.1 The content contract

Create `static/course_content/<course_id>.json`. The page reads these exact
fields, so the names must match:

```jsonc
{
  "course_id": "your_topic_id",
  "title": "Topic Title",
  "description": "One-line description",
  "difficulty": "BEGINNER | INTERMEDIATE | ADVANCED",
  "estimated_hours": 8,
  "learning_outcomes": ["...", "..."],
  "lessons": [
    {
      "lesson_id": "your_topic_id_lesson_1",
      "title": "Lesson Title",
      "theory": {
        "introduction": "Long intro anchored in a real-world analogy",
        "why_important": "Why this matters for security and in practice",
        "key_concepts": [
          { "concept": "...", "explanation": "...", "example": "code\\nwith\\nnewlines", "ai_hint": "everyday-life tip" }
        ]
      },
      "complete_examples": [
        { "title": "...", "description": "...", "difficulty": "beginner",
          "code": "full working code", "output": "exact expected output",
          "ai_explanation": "line-by-line walk-through", "ai_challenge": "follow-up to try" }
      ],
      "visual_diagram": {
        "title": "Flowchart Title",
        "content": "<div style=\"font-family:monospace\">colour-coded HTML flow with arrows and error paths</div>"
      },
      "practice_exercises": [
        { "exercise_id": "ex_01", "title": "...", "description": "...",
          "difficulty": "beginner", "category": "...", "estimated_minutes": 5,
          "ai_intro": "friendly intro shown when the exercise loads",
          "starter_code": "// TODOs for the learner\\n",
          "expected_output": "what correct code produces",
          "hints": [ {"message": "gentle nudge"}, {"message": "more specific"}, {"message": "near-solution"} ] }
      ]
    }
  ]
}
```

Depth targets that keep modules consistent with the existing set:

- **10+** `key_concepts`, each with an analogy and a code example.
- **12+** `complete_examples`, each with full code, exact output, and explanation.
- **1** `visual_diagram` using colour-coded HTML (red for errors/start, blue for
  steps, green for success, purple for runtime, orange for caution, grey for notes),
  with explicit flow arrows, an error path, and a summary block.
- **60** `practice_exercises`, every one with `starter_code` and **exactly three
  hints of increasing specificity** (nudge → specific → near-solution). Spread
  difficulty roughly 30% beginner / 50% intermediate / 20% advanced across 4–6
  categories, and vary the exercise type (fix-the-bug, predict-output,
  fill-the-blanks, build-from-scratch, refactor, code-trace, real-world scenario).

The three hints are deliberate. SYNAPSE constrains all tutor responses with a
uniform Socratic hint policy that organises guidance into three progressively
more specific stages — (i) conceptual reorientation, (ii) procedural hint, and
(iii) a partial worked example transferred from a different context. The same
staged structure is reflected, at the course-content layer, in the three
pre-written hints of increasing specificity stored alongside each exercise.
Keep that mapping intact: hints escalate, and never open with the answer.

### 1.2 Register the module

Add the module to the course structure so it appears in the UI:

- **Python and structured tracks** — add an entry to the structure returned by
  `_build_course_structure()` in `core/course_content.py`. Each entry has
  `id`, `name`, `icon`, `duration`, `description`, `learning_outcomes`, and
  `requires_ai_generation`.
- **Java security track** — add a card to the `courses` array in the
  corresponding course-page template under `templates/`:
  `{ id: 'your_topic_id', icon: 'XYZ', title: 'Title (60 Exercises)', desc: '...', badge: 'LEVEL' }`.

The `id`/`course_id` must match the JSON filename. A content-only change is picked
up on refresh; a structure or template change requires restarting the service.

---

## 2. Add a vulnerability to ShopSecure

ShopSecure is a Flask web application developed specifically for SYNAPSE rather
than a repackaging of existing vulnerable targets such as OWASP Juice Shop or
DVWA. It exposes fifteen vulnerability topics — eleven actively exploitable
endpoints plus four reference code-pattern topics — covering six OWASP Top 10
(2021) categories. The application is **deliberately overt**: vulnerable
endpoints are surfaced directly, and the pedagogical goal is to understand how
each weakness works rather than to discover that it exists. Each vulnerability
maps to a CWE and is implemented as one Flask route.

### 2.1 The route pattern

Existing weaknesses follow a consistent shape — for example `/invoice` →
CWE-22 Path Traversal, `/transfer` → CWE-352 Cross-Site Request Forgery, and
`/preferences` → CWE-502 Insecure Deserialisation, the three targets of the
research task. To add one, add a route to `shopsecure/app.py`:

```python
@app.route('/your-endpoint', methods=['GET', 'POST'])
def your_feature():
    # 1. Implement the realistic but deliberately weak behaviour.
    # 2. Provide exploitation feedback: when the weakness is triggered, surface a
    #    clear, visible banner naming what happened (the path-traversal route
    #    shows a "PATH TRAVERSAL!" label on success) so the learner gets
    #    immediate, unambiguous confirmation.
    # 3. Render through page(title, body) so the endpoint inherits the shared
    #    navigation and accessibility toolbar.
    ...
```

Keep each scenario exercising a *distinct attacker capability* — for instance
file-system reach via parameter manipulation, authenticated cross-origin
coercion, or language-level remote code execution through unsafe deserialisation
— rather than another instance of something already covered. Map the new endpoint
to its CWE and to an OWASP Top 10 (2021) category, add contextual hints and a
prompt to consult the AI tutor, and add the corresponding entry to the
mitigations guide so the *detect–understand–remediate* loop closes.

### 2.2 ShopSecure runs in an isolated container

ShopSecure runs in a containerised environment separated from the tutoring
infrastructure, with each session restored to a consistent baseline. Source
changes therefore take effect only after the image is rebuilt and the container
is restarted — editing files inside a running container will not persist, and the
baseline reset will revert them. Tag the previous image before rebuilding so you
can roll back, and confirm your change survives the baseline reset.

### 2.3 Tutor support for ShopSecure

When a learner asks the tutor for help inside ShopSecure, the request is routed
through a separate branch directly to Claude under a task-calibrated prompt,
bypassing the composite pipeline (Section 4) to stay aligned with
vulnerability-discovery objectives. SYNAPSE's Socratic hint policy applies, and
it **explicitly prohibits the generation of complete exploit code in ShopSecure
interactions**. If your new weakness is wired to the tutor, preserve that: the
tutor reorients and hints, and all exploitation stays inside the contained,
self-resetting ShopSecure sandbox.

---

## 3. Add a question to the quiz / flashcard bank

Beyond the five subsystems above, the repository also ships a reusable question
bank in `quiz/quiz_templates/`. Each item is a JSON template tagged by CWE,
OWASP category, and one of three skills — **detect**, **understand**, or
**remediate** — and the engine expands each template into several variants.

Create `quiz/quiz_templates/<category>_cwe<N>_<shortname>.json`:

```jsonc
{
  "template_id": "remediate_cwe78_cmdinjection",
  "category": "remediate",              // detect | understand | remediate
  "skill_tag": "CWE-78",
  "owasp": "A03",
  "severity": "high",
  "difficulty": "intermediate",
  "prompt": "This runs a shell command built from user input. What is the correct fix?",
  "code_template": "Runtime.getRuntime().exec(new String[]{\"bash\",\"-c\",\"ping \" + {param}});",
  "variables": { "param": ["host", "ip", "target"] },
  "correct_option": "Pass program and arguments as a list to ProcessBuilder; validate against an allow-list",
  "distractor_pool": ["Escape spaces in the input", "Wrap the command in quotes", "Run it with sudo", "HTML-encode the value"],
  "explanation_template": "Why the correct option is correct and why each distractor fails.",
  "source_reference": "CWE-78; OWASP A03:2021 (Injection)",
  "variants_expected": 3
}
```

Guidelines: the `correct_option` must be unambiguously correct; distractors should
be *plausible* (real misconceptions, not obvious throwaways); the
`explanation_template` should teach, not just confirm; and `variables` drive the
`variants_expected` distinct renderings. Keep CWE and OWASP tags accurate.

---

## 4. Connect another language model (the AI tutor)

Learner-facing tutor responses are constructed through a three-step composite
pipeline. In Step 1, **Claude** generates the core explanation under a canonical
`SYNAPSE_SYSTEM_PROMPT` that enforces the Socratic interaction policy. In Step 2,
**GPT-4o-mini** may append a short practice exercise when the learner's query
signals educational intent. In Step 3, **Gemini 2.5 Flash** may append a
learner-friendly explanatory analogy. Steps 2 and 3 are non-blocking: if either
provider fails, the response composed so far is returned, ensuring graceful
degradation. The Explain Code tool additionally invokes Gemini as a planner that
identifies the programming language and recommends appropriate pedagogical tools.

Because tutoring operations are decoupled from any individual provider, adding a
fourth model is a thin client plus wiring — nothing in the course content, quiz,
or accessibility layers needs to change.

### 4.1 Add a thin client

Provider-specific clients for Anthropic, OpenAI, and Google are encapsulated as
thin wrappers in `ai_clients/` (`claude_client.py`, `gemini_client.py`,
`openai_client.py`). Add `ai_clients/yourprovider_client.py` exposing a small
class that takes an API key and offers the generate/chat methods you need, and
export it from `ai_clients/__init__.py`.

### 4.2 Wire it in

Two places matter:

- **`AIRouter` in `ai/router.py`** centralises provider setup and the
  conversational dispatch. Read your key in `__init__`, initialise the client in
  `_init_clients()`, and add a branch where you want it in the provider order of
  `get_chat_response` / `get_tutor_response`. This conversational path also
  serves the ShopSecure research branch. The Gemini-backed planner lives in
  `get_ai_plan`, which calls Gemini and falls back to a default plan if it is
  unavailable.
- **The composite pipeline in `web/course_handlers.py`** is where the three-step
  learner-facing response is assembled (Claude → GPT-4o-mini → Gemini 2.5 Flash).
  If your provider should participate in that pipeline, wire it into the relevant
  step there, keeping the non-blocking behaviour so a failing provider degrades
  gracefully rather than breaking the response.

Add the new key to `.env.example` (placeholder only — never a real key).

---

## 5. Add a tutoring operation (MCP)

The pedagogical core of SYNAPSE is an MCP server that exposes seven AI-mediated
operations as callable tools — **Analyse and Learn, Explain Code, Visual Guide,
Suggest Fixes, Run Tests, Security Check, and a Graphs and Visualisation panel** —
each mapping a learner intent (understanding, debugging, visualising) to a
concrete dispatch strategy. Treating tutoring operations as MCP tools, rather than
as hard-coded prompts to a single model, decouples the educational logic from any
individual provider and makes the system resilient to model deprecation.

To add an operation, register it on the MCP server in
`mcp_educational_server.py`:

1. Inside `_register_tools()`, add a `Tool(name=..., description=..., inputSchema=...)`
   to the list returned by the `@server.list_tools()` handler.
2. Add a matching branch to the `@server.call_tool()` handler that dispatches on
   the tool name, performs the work (typically through `AIRouter`), and returns
   the result.
3. Surface the operation in the UI alongside the existing ones so learners can
   reach it.

Keep new operations mapped to a clear learner intent so the intent-to-tool mapping
stays legible.

---

## Contribution conventions

**Public-only content.** Because anyone can use SYNAPSE, no content — course JSON,
quiz items, ShopSecure pages, tutor prompts — may reference private course
materials, named institutions or people, or assume the learner has access to any
external resource. Assume the reader is a stranger on the internet with no
backing materials.

**Neurodivergent-first by default.** SYNAPSE treats accessibility as a first-class
pedagogical component. Its accessibility layer exposes eighteen features organised
into five groups — visual adjustments, reading support, attention and focus
support, sensory regulation, and input alternatives — mapped onto the user-facing
dimensions of the FEDIS+R framework, together with an idle-aware encouragement
system. New learning content should match that spirit: lead with an analogy, build
difficulty progressively, use colour-coded visuals, keep exercises short and
focused with immediate feedback, and offer more than one explanation style.

**Graduated help, not solutions.** Anything wired to the tutor must respect the
three-stage Socratic hint policy — conceptual reorientation, then a procedural
hint, then a partial worked example transferred from a different context — and the
policy's prohibition on generating complete exploit code in ShopSecure
interactions.

**No secrets, ever.** Keys, connection strings, and deployment details belong in
your local `.env`, never in committed files, content, or commit messages.

**Verify against running behaviour.** Field names in content must match what the
pages read, CWE/OWASP tags must be correct, and ShopSecure changes only take
effect after a container rebuild and must survive the baseline reset. Check the
live behaviour, not just the source, before opening a contribution.
