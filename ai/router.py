import os
import json
import anthropic
import openai
import google.generativeai as genai
from typing import Optional

# ============================================================
# SYNAPSE AI TUTOR SYSTEM PROMPT
# This is the brain of the AI tutor. It controls ALL responses.
# ============================================================
SYNAPSE_SYSTEM_PROMPT = """You are the Synapse AI Security Tutor — an expert, patient, and encouraging tutor for the Synapse cybersecurity and Java programming learning platform designed for neurodivergent learners.

=== ABSOLUTE RULES (NEVER BREAK THESE) ===

1. NEVER mention: SET10113, Edinburgh Napier, coursework, assignments, lectures, slides, practicals, labs, lab sessions, module handbook, university, professor, lecturer, or any academic institution.
2. NEVER say "check your course materials", "refer to your lectures", "ask your professor", or "access your university resources."
3. You ARE the expert. Provide deep, comprehensive answers directly. Never deflect or say you don't have enough information without trying to answer first.
4. This is a PUBLIC platform — anyone in the world can use it. Assume the learner has NO access to any university or institutional materials.
5. When asked about vulnerabilities, attacks, or security concepts, ALWAYS provide the full answer with CWE numbers, real-world examples, and code samples.
6. ALWAYS include relevant external links for deeper learning:
   - OWASP Top 10: https://owasp.org/Top10/
   - PortSwigger Web Security Academy: https://portswigger.net/web-security
   - CWE Database: https://cwe.mitre.org/
   - HackTheBox Academy: https://academy.hackthebox.com/
   - TryHackMe: https://tryhackme.com/
   - NIST NVD: https://nvd.nist.gov/
   - Java Security: https://docs.oracle.com/en/java/javase/17/security/

=== YOUR PERSONALITY ===

- Encouraging, patient, never judgmental — celebrate every small win
- Use real-world analogies: restaurants, postal service, locks/keys, airport security
- Break complex topics into small, digestible steps
- Offer multiple explanation styles: analogy, visual, step-by-step, code trace, comparison
- If a learner makes a mistake, explain WHY without making them feel bad
- Proactively suggest exercises and next steps
- Use emoji sparingly for engagement: 🔒 🛡️ ⚠️ 💡 ✅ ❌ 🎯 💪

=== VULNERABILITY KNOWLEDGE ===

When asked about vulnerabilities or risk levels, ALWAYS provide this comprehensive answer:

**CRITICAL RISK 🚨:**
- Remote Code Execution (CWE-94) — Attacker runs arbitrary code on your server
- OS Command Injection (CWE-78) — Attacker executes shell commands via your app
- Authentication Bypass (CWE-287) — Skipping login entirely
- Deserialization of Untrusted Data (CWE-502) — Arbitrary object creation
- Server-Side Request Forgery (SSRF) (CWE-918) — Server makes requests for attacker

**HIGH RISK 🔥:**
- SQL Injection (CWE-89) — Attacker controls database queries, steals/deletes data
- Stored/Persistent XSS (CWE-79) — Malicious script saved, attacks ALL visitors
- Broken Access Control (CWE-284) — Accessing other users' data or admin functions
- Path Traversal (CWE-22) — Reading files outside the web root (../../etc/passwd)
- XML External Entity (XXE) (CWE-611) — Reading server files via XML parsing
- Privilege Escalation (CWE-269) — Normal user gains admin access
- Insecure Direct Object Reference (IDOR) (CWE-639) — Manipulating IDs to access others' data

**MEDIUM RISK ⚡:**
- Reflected XSS (CWE-79) — Script in URL executes in victim's browser
- Cross-Site Request Forgery (CSRF) (CWE-352) — Tricking users into unwanted actions
- Session Fixation (CWE-384) — Attacker sets session ID before victim logs in
- DOM-based XSS (CWE-79) — Client-side JavaScript vulnerability
- Clickjacking (CWE-1021) — Invisible iframe overlay tricks user into clicking
- Open Redirect (CWE-601) — Redirecting users to malicious sites
- Insecure Cryptographic Storage (CWE-327) — Weak encryption algorithms

**LOW RISK 💡:**
- Information Disclosure (CWE-200) — Leaking software versions, internal paths
- Missing Security Headers (CWE-693) — No CSP, X-Frame-Options, HSTS
- Weak Password Policy (CWE-521) — Allowing simple passwords
- Cookie without Secure Flag (CWE-614) — Session cookie sent over HTTP
- Cookie without HttpOnly Flag (CWE-1004) — JavaScript can steal session cookies
- Verbose Error Messages (CWE-209) — Stack traces shown to users
- HTTP instead of HTTPS (CWE-319) — Unencrypted communication

For each vulnerability, always explain: what it is, why it's dangerous, how to exploit it (for learning), how to defend against it, and a real-world breach example.

=== HOW TO ANSWER QUESTIONS ===

1. FIRST: Check if the loaded course content has relevant information. Use it as primary source.
2. SECOND: Supplement with your own expert knowledge — go DEEPER than the course content.
3. ALWAYS: Include practical code examples (Java for security topics, Python for programming).
4. ALWAYS: Include CWE numbers when discussing vulnerabilities.
5. ALWAYS: End with external links for learners who want to go deeper.
6. FORMAT: Use Markdown — ## headers, **bold** key terms, `code blocks`, bullet points.
7. Keep paragraphs short (2-3 sentences max) for neurodivergent-friendly reading.

=== COURSE CONTEXT ===

The Synapse platform teaches:
- Phase 1: Java Programming (11 topics: syntax, variables, operators, conditions, loops, methods, classes, OOP, collections, strings/security, capstone)
- Phase 2: Security Topics (exceptions handling, SQL injection, XSS/web security, CSRF, path traversal, OWASP Top 10, static analysis, security engineering)

Each topic has: Theory tab, Slides tab (code examples), Flowchart tab, and Practice tab (60+ exercises).

=== EXAMPLE RESPONSES ===

GOOD: "SQL Injection (CWE-89) happens when user input is concatenated into SQL queries. Here's how it works... [code example] ... To defend against it, use PreparedStatement... [secure code] ... The Heartland Payment Systems breach in 2008 exposed 130 million cards through SQL injection. 📚 Go deeper: https://portswigger.net/web-security/sql-injection"

BAD: "I don't have access to the specific course content. Please check your SET10113 materials for vulnerability classifications."

NEVER give the BAD response. ALWAYS give the GOOD response."""


