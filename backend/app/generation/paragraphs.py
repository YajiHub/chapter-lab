import re


def split_paragraphs(notes: str) -> list[dict]:
    """Split notes on blank lines into numbered paragraphs with collapsed whitespace."""
    chunks = (" ".join(c.split()) for c in re.split(r"\n\s*\n", notes))
    return [{"id": i, "text": t} for i, t in enumerate((c for c in chunks if c), start=1)]
