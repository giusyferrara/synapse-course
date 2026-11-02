"""Which language is the student writing in?

Shared by the mission tutor (app.py) and the course tutor
(web/course_handlers.py): both glue stored notes or pasted code onto the
student message, and both used to let the model guess the language from
the result. Measured on the live server, the same call three times came
back Italian, English, Italian.
"""
import re


# ---------------------------------------------------------------------------
# Which language is the student writing in?
#
# The mission tutor used to be told "reply in the student's own language" and
# left to work it out. Measured on the live server, the same call three times
# came back Italian, English, Italian: without a hard rule it is a coin toss,
# and a reader typing English got Italian back. So the server decides, and
# tells the model plainly.
#
# The most recent message that actually contains words wins. A pasted error or
# a bare "ok" carries no language, so we keep looking backwards; if nothing in
# the conversation carries one, we say nothing and leave the model be.
# ---------------------------------------------------------------------------
_IT_WORDS = set("che non hai sei per della come cosa quale gia perche sono anche piu "
                "devo voglio dove quindi questo questa mio mia con nel una uno del "
                "allora adesso fatto provato capito riesco riuscita".split())
_EN_WORDS = set("the you what that your have which does from this with when where "
                "should could would and but for not are was there here about into "
                "why how did doing done try tried".split())


def detect_student_language(texts):
    """Return 'English', 'Italian' or None, reading the newest text first."""
    import re as _lang_re
    for raw in reversed(texts or []):
        words = _lang_re.findall(r"[a-zA-Za-zàèéìòùÀÈÉÌÒÙ']+", (raw or "").lower())
        words = [w for w in words if len(w) > 1]
        if len(words) < 3:
            continue
        it = sum(1 for w in words if w in _IT_WORDS)
        en = sum(1 for w in words if w in _EN_WORDS)
        if it > en:
            return "Italian"
        if en > it:
            return "English"
    return None