class AIRouter:
    def __init__(self):
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self._gemini = None
        self._anthropic = None
        self._openai = None
        self._init_clients()

    def _init_clients(self):
        if self.google_key:
            try:
                genai.configure(api_key=self.google_key)
                # Use the working model names from your list
                model_names = [
                    'gemini-2.5-flash',
                    'gemini-2.5-flash',
                    'gemini-2.5-flash',
                    'gemini-2.5-flash'
                ]

                for model_name in model_names:
                    try:
                        self._gemini = genai.GenerativeModel(model_name)
                        # Test the model with a simple request
                        test_response = self._gemini.generate_content("Hello")
                        if test_response.text:
                            print(f"✅ Google Gemini client initialized with model: {model_name}")
                            break
                    except Exception as model_error:
                        print(f"⚠️ Failed to initialize {model_name}: {model_error}")
                        continue

                if not self._gemini:
                    print("❌ Could not initialize any Gemini model")

            except Exception as e:
                print(f"❌ Google Gemini initialization failed: {e}")

        if self.anthropic_key:
            try:
                self._anthropic = anthropic.Anthropic(api_key=self.anthropic_key)
                print("✅ Anthropic Claude client initialized.")
            except Exception as e:
                print(f"❌ Anthropic Claude initialization failed: {e}")

        if self.openai_key:
            try:
                self._openai = openai.OpenAI(api_key=self.openai_key)
                print("✅ OpenAI client initialized.")
            except Exception as e:
                print(f"❌ OpenAI initialization failed: {e}")

    async def get_ai_plan(self, orchestrator_prompt: str) -> dict:
        """Get AI planning response from Gemini"""
        # Fallback plan if Gemini fails
        fallback_plan = {"plan": ["suggest_fixes"]}

        if not self._gemini:
            print("⚠️ Gemini not available, using fallback plan")
            return fallback_plan

        try:
            response = self._gemini.generate_content(orchestrator_prompt)
            if not response.text:
                print("⚠️ Gemini returned empty response, using fallback")
                return fallback_plan

            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            plan = json.loads(cleaned_text)
            return plan

        except json.JSONDecodeError as e:
            print(f"⚠️ Gemini returned invalid JSON: {e}, using fallback")
            return fallback_plan
        except Exception as e:
            print(f"⚠️ Error during Gemini planning: {e}, using fallback")
            return fallback_plan

    async def get_tutor_response(self, tutor_prompt: str) -> str:
        """Get tutoring response from Claude or GPT-4"""
        # Use the comprehensive Synapse system prompt
        system_prompt = SYNAPSE_SYSTEM_PROMPT

        if self._anthropic:
            try:
                message = self._anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": tutor_prompt}],
                )
                return message.content[0].text if message.content else "AI failed to generate a response."
            except Exception as e:
                print(f"❌ Claude API failed: {e}")

        # Fallback to OpenAI GPT-4 if Claude fails
        if self._openai:
            try:
                response = self._openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": tutor_prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.3,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"❌ OpenAI API failed: {e}")

        return "AI communication failed. Please check API keys and server logs."

    async def generate_educational_image(self, prompt: str) -> str:
        """Generate educational images using DALL-E for visual learners"""
        if not self._openai:
            return None

        try:
            # Enhanced prompt for educational, child-friendly images
            enhanced_prompt = f"""Educational illustration for children learning programming: {prompt}.
            Style: colorful, friendly, cartoon-like, safe for children, educational diagram"""

            response = self._openai.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            return response.data[0].url if response.data else None
        except Exception as e:
            print(f"❌ DALL-E image generation failed: {e}")
            return None

    async def get_visual_explanation_with_image(self, code: str, concept: str) -> dict:
        """Generate both text explanation and visual image for programming concepts"""

        # Generate text explanation
        text_prompt = f"""Create a visual, child-friendly explanation of this programming concept: {concept}

        Code: {code}

        Include:
        1. Simple analogy (like LEGO blocks, cooking recipes, etc.)
        2. Step-by-step breakdown
        3. Fun emojis and visual ASCII art
        4. What could go wrong and how to fix it

        Make it engaging for neurodivergent students aged 8-16."""

        text_explanation = await self.get_tutor_response(text_prompt)

        # Generate accompanying image
        image_prompt = f"""Programming concept visualization: {concept}.
        Show code execution as colorful building blocks or cooking steps.
        Include cute robot character explaining. Simple diagram with arrows showing data flow."""

        image_url = await self.generate_educational_image(image_prompt)

        return {
            "text_explanation": text_explanation,
            "image_url": image_url,
            "concept": concept
        }

    async def get_chat_response(self, system_prompt: str, messages: list) -> str:
        """Get AI response with conversation context"""
        # If the caller passes a weak/empty system prompt, use the Synapse prompt
        if not system_prompt or len(system_prompt) < 100:
            system_prompt = SYNAPSE_SYSTEM_PROMPT

        if self._anthropic:
            try:
                # Format messages for Claude
                formatted_messages = []
                for msg in messages:
                    # Ensure correct format for Claude
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        # Convert 'system' role to 'assistant' for Claude if needed
                        role = msg['role']
                        if role == 'system':
                            continue  # Skip system messages in the message list
                        formatted_messages.append({
                            "role": role if role in ['user', 'assistant'] else 'user',
                            "content": msg['content']
                        })

                response = self._anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    system=system_prompt,
                    messages=formatted_messages
                )
                return response.content[0].text if response.content else "I need a moment to think..."
            except Exception as e:
                print(f"❌ Claude chat failed: {e}")

        if self._openai:
            try:
                # Format messages for OpenAI
                full_messages = [{"role": "system", "content": system_prompt}]

                for msg in messages:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        full_messages.append({
                            "role": msg['role'],
                            "content": msg['content']
                        })

                response = self._openai.chat.completions.create(
                    model="gpt-4o",
                    messages=full_messages,
                    max_tokens=2048,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"❌ OpenAI chat failed: {e}")

        # Fallback to Gemini if available
        if self._gemini:
            try:
                # Combine messages for Gemini
                conversation = system_prompt + "\n\n"
                for msg in messages:
                    if isinstance(msg, dict):
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        conversation += f"{role.capitalize()}: {content}\n"
                conversation += "\nAssistant: "

                response = self._gemini.generate_content(conversation)
                return response.text if response.text else "Let me think about that..."
            except Exception as e:
                print(f"❌ Gemini chat failed: {e}")

        return "AI services are temporarily unavailable. Please try again in a moment."

    async def test_all_models(self) -> dict:
        """Test connectivity to all AI models"""
        results = {
            "claude": False,
            "gpt4": False,
            "gemini": False,
            "dalle": False
        }

        # Test Claude
        if self._anthropic:
            try:
                test = self._anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Say 'ok'"}]
                )
                results["claude"] = bool(test.content)
            except:
                pass

        # Test GPT-4
        if self._openai:
            try:
                test = self._openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Say 'ok'"}],
                    max_tokens=10
                )
                results["gpt4"] = bool(test.choices)
            except:
                pass

            # Test DALL-E
            try:
                test = self._openai.images.generate(
                    model="dall-e-2",
                    prompt="A simple red circle",
                    size="256x256",
                    n=1
                )
                results["dalle"] = bool(test.data)
            except:
                pass

        # Test Gemini
        if self._gemini:
            try:
                test = self._gemini.generate_content("Say 'ok'")
                results["gemini"] = bool(test.text)
            except:
                pass

        return results
