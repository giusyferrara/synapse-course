"""Safe text extraction from an AI provider's message response.

Current models run adaptive thinking, so `response.content[0]` is frequently a
thinking block with no `.text` attribute. Indexing position 0 raises
AttributeError and takes the tutor down. Always scan the blocks and keep the
text ones.
"""


def response_text(response, default=""):
    """Return the text blocks of a message response, joined and stripped.

    Falls back to `default` when the response carries no text block at all
    (empty content, or a refusal that produced only a stop_reason).
    """
    blocks = getattr(response, "content", None) or []
    text = "".join(
        b.text for b in blocks if getattr(b, "type", None) == "text"
    ).strip()
    return text or default
